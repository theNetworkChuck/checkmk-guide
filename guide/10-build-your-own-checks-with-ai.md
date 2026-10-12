# 10. Build your own checks with AI (Plex and Home Assistant)

**What you'll end up with:** a custom check for something Checkmk has no built-in support for. The examples are a Plex server (who is streaming, library sizes) and Home Assistant (unavailable entities, cameras down). The same method works for anything with an API.

Video: starts at 27:18.

## What you need first

- Chapter 1 done.
- `sudo` on the Checkmk server.
- The thing to monitor, and its API token:
  - **Plex:** a Plex token. See Plex's article [Finding an authentication token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/).
  - **Home Assistant:** a long-lived access token. In Home Assistant open your profile (your name, bottom left), go to **Security**, scroll to **Long-lived access tokens** and click **Create token**. See [Home Assistant's authentication docs](https://www.home-assistant.io/docs/authentication/#your-account-profile).
- Either an AI coding agent you trust with access to the Checkmk server, **or** the ready-made scripts in this repo's [`scripts/`](../scripts) folder (`check_plex.py` and `check_homeassistant.py`). The scripts are plain Python 3 with no extra libraries.

How it works: this is an **active check**. The script runs on the Checkmk server. It asks the API, prints one line such as `OK - Plex 1.43.3: 1 stream(s) ...`, and exits with `0` (OK), `1` (WARN), `2` (CRIT) or `3` (UNKNOWN). Nothing runs on Plex or Home Assistant. Checkmk turns that into a service.

## Steps

### Step 1: Store the token where only the site can read it

Keep the token in a file that only the Checkmk site user can read. Do not put it on a command line. Run on the Checkmk server:

```bash
sudo -u monitoring tee /omd/sites/monitoring/etc/plex.token >/dev/null
```

Paste the token, press Enter, then press Ctrl-D. Then lock the file down:

```bash
sudo -u monitoring chmod 600 /omd/sites/monitoring/etc/plex.token
```

For Home Assistant, do the same with `/omd/sites/monitoring/etc/ha.token`.

### Step 2: Get the script

**Option A: ask your AI agent to write it.** Tell it what you want to see, where the token file is, and where to put the script. For example:

> Write me a Checkmk active check for my Plex server at `<plex-server-ip>`. I want the Plex version, how many streams are active and who is watching, how many are transcoding, and the item count per library. The token is in `/omd/sites/monitoring/etc/plex.token`; read it from that file and never print it. The script must print one Nagios-style status line with metrics and exit 0, 1, 2 or 3. Put it in `/omd/sites/monitoring/local/lib/nagios/plugins/`, make it executable, and run it once so I can see the output.

**Option B: use the scripts from this repo.** From a copy of this repo on the Checkmk server:

```bash
sudo install -o monitoring -g monitoring -m 755 scripts/check_plex.py /omd/sites/monitoring/local/lib/nagios/plugins/check_plex.py
sudo install -o monitoring -g monitoring -m 755 scripts/check_homeassistant.py /omd/sites/monitoring/local/lib/nagios/plugins/check_homeassistant.py
```

Checkmk looks for check programs in the site's `local/lib/nagios/plugins` folder.

### Step 3: Run the script once by hand

```bash
sudo -u monitoring /omd/sites/monitoring/local/lib/nagios/plugins/check_plex.py \
  --host <plex-server-ip> --token-file /omd/sites/monitoring/etc/plex.token
```

You should see one line like:

```
OK - Plex 1.43.3: 1 stream(s), 0 transcoding (someone watching Some Show); libraries: Movies 64, TV Shows 6 | streams=1 transcoding=0 lib_Movies=64 lib_TV_Shows=6
```

For Home Assistant:

```bash
sudo -u monitoring /omd/sites/monitoring/local/lib/nagios/plugins/check_homeassistant.py \
  --url http://<home-assistant-ip>:8123 --token-file /omd/sites/monitoring/etc/ha.token
```

You should see a line starting with `OK`, `WARN` or `CRIT` that names the Home Assistant version, the number of entities, how many are unavailable and how many cameras are down. Add `--house` to get lights on, air quality and motion events instead.

If the line does not look right, fix the script first. Checkmk shows exactly what the script prints.

### Step 4: Add a host for the thing you monitor

1. **Setup** > **Hosts** > **Hosts** > **Add host**.
2. **Host name:** `plex` (or `homeassistant`).
3. **IPv4 address:** its IP address.
4. **Monitoring agents** box > **Checkmk agent / API integrations:** **No API integrations, no Checkmk agent**.
5. Click **Save & view folder**.

### Step 5: Add the rule that runs the script

1. Click **Setup** and type `Integrate Nagios` in the search box.
2. Open **Integrate Nagios plug-ins** (under **Services** > **Other services**) and click **Add rule**.
3. **Service name:** `Plex`.
4. **Command line:** the script name and its arguments. A bare script name is looked up in the site's `local/lib/nagios/plugins` folder:

```
check_plex.py --host <plex-server-ip> --token-file /omd/sites/monitoring/etc/plex.token
```

5. In **Conditions**, tick **Explicit hosts** and pick the `plex` host.
6. Click **Save**.
7. **Changes** icon > **Activate pending changes**.

Repeat for Home Assistant, with service name `Home Assistant` and:

```
check_homeassistant.py --url http://<home-assistant-ip>:8123 --token-file /omd/sites/monitoring/etc/ha.token
```

### Step 6: Look at it

**Monitor** > **All hosts** > `plex`. The **Plex** service shows the line your script printed, and Checkmk draws graphs from the numbers after the `|` (streams, transcodes, items per library). Start a video and watch the stream count change within a minute or two.

## What you should see

A new service per rule, with the script's text as its summary. WARN or CRIT when the script says so. For Home Assistant you may find problems its own interface never shows, such as cameras that have been unavailable for a while.

## If it doesn't work

| You see | Do |
|---|---|
| `UNKNOWN - cannot read token file` | The token file is missing, or the site user cannot read it (Step 1). It must be owned by `monitoring` and mode `600`. |
| `CRIT - Plex API answered 401` (or the Home Assistant version) | The token is wrong or was revoked. |
| `CRIT - ... unreachable` | The Checkmk server cannot reach that address and port. Test with `curl` from the Checkmk server. |
| The service never appears | Check the rule's **Explicit hosts** condition and that you activated the changes. |
| The command is "not found" | The script must be in `~/local/lib/nagios/plugins/`, owned by the site user, and executable. |
| You cannot find the rule | Its name is **Integrate Nagios plug-ins**, found with the Setup search. The rule needs the permission "Can add or modify executables", which administrators have. |

More background in [Checkmk's article on active checks](https://docs.checkmk.com/latest/en/active_checks.html).
