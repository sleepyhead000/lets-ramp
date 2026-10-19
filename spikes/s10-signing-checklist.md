# S10. Code Signing & Notarization Checklist (manual)

Spikes S1–S9 are automated by `run_spikes.py`. S10 is distribution
infrastructure: it needs Apple/Google-issued certificates, so it stays a
manual checklist. Tick every line before Phase 4 (Commerce) exit.

## macOS (Intel + Apple Silicon)

- [ ] Apple Developer Program membership active ($99/yr).
- [ ] Developer ID Application certificate created (for the Electron app).
- [ ] Developer ID Installer certificate created (for the .pkg).
- [ ] `electron-builder` config set: `mac.identity` = Developer ID, hardened runtime ON.
- [ ] Notarization: `xcrun notarytool submit lets-ramp.pkg --keychain-profile ... --wait` succeeds.
- [ ] Staple: `xcrun stapler staple lets-ramp.pkg` succeeds.
- [ ] Clean macOS machine (or VM): install .pkg, Resolve finds the plugin, panel opens.
- [ ] Uninstall removes all files (run the clean-uninstaller test).

## Windows 10/11

- [ ] Code signing certificate (OV or EV; EV avoids SmartScreen reputation wait).
- [ ] Sign the installer: `signtool sign /fd SHA256 /tr http://timestamp.digicert.com lets-ramp-setup.exe`.
- [ ] Sign every shipped .exe/.dll (Electron app + any helper).
- [ ] Verify: `signtool verify /pa lets-ramp-setup.exe` reports a valid signature.
- [ ] Clean Windows VM: install, SmartScreen does not block (or shows publisher name), Resolve finds the plugin.
- [ ] Uninstall via Apps & Features leaves no leftovers.

## Plugin install paths (fill in after testing) `[VERIFY paths]`

- [ ] macOS Workflow Integration path confirmed (e.g. `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Developer/Workflow Integrations/`).
- [ ] Windows Workflow Integration path confirmed (e.g. `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Workflow Integrations\`).
- [ ] Fusion templates (.setting macros) install path confirmed (LUT folder or Fusion templates folder).
- [ ] Installer writes to the correct path for the detected Resolve version.

## Update channel

- [ ] In-app update check hits our server over HTTPS.
- [ ] Downloaded update is signature-verified before install.
- [ ] Update installs over the previous version without losing user presets/license.

## Results

Record certificate types, tool versions, and any path surprises in
`RESULTS.md` (append a manual "S10" section) and link the signed build
hashes here:

- macOS build: _pending_
- Windows build: _pending_
