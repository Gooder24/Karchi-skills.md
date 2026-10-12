# Several accounts at once

Use the accounts gateway when a task needs more than one logged-in user: checking what each role
sees, that one user cannot reach another user's data, or a flow where one user acts and another
one sees the result.

The gateway gives every test account its own local address and keeps the login itself. Opening the
address is being that account. No login steps, no storage state files.

## Start the gateway

The gateway comes with this skill: `accounts/` in the skill's folder, next to `SKILL.md`.

```bash
node ~/.claude/skills/playwright-cli/accounts/gateway.js accounts.local.json
```

It prints one address per account and keeps running. Run it in the background and read the
addresses from its output. See [accounts/README.md](../accounts/README.md) for the config.

## One session per account

```bash
playwright-cli -s=admin open http://127.0.0.1:4301/
playwright-cli -s=viewer open http://127.0.0.1:4302/

# Act as one account, observe as the other
playwright-cli -s=admin click e12
playwright-cli -s=viewer goto http://127.0.0.1:4302/reports/
playwright-cli -s=viewer snapshot
```

Name the session after the account so the commands read as who is acting.

## Who may see an address

Ask every account for the same path and compare the status codes:

```bash
for port in 4301 4302 4303; do
  curl -s -o /dev/null -w "$port %{http_code}\n" http://127.0.0.1:$port/admin/users/
done
```

A `200` where a `403`, `404` or a redirect to the login page was expected is a finding.

## All accounts on one screen

`http://127.0.0.1:4300/` is a board with every account in its own pane. Open it in a session to
take one screenshot of all roles:

```bash
playwright-cli -s=board open http://127.0.0.1:4300/
playwright-cli -s=board screenshot
```

## If an account shows the login page

The session of that account ended (logout, expiry, password change). Open
`/__accounts/relogin` on its address to repeat the login:

```bash
playwright-cli -s=viewer goto http://127.0.0.1:4302/__accounts/relogin
```

A one-time code cannot be used twice, so wait 30 seconds before repeating a login that has a second factor.
