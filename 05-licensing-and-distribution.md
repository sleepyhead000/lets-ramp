# 05. Licensing, Payments & Distribution

## Purchase flow
1. Customer buys on sales page (payment provider/merchant of record `[DECIDE]`, handles tax).
2. Receives license key + installer links by email.
3. Installs, opens panel, enters key -> activated.

## License model
- Lifetime license, N devices (e.g., 2) `[DECIDE]`.
- Activation: key + machine fingerprint -> server returns **signed token**.
- Offline use: token valid; re-check every 30 days with 14-day grace `[DECIDE]`.
- Deactivate device from panel or support to move machines.
- Refund -> key revoked at next check.
- Piracy: signed tokens, key rate-limits; don't harm paying users with aggressive DRM.

## Refund policy ("100% satisfaction")
Define window (e.g., 14 or 30 days) `[DECIDE]`, state it on the page, automate via payment provider, and offer a "Tell us why" form.

## Lifetime updates
Define clearly: free updates for the life of the product (v1.x and later); a possible future major version needs a policy statement now to avoid disputes. Update channel inside the panel.

## Distribution
- Mac: signed + notarized `.pkg` (Intel + Apple Silicon). Windows: signed `.msi`/`.exe`.
- Installer places plugin in Resolve's plugin folder `[VERIFY paths]`, installs template assets, and checks for Resolve Studio.
- Clean uninstaller.
- Update: in-app check, signed download.

## Compatibility messaging
Sales page already says Studio only. Panel detects Free and explains. Publish a tested-versions table.

## Support
Docs site, quick-start video, FAQ, email support, diagnostics export, public changelog. Target first response < 24 h.

## Legal
EULA, privacy policy (telemetry opt-in), no use of Blackmagic trademarks beyond factual compatibility statements `[check with lawyer]`.
