# 1. Install Checkmk

**What you'll end up with:** a running Checkmk Community site named `monitoring` that you can log into in your browser.

Video: starts at 00:53.

## What you need first

- A Linux server or VM running **Ubuntu 24.04** where you can use `sudo`. Put it somewhere it can reach the things you want to watch (your servers, switches, Proxmox, and so on).
- A browser on the same network.

Checkmk can also run as a Docker container. This guide uses the package install, because that is what the video does. The container route is in [Checkmk's Docker install article](https://docs.checkmk.com/latest/en/introduction_docker.html).

## Steps

### Step 1: Get the right package

1. Go to [checkmk.io/networkchuck](https://checkmk.io/networkchuck) and open the **Downloads** page.
2. Choose **Linux**, then your Ubuntu version (**24.04**), then the **Community** edition.
3. Copy the download command the page gives you. The video used version 2.5.0p13. Patch numbers move up over time, so use the one the page offers. The command looks like this:

```bash
wget https://download.checkmk.com/checkmk/2.5.0p13/check-mk-community-2.5.0p13_0.noble_amd64.deb
```

> [!WARNING]
> Pick the file that matches your Ubuntu release. `noble` is Ubuntu 24.04. A package built for a different release is refused by `apt`, with errors about packages that are "not installable".

### Step 2: Install the package

Use the full file name, with `./` in front if you are in the same folder:

```bash
sudo apt install ./check-mk-community-2.5.0p13_0.noble_amd64.deb
```

Answer `Y` when it asks to continue.

Optional: Checkmk signs its packages. To check the signature before installing, see the "Signed package installation" section of [Checkmk's Debian and Ubuntu install article](https://docs.checkmk.com/latest/en/install_packages_debian.html).

### Step 3: Check the install

```bash
omd version
```

You should see a line like:

```
OMD - Open Monitoring Distribution Version 2.5.0p13.community
```

### Step 4: Create a monitoring site

A Checkmk "site" is one complete monitoring setup. Create one called `monitoring`:

```bash
sudo omd create monitoring
```

When it finishes, the last lines include the web address and the admin login. Copy the password now:

```
Created new site monitoring with version 2.5.0p13.community.
  The site can be started with omd start monitoring.
  The default web UI is available at http://<your-server>/monitoring/
  The admin user for the web applications is cmkadmin with password: <generated-password>
```

If you would rather choose the password yourself, add `--admin-password` to the command (see [Checkmk's setup guide](https://docs.checkmk.com/latest/en/intro_setup.html)).

### Step 5: Start the site

```bash
sudo omd start monitoring
```

### Step 6: Log in

1. In a browser, open `http://<checkmk-server-ip>/monitoring/`.
2. User: `cmkadmin`. Password: the one from Step 4.

To change that password later, switch to the site user and run `cmk-passwd`:

```bash
sudo omd su monitoring
cmk-passwd cmkadmin
```

## What you should see

The Checkmk main page after login. Checkmk offers a short built-in tutorial on first start. You can skip it. The next chapters cover adding things to monitor.

Two ports matter later: **80** serves the web interface, and **8000** is used when agents register with the server (only needed if you choose to register agents, see chapter 2).

## If it doesn't work

| You see | Do |
|---|---|
| `apt` refuses the package ("not installable") | You downloaded the package for a different Ubuntu release. Download the `noble` file for 24.04. |
| `omd: command not found` | The install did not finish. Re-run Step 2 and read the first error it prints. |
| The browser cannot open the page | Run `sudo omd status monitoring`. Everything should say `running`. Then check that port 80 is open between your browser and the server. |
| You lost the admin password | `sudo omd su monitoring`, then `cmk-passwd cmkadmin` to set a new one. |
