# 11. Local checks: monitor anything a script can print

**What you'll end up with:** your own services in Checkmk, produced by a script that runs on the monitored server and is picked up by the agent. The example is a set of checks for a Hermes AI agent.

Video: starts at 28:56.

## What you need first

- Chapter 2 done. The server runs the Checkmk agent and is already a host in Checkmk.
- `sudo` on that server.
- Any scripting language the server has (shell, Python, anything).

How it works: the Checkmk agent runs every file in a special folder each time it is polled. Every line a script prints becomes **one service** in Checkmk. This is different from the active checks in chapter 10: here the script runs **on the monitored server**, not on the Checkmk server.

## The one line format

Each line has four parts, separated by spaces:

```
0 "My service" myvalue=73 My output text which may contain spaces
```

| Part | Meaning |
|---|---|
| `0` | State: `0` OK, `1` WARN, `2` CRIT, `3` UNKNOWN. Use `P` to let Checkmk compute the state from thresholds. |
| `"My service"` | The service name, in double quotes. Must be unique on the host. |
| `myvalue=73` | A metric (`name=value`, optional `;warn;crit` thresholds). Write `-` for none. Several metrics are separated with `\|`. |
| `My output text...` | The text shown in Checkmk. |

One script can print many lines, and each line becomes its own service.

## Steps

### Step 1: Try the smallest possible check

On the monitored server:

```bash
sudo tee /usr/lib/check_mk_agent/local/mylocalcheck >/dev/null <<'EOF'
#!/bin/bash
echo "0 \"My first service\" - This static service is always OK"
EOF
sudo chmod +x /usr/lib/check_mk_agent/local/mylocalcheck
sudo /usr/lib/check_mk_agent/local/mylocalcheck
```

You should see the line printed back:

```
0 "My first service" - This static service is always OK
```

### Step 2: Add it to Checkmk

1. **Setup** > **Hosts** > **Hosts**, click the host.
2. **Save & run service discovery**, then **Rescan**.
3. Click **Monitor undecided services** (or **Accept all**).
4. **Changes** icon > **Activate pending changes**.

The new service **My first service** appears on the host. Any local check you add later shows up the same way: put the script in place, rescan, accept, activate.

### Step 3: Install the Hermes agent check

The script in this repo's [`scripts/local/`](../scripts/local) folder checks a [Hermes](https://www.youtube.com/watch?v=QQEgIo4Juxg) AI agent. Use it as a real example, or as a starting point for a check of your own.

`hermes_agent` prints three services every time the agent is polled.

The video also shows "Hermes model login" and "Hermes usage" services. They are custom checks built the same way as `hermes_agent` and are not included here because they depend on a provider's undocumented endpoint.

```bash
sudo install -m 0755 scripts/local/hermes_agent /usr/lib/check_mk_agent/local/hermes_agent
```

Checks that are slow or call an outside service can go in a folder named for a number of seconds, for example `/usr/lib/check_mk_agent/local/300/`. The agent then runs the scripts inside only that often and caches the result.

Run it by hand:

```bash
sudo /usr/lib/check_mk_agent/local/hermes_agent
```

`hermes_agent` should print three lines:

```
0 "Hermes gateway" uptime_min=... Running, up ... min, heartbeat ...s ago
P "Hermes replies" hours_since_reply=...;24;48|replies_24h=... Last answer ... min ago, ... replies in 24 h
0 "Hermes crons" enabled=...|failing=0 All ... scheduled jobs OK, scheduler ticked ...s ago
```

Read the comments at the top of the script. They explain what it reads and what to change.

### Step 4: Add the services to Checkmk

Do Step 2 again for the Hermes host. You get these services:

- **Hermes gateway**: running, and its heartbeat is fresh.
- **Hermes replies**: when the agent last answered, and how many answers in 24 hours.
- **Hermes crons**: the scheduler is ticking and no job is failing.

### Step 5: Use the pattern for your own checks

Copy `mylocalcheck`, change the echo line, and anything you can script becomes a service. The state decides the color. Metrics become graphs. Whatever you can measure with a script, Checkmk can watch.

## What you should see

Your own services on the host, alongside the built-in ones, with graphs for any metrics you printed.

## If it doesn't work

| You see | Do |
|---|---|
| The service does not appear after a rescan | Run the script by hand. The line must have the four parts, with the service name in double quotes. Make sure the file is executable and in the right folder. |
| A service shows UNKNOWN | The script printed a state of `3`, or the line could not be read. |
| The same service name appears twice | Service names must be unique on a host. Rename one. |
| A cached check (in a numbered folder) shows old data | That is by design. It refreshes every N seconds. |
| Special characters in the service name vanish | The Community edition's core removes `` ` ; ~ ! $ % ^ & * \| \ ' " < > ? , ( ) = `` from service names. Avoid them. |

More in [Checkmk's article on local checks](https://docs.checkmk.com/latest/en/localchecks.html).
