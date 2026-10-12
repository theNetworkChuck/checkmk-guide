# 13. Send an alert to an AI agent as a ticket

**What you'll end up with:** when a chosen service goes critical, Checkmk files a ticket on a Paperclip board, assigned to an AI agent that investigates and fixes it. The video uses this for a stopped Hermes gateway, with an IT-department agent as the assignee.

Video: starts at 31:11.

## What you need first

- Chapter 12 done (notification rules). Chapter 11 is useful too, because the video alerts on a local check.
- A running Paperclip with a company and an agent that can take the ticket. See the [Paperclip companion guide](https://github.com/theNetworkChuck/paperclip-guide) for how to set that up.
- Your Paperclip **company ID** and the **agent ID** of the assignee. `paperclipai company list` shows the company ID.
- `sudo` on the Checkmk server.

How it works: Checkmk has no built-in "send to Paperclip" method, but it lets you drop your own script into a folder and use it as a notification method. When a rule fires, Checkmk runs the script and passes every fact about the alert as `NOTIFY_*` environment variables. The script turns them into a ticket through the Paperclip API. The script is in this repo: [`scripts/notifications/paperclip_ticket.py`](../scripts/notifications/paperclip_ticket.py).

> [!WARNING]
> Every alert that matches the rule becomes a ticket for an agent that may have access to your servers. Scope the rule narrowly, as in Step 4, and widen it on purpose later. Anything you let the agent do on its own, such as restarting a stopped service, is decided by the text in the script's ticket description. Read it and adjust it to your comfort level before you use it.

## Steps

### Step 1: Make a Paperclip board key

The script needs a credential to create tickets. On the Paperclip server:

```bash
paperclipai token board create --company-id <your-company-id> --name checkmk --ttl-days 30 --json
```

Copy the `token` value from the output. Treat it like a password. If your version of the command prints different options, run `paperclipai token board create --help`, and see [Paperclip's authentication docs](https://docs.paperclip.ing/api/authentication).

### Step 2: Put the key on the Checkmk server

Store it in a file owned by the site user, readable only by that user. After running the first command, paste the key, press Enter, then Ctrl-D:

```bash
sudo -u monitoring tee /omd/sites/monitoring/etc/paperclip.key >/dev/null
sudo -u monitoring chmod 600 /omd/sites/monitoring/etc/paperclip.key
```

### Step 3: Install the script

From a copy of this repo on the Checkmk server:

```bash
sudo install -o monitoring -g monitoring -m 755 scripts/notifications/paperclip_ticket.py \
  /omd/sites/monitoring/local/share/check_mk/notifications/paperclip_ticket.py
```

Now open the installed file:

```bash
sudo -u monitoring nano /omd/sites/monitoring/local/share/check_mk/notifications/paperclip_ticket.py
```

Change the first three lines to your own values. Leave `KEY_FILE` as it is, because it points at the file you made in Step 2 (`~` is the site user's home, `/omd/sites/monitoring`):

```python
PAPERCLIP = "http://<paperclip-host>:3100"
COMPANY = "<your-company-id>"
ASSIGNEE = "<agent-id-that-gets-the-ticket>"
KEY_FILE = os.path.expanduser("~/etc/paperclip.key")
```

Checkmk finds notification scripts in `~/local/share/check_mk/notifications/` if they are executable. The comment on the **second line** (`# Paperclip ticket`) is the name Checkmk shows in its menu.

Without the key file, the script only prints what it would send. That is a safe way to test.

### Step 4: Make the notification rule

1. **Setup** > **Events** > **Notifications** > **Add notification rule**.
2. **Triggering events:** leave the defaults and click **Next step**. The one that matters is any state to CRIT.
3. **Filter for hosts/services:** this is where you narrow it down. Under **Host filters** > **Hosts**, choose the one host. Under **Service filters** > **Services**, choose the one service (for example `Hermes gateway`). Click **Next step**.
4. **Notification method:** **Send notification**, method **Paperclip ticket**.
5. Next to **Select parameters** click **Create**. A parameter set is required even though this script has no settings. Give it a description such as `IT board` and save it. Click **Next step**.
6. **Recipient:** **Specific users**, then **cmkadmin**. One recipient means one ticket per alert.
7. **General properties:** description `Ticket to the IT department`. Review and **Save**.
8. **Changes** icon > **Activate pending changes**.

### Step 5: Trigger it

Make the service go critical. In the video, the Hermes gateway service on one agent was stopped. You can also send a test notification for a service that is already CRIT: open the service, open the **Commands** menu, click **Send custom notification**, add a comment, and send. The script accepts normal alerts and custom notifications.

### Step 6: Watch for the ticket

A ticket appears on your Paperclip board with a title like `Checkmk: <service> on <host> is CRITICAL`, priority high, assigned to your agent. The description contains the check's output and the instructions for the agent. A ticket created as `todo` with an assignee starts the agent on its own.

In the video, the agent restarted the stopped gateway, and the service in Checkmk went back to OK.

You can see what the script did in Checkmk's notification log, as the site user:

```bash
tail ~/var/log/notify.log
```

A successful run shows `Filed NET-...` (your ticket prefix will differ).

## What you should see

A new ticket per alert, with the alert's details inside. When the fix works, Checkmk shows the service as OK again and your Slack rule (chapter 12) posts the recovery. The ticket script ignores recoveries on purpose, so a recovery does not create a second ticket.

## If it doesn't work

| You see | Do |
|---|---|
| "Paperclip ticket" is missing from the method list | The script is not executable, is in the wrong folder, or its second line is not the `# Paperclip ticket` comment. |
| `notify.log` says "No rule matched" | The rule's host filter, service filter or recipient does not match the alert. |
| `DRY RUN (no key file)` in the log | The key file from Step 2 is missing or at a different path than `KEY_FILE`. |
| HTTP 401 or 403 from Paperclip | The key is wrong, expired (it was made with `--ttl-days 30`), or not a board key. Make a new one. |
| `Already open: ...` | Paperclip merges a new ticket into an open one with the same title from the last 48 hours. Close or cancel the old ticket to get a new one. |
| Connection refused or timeout | The Checkmk server cannot reach the `PAPERCLIP` address. Test it with `curl` from the Checkmk server. |
