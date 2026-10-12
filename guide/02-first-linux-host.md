# 2. Add your first Linux host with the agent

**What you'll end up with:** one Linux server reporting its CPU, memory, disks, network and services into Checkmk, using the Checkmk agent.

Video: starts at 03:00.

## What you need first

- Chapter 1 done: a Checkmk site you can log into.
- A Linux server you want to monitor, and `sudo` on it. The steps below show both Debian/Ubuntu (`.deb`) and Red Hat style systems such as Rocky Linux (`.rpm`).
- The Checkmk server must be able to reach **TCP port 6556** on that server.

How it works: the **agent** is a small program that runs on the server you want to watch. Checkmk connects to it on port 6556 and asks "what do you see?".

## Steps

### Step 1: Start adding the host

1. In Checkmk, click **Setup** in the left sidebar, then **Hosts**, then **Hosts**.
2. Click **Add host**.
3. **Host name:** a name for the server. Keep it simple (letters, numbers, dashes).
4. Under **Network address**, tick **IPv4 address** and enter the server's IP address.
5. Do not save yet. Leave this page open.

### Step 2: Get the agent package from your Checkmk server

1. Open the Checkmk web interface in a second browser tab.
2. Click **Setup**, then **Agents**, then **Linux**.
3. In the box **Packaged agents**, right-click the package for your system and copy the link address: the **DEB** for Debian/Ubuntu, the **RPM** for Red Hat style systems.

The link has this shape:

```
http://<checkmk-server-ip>/monitoring/check_mk/agents/check-mk-agent_2.5.0p13-1_all.deb
http://<checkmk-server-ip>/monitoring/check_mk/agents/check-mk-agent-2.5.0p13-1.noarch.rpm
```

### Step 3: Install the agent on the server

Log in to the server you want to monitor. Download the package with the link you copied, then install it.

Debian or Ubuntu:

```bash
curl -O http://<checkmk-server-ip>/monitoring/check_mk/agents/check-mk-agent_2.5.0p13-1_all.deb
sudo apt install ./check-mk-agent_2.5.0p13-1_all.deb
```

Rocky, RHEL and similar:

```bash
curl -O http://<checkmk-server-ip>/monitoring/check_mk/agents/check-mk-agent-2.5.0p13-1.noarch.rpm
sudo dnf install -y ./check-mk-agent-2.5.0p13-1.noarch.rpm
```

### Step 4: Open port 6556 for the Checkmk server

If the server has a firewall, allow the Checkmk server to reach port 6556. These examples allow only the Checkmk server, which is safer than opening the port to everyone.

Rocky, RHEL and similar (`firewalld`):

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="<checkmk-server-ip>" port port="6556" protocol="tcp" accept'
sudo firewall-cmd --reload
```

Ubuntu (`ufw`):

```bash
sudo ufw allow from <checkmk-server-ip> to any port 6556 proto tcp
```

No firewall running? Skip this step.

### Step 5: Test the connection from Checkmk

1. Go back to the **Add host** page.
2. Scroll to the **Monitoring agents** box. Leave **Checkmk agent / API integrations** on its default value.
3. Click **Test agent connection**.

You should get a success message. If you get an error, see the table at the end.

### Step 6: Save and discover

1. Click **Save & run service discovery**.
2. Wait a few seconds. Checkmk asks the agent what is on the server and lists everything it found as **Undecided services**. Those are things it can monitor but is not monitoring yet.
3. At the top, click **Monitor undecided services** (the button may also be labelled **Accept all**).

### Step 7: Activate the changes

Nothing you configure takes effect until you activate it.

1. Click the **Changes** icon in the left sidebar (it shows a number for the pending changes).
2. Click **Activate pending changes**, then **Activate on selected sites** if asked.

Give it a few minutes for the first data to arrive. Checkmk checks every service about once a minute.

### Step 8: Look at your host

1. Click **Monitor**, then **All hosts**.
2. Click the host name to see its services.
3. Click any service, for example **CPU utilization**, to see its graph and thresholds.

## What you should see

A list of services for the server: CPU, memory, disks and filesystems, network interfaces, uptime, and more, each marked OK, WARN or CRIT. Each metric comes with default thresholds, so you will be alerted when a value goes bad (alerts are set up in chapters 12 and 13).

Services that show red can be real findings, for example a failed cluster service or a nearly full disk. Fix them, or tell Checkmk to ignore them later.

## If it doesn't work

| You see | Do |
|---|---|
| **Test agent connection** fails or times out | Port 6556 is not reachable. On the Checkmk server run `echo \| nc <host-ip> 6556`. A working agent prints `16` or starts printing agent text (`<<<check_mk>>>`). If nothing comes back, check the firewall from Step 4. |
| The **Check_MK Agent** service shows WARN: "TLS is not activated on monitored host" | The agent works but the connection is not encrypted yet. To encrypt it, register the agent with `sudo cmk-agent-ctl register`. Follow the "Registering" part of [Checkmk's Linux agent article](https://docs.checkmk.com/latest/en/agent_linux.html). The host name you pass must match the name in Setup exactly. |
| Host name does not resolve | Make sure you filled in the IPv4 address in Step 1. |
| The host shows no data after Step 7 | Wait a few minutes, then reload. Make sure you activated the changes. |
