# 6. Monitor a website from the outside

**What you'll end up with:** a check that loads a web page from the Checkmk server on a schedule, and goes critical if the page is down or the text you expect is missing.

Video: starts at 20:24.

## What you need first

- Chapter 1 done.
- A website URL that the Checkmk server can reach.

How it works: this is an **active check**. Nothing is installed anywhere. The Checkmk server itself requests the page, like a visitor would. Looking for a specific piece of text in the page also tells you if the site was replaced or defaced.

## Steps

### Step 1: Add the website as a host

1. **Setup** > **Hosts** > **Hosts** > **Add host**.
2. **Host name:** the website's domain, for example `example.com`. Checkmk resolves it through DNS, so you can leave the IP address empty.
3. **Monitoring agents** box > **Checkmk agent / API integrations:** choose **No API integrations, no Checkmk agent**.
4. Click **Save & view folder**.

### Step 2: Open the web check rule

1. Click **Setup** and type `HTTP` in the search box.
2. Open **Check HTTP web service**.
3. Click **Add rule**.

### Step 3: Fill in the rule

1. **Description:** something like `HTTP checks`. One rule can cover several hosts.
2. Under **HTTP web service endpoints to monitor**, click **Add new endpoint**.
3. **Name:** a service name, for example `homepage`.
4. **URL:** the full address, for example `https://example.com`.
5. Click the button for **Individual settings to use for this endpoint**.
6. Here you can also check the status code or the response time. For this chapter, find **Search for strings**, then **Search in body**, choose **Fixed string**, and type a word that must always appear on the page, such as the site's name.
7. In the **Conditions** box, tick **Explicit hosts** and pick the host from Step 1.
8. Click **Save**.

### Step 4: Activate, then discover

1. **Changes** icon > **Activate pending changes**.
2. **Setup** > **Hosts** > **Hosts**, click the website host, then **Save & run service discovery**, then **Rescan**.
3. Click **Monitor undecided services** (or **Accept all**) if the service is listed as undecided.
4. **Changes** icon > **Activate pending changes** again.

### Step 5: Look at it

**Monitor** > **All hosts** > the website host. You should see a service named `HTTP` or `HTTPS` followed by your endpoint name. Click it to see the response time, the status, and the **expected string** result.

### Step 6: Prove it can fail

1. Edit the rule and change the fixed string to a word that is not on the page.
2. **Changes** icon > **Activate pending changes**.
3. If the service does not update on its own, run **Save & run service discovery** and **Rescan** on the host, and activate again.
4. Within a minute or two the service goes **CRIT** with a message like "expected string not found".
5. Change the string back and activate.

## What you should see

A service that is OK while the page loads and contains your string, and CRIT when it does not.

## If it doesn't work

| You see | Do |
|---|---|
| No HTTP service appears on the host | Check the rule's **Explicit hosts** condition names the host exactly. Activate, then run discovery again (Step 4). |
| The service is UNKNOWN or CRIT with a connection error | The Checkmk server cannot reach the URL. Test from the Checkmk server: `curl -I https://example.com`. |
| A redirect makes it fail | In the endpoint's individual settings, find **How to handle redirects** and choose **Follow the redirection**. |

Other things this rule can check: certificate expiry, response time, status codes. See [Checkmk's article on monitoring network services](https://docs.checkmk.com/latest/en/active_checks.html).
