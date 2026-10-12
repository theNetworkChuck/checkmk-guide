# 9. Install a package from the Checkmk Exchange (UniFi example)

**What you'll end up with:** a community-made Checkmk extension installed and enabled, and your UniFi controller, access points, switches, SSIDs and clients monitored through it.

Video: starts at 25:27.

## What you need first

- Chapter 1 done.
- A UniFi console or controller that the Checkmk server can reach.
- A **local** UniFi account on that console (username and password). This package signs in the way you do in the UniFi web interface. A UniFi API key does not work with this package.
- `sudo` on the Checkmk server.

How it works: the **Checkmk Exchange** ([exchange.checkmk.com](https://exchange.checkmk.com)) is where people share extensions. They come as `.mkp` files (extension packages). In Checkmk Community you install them from the command line, because the **Extension packages** page in Setup is a commercial-edition feature.

> [!WARNING]
> Exchange packages are written by community members. Install them at your own risk, and read what a package does before you run it.

## Steps

### Step 1: Find the package

1. Go to [exchange.checkmk.com](https://exchange.checkmk.com) and search for `unifi`.
2. Open **Unifi Controller Special-Agent**: [exchange.checkmk.com/p/unifi](https://exchange.checkmk.com/p/unifi).
3. Click **All versions**. Check that the minimum Checkmk version fits yours. Version 3.0.0 needs Checkmk 2.4.0p19 or newer, which includes 2.5.
4. Right-click the `.mkp` file link and copy the link address. The link at the time of writing:

```
https://exchange.checkmk.com/packages/unifi/2745/unifi-3.0.0.mkp
```

### Step 2: Become the site user on the Checkmk server

The `mkp` command belongs to the site, not to your normal user. Without this step you get "mkp: command not found".

```bash
sudo su - monitoring
```

(`sudo omd su monitoring` does the same thing.) The prompt changes to `OMD[monitoring]:~$`.

### Step 3: Download and add the package

```bash
curl -O https://exchange.checkmk.com/packages/unifi/2745/unifi-3.0.0.mkp
mkp add unifi-3.0.0.mkp
```

`mkp add` stores the package but does not turn it on yet.

### Step 4: Enable it

Use the package **name** and **version** from the list, not the file name:

```bash
mkp list
mkp enable unifi 3.0.0
```

`mkp list` first shows the package as disabled. After `mkp enable` (which prints nothing when it works), run `mkp list` again. The **State** column should say `Enabled (active on this site)`.

You do not need to restart anything. The new rule shows up in Setup right away.

### Step 5: Add the rule

1. In Checkmk, click **Setup** and type `unifi` in the search box.
2. Open **UniFi connection parameters** and click **Add rule**.
3. Fill in:
   - **Username** and **Password** of the local UniFi account.
   - **HTTPS port:** `443`, unless you changed it.
   - **Certificate validation:** if your console uses its default self-signed certificate, tick the option to disable certificate validation.
   - **UDM-Pro API:** tick **Use UDM-Pro API endpoints** if your console is a UniFi OS device (UDM, UDM Pro, Cloud Gateway and similar).
   - **Device piggyback:** switch this **on**. It makes each UniFi device (access points, switches and so on) report its own data. Without it you only get the controller and site services.
4. In **Conditions**, tick **Explicit hosts** and pick the UniFi console host (Step 6).
5. Click **Save**.

### Step 6: Make the UniFi console a host

Add it, or reuse the host the network scan found in chapter 3:

1. **Setup** > **Hosts** > **Hosts** > **Add host** (or open the existing host and **Edit properties**).
2. Name and IP address of the UniFi console.
3. **Monitoring agents** box > **Checkmk agent / API integrations:** **Configured API integrations, no Checkmk agent**.
4. Click **Save & run service discovery**, then **Monitor undecided services** (or **Accept all**).
5. **Changes** icon > **Activate pending changes**.

### Step 7: Create hosts for the UniFi devices

Each UniFi device arrives as piggyback data under its UniFi name, just like the Docker containers in chapter 4. List the names, as the site user on the Checkmk server:

```bash
ls ~/tmp/check_mk/piggyback/
```

(The folder fills after the first check run, so wait a minute or two.) Then repeat chapter 4, Steps 9 to 12, with a new folder called `UniFi devices`, using the device names from that list as the CSV, with `host_name` on the first line.

### Step 8: Look at the result

**Monitor** > **All hosts**. Open an access point. You should see services for the device, its radios and each SSID, and for switches, its ports and PoE usage.

## What you should see

Services such as `UniFi Controller`, one per UniFi device, one per radio (`UniFi Radio ...`), one per SSID (`UniFi SSID ...`), and for clients and switch ports. All of it comes from one API connection.

## If it doesn't work

| You see | Do |
|---|---|
| `mkp: command not found` | You are not the site user. Run `sudo su - monitoring` first (Step 2). |
| The download returns 404 | Use the link from the **All versions** tab on `exchange.checkmk.com`. The domain is `exchange.checkmk.com`, not `checkmk.com`. |
| `mkp enable unifi-3.0.0.mkp` fails | Enable by name and version: `mkp enable unifi 3.0.0`. |
| The rule is not in Setup | `mkp list` must show `Enabled`. If it says `Disabled`, run Step 4. |
| A certificate error: `CERTIFICATE_VERIFY_FAILED` | Tick the option to disable certificate validation in the rule (Step 5). |
| A login error (403) from the console | The username or password is wrong, or the account is not a local account. An API key will not work here. |
| Only `UniFi Controller` and a site service appear | **Device piggyback** is off. Turn it on in the rule, activate, and rescan. |
| A device name is rejected as a host name | See the "Host name translation for piggybacked hosts" rule in [Checkmk's piggyback article](https://docs.checkmk.com/latest/en/piggyback.html). |
