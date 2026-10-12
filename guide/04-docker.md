# 4. Monitor Docker and every container

**What you'll end up with:** your Docker host monitored, and each container showing up as its own monitored item with CPU, memory, disk and status.

Video: starts at 10:49.

## What you need first

- Chapter 2 done. You know how to install the agent and add a host.
- A Debian or Ubuntu Docker host (the commands below use `apt`) with `sudo`.
- Python 3 on the Docker host. The Docker plugin is a Python script.

How it works: the Docker host runs the Checkmk agent plus one extra plugin, `mk_docker.py`, which asks Docker about its containers. Containers have no agent of their own, so you add each one to Checkmk as a host that gets its data **piggybacked** on the Docker host's report.

## Steps

### Step 1: Install the agent on the Docker host

Follow chapter 2, Steps 2 to 4, on the Docker host. For Debian or Ubuntu:

```bash
curl -O http://<checkmk-server-ip>/monitoring/check_mk/agents/check-mk-agent_2.5.0p13-1_all.deb
sudo apt install ./check-mk-agent_2.5.0p13-1_all.deb
```

### Step 2: Add the Docker host to Checkmk

Follow chapter 2, Steps 1, 5 and 6: **Setup** > **Hosts** > **Hosts** > **Add host**, enter the name and IP address, then **Save & run service discovery**.

It finds the normal Linux services but nothing about Docker. That is expected. The Docker check needs its plugin, which is not turned on automatically.

### Step 3: Install the Python Docker library

```bash
sudo apt install python3-docker
```

Use your system package, not `pip`. Checkmk's documentation warns that `pip` can damage Python packages that come with the distribution.

### Step 4: Install the plugin

The Checkmk server hands out the plugin file. Download it into the agent's plugins folder and make it executable:

```bash
sudo curl -o /usr/lib/check_mk_agent/plugins/mk_docker.py http://<checkmk-server-ip>/monitoring/check_mk/agents/plugins/mk_docker.py
sudo chmod +x /usr/lib/check_mk_agent/plugins/mk_docker.py
```

You can also find the plugin in Checkmk under **Setup** > **Agents** > **Linux**, in the **Plugins** box.

### Step 5: Download the plugin's config file

The plugin reads `/etc/check_mk/docker.cfg`. Checkmk ships an example file that works as it is. In that example, `container_id: name` makes containers show up under their names instead of 12-character IDs.

```bash
sudo mkdir -p /etc/check_mk
sudo curl -o /etc/check_mk/docker.cfg http://<checkmk-server-ip>/monitoring/check_mk/agents/cfg_examples/docker.cfg
```

### Step 6: Get the list of container names

```bash
docker ps --format '{{.Names}}'
```

Copy the output. You will paste it into Checkmk in Step 11. Each line is one running container.

### Step 7: Check the plugin works

```bash
sudo /usr/lib/check_mk_agent/plugins/mk_docker.py | grep '^<<<<' | sort -u
```

You should see one line like `<<<<nginx>>>>` per container. If you see `mk_docker requires the docker library`, repeat Step 3.

### Step 8: Re-run discovery on the Docker host

1. **Setup** > **Hosts** > **Hosts**, click the Docker host.
2. **Save & run service discovery**, then **Rescan**.
3. You should now see **Docker container** and **Docker node info** under undecided services. Click **Monitor undecided services** (or **Accept all**).
4. **Changes** icon > **Activate pending changes**.

### Step 9: Make a folder for the containers

The containers are not real machines. This folder tells Checkmk: no IP address, no agent, just use the piggyback data.

1. **Setup** > **Hosts** > **Hosts** > **Add folder**.
2. **Title:** `Docker containers`.
3. Click **show more** if the fields below are hidden.
4. **Network address** box > **IP address family:** tick it and choose **No IP**.
5. **Monitoring agents** box > **Checkmk agent / API integrations:** tick it and choose **No API integrations, no Checkmk agent**.
6. Same box > **Piggyback:** tick it and choose **Always use and expect piggyback data**.
7. Click **Save**.

### Step 10: Open the folder

Click into the new `Docker containers` folder.

### Step 11: Import the containers as hosts

1. Open the **Hosts** menu at the top and click **Import hosts via CSV file**.
2. For **Import hosts**, choose **Content of CSV file**.
3. In the text box, paste the container names from Step 6.
4. Add one new line **above** them with exactly this text, so Checkmk knows what the column is:

```
host_name
nginx
postgres
```

(Those two names are examples. Use your own.)

5. Tick **Perform automatic service discovery**.
6. Click **Upload**. The preview should show the column mapped to **Host name**.
7. Click **Import**. A bulk discovery page opens. Start it and let it finish.

### Step 12: Activate

**Changes** icon > **Activate pending changes**. Give it a minute or two.

### Step 13: Look at the containers

1. **Monitor** > **All hosts**. Every container is now a host.
2. **Monitor** > **Applications** > **Docker containers** shows them together.
3. Click a container to see its CPU, disk I/O, status, memory and uptime.

## What you should see

Each container as its own host, with its own services. A host that is stopped shows as down.

## About the paid editions

Community works as shown above: you create the container hosts yourself, here by pasting names. Checkmk has commercial editions (Pro, Ultimate, Ultimate MT and Cloud) that can create hosts from piggyback data for you, with a feature called Dynamic host management. Compare the editions at [checkmk.com/pricing](https://checkmk.com/pricing).

## If it doesn't work

| You see | Do |
|---|---|
| Discovery finds no Docker services | Check that `mk_docker.py` is executable (Step 4), that `python3-docker` is installed (Step 3), then run Step 7. |
| Container hosts exist but stay empty or PENDING | The container name in Checkmk must match the name in the plugin output exactly. Run Step 7 to compare. Check that `docker.cfg` is in place (Step 5), otherwise names are 12-character IDs. |
| Container hosts show as DOWN with no data | The folder (Step 9) must say **No IP**, **No API integrations, no Checkmk agent** and **Always use and expect piggyback data**. Fix the folder, then activate. |
| You want to see the raw piggyback files | On the Checkmk server, as the site user: `ls ~/tmp/check_mk/piggyback/`. |
