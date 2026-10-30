# Getting started

English · [Deutsch](de/getting-started.md)

This guide takes you from an empty install to a daily routine in about ten minutes.

## 1. Start the app

Pick one way from the [README](../README.md#quick-start): Docker, plain Python, or the demo data. The app listens on port 8000.

## 2. Choose the admin password

The first visit redirects to `/setup`. Choose a password with at least ten characters. This is the only account: it protects the dashboard and the admin area. You are signed in for 30 days afterwards.

Lost the password later? See [Deployment → Reset the admin password](deployment.md#reset-the-admin-password). Once you use HTTPS you can sign in with a passkey instead, see [Phone and desktop](phone-and-desktop.md#passkeys).

## 3. Basic settings

Open **Admin → Settings** (the *Admin* link in the side menu or under *More* on the phone).

| Setting | What to do |
|---|---|
| Site title | Anything you like, shown in the top bar and the browser tab |
| Language | German or English. Applies to the interface and to the morning briefing |
| Groups | One group per line, for example `Customer sites`, `Internal tools`, `Infrastructure`. Projects are grouped by these on the *Projects* view |
| Your first name | Used in the greeting of the morning briefing |
| GitHub account and token | Optional, see below |

All settings are described in [Configuration](configuration.md).

### Optional: GitHub

With a GitHub account and a read-only token, project pages show branches and the latest commits, the project list shows the time of the last push, and open pull requests appear in the inbox and the briefing.

1. Open <https://github.com/settings/personal-access-tokens/new>
2. Resource owner: your account. Repository access: *All repositories* (so new repositories appear automatically)
3. Repository permissions, all **Read-only**: *Contents*, *Pull requests*, *Metadata*
4. Paste the token into **Admin → Settings → GitHub token** and enter your account name

Without a token everything else works unchanged.

## 4. Add your projects

You have three options.

**Create them in the admin area.** **Admin → Projects → New project**. Fill in name, group, status and, if you want, hosting, stack, a one-line summary, the GitHub repository (`owner/name`), a wiki address and links to notes (one web address per line).

**Import from Markdown.** **Admin → Data → Import Markdown**. Level-2 headings become projects, checkboxes become tasks:

```markdown
## Website relaunch
- [ ] Compress hero images
- [x] Set up the contact form

## Home server
- [ ] Rotate the VPN keys
```

**Use the API.** Agents can create projects themselves, see [API](api.md#projects).

Then decide which projects are **live** (in production or at a customer): tick the *live* box on the project page. Live projects get their own section in the briefing and a lamp in the side menu, see [Briefing and checks](briefing-and-checks.md#the-live-flag).

## 5. Work with tasks

A project page has four tabs: **Tasks** (open tasks, ideas, finished), **Notes**, **Documents** and **Activity** (log, Git, hosting). Add tasks and ideas, choose a priority, tick them off. Give tasks a short, plain-language title if you create them through the API: it is what the briefing shows.

On the home page:

- **Today first** lists all urgent tasks (priority 1) of the active projects.
- The **inbox** appears when agents have created tasks. For each task choose *Accept* (keep it), *Already done* (store it as done) or *Discard* (delete it).
- The **priority board** (folded by default on the desktop) shows every open task in three columns. Drag a card to change its priority.
- On the phone, the bottom bar switches between **Today**, **Projects**, **Briefing** and **More**. The **+** button adds a task from anywhere.

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

## 8. Get the briefing every morning

1. Serve the app over HTTPS and install it on your phone, see [Phone and desktop](phone-and-desktop.md).
2. On the **Briefing** page tap **Enable notifications**.
3. Set up the daily timer, see [Deployment → Morning briefing and checks](deployment.md#morning-briefing-and-checks).

## A typical day

1. The briefing arrives. Tap it, read what is urgent in your live projects.
2. Look at the *Inbox* and accept or discard what agents proposed.
3. Pick a project, let the agent read its briefing and work (on Windows, the `>_` button opens a terminal for a task).
4. At the end the agent logs what it did and leaves a note for anything worth remembering.
5. Checks close what they can prove. The next morning the briefing shows the new state.
