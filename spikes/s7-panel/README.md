# S7 Panel Scaffold (manual load test)

Minimal Workflow Integration used only to verify spike S7: that Resolve
Studio loads an Electron/HTML panel and the panel can talk to the
Resolve API to read the current selection.

## Install (per OS) `[VERIFY exact paths]`

**macOS**
```
mkdir -p "~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Developer/Workflow Integrations/LetsRamp"
cp manifest.json index.html "<that folder>/"
```

**Windows**
```
mkdir "%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Workflow Integrations\LetsRamp"
copy manifest.json index.html "%APPDATA%\...\LetsRamp\"
```

Then restart Resolve. Open **Workspace > Workflow Integrations > LetsRamp**.

## Pass criteria (fill in RESULTS.md)

- [ ] Panel appears in the menu after restart.
- [ ] Panel renders without a blank/white screen.
- [ ] With a clip selected on the timeline, the panel displays the clip name.
- [ ] Panel can read clip duration and fps.

If any box fails: S7 FAIL -> fall back to Python/Lua script + helper app
(decision table in `02-feasibility-and-spikes.md`).

## What index.html does

Shows the selected clip's name/duration via the Workflow Integration UI
API bridge. Pure diagnostic UI; the real panel is built in Phase 1.
