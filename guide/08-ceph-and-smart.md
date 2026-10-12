# 8. Add the Ceph and SMART plugins

**What you'll end up with:** Ceph cluster health and pool usage, and the SMART health and temperature of every disk, monitored on a Linux server.

Video: starts at 23:57.

## What you need first

- Chapter 2 done. The server is already a host in Checkmk with the agent installed.
- **For Ceph:** a Ceph node (or any machine that can run `ceph` commands) with a working `/etc/ceph/ceph.conf` and the admin keyring, and Python 3 with the **`rados`** library. On most distributions that is the `python3-rados` package from your Ceph repository.
- **For SMART:** the `smartmontools` package, **version 7 or newer** (it provides `smartctl`), and `root` on the server.

How it works: Checkmk's default checks do not cover everything. Some checks come from **agent plugins**, which are extra scripts the agent runs. Both plugins here ship with Checkmk 2.5 Community. You copy them onto the server you want to watch, the same way as the Docker plugin in chapter 4.

## Part A: SMART disk health

### Step 1: Install smartmontools

Debian or Ubuntu:

```bash
sudo apt install smartmontools
```

Rocky, RHEL and similar:

```bash
sudo dnf install -y smartmontools
smartctl -V
```

`smartctl -V` should print a version starting with `smartctl 7` or higher.

### Step 2: Install the plugin

The plugin is called `smart_posix`. Download it from your Checkmk server into the agent's plugin folder:

```bash
sudo curl -o /usr/lib/check_mk_agent/plugins/smart_posix http://<checkmk-server-ip>/monitoring/check_mk/agents/plugins/smart_posix
sudo chmod +x /usr/lib/check_mk_agent/plugins/smart_posix
```

(In the Checkmk interface the same file is under **Setup** > **Agents** > **Linux**, in the **Plugins** box.)

### Step 3: Test it on the server

```bash
sudo /usr/lib/check_mk_agent/plugins/smart_posix | head -n 5
```

You should see a section header `<<<smart_posix_all:sep(0)>>>` followed by JSON from `smartctl`. If it prints `ERROR: smartctl not found` or `smartctl version 7 or newer is required`, go back to Step 1.

## Part B: Ceph

### Step 4: Copy the Ceph plugin from the Checkmk server

Unlike the plugins above, the Ceph plugin is **not** offered on the Checkmk agents download page. It lives inside the Checkmk installation. Copy it from the Checkmk server to the Ceph node. Run this on the **Checkmk server** (use any account that can log in to the Ceph node):

```bash
scp /omd/sites/monitoring/lib/python3/cmk/plugins/ceph/agents/mk_ceph.py <your-user>@<ceph-node-ip>:/tmp/mk_ceph.py
```

Then on the **Ceph node**, put it in the agent's plugin folder and make it executable:

```bash
sudo install -m 0755 /tmp/mk_ceph.py /usr/lib/check_mk_agent/plugins/mk_ceph.py
```

### Step 5: Test it on the Ceph node

```bash
sudo /usr/lib/check_mk_agent/plugins/mk_ceph.py | head -n 5
```

You should see section headers starting with `<<<cephstatus:sep(0)>>>` followed by JSON about the cluster. If you see a JSON line with `deployment_error` saying `mk_ceph requires the library 'rados'`, install the `python3-rados` package for the Python that runs the plugin.

If your Ceph configuration or client name differ from the defaults (`/etc/ceph/ceph.conf` and `client.admin`), copy the example config from the Checkmk server to `/etc/check_mk/ceph.cfg` on the Ceph node and edit it:

```bash
sudo curl -o /etc/check_mk/ceph.cfg http://<checkmk-server-ip>/monitoring/check_mk/agents/cfg_examples/ceph.cfg
```

## Part C: Tell Checkmk about the new services

### Step 6: Re-run discovery

For each host you added a plugin to:

1. **Setup** > **Hosts** > **Hosts**, click the host.
2. **Save & run service discovery**, then **Rescan**.
3. Click **Monitor undecided services** (or **Accept all**).
4. **Changes** icon > **Activate pending changes**.

## What you should see

- **SMART:** for each disk, a service named `SMART <disk> Stats` (health and error counters) and `Temperature SMART <disk>`.
- **Ceph:** services such as `Ceph Status`, one `Ceph Pool <name>` per pool, and one `Ceph OSD <number>` per disk. A cluster that is nearly full or has warnings shows up in Checkmk with the same state Ceph reports.

## If it doesn't work

| You see | Do |
|---|---|
| No new services after the rescan | Check the plugin file is executable and sits in `/usr/lib/check_mk_agent/plugins/`. Run it by hand (Steps 3 and 5): the agent can only pass on what the script prints. |
| `TypeError: 'type' object is not subscriptable` when running `mk_ceph.py` | The `python3` on that node is too old for the plugin (the plugin needs a newer Python 3 than some older distributions ship, for example Rocky 8's default 3.6). Run it with a newer Python that also has the `rados` library. The `#!` first line of the plugin decides which Python runs. |
| `ERROR: smartctl not found` | Install `smartmontools` (Step 1). |
| Your disks sit behind a RAID controller and nothing shows | `smartctl` may need controller-specific options. That is outside the scope of this guide. See the plugin's comments and [Checkmk's Linux agent article](https://docs.checkmk.com/latest/en/agent_linux.html). |
