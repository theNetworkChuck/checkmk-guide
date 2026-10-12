# 12. Get alerts in Slack

**What you'll end up with:** a Slack channel that receives a message when something in Checkmk goes critical, and another when it recovers.

Video: starts at 30:08.

## What you need first

- Chapter 1 done, with at least one host monitored (chapter 2).
- A Slack workspace where you can create an app.

How it works: Slack gives you a **webhook URL**. Anyone who has that URL can post to your channel, so treat it like a password. Checkmk posts to it whenever a notification rule fires.

## Steps

### Step 1: Make a Slack webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**, then **From scratch**.
2. Name it (for example `Checkmk`), pick your workspace, and click **Create App**.
3. In the left menu click **Incoming Webhooks** and turn **Activate Incoming Webhooks** on.
4. At the bottom click **Add New Webhook to Workspace**, pick the channel for alerts, and click **Allow**.
5. Copy the **Webhook URL**. It starts with `https://hooks.slack.com/services/`. Keep it private.

Checkmk's own steps are in its [Slack article](https://docs.checkmk.com/latest/en/notifications_slack.html).

### Step 2: Start a notification rule in Checkmk

1. Click **Setup**, then under **Events** click **Notifications**.
2. Click **Add notification rule**. A step-by-step wizard opens.

### Step 3: Walk through the wizard

1. **Triggering events:** leave the defaults and click **Next step**. The defaults cover service events (any state to CRIT, WARN or OK) and host events (any to DOWN, any to UP).
2. **Filter for hosts/services:** leave empty to send everything, then **Next step**.
3. **Notification method:** choose **Send notification**, and as the method choose **Slack or Mattermost**.
4. Next to **Select parameters**, click **Create**. Under **Webhook URL**, choose **Explicit** and paste the webhook from Step 1. Give the parameter set a description and save it.
5. Click **Next step**.
6. **Recipient:** remove **All contacts of the affected object** and choose **Specific users**, then pick **cmkadmin**. On a fresh install nobody belongs to a contact group, so "all contacts" would reach nobody. One specific user also means exactly one Slack message per alert.
7. Click **Next step** through **Sending conditions**.
8. **General properties:** give the rule a description such as `Slack alerts`, review, and click **Save**.

### Step 4: Activate

**Changes** icon > **Activate pending changes**.

### Step 5: Make something fail on purpose

Stop a service on one of your monitored hosts, for example a service that has its own check (the video stopped an AI agent's gateway service). Then wait about a minute for Checkmk's next check.

You should get a message in the Slack channel. Start the service again. After the next check you get a recovery message.

## What you should see

A Slack post like "Problem (CRITICAL): Service ... on ..." with the check's output, and later a recovery post.

## If it doesn't work

| You see | Do |
|---|---|
| Nothing in Slack | As the site user (`sudo omd su monitoring`), read `~/var/log/notify.log`. "No rule matched" means the rule's filter or recipient does not match. |
| Nothing arrives and the log says no contacts | The recipient is "all contacts" and nobody is a contact. Use **Specific users** (Step 3, point 6). |
| Two Slack posts per alert | More than one recipient is selected. Use one specific user. |
| Slack rejects the post | The webhook URL is wrong or the app was removed from the channel. Make a new webhook (Step 1). |
| You want a test without breaking something | In a service's view, open the **Commands** menu and choose **Send custom notification**. |
