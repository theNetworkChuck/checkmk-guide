# 5. Monitor Proxmox VE and every VM through its API

**What you'll end up with:** your Proxmox VE host monitored through its API, with nothing installed on Proxmox, and your VMs showing up with their Proxmox data (CPU, memory, disk, network, backup status, snapshot age).

Video: starts at 16:47.

## What you need first

- Chapter 1 done.
- A Proxmox VE server and `root` access to its shell.
- The Proxmox web/API port, **8006**, reachable from the Checkmk server.

How it works: instead of putting an agent inside Proxmox, Checkmk logs in to the Proxmox API with a read-only user and asks about the host and every VM. In Checkmk this is called a **special agent**.

> [!NOTE]
> You do not have to choose between an agent and the API. You can run the Checkmk agent on the Proxmox host and the API integration together. Each sees the machine from a different angle. To do that, in Step 5 choose **Configured API integrations and Checkmk agent**. Checkmk's own Proxmox article recommends this too.

## Steps

### Step 1: Make a read-only user in Proxmox

Do this once, on any Proxmox node, as `root`. Proxmox users apply to the whole cluster. This creates a user called `checkmk` in the Proxmox VE authentication realm (`pve`), gives it a password, and gives it the built-in read-only role **PVEAuditor** on the whole tree (`/`).

```bash
pveum user add checkmk@pve --comment "Checkmk read-only monitoring"
pveum passwd checkmk@pve
pveum acl modify / --users checkmk@pve --roles PVEAuditor
```

- The second command asks you to type the new password twice. Pick a long random one and save it in a password manager. You need it in Step 4. Typing it at the prompt keeps it out of your shell history.
- `PVEAuditor` can read everything and change nothing.

Check the result:

```bash
pveum user permissions checkmk@pve
```

You should see only audit-style privileges (names ending in `.Audit`, such as `VM.Audit`) on `/`. If you see privileges like `VM.PowerMgmt` or `Sys.Modify`, the wrong role was assigned.

### Step 2: Add the Proxmox host to Checkmk

1. **Setup** > **Hosts** > **Hosts** > **Add host**.
2. **Host name:** the Proxmox node's name (the name Proxmox shows for the node).
3. **IPv4 address:** the node's IP address.
4. **Monitoring agents** box > **Checkmk agent / API integrations:** choose **Configured API integrations, no Checkmk agent**.
5. Click **Save & view folder**. Do not run discovery yet. There is nothing to discover until the rule from Step 4 exists.

### Step 3: Open the Proxmox rule

1. Click **Setup** and type **Proxmox** in the search box.
2. Open **Proxmox VE** (it lives under **Agents** > **VM, cloud, container**).
3. Click **Add rule**.

### Step 4: Fill in the rule

1. **Description:** `Proxmox` (any text you like).
2. Under **Proxmox VE**, tick **Username** and enter `checkmk@pve`.
3. Tick **Password**, choose **Explicit** (or **From password store** if you stored it there), and enter the password from Step 1.
4. Tick **Port** and leave it at `8006`.
5. For **Specify Proxmox VE host via**, choose **IP address**.
6. If your Proxmox uses its default self-signed certificate, tick **Disable SSL certificate validation**. If you have a trusted certificate, leave it off.
7. In the **Conditions** box, tick **Explicit hosts**, and pick the Proxmox host from Step 2. This limits the rule to that host only.
8. Click **Save**.

### Step 5: Activate and discover

1. **Changes** icon > **Activate pending changes**.
2. **Setup** > **Hosts** > **Hosts**, click your Proxmox host, then **Save & run service discovery**.
3. Click **Monitor undecided services** (or **Accept all**).
4. **Changes** icon > **Activate pending changes** again.

Checkmk finds the Proxmox information for the host: node info, CPU and memory allocation, storages and more.

### Step 6: Get the VMs

Each VM's data arrives as piggyback data on the Proxmox host, filed under the **VM's name in Proxmox**. For Checkmk to use it, a Checkmk host must exist with **exactly that name**.

- **A VM you already monitor** (for example your Docker VM from chapter 4): make its Checkmk host name match the Proxmox VM name exactly. If it does not, rename it: **Setup** > **Hosts** > **Hosts**, click the host, **Host** menu > **Rename**, type the Proxmox VM name (watch the capital letters), and confirm. Then open the host, **Save & run service discovery**, **Rescan**, **Monitor undecided services**.
- **A VM with nothing installed on it:** **Add host**, name = the Proxmox VM name, **IP address family:** **No IP**, **Monitoring agents:** **No API integrations, no Checkmk agent**, then **Save & run service discovery**.

Finish with **Changes** icon > **Activate pending changes**.

## What you should see

On the Proxmox host: node-level services. On each matching VM host: new services with the VM's CPU, memory, disk and network throughput, backup status and snapshot age. A VM with no snapshot, or no recent backup, shows up as a finding.

## About the paid editions

In Community you create a host for each VM yourself. Checkmk's commercial editions (Pro, Ultimate, Ultimate MT and Cloud) can create those hosts for you from the Proxmox data with Dynamic host management. See [checkmk.com/pricing](https://checkmk.com/pricing).

## If it doesn't work

| You see | Do |
|---|---|
| Discovery on the Proxmox host finds nothing | The rule is not matching. Open the rule, check **Explicit hosts** names this host, and make sure you activated the changes. Also check the host is set to **Configured API integrations, no Checkmk agent** (or the one with the agent). |
| The Proxmox services show a login or authentication error | The username must include the realm: `checkmk@pve`. Re-check the password. |
| SSL or certificate error | Tick **Disable SSL certificate validation** in the rule (Step 4), or install a trusted certificate on Proxmox. |
| A VM host exists but has no Proxmox services | The Checkmk host name does not match the Proxmox VM name exactly. Rename it (Step 6), then rescan. |
| You want to see which VM names were sent | On the Checkmk server, as the site user: `ls ~/tmp/check_mk/piggyback/`. |
| `pveum acl modify` complains about an unknown role | Role names are case sensitive: `PVEAuditor`. |

More in [Checkmk's Proxmox article](https://docs.checkmk.com/latest/en/monitoring_proxmox.html) and the [Proxmox user management documentation](https://pve.proxmox.com/wiki/User_Management).
