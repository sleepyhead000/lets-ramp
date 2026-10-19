# Install Let's Ramp (Windows)

Two options. Neither needs Python installed - Resolve runs the script
with its own bundled Python.

## Option A - one command

Right-click **Start** > **Windows PowerShell**, paste:

```powershell
Copy-Item "$PSScriptRoot\LetsRamp.py" "$env:PROGRAMDATA\Blackmagic Design\DaVinci Resolve\Support\Editor Pages\Scripts\Utility\" -Force
```

(If you downloaded the release zip, `cd` into the extracted folder first.)

## Option B - manual

1. Open this folder in Explorer.
2. Press **Win+R**, paste `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Editor Pages\Scripts\Utility` and Enter.
   (If the folder does not exist, create it.)
3. Copy `LetsRamp.py` into it.

## Run in Resolve

1. Restart DaVinci Resolve Studio (or reopen the project).
2. Menu: **Workspace > Scripts > Utility > LetsRamp**.
3. Select a clip on the timeline, pick a preset, click **Ramp It**
   (experimental in this alpha) or **Run diagnostics** and paste the
   result into a GitHub issue.

## Uninstall

Delete `LetsRamp.py` from the Utility folder.
