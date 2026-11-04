# Prehľad dvora

What runs on Karchi's machines on a schedule or all the time, which of it calls AI and on what
subscription, and what is waiting for an update. Served on asus by the user unit `prehlad.service` at https://rerun.dvoriste.xyz/prehlad/ (next to
Rerun, behind Cloudflare Access) and on Tailscale at https://100.110.180.15:3443/prehlad/.

- `inventory.py`: every recurring or always-on process on asus, dell, e540, x270 and the VPS (read-only).
- `updates.py`: system updates per machine and the hand-installed tools on asus against their newest release.
- `prehlad/server.py`: reruns both (30 min and 6 h), works out the next run of each job, serves the page.
- `prehlad/farby.default.json`: project families and their colours, taken from Kalendarix where a
  calendar fits. Edits from the page land in `~/.config/prehlad/farby.json`.

Install on asus: copy `prehlad.service` below to `~/.config/systemd/user/` and
`systemctl --user enable --now prehlad`; Caddy (`~/matrix-spike/web/Caddyfile`) routes `/prehlad/*` to 127.0.0.1:3460.

```ini
[Unit]
Description=Prehľad dvora
After=network-online.target

[Service]
Environment=PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 %h/.work/karchi-skills/inventory/prehlad/server.py 3460
Restart=on-failure

[Install]
WantedBy=default.target
```
