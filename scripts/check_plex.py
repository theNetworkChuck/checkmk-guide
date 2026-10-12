#!/usr/bin/env python3
"""Checkmk active check for a Plex Media Server, using Plex's own API.

WHAT IT DOES
  Asks Plex for its version, who is streaming right now, how many streams are
  transcoding, and how many items each library holds. Prints ONE Nagios-style line
  (STATE - text | metrics) and exits 0 (OK), 1 (WARN), 2 (CRIT) or 3 (UNKNOWN).

WHAT TO CHANGE
  Nothing in the file. Pass your own values on the command line:
    check_plex.py --host <plex-server-ip> [--port 32400] \
                  --token-file /omd/sites/<site-name>/etc/plex.token \
                  [--warn-streams N] [--crit-streams N]
  The token file holds your Plex token on one line. Keep it readable by the Checkmk
  site user only (chmod 600). Never put the token on the command line.

WHERE IT GOES
  Checkmk server, as the site user: ~/local/lib/nagios/plugins/check_plex.py (chmod +x).
  Then wire it in with the "Integrate Nagios plug-ins" rule (guide chapter 10).
"""
import argparse, json, re, sys, urllib.error, urllib.request

def get(base, path, token):
    req = urllib.request.Request(f"{base}{path}", headers={"Accept": "application/json", "X-Plex-Token": token})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True); ap.add_argument("--port", type=int, default=32400)
    ap.add_argument("--token-file", required=True)
    ap.add_argument("--warn-streams", type=int); ap.add_argument("--crit-streams", type=int)
    a = ap.parse_args()
    try:
        token = open(a.token_file).read().strip()
    except OSError as e:
        print(f"UNKNOWN - cannot read token file {a.token_file}: {e.strerror}"); sys.exit(3)
    base = f"http://{a.host}:{a.port}"
    try:
        ident = get(base, "/identity", token)["MediaContainer"]
        sess = get(base, "/status/sessions", token)["MediaContainer"]
        libs = get(base, "/library/sections", token)["MediaContainer"].get("Directory", []) or []
    except urllib.error.HTTPError as e:
        print(f"CRIT - Plex API answered {e.code} on {base} (bad token?)"); sys.exit(2)
    except Exception as e:
        print(f"CRIT - Plex unreachable at {base}: {e}"); sys.exit(2)
    meta = sess.get("Metadata", []) or []
    streams = len(meta)
    transcoding = sum(1 for m in meta if "TranscodeSession" in m)
    who = "; ".join(f"{m.get('User', {}).get('title', '?')} watching {m.get('grandparentTitle') or m.get('title', '?')}" for m in meta)
    counts = {}
    for d in libs:
        try:
            c = get(base, f"/library/sections/{d['key']}/all?X-Plex-Container-Start=0&X-Plex-Container-Size=0", token)["MediaContainer"]
            counts[d["title"]] = int(c.get("totalSize", c.get("size", 0)))
        except Exception:
            counts[d["title"]] = -1
    state = 0
    if a.crit_streams is not None and streams >= a.crit_streams: state = 2
    elif a.warn_streams is not None and streams >= a.warn_streams: state = 1
    perf = [f"streams={streams}", f"transcoding={transcoding}"]
    perf += [f"lib_{re.sub(r'[^A-Za-z0-9]+', '_', k)}={v}" for k, v in counts.items() if v >= 0]
    libtxt = ", ".join(f"{k} {v}" for k, v in counts.items())
    label = ["OK", "WARN", "CRIT"][state]
    print(f"{label} - Plex {ident.get('version', '?')}: {streams} stream(s), {transcoding} transcoding{(' (' + who + ')') if who else ''}; libraries: {libtxt} | " + " ".join(perf))
    sys.exit(state)

main()
