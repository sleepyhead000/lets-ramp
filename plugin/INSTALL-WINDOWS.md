# Install Let's Ramp (Windows)

## One-click install (recommended)

1. Extract the release zip.
2. Double-click **Install-LetsRamp.cmd**.
   - Accept the UAC prompt (admin is needed to write to ProgramData).
   - The script copies `LetsRamp.py` into Resolve's **Workflow
     Integration Plugins** root (the panel appears under
     **Workspace > Workflow Integrations**) and into the **Scripts >
     Utility** folder as a fallback for older Resolve versions.
3. Open (or restart) DaVinci Resolve Studio.
4. Menu: **Workspace > Workflow Integrations > LetsRamp**
   (fallback: **Workspace > Scripts > Utility > LetsRamp**).

If `LetsRamp.py` is missing next to the script, it is downloaded
automatically from the GitHub repo.

## Uninstall

Double-click the same `Install-LetsRamp.cmd` with the `-Uninstall`
argument, or run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File Install-LetsRamp.ps1 -Uninstall
```

## Manual install (no script)

1. Press **Win+R**, paste
   `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Workflow Integration Plugins`
   and Enter (create the folder if needed).
2. Copy `LetsRamp.py` into it.
3. Optional fallback for older versions: also copy it into
   `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Editor Pages\Scripts\Utility`.
4. Restart Resolve. **Workspace > Workflow Integrations > LetsRamp**.

## Troubleshooting

- **UAC denied** → run the `.cmd` again and accept, or use the manual steps.
- **Menu item missing** → confirm the file sits directly in the
  `Workflow Integration Plugins` folder (not a subfolder), then restart
  Resolve. If your Resolve version predates Workflow Integrations, use
  the Scripts > Utility fallback path.
- **Panel says "could not attach to Resolve"** → make sure you launch it
  from inside Resolve's menu, and that you run Resolve **Studio**.
- **Panel opens but Ramp It does nothing** → open **Settings > Run
  diagnostics**, copy the report, and paste it into a GitHub issue -
  your Resolve version's API surface is exactly what we need.
