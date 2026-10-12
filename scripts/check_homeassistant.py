#!/usr/bin/env python3
"""Checkmk active check for Home Assistant, using its REST API.

WHAT IT DOES
  Health mode (default): Home Assistant version and state, entity totals, how many
  entities are unavailable, how many cameras are down, and the worst domains.
  House mode (--house): lights on, worst air-quality reading per kind, and motion
  events in the last N minutes. Prints ONE Nagios-style line and exits 0/1/2/3.

WHAT TO CHANGE
  Nothing in the file. Pass your own values on the command line. The token file holds
  a Home Assistant long-lived access token on one line (chmod 600, site user only).
  Entities that are "unknown" by design (buttons, scenes) are not counted as dead
  unless you pass --count-unknown.

WHERE IT GOES
  Checkmk server, as the site user: ~/local/lib/nagios/plugins/check_homeassistant.py
  (chmod +x), wired in with the "Integrate Nagios plug-ins" rule (guide chapter 10).

USAGE
Health:  check_homeassistant.py --url http://<home-assistant-ip>:8123 --token-file /omd/sites/<site-name>/etc/ha.token [--warn-cameras 1] [--crit-cameras N] [--count-unknown]
         HA version + state, entity totals, how many are unavailable (and unknown), cameras down, the worst domains.
House:   check_homeassistant.py --house --url ... --token-file ... [--motion-window 60] [--co2-warn 1000 --co2-crit 2000] [--pm25-warn 35 --pm25-crit 55]
         Lights on, air quality (worst sensor per kind), motion events in the last N minutes and the busiest room."""
import argparse, json, sys, urllib.error, urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# device_class -> (metric name, label, unit shown in the text)
AIR = {"carbon_dioxide": ("co2_ppm", "CO2", "ppm"), "pm25": ("pm25", "PM2.5", "ug/m3"),
       "pm10": ("pm10", "PM10", "ug/m3"), "volatile_organic_compounds_parts": ("voc_ppb", "VOC", "ppb")}

def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

def health(base, token, a):
    cfg = get(base + "/api/config", token); states = get(base + "/api/states", token)
    dead = {"unavailable"} | ({"unknown"} if a.count_unknown else set())
    total = len(states)
    unavailable = sum(1 for s in states if s["state"] == "unavailable")
    unknown = sum(1 for s in states if s["state"] == "unknown")
    per_domain = Counter(s["entity_id"].split(".")[0] for s in states if s["state"] in dead)
    cams = [s for s in states if s["entity_id"].startswith("camera.")]
    cams_dead = [s for s in cams if s["state"] == "unavailable"]
    state = 0
    if a.crit_cameras is not None and len(cams_dead) >= a.crit_cameras: state = 2
    elif len(cams_dead) >= a.warn_cameras: state = 1
    if cfg.get("state") != "RUNNING": state = 2
    names = [s["entity_id"].split(".", 1)[1] for s in cams_dead]
    shown = ", ".join(names[:6]) + (f" +{len(names) - 6} more" if len(names) > 6 else "")
    top = ", ".join(f"{d} {n}" for d, n in per_domain.most_common(5))
    perf = f"entities={total} unavailable={unavailable} unknown={unknown} cameras={len(cams)} cameras_unavailable={len(cams_dead)}"
    return state, f"Home Assistant {cfg.get('version', '?')} {cfg.get('state', '?')}: {total} entities, {unavailable} unavailable, {unknown} unknown; cameras {len(cams_dead)} of {len(cams)} unavailable ({shown or 'none'}); dead by domain: {top or 'none'} | {perf}"

