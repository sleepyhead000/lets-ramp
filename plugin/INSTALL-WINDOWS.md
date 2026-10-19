# Install Let's Ramp (Windows)

## One-click install (recommended)

1. Extract the release zip.
2. Double-click **Install-LetsRamp.cmd**.
   - Accept the UAC prompt (admin is needed to write to ProgramData).
   - The script finds Resolve, copies `LetsRamp.py` into the right
     folder (creating it if needed), and tells you when it's done.
3. Open (or restart) DaVinci Resolve Studio.
4. Menu: **Workspace > Scripts > Utility > LetsRamp**.

If `LetsRamp.py` is missing next to the script, it is downloaded
automatically from the GitHub repo.

## Uninstall

Double-click the same `Install-LetsRamp.cmd` with the `-Uninstall`
argument, or run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Install-LetsRamp.ps1 -Uninstall
```

## Manual install (no script)

1. Press **Win+R**, paste `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Editor Pages\Scripts\Utility` and Enter (create the folder if needed).
2. Copy `LetsRamp.py` into it.
3. Restart Resolve. **Workspace > Scripts > Utility > LetsRamp**.

## Troubleshooting

- **UAC denied** → run the `.cmd` again and accept, or use the manual steps.
- **Menu item missing** → confirm the file is in
  `...\Editor Pages\Scripts\Utility` (not a subfolder), then restart Resolve.
- **Panel says "could not attach to Resolve"** → make sure you launch it
  from inside Resolve's Scripts menu, and that you run Resolve **Studio**.
