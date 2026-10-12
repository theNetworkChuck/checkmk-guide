# 14. Give an AI agent the keys: an automation user and the REST API

**What you'll end up with:** a Checkmk "automation user" that an AI agent (or any script) uses to add hosts, run discovery, activate changes and build dashboards through the Checkmk REST API.

Video: starts at 32:23.

## What you need first

- Chapters 1 to 4 done, so you know how Checkmk works by hand. An agent is only as good as the person who can check its work.
- Administrator access to Checkmk.
- An AI agent that can send web requests to your Checkmk server (or just a terminal with `curl`).

How it works: an **automation user** is a login for machines. It has no password for the web interface. Instead it has an **automation secret**, which scripts send with each request. The user has a role, just like a person, so you can limit what it may do.

> [!WARNING]
> The video gives the agent's user the **Administrator** role, which can change anything. Do the same only if you trust the agent and the machine it runs on. Checkmk's REST API article describes how to make a role with narrower permissions and use that instead.

## Steps

### Step 1: Create the automation user

1. **Setup** > **Users** > **Users**.
2. Click **Add user**.
3. **Username:** a name for the agent, for example `agent`. **Full name:** anything descriptive.
4. In the **Security** box, choose **Automation secret for machine accounts** instead of a password. Let Checkmk generate the secret, and copy it somewhere safe. Treat it like a password.
5. **Roles:** tick **Administrator** (or a narrower role you made).
6. Click **Save**.

### Step 2: Activate

**Changes** icon > **Activate pending changes**. A new user does not see everything until changes are activated.

### Step 3: Test the login

From any machine that can reach the Checkmk server, with the secret in an environment variable so it never lands in your shell history or a chat log:

```bash
export CMK_URL="http://<checkmk-server-ip>/monitoring"
export CMK_USER="agent"
read -rs CMK_SECRET && export CMK_SECRET     # type or paste the secret, press Enter

curl -s \
  --header "Authorization: Bearer $CMK_USER $CMK_SECRET" \
  --header "Accept: application/json" \
  "$CMK_URL/check_mk/api/v1/domain-types/host_config/collections/all"
```

You should get JSON that lists your hosts. If you get `{"title": "Unauthorized", "status": 401 ...}`, the username or secret is wrong.

The header is always `Authorization: Bearer <username> <secret>` (a space between them).

### Step 4: Try one of the common calls

Add a host (adjust the name and IP):

```bash
curl -s --request POST \
  --header "Authorization: Bearer $CMK_USER $CMK_SECRET" \
  --header "Accept: application/json" --header "Content-Type: application/json" \
  --data '{"host_name": "example-host", "folder": "/", "attributes": {"ipaddress": "<host-ip>"}}' \
  "$CMK_URL/check_mk/api/v1/domain-types/host_config/collections/all"
```

Then check **Setup** > **Hosts** in the web interface. The host is there, and the **Changes** icon shows a pending change. API changes need activating, just like changes you make by hand.

### Step 5: Hand the agent the keys

Give your AI agent three things: the Checkmk address, the username, and the secret. Put the secret in the agent's environment or secret store, not in the prompt. Then ask for the work. For example:

> Use the Checkmk REST API at `<checkmk-url>` (user `agent`, secret in `$CMK_SECRET`). List the hosts that exist. Add these servers as hosts with the Checkmk agent: `<list>`. Run service discovery on each and accept all services. Then activate the changes. Tell me what you changed.

For a ready starting point, this repo has a small helper, [`scripts/api/cmk_api.py`](../scripts/api/cmk_api.py), that lists hosts, adds a host, runs discovery and activates. Your agent can read it for the exact API calls. The full reference is in Checkmk under **Help** > **Developer resources** > **REST API**, and in [Checkmk's REST API article](https://docs.checkmk.com/latest/en/rest_api.html).

In the video, the agent was also asked to build a dashboard. That uses a part of the API that is marked unstable, so the details can change between versions. Let the agent read the API documentation on your own server rather than guessing.

### Step 6: Check the agent's work

Open **Monitor** > **All hosts** and look. Ask the agent to describe anything you do not recognize. Remember that the agent can only activate changes that it made itself, unless it asks to force activation of other people's changes. That is a safety feature. See the "pending changes" part of the REST API article.

## What you should see

New hosts and services appearing in Checkmk without you clicking through Setup, and an audit trail: every change the agent makes is logged under the automation user's name (**Setup** > **General** > **Audit log**).

## If it doesn't work

| You see | Do |
|---|---|
| `401 Unauthorized` | Wrong username or secret, or the user has not been activated yet (Step 2). |
| `403` or a permission error | The user's role does not allow that action. Give it a role that does. |
| The agent adds hosts but nothing is monitored | Discovery and activation are separate steps. Ask it to run discovery on the new hosts, then activate. |
| The agent cannot activate changes | By default the API only activates changes made through the API by the same user. Make the changes through the API, or see the REST API article for the force option. |
| The URL returns 404 | Check the site name in the URL. It is the site you made in chapter 1 (`monitoring`). |
