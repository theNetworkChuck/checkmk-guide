Get Checkmk: https://checkmk.io/networkchuck

# Monitor everything in your homelab with Checkmk

**The companion guide to the NetworkChuck video "You can monitor EVERYTHING in your homelab with this".**

Disclosure: the video is sponsored by Checkmk.

Watch the video: [You can monitor EVERYTHING in your homelab with this](https://www.youtube.com/watch?v=Bjifz55TTPI)

This guide repeats every step of the video, one chapter at a time, with the exact commands and clicks. Follow it in order the first time. Each chapter ends with a fix-it table.

## The path

The timestamp is where that part starts in the video. The first minute (00:00 to 00:53) is the introduction and has no steps.

| # | Chapter | Starts at | What you'll do |
|---|---------|-----------|----------------|
| 1 | [Install Checkmk](guide/01-install-checkmk.md) | 00:53 | Install Checkmk Community on Ubuntu 24.04, create a site, log in |
| 2 | [Add your first Linux host](guide/02-first-linux-host.md) | 03:00 | Install the agent, open port 6556, test the connection, run service discovery, activate changes |
| 3 | [Scan your network with SNMP](guide/03-network-scan-snmp.md) | 07:16 | Turn on SNMP on a switch, scan an IP range in a folder, switch the found devices on, discover |
| 4 | [Monitor Docker and every container](guide/04-docker.md) | 10:49 | Docker agent plugin, a piggyback folder, import containers from a CSV |
| 5 | [Monitor Proxmox VE and every VM](guide/05-proxmox.md) | 16:47 | Make a read-only Proxmox user, add the Proxmox special agent rule, match VM names |
| 6 | [Monitor a website](guide/06-websites.md) | 20:24 | The "Check HTTP web service" rule with an expected string |
| 7 | [Monitor a Windows PC](guide/07-windows.md) | 22:15 | The MSI agent, a firewall rule, restart the agent service |
| 8 | [Ceph and SMART plugins](guide/08-ceph-and-smart.md) | 23:55 | Add the Ceph and SMART agent plugins for cluster and disk health |
| 9 | [Install a package from the Checkmk Exchange](guide/09-exchange-packages.md) | 25:27 | UniFi example: `mkp add`, `mkp enable`, the rule, piggyback hosts |
| 10 | [Build your own checks with AI](guide/10-build-your-own-checks-with-ai.md) | 27:18 | Plex and Home Assistant checks wired in with "Integrate Nagios plug-ins" |
| 11 | [Local checks](guide/11-local-checks.md) | 28:56 | A script on the monitored server prints one line per service |
| 12 | [Alerts in Slack](guide/12-slack-alerts.md) | 30:08 | A webhook and a notification rule |
| 13 | [Send an alert to an AI agent as a ticket](guide/13-alert-to-ai-ticket.md) | 31:11 | A custom notification script that files a Paperclip ticket |
| 14 | [Give an AI agent the keys](guide/14-automation-user-rest-api.md) | 32:23 | An automation user and the REST API |

## Take-home files

Sanitized, working copies of the custom pieces from the video. Read the header of each file before you use it.

| File | What it's for |
|------|---------------|
| [`scripts/check_plex.py`](scripts/check_plex.py) | Plex check: version, who is streaming, transcodes, library sizes (chapter 10) |
| [`scripts/check_homeassistant.py`](scripts/check_homeassistant.py) | Home Assistant check: entities, unavailable devices, cameras down; `--house` for lights, air quality, motion (chapter 10) |
| [`scripts/local/hermes_agent`](scripts/local/hermes_agent) | Local check for a Hermes AI agent: gateway, replies, crons (chapter 11) |
| [`scripts/notifications/paperclip_ticket.py`](scripts/notifications/paperclip_ticket.py) | Notification script that turns a Checkmk alert into a Paperclip ticket (chapter 13) |
| [`scripts/api/cmk_api.py`](scripts/api/cmk_api.py) | Small REST API helper: list hosts, add a host, discover, activate (chapter 14) |

See [`scripts/README.md`](scripts/README.md) for what to change in each.

## Before you start

- **A Linux machine or VM running Ubuntu 24.04** for the Checkmk server. Place it where it can reach the things you want to monitor.
- **Things to monitor.** Each chapter lists what it needs: a Linux server, a switch with SNMP, a Docker host, Proxmox, a website, a Windows PC, and so on. Do only the chapters that match what you have.
- **Optional:** an AI coding agent, for chapters 10, 13 and 14.

> [!NOTE]
> The video runs **Checkmk Community 2.5.0p13**, which is what the commands in this guide were checked against, together with the [Checkmk 2.5 documentation](https://docs.checkmk.com/latest/en/). Checkmk releases patch versions often, so file names in the download commands may show a newer number. If a screen differs from this guide, the official documentation wins.

## About the editions

This guide uses **Checkmk Community**, the free, open source edition. Some things need manual setup in Community, for example creating a host for each Docker container or Proxmox VM yourself. Checkmk also has commercial editions: **Pro**, **Ultimate**, **Ultimate with multi-tenancy (MT)** and **Cloud** (the SaaS platform). Compare them at [checkmk.com/pricing](https://checkmk.com/pricing).

Checkmk offers a free trial of Checkmk Ultimate. As described in the video, the trial covers up to 750 services on one site. Check the pricing page for the current terms.

## Links

- Get Checkmk: [checkmk.io/networkchuck](https://checkmk.io/networkchuck)
- Checkmk documentation: [docs.checkmk.com](https://docs.checkmk.com/latest/en/)
- Checkmk Exchange (community extensions): [exchange.checkmk.com](https://exchange.checkmk.com)
- Proxmox user management: [pve.proxmox.com/wiki/User_Management](https://pve.proxmox.com/wiki/User_Management)
- Companion guide for the Paperclip video (used in chapter 13): [theNetworkChuck/paperclip-guide](https://github.com/theNetworkChuck/paperclip-guide)

## License

This guide and its scripts are [MIT licensed](LICENSE). Checkmk is a separate product by Checkmk GmbH and has its own licenses.
