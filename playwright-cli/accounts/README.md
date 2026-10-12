# Several accounts side by side

A small gateway for testing an app as several users at once, in one browser. It comes with the
`playwright-cli` skill.

A browser keeps one login per site, so a second account normally overwrites the first. The gateway
gives every test account its own local address and keeps that account's cookies itself. The browser
holds no cookies at all. The account is the port:

```
http://127.0.0.1:4300/   board: every account in its own pane, side by side
http://127.0.0.1:4301/   the app as the first account
http://127.0.0.1:4302/   the app as the second account
```

Because an account is just an address, every tool works with several accounts unchanged: browser
tabs, `curl`, and `playwright-cli` sessions.

> For test environments with throwaway accounts only. Anyone who can reach the ports on this
> machine is logged in as those accounts. The gateway listens on 127.0.0.1 and refuses requests
> that come from other websites or carry a foreign host name.

## Start

```bash
skill=~/.claude/skills/playwright-cli                            # where the skill is installed
cp $skill/accounts/accounts.example.json accounts.local.json    # holds passwords: keep it out of git
node $skill/accounts/gateway.js accounts.local.json
```

No dependencies, Node.js 18 or newer. The gateway logs every account in, prints the addresses and
keeps running until you stop it.

## Config

| Key | Meaning |
| --- | --- |
| `port` | Port of the board. Accounts follow: first account on `port + 1`, and so on. Default 4300. |
| `targets` | Name and address of the app. With two targets (for example the old and the new build over one database) the board gets a switch; the second target's accounts listen 10 ports higher. The targets must accept the same login, because every account is logged in once, against the first target. |
| `accounts[].name` | Label of the pane. |
| `accounts[].home` | Path opened first. Default `/`. |
| `accounts[].login` | Steps, in order. Each step opens `path`, takes the hidden fields of that page (CSRF token and the like), adds `fields` and posts the form. |
| `fields` value `{ "totp": "BASE32" }` | Replaced by the current six-digit code for that secret, for a second factor. |
| `accounts[].follow` | `false` keeps the pane where it is when "Open in all" is used. For accounts that live under their own address. |

An account counts as logged in when its `home` answers 200 after the steps.

## Board

- **Open in all** opens one path in every pane, to compare what each account sees at the same address.
- **Columns** sets the layout: 2 for a 2 x 2 grid, 4 for narrow phone-width panes.
- **log in again** repeats the login for one account, for example after logging out in its pane.
- **own tab** opens the account in a normal tab.
- **Ctrl+Space** zooms the pane under the pointer to the whole window, Ctrl+Space again brings the
  grid back. The other panes stay loaded, nothing reloads. **zoom** in the pane's header does the same.

Logging out or logging in by hand inside a pane works as in a normal browser; the gateway picks up
the new cookies.

For the shortcut to work while the focus is inside a pane, the gateway adds one script tag
(`/__accounts/pane.js`) to every HTML page it forwards and asks the app for uncompressed pages.

## Use with playwright-cli

One named session per account, no login steps needed:

```bash
playwright-cli -s=admin open http://127.0.0.1:4301/
playwright-cli -s=viewer open http://127.0.0.1:4302/
playwright-cli -s=viewer snapshot
playwright-cli show            # watch and control all sessions in one window
```

A quick check of who may see an address:

```bash
for port in 4301 4302; do curl -s -o /dev/null -w "$port %{http_code}\n" http://127.0.0.1:$port/admin/; done
```

## Limits

- One flat cookie jar per account: cookie `Path` and `Domain` are ignored. Enough for one app per gateway.
- No WebSocket forwarding.
- At most 9 accounts per board.
- Inside a pane, Ctrl+Space needs the app to allow scripts from its own origin. With a stricter
  Content-Security-Policy use the pane's **zoom** link, or press the shortcut with the focus on the board.

## Tests

```bash
node --test ~/.claude/skills/playwright-cli/accounts/gateway.test.js
```
