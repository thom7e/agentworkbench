# Phone and desktop

English · [Deutsch](de/phone-and-desktop.md)

## The phone app

AgentWorkbench is a progressive web app. It opens full screen and works like an app, without an app store.

**Install:** open the site in Safari (iPhone) or Chrome (Android) and choose **Share → Add to Home Screen**. Serve the site over HTTPS if you open it from outside your home network, see [Deployment](deployment.md#https-and-reverse-proxy).

**What you get on the phone**

| Feature | How it works |
|---|---|
| Tab bar | *Today*, *Projects*, *Briefing* and *More* at the bottom. *Today* and *Projects* are two views of the home page that switch instantly |
| Quick add | The round **+** button. Enter a task or idea (use the microphone key of the keyboard to dictate), pick the project and priority, save. Without a connection the entry is kept on the phone and sent when you are back online |
| Swipe to tick off | Swipe a task card to the left |
| Pull to refresh | Pull down at the top of a page |
| Offline reading | Pages you opened are kept. Signing out clears them |
| Notifications | See below |

**Updates:** the app files carry a version number, so a new version loads by itself the next time you open the app. If something looks old, close the app completely and open it again.

## Notifications

The morning briefing and the "ticked off automatically" hints arrive as web push notifications.

1. Open the **Briefing** page in the installed app and tap **Enable notifications**. Allow them when the phone asks. A test notification arrives right away.
2. **iPhone:** web push works from iOS 16.4 on, and **only for the app added to the home screen**, not in the browser tab.
3. Tapping a notification opens the briefing page.

Notifications need HTTPS. Apple requires a valid sender contact, set it under **Admin → Settings → Contact for push messages** (a `mailto:` address you own). The server creates its own VAPID key on first use and stores it in the database.

Which devices receive notifications is decided by who tapped the bell: each device registers itself. A device that unsubscribed or was reset is removed automatically.

## Passkeys

A passkey signs you in with Face ID, Touch ID or Windows Hello instead of typing the password. It cannot be phished and cannot be guessed.

- **Add one:** **Admin → Settings → Passkeys**, enter a name (for example *iPhone*), tap **Add passkey** and confirm on the device. Passkeys need HTTPS (or `localhost`).
- **Use it:** on the login page choose **Sign in with passkey**.
- **Recommended:** one passkey per device you use, and at least two overall. The password stays as a fallback.
- **Remove one:** the list under *Passkeys* has a *Remove* link per device.

The passkey is bound to the address you registered it on. If you move the site to a new domain, add the passkeys again.

## The desktop terminal (optional, Windows)

On the desktop a small `>_` button appears next to each task, and a *Terminal* chip in the project header. A click opens **Windows Terminal in the project folder and starts your AI agent with the task as its starting prompt**. It is only shown in desktop browsers, never on phones and tablets.

**How it works.** The button is a link with a custom scheme, `agentworkbench://run?project=<slug>&todo=<id>`. A small handler registered for your Windows user receives it. The handler only accepts a valid project slug and a numeric task id, and it builds a **fixed prompt** from them (*work on task #12 of project X, read the briefing first*). Nothing from the link is ever executed as a command, and nothing is sent over the network.

**Set it up**

1. Make sure `wt.exe` (Windows Terminal) and your agent command (`claude`) are on your `PATH`.
2. Register the handler for your user (no admin rights needed):

   ```powershell
   powershell -File desktop\install_windows.ps1
   ```

3. Tell the handler where your projects live. Either set the environment variable `AWB_PROJECTS_ROOT` (default `~/projects`), or create `~/.claude/awb_paths.json`:

   ```json
   {"_root": "C:\\Users\\you\\Documents\\projects", "website": "C:\\work\\website-v2"}
   ```

   `_root` is searched for a folder named like the project slug (case, `-` and `_` ignored). Individual projects can be mapped to any folder by slug.

4. The agent finds its credentials as described in [Working with agents](agents.md#claude-code).

To use another agent or terminal, edit the last line of `desktop/awb_run.py`.
