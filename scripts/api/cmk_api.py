#!/usr/bin/env python3
"""A tiny Checkmk REST API helper: list hosts, add a host, run discovery, activate changes.

WHAT IT DOES
  Shows the four calls an AI agent (or you) needs to add things to Checkmk from a script:
    hosts                       list every host in Setup
    add-host NAME [--ip IP] [--folder /path] [--no-agent]
    discover HOST [HOST ...]    service discovery, accepting every new service
    pending                     how many changes are waiting to be activated
    activate                    activate all pending changes

WHAT TO CHANGE
  Nothing in the file. Set three environment variables:
    CMK_URL     the site address, e.g. http://<checkmk-server-ip>/<site-name>
    CMK_USER    the name of the automation user you created in Setup > Users
    CMK_SECRET  that user's automation secret (never paste it into code or chat logs)
  Optional: CMK_SITE (default: the last part of CMK_URL) is the site name that activate targets.

WHERE IT GOES
  Anywhere that can reach the Checkmk server over HTTP(S). Plain Python 3, no libraries.

NOTES
  * `activate` passes force_foreign_changes, so it also activates changes made in the GUI by
    other users. Remove that line if you want the API to touch only its own changes.
  * Based on calls that were run against a Checkmk 2.5.0p13 Community site. Docs:
    https://docs.checkmk.com/latest/en/rest_api.html
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

URL = os.environ.get("CMK_URL", "").rstrip("/")
USER = os.environ.get("CMK_USER", "")
SECRET = os.environ.get("CMK_SECRET", "")
SITE = os.environ.get("CMK_SITE") or URL.rsplit("/", 1)[-1]
BASE = f"{URL}/check_mk/api/1.0"


def call(method, path, body=None, headers=None):
    h = {"Authorization": f"Bearer {USER} {SECRET}", "Accept": "application/json", "Content-Type": "application/json"}
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, method=method, headers=h, data=data)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except ValueError:
            return e.code, {"detail": raw.decode(errors="replace")[:300]}


def need_ok(status, reply):
    if status >= 400:
        sys.exit(f"Checkmk answered {status}: {reply.get('title', '')} {reply.get('detail', '')}".strip())
    return reply


def main():
    if not (URL and USER and SECRET):
        sys.exit("Set CMK_URL, CMK_USER and CMK_SECRET first (see the header of this file).")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("hosts")
    a = sub.add_parser("add-host"); a.add_argument("name"); a.add_argument("--ip"); a.add_argument("--folder", default="/")
    a.add_argument("--no-agent", action="store_true", help="host has no Checkmk agent (API integrations / SNMP only)")
    d = sub.add_parser("discover"); d.add_argument("hosts", nargs="+")
    sub.add_parser("pending")
    sub.add_parser("activate")
    args = ap.parse_args()

    if args.cmd == "hosts":
        r = need_ok(*call("GET", "/domain-types/host_config/collections/all"))
        for h in r["value"]:
            print(h["id"], h["extensions"]["attributes"].get("ipaddress", ""))
    elif args.cmd == "add-host":
        attrs = {}
        if args.ip: attrs["ipaddress"] = args.ip
        if args.no_agent: attrs["tag_agent"] = "no-agent"
        need_ok(*call("POST", "/domain-types/host_config/collections/all",
                      {"host_name": args.name, "folder": args.folder, "attributes": attrs}))
        print(f"added {args.name} (not active until you run: activate)")
    elif args.cmd == "discover":
        r = need_ok(*call("POST", "/domain-types/discovery_run/actions/bulk-discovery-start/invoke", {
            "hostnames": args.hosts, "do_full_scan": True, "bulk_size": 10, "ignore_errors": True,
            "options": {"monitor_undecided_services": True, "remove_vanished_services": False,
                        "update_service_labels": True, "update_service_parameters": False,
                        "update_host_labels": True}}))
        job = r.get("id")
        for _ in range(200):  # wait for the background job to finish
            s, j = call("GET", f"/objects/background_job/{job}")
            if j.get("extensions", {}).get("active") is False:
                break
            time.sleep(3)
        print("discovery finished for", ", ".join(args.hosts))
    elif args.cmd == "pending":
        r = need_ok(*call("GET", "/domain-types/activation_run/collections/pending_changes"))
        print(len(r.get("value", [])), "pending change(s)")
    elif args.cmd == "activate":
        r = need_ok(*call("POST", "/domain-types/activation_run/actions/activate-changes/invoke",
                          {"redirect": False, "sites": [SITE], "force_foreign_changes": True}, {"If-Match": "*"}))
        run = r.get("id")
        for _ in range(60):
            s, j = call("GET", f"/objects/activation_run/{run}")
            if not j.get("extensions", {}).get("is_running"):
                break
            time.sleep(2)
        print("activation finished")


main()
