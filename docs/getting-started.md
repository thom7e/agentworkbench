# Getting started

This guide takes you from an empty install to a daily routine in about ten minutes.

## 1. Start the app

Pick one way from the [README](../README.md#quick-start): Docker, plain Python, or the demo data. The app listens on port 8000.

## 2. Choose the admin password

The first visit redirects to `/setup`. Choose a password with at least ten characters. This is the only account: it protects the dashboard and the admin area. You are signed in for 30 days afterwards.

Lost the password later? See [Deployment → Reset the admin password](deployment.md#reset-the-admin-password).

## 3. Basic settings

Open **Admin → Settings** (the *Admin* link in the top bar).

| Setting | What to do |
|---|---|
| Site title | Anything you like, shown in the top bar and the browser tab |
| Language | German or English |
| Groups | One group per line, for example `Customer sites`, `Internal tools`, `Infrastructure`. Projects are grouped by these on the home page |
| GitHub account and token | Optional, see below |

All settings are described in [Configuration](configuration.md).

### Optional: GitHub

With a GitHub account and a read-only token, project pages show branches, the latest commits and a README excerpt, the home page shows the time of the last push, and the inbox lists open pull requests.

1. Open <https://github.com/settings/personal-access-tokens/new>
2. Resource owner: your account. Repository access: *All repositories* (so new repositories appear automatically)
3. Repository permissions, all **Read-only**: *Contents*, *Pull requests*, *Metadata*
4. Paste the token into **Admin → Settings → GitHub token** and enter your account name

Without a token everything else works unchanged.

## 4. Add your projects

You have three options.

**Create them in the admin area.** **Admin → Projects → New project**. Fill in name, group, status and, if you want, hosting, stack, a one-line summary, the GitHub repository (`owner/name`, the field suggests your repositories), a wiki address and links to notes (one per line, any URL).

**Import from Markdown.** **Admin → Data → Import Markdown**. Level-2 headings become projects, checkboxes become tasks:

```markdown
## Website relaunch
- [ ] Compress hero images
- [x] Set up the contact form

## Home server
- [ ] Rotate the VPN keys
```

**Use the API.** Agents can create projects themselves, see [API](api.md#projects).

## 5. Work with tasks

On a project page you can add tasks and ideas, choose a priority and tick them off. On the home page:

- **Today first** lists all urgent tasks (priority 1).
- The **priority board** shows every open task in three columns. Drag a card to another column to change its priority. On a phone use the small **1 2 3** buttons on the card. The dropdown above the board filters by project.
- The **inbox** appears when agents have created tasks. For each task choose *Accept* (keep it, it appears on the board), *Already done* (store it as done) or *Discard* (delete it).

## 6. Notes, documents, activity

| Use | For |
|---|---|
| **Activity** | What was done, one sentence, in time order |
| **Notes** | What you should still know in six months: decisions and their reasons, pitfalls, how to reach something. Pin the important ones |
| **Documents** | Longer Markdown pages: runbooks, checklists, specifications |

Everything is searchable from the search field on the home page.

## 7. Let an agent work with it

1. **Admin → API access → Create access**, give it a name such as `claude`. Copy the token, it is shown only once.
2. Follow [Working with agents](agents.md) to set up the skill for Claude Code, or call the [API](api.md) from any tool.

## 8. Install it on your phone

Open the site in Safari (iPhone) or Chrome (Android) and use **Share → Add to Home Screen**. It opens without browser bars. If you reach the app from outside your home network, serve it over HTTPS, see [Deployment](deployment.md#https-and-reverse-proxy).

## A typical day

1. Open the dashboard. Look at *Inbox* and *Today first*.
2. Accept or discard what agents proposed.
3. Pick a project, let the agent read its briefing and work.
4. At the end the agent logs what it did and leaves a note for anything worth remembering.
5. The next morning the board shows the new state.
