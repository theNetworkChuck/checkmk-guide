#!/usr/bin/env python3
# Paperclip ticket
# (Line 2 above is the name Checkmk shows in the notification method list. Keep it on line 2.)
#
# WHAT IT DOES
#   A Checkmk notification script. When a notification rule fires, Checkmk runs this
#   file and hands it every fact about the alert as NOTIFY_* environment variables.
#   The script turns them into one ticket on a Paperclip board, assigned to one agent.
#   Recoveries and acknowledgements are ignored on purpose: they are not new tickets.
#
# WHAT TO CHANGE (the four lines below)
#   PAPERCLIP  address of your Paperclip server
#   COMPANY    your Paperclip company ID        (paperclipai company list)
#   ASSIGNEE   the agent ID that gets the ticket
#   KEY_FILE   a file holding a Paperclip board key on one line. ~ is the site user's
#              home, so this is /omd/sites/<site-name>/etc/paperclip.key
#   With no key file the script only PRINTS what it would send (a dry run).
#
# WHERE IT GOES
#   Checkmk server: ~/local/share/check_mk/notifications/paperclip_ticket.py (chmod +x)
#   Output of each run lands in ~/var/log/notify.log
import json, os, sys, urllib.request

# Where the ticket goes.
PAPERCLIP = "http://<paperclip-host>:3100"
COMPANY = "<your-company-id>"
ASSIGNEE = "<agent-id-that-gets-the-ticket>"
KEY_FILE = os.path.expanduser("~/etc/paperclip.key")  # a Paperclip board key, one line

# Checkmk hands us the whole alert as NOTIFY_* environment variables.
n = os.environ
if n["NOTIFY_NOTIFICATIONTYPE"] not in ("PROBLEM", "CUSTOM"):
    sys.exit(0)  # a recovery or an acknowledgement is not a new ticket
host = n["NOTIFY_HOSTNAME"]
if n["NOTIFY_WHAT"] == "SERVICE":
    what, state, output = f"{n['NOTIFY_SERVICEDESC']} on {host}", n["NOTIFY_SERVICESTATE"], n["NOTIFY_SERVICEOUTPUT"]
else:
    what, state, output = host, n["NOTIFY_HOSTSTATE"], n["NOTIFY_HOSTOUTPUT"]

ticket = {
    "title": f"Checkmk: {what} is {state}",
    "description": f"Checkmk says **{what}** ({n['NOTIFY_HOSTADDRESS']}) is **{state}**:\n\n"
                   f"```\n{output}\n```\n\nFind out why and fix it yourself. If the fix is restarting a stopped "
                   "service, just do it. Anything bigger (reboots, deleting things, config changes): ask on "
                   "this ticket first. Say what you found and what you did. Done means Checkmk shows it OK again.",
    "status": "todo",  # todo + an assignee = the agent wakes up and starts
    "priority": "high",
    "assigneeAgentId": ASSIGNEE,
}
url = f"{PAPERCLIP}/api/companies/{COMPANY}/issues"

if not os.path.exists(KEY_FILE):  # no key yet = dry run: print what we would send
    print("DRY RUN (no key file), would POST", url, json.dumps(ticket))
    sys.exit(0)

key = open(KEY_FILE).read().strip()
req = urllib.request.Request(url, json.dumps(ticket).encode(), method="POST",
                             headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
issue = json.load(urllib.request.urlopen(req, timeout=20))
print(("Already open: " if issue.get("deduplicated") else "Filed ") + issue["identifier"])
