# 7. Monitor a Windows PC

**What you'll end up with:** a Windows machine reporting CPU, memory, disks, network interfaces, Windows services and more into Checkmk.

Video: starts at 22:15.

## What you need first

- Chapter 1 done.
- A Windows PC or server where you can run programs as administrator.
- The Checkmk server must be able to reach **TCP port 6556** on the Windows machine.

## Steps

### Step 1: Download the Windows agent

On the Windows machine, open the Checkmk web interface in a browser, then:

1. **Setup** > **Agents** > **Windows**.
2. In the **Packaged agents** box, click **check_mk_agent.msi** to download it. If your browser asks whether to keep the file, keep it.

You can also download it directly from `http://<checkmk-server-ip>/monitoring/check_mk/agents/windows/check_mk_agent.msi`.

### Step 2: Install it

1. Double-click the downloaded `check_mk_agent.msi`.
2. Accept the license, click through the installer, and click **Finish**.

The installer creates a Windows service for the agent and, per Checkmk's documentation, adds a Windows Firewall rule for port 6556.

### Step 3: Add the host in Checkmk

1. **Setup** > **Hosts** > **Hosts** > **Add host**.
2. **Host name:** the machine's name.
3. **IPv4 address:** the machine's IP address.
4. Leave **Checkmk agent / API integrations** on the default.
5. Click **Test agent connection**.

If it succeeds, skip to Step 6. In the video the first test failed, which is the next two steps.

### Step 4: Add a firewall rule (only if the test failed)

Open **PowerShell as administrator** (right-click, **Run as administrator**) and run Checkmk's documented rule. It allows inbound TCP 6556 for the agent on private and domain networks:

```powershell
netsh advfirewall firewall add rule `
   name="Checkmk Agent" `
   description="Allow inbound network traffic to the Checkmk Agent" `
   dir=in `
   localport=6556 `
   protocol=tcp `
   action=allow `
   program="%ALLUSERSPROFILE%\checkmk\agent\bin\cmk-agent-ctl.exe" `
   profile=private,domain `
   enable=yes
```

You should see `Ok.`

To restrict the rule to the Checkmk server, add `remoteip=<checkmk-server-ip>` to the command.

### Step 5: Restart the agent service

In the video, the new rule did not take effect until the agent service was restarted. In the same administrator PowerShell:

```powershell
Get-Service -DisplayName '*Checkmk*' | Restart-Service
```

You can also open **Services** (`services.msc`), find the Checkmk agent service, right-click it, and choose **Restart**.

Then go back to Checkmk and click **Test agent connection** again.

### Step 6: Save and discover

1. Click **Save & run service discovery**.
2. Click **Monitor undecided services** (or **Accept all**).
3. **Changes** icon > **Activate pending changes**.

### Step 7: Look at it

**Monitor** > **All hosts** > click the Windows host.

## What you should see

Services for CPU, memory, each disk and filesystem, each network interface, the Windows time service, uptime and more. Real findings can show up right away, such as a nearly full disk, a network card running slower than its rated speed, or a stopped Windows time service.

## If it doesn't work

| You see | Do |
|---|---|
| **Test agent connection** still fails after Step 5 | From the Checkmk server run `echo \| nc <windows-ip> 6556`. Nothing back means the firewall is still blocking it. Open `wf.msc` (Windows Defender Firewall with Advanced Security) and look at the inbound rules. See the "Windows Firewall" part of [Checkmk's Windows agent article](https://docs.checkmk.com/latest/en/agent_windows.html). |
| The `netsh` command says access is denied | The PowerShell window is not running as administrator. |
| The Windows network profile is "public" | The rule above covers `private` and `domain` profiles only. Change the network profile to private, or change `profile=` in the command. |
| `Check_MK Agent` shows a WARN about TLS | Same as chapter 2: the agent works but is not registered yet. See the registration part of the Windows agent article. |
