# Security

English · [Deutsch](de/security.md)

AgentWorkbench is meant for a person or a small trusted team. This page says what it protects and what it does not.

## What is in place

- **Everything requires a login.** Except `/login`, `/setup`, `/healthz`, the passkey sign-in endpoints, the service worker and static files, every page needs a signed-in session. The API needs a token.
- **Passwords, passkeys and tokens.** The admin password is hashed with scrypt. Passkeys (WebAuthn) are stored as public keys only, user verification is required, and the signature counter is checked. API tokens are random, shown once and stored as SHA-256 hashes, so a stolen database does not reveal them.
- **Sessions.** A signed cookie, `HttpOnly`, `SameSite=Lax`, valid for 30 days. Set `AGENTWORKBENCH_COOKIE_SECURE=1` behind HTTPS to mark it `Secure`.
- **Login throttling.** After ten failed password logins from one IP within ten minutes, further attempts are blocked. Every failed attempt is delayed by one second.
- **Cross-site requests.** Form posts whose `Origin` header does not match the host are rejected. Together with `SameSite=Lax` cookies this covers the usual CSRF cases.
- **Rendered Markdown is sanitized.** Notes and documents are converted to HTML and cleaned with an allow-list. Scripts, event handlers and unknown tags are removed, and only `http`, `https` and `mailto` links are kept.
- **Read-only integrations.** The GitHub token should be read-only. The Proxmox token uses the `PVEAuditor` role. The dashboard only reads.
- **Checks are probes, not commands.** A task check can only fetch a URL, resolve a name or open a TCP connection. It runs no commands and does not log in anywhere.
- **The desktop terminal link cannot run commands.** It carries only a project slug and a task number, both validated, and builds a fixed prompt from them.
- **First-run setup is one-shot.** `/setup` works only while no password exists.

## What to know

- **One admin, no roles.** Everyone with the password or a passkey can change everything, including tokens and settings.
- **API tokens have full access.** A token can read all projects, notes and documents and write tasks, notes and documents. It cannot read settings or other tokens, and it cannot reach the admin area. Create one token per agent and revoke it when it is no longer needed.
- **Secrets in the database.** The GitHub token, the Proxmox token secret and the push signing key are stored in plain text in the `settings` table, because the app must use them. Protect the database file and its backups, and use tokens with the least rights.
- **No secret scanning.** Notes and documents are stored as written. Do not put credentials into them. When importing existing notes, filter secrets first.
- **No transport encryption by itself.** The app serves plain HTTP. Use a reverse proxy with HTTPS if it leaves your private network. Passkeys and push notifications work only over HTTPS.
- **Keep the password as a fallback, but keep it strong.** If you can reach the app from the internet, put an access layer in front (for example a tunnel with a login, such as Cloudflare Access, or a VPN). Then a leaked password alone is not enough.
- **SQLite file permissions.** Make the database readable only by the user that runs the app.

## Reporting a problem

If you find a security issue, please open a private security advisory on the GitHub repository instead of a public issue. See [SECURITY.md](../SECURITY.md).
