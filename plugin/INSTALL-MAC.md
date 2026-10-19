# Install Let's Ramp (macOS)

Neither option needs Python installed - Resolve runs the plugin with
its own bundled Python.

## Option A - one command

Open **Terminal** and run:

```bash
sudo mkdir -p "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins"
sudo cp LetsRamp.py "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/"
```

Optional fallback for older Resolve versions:

```bash
sudo mkdir -p "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility"
sudo cp LetsRamp.py "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility/"
```

## Option B - manual

1. In Finder press **Cmd+Shift+G** and paste:
   `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins`
2. Copy `LetsRamp.py` into that folder (authenticate if asked).
   Create the folders if they do not exist.

## Run in Resolve

1. Restart DaVinci Resolve Studio.
2. Menu: **Workspace > Workflow Integrations > LetsRamp**
   (fallback: **Workspace > Scripts > Utility > LetsRamp**).
3. Select a clip, pick a preset, **Ramp It**, or open **Settings > Run
   diagnostics** and paste the result into a GitHub issue.

## Uninstall

Remove `LetsRamp.py` from the Workflow Integration Plugins folder
(and the Utility folder if you used the fallback).