def house(base, token, a):
    states = get(base + "/api/states", token)
    # Lights: light groups carry their members in an entity_id attribute, so skip them or every bulb counts twice
    lights = [s for s in states if s["entity_id"].startswith("light.") and "entity_id" not in s["attributes"]]
    lights_on = sum(1 for s in lights if s["state"] == "on")
    # Air: the worst reading of each kind across every sensor that reports it
    air = {}
    for s in states:
        kind = AIR.get(s["attributes"].get("device_class"))
        if kind and s["entity_id"].startswith("sensor."):
            try: v = float(s["state"])
            except ValueError: continue
            air[kind] = max(v, air.get(kind, v))
    # Motion: "on" events per room in the window; a room seen by two integrations counts once (the max, not the sum)
    room = {s["entity_id"]: s["attributes"].get("friendly_name", s["entity_id"]).replace(" Motion", "")
            for s in states if s["entity_id"].startswith("binary_sensor.") and s["attributes"].get("device_class") == "motion"}
    per_room = {}
    motion_ok = True
    if room:
        start = quote((datetime.now(timezone.utc) - timedelta(minutes=a.motion_window)).isoformat())
        try:
            hist = get(f"{base}/api/history/period/{start}?filter_entity_id={','.join(room)}&minimal_response&no_attributes", token)
        except Exception:
            hist, motion_ok = [], False
        for series in hist:
            if not series: continue
            r = room.get(series[0].get("entity_id"), "?")
            n = sum(1 for h in series[1:] if h.get("state") == "on")   # series[0] is the state at window start, not an event
            per_room[r] = max(n, per_room.get(r, 0))
    events = sum(per_room.values())

    state, air_txt, perf = 0, [], [f"lights_on={lights_on}", f"lights={len(lights)}"]
    limits = {"co2_ppm": (a.co2_warn, a.co2_crit), "pm25": (a.pm25_warn, a.pm25_crit)}
    for (metric, label, unit), v in air.items():
        w, c = limits.get(metric, (None, None))
        mark = ""
        if c is not None and v >= c: state, mark = 2, " (!!)"
        elif w is not None and v >= w: state, mark = max(state, 1), " (!)"
        air_txt.append(f"{label} {v:g} {unit}{mark}")
        perf.append(f"{metric}={v:g}" + (f";{w};{c}" if w is not None else ""))
    if motion_ok:
        busiest = max(per_room.items(), key=lambda kv: kv[1]) if events else None
        motion_txt = f"{events} motion events in the last {a.motion_window} min" + (f", busiest: {busiest[0]} {busiest[1]}" if busiest else "")
        perf.append(f"motion_events={events}")
    else:
        motion_txt = "motion history unavailable"
    return state, f"House: {lights_on} of {len(lights)} lights on; air: {', '.join(air_txt) or 'no sensors'}; {motion_txt} | " + " ".join(perf)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True); ap.add_argument("--token-file", required=True)
    ap.add_argument("--house", action="store_true", help="lights, air quality and motion instead of the health check")
    ap.add_argument("--warn-cameras", type=int, default=1); ap.add_argument("--crit-cameras", type=int)
    ap.add_argument("--count-unknown", action="store_true", help="treat 'unknown' as dead too (buttons/scenes sit at unknown by design)")
    ap.add_argument("--motion-window", type=int, default=60, help="minutes of motion history to count")
    ap.add_argument("--co2-warn", type=float, default=1000); ap.add_argument("--co2-crit", type=float, default=2000)
    ap.add_argument("--pm25-warn", type=float, default=35); ap.add_argument("--pm25-crit", type=float, default=55)
    a = ap.parse_args()
    try:
        token = open(a.token_file).read().strip()
    except OSError as e:
        print(f"UNKNOWN - cannot read token file {a.token_file}: {e.strerror}"); sys.exit(3)
    base = a.url.rstrip("/")
    try:
        state, text = (house if a.house else health)(base, token, a)
    except urllib.error.HTTPError as e:
        print(f"CRIT - Home Assistant API answered {e.code} (bad token?)"); sys.exit(2)
    except Exception as e:
        print(f"CRIT - Home Assistant unreachable at {base}: {e}"); sys.exit(2)
    print(f"{['OK', 'WARN', 'CRIT'][state]} - {text}")
    sys.exit(state)

main()
