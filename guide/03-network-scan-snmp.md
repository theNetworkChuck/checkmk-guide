# 3. Scan your network with SNMP

**What you'll end up with:** your switches, routers and other network gear found automatically by an IP range scan and monitored over SNMP, with no software installed on any of them.

Video: starts at 07:16.

## What you need first

- Chapter 1 done.
- A switch, router or access point that supports **SNMP**. Most managed network gear does, but it is usually switched off by default.
- The IP range your network devices live in. Keep the scan small. Checkmk's guidance is to stay within about a `/21` at the very most, and a `/24` is plenty for a home lab.

SNMP (Simple Network Management Protocol) is a standard way for network devices to report their state. For SNMP version 2c, the **community string** acts like a password. Pick your own value instead of the common default `public`.

## Steps

### Step 1: Turn on SNMP on the device

Every device keeps this setting in a different place, so look for "SNMP" in its settings. You need:

1. SNMP **enabled for read access** (the "active queries", also called SNMP GET, not traps).
2. SNMP version **v2c** (or v3 if you want it).
3. A **community string** of your choice. Write it down.
4. If the device lets you restrict who may ask, allow the **Checkmk server's IP address**.

Do this on each device type you want to scan (switches, routers, access points).

### Step 2: Create a folder for network gear

Folders let you set things once for a whole group of hosts.

1. **Setup** > **Hosts** > **Hosts**.
2. Click **Add folder**.
3. **Title:** `networking`.
4. Do not save yet. The next two steps happen on this same page.

### Step 3: Tell the folder to use SNMP

1. In the **Monitoring agents** box, set **Checkmk agent / API integrations** to **No API integrations, no Checkmk agent**.
2. In the same box, tick **SNMP** and choose **SNMPv2 or v3**.
3. Under **SNMP credentials**, choose the SNMPv2 option and enter the community string from Step 1.

### Step 4: Turn on the network scan

1. In the **Network Scan** box, tick **Enable**.
2. Under **IP ranges to scan**, add your range. For example the whole network `192.168.1.0/24` (use your own range), or a start and end address.
3. Leave **Set criticality host tag** on its default, **Do not monitor this host**. You will switch the devices you want on in Step 7.
4. Click **Save**.

### Step 5: Activate the changes

Click the **Changes** icon in the left sidebar, then **Activate pending changes**.

### Step 6: Wait for the scan

Checkmk checks every minute whether a scan is due, and a new scan starts shortly after you save. The scan pings every address in your range. For each address that answers, Checkmk tries to find a host name and creates the host in the folder.

Open **Setup** > **Hosts** > **Hosts** and click into the `networking` folder. The hosts it found appear in the list.

> [!NOTE]
> The scan works by ping. A device that does not answer ping is not found. Checkmk also skips names that already exist as hosts.

### Step 7: Choose which devices to monitor

Found hosts are created with **Do not monitor this host** set. Change that for the ones you want.

1. In the folder, tick the box next to each device you want to monitor.
2. Open the **Hosts** menu at the top and, under **On selected hosts**, click **Edit attributes**.
3. Find the **Criticality** setting (in the **Custom attributes** box), tick it, and choose **Productive system**.
4. Click **Save**.

The warning marker on those hosts goes away.

### Step 8: Discover what each device offers

For each device you selected:

1. Click the host name, then **Save & run service discovery**.
2. Click **Rescan** (the full scan) so Checkmk uses the SNMP credentials to ask the device what it has.
3. Click **Monitor undecided services** (or **Accept all**).

Do the same for every device.

### Step 9: Activate again

**Changes** icon > **Activate pending changes**.

### Step 10: Look at the result

**Monitor** > **All hosts**. Click a switch. Wait a minute or two for data to arrive.

## What you should see

For a typical switch: every interface with traffic graphs, CPU utilization, uptime, and more. Uptime is a useful first find. A device that has been running for over a year may be due for a reboot or update.

## If it doesn't work

| You see | Do |
|---|---|
| No hosts show up in the folder | Check the IP range, make sure you activated the changes, and wait a few minutes. The scan only finds devices that answer ping. |
| Discovery finds nothing on a device | SNMP is probably off, the community string is wrong, or the device only answers certain addresses. Re-check Step 1, including the allowed-address list. |
| The hosts show as UNKNOWN or have no services after Step 9 | Make sure the folder says **No API integrations, no Checkmk agent** and has SNMP ticked (Step 3). |
| You want SNMPv3 | In Step 3 choose an SNMPv3 option instead and fill in the user and passwords. See [Checkmk's SNMP article](https://docs.checkmk.com/latest/en/snmp.html). |
