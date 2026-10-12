# Scripts

Each file starts with a header that says what it does and what to change. Nothing in this folder contains a password, token or address from a real network. Every value you must set is a `<placeholder>` or an environment variable.

| File | Runs on | Install path | Chapter |
|---|---|---|---|
| `check_plex.py` | Checkmk server | `~/local/lib/nagios/plugins/` (as the site user), `chmod +x` | [10](../guide/10-build-your-own-checks-with-ai.md) |
| `check_homeassistant.py` | Checkmk server | `~/local/lib/nagios/plugins/`, `chmod +x` | [10](../guide/10-build-your-own-checks-with-ai.md) |
| `local/hermes_agent` | monitored Linux host | `/usr/lib/check_mk_agent/local/`, `chmod 755` | [11](../guide/11-local-checks.md) |
| `notifications/paperclip_ticket.py` | Checkmk server | `~/local/share/check_mk/notifications/`, `chmod +x` | [13](../guide/13-alert-to-ai-ticket.md) |
| `api/cmk_api.py` | anywhere that can reach Checkmk | wherever you like | [14](../guide/14-automation-user-rest-api.md) |

All of them are plain Python 3 (the standard library only), so there is nothing to install.

## Secrets

- The Plex and Home Assistant checks read their token from a file you point them at (`--token-file`). Keep that file readable by the Checkmk site user only (`chmod 600`).
- The ticket script reads a Paperclip board key from a file (`~/etc/paperclip.key` for the site user).
- `cmk_api.py` reads `CMK_URL`, `CMK_USER` and `CMK_SECRET` from the environment.

## Test them

The Plex, Home Assistant, ticket and API scripts were run against stand-in servers with sample data. `hermes_agent` was run on a machine with a Hermes agent. Run each script once by hand before you wire it into Checkmk, as the chapters show.
