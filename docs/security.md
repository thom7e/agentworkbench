# Security

AgentWorkbench is meant for a person or a small trusted team. This page says what it protects and what it does not.

## What is in place

- **Everything requires a login.** Except `/login`, `/setup`, `/healthz` and static files, every page needs the admin password. The API needs a token.
- **Passwords and tokens.** The admin password is hashed with scrypt. API tokens are random, shown once and stored as SHA-256 hashes, so a stolen database does not reveal them.
- **Sessions.** A signed cookie, `HttpOnly`, `SameSite=Lax`, valid for 30 days. Set `AGENTWORKBENCH_COOKIE_SECURE=1` behind HTTPS to mark it `Secure`.
- **Login throttling.** After ten failed logins from one IP within ten minutes, further attempts are blocked. Every failed attempt is delayed by one second.
- **Cross-site requests.** Form posts whose `Origin` header does not match the host are rejected. Together with `SameSite=Lax` cookies this covers the usual CSRF cases.
- **Rendered Markdown is sanitized.** Notes and documents are converted to HTML and cleaned with an allow-list. Scripts, event handlers and unknown tags are removed, and only `http`, `https` and `mailto` links are kept.
- **Read-only integrations.** The GitHub token should be read-only. The Proxmox token uses the `PVEAuditor` role. The dashboard only reads.
- **First-run setup is one-shot.** `/setup` works only while no password exists.

## What to know

- **One admin, no roles.** Everyone with the password can change everything, including tokens and settings.
- **API tokens have full access.** A token can read all projects, notes and documents and write tasks, notes and documents. It cannot read settings or other tokens, and it cannot reach the admin area. Create one token per agent and revoke it when it is no longer needed.
- **Secrets in the database.** The GitHub token and the Proxmox token secret are stored in plain text in the `settings` table, because the app must send them. Protect the database file and its backups, and use tokens with the least rights.
- **No secret scanning.** Notes and documents are stored as written. Do not put credentials into them. When importing existing notes, filter secrets first.
- **No transport encryption by itself.** The app serves plain HTTP. Use a reverse proxy with HTTPS if it leaves your private network.
- **SQLite file permissions.** Make the database readable only by the user that runs the app.

## Reporting a problem

If you find a security issue, please open a private security advisory on the GitHub repository instead of a public issue.
