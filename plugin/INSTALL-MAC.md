# Install Let's Ramp (macOS)

Neither option needs Python installed - Resolve runs the script with
its own bundled Python.

## Option A - one command

Open **Terminal** and run:

```bash
sudo mkdir -p "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility"
sudo cp LetsRamp.py "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility/"
```

## Option B - manual

1. In Finder press **Cmd+Shift+G** and paste:
   `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility`
2. Copy `LetsRamp.py` into that folder (authenticate if asked).
   Create the folders if they do not exist.

## Run in Resolve

1. Restart DaVinci Resolve Studio.
2. Menu: **Workspace > Scripts > Utility > LetsRamp**.
3. Select a clip, pick a preset, **Ramp It** (experimental) or
   **Run diagnostics** and paste the result into a GitHub issue.

## Uninstall

Remove `LetsRamp.py` from the Utility folder.
