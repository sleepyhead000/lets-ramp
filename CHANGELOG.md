# Changelog

## 0.1.0-alpha

First public release. Installable Resolve script + engine + spike harness.

### Added
- `plugin/Install-LetsRamp.cmd` + `Install-LetsRamp.ps1` - one-click
  Windows installer: finds Resolve, creates the Utility folder, copies
  the script (downloads it from GitHub if missing), verifies the file,
  supports `-Uninstall`
- `plugin/LetsRamp.py` - DaVinci Resolve Studio utility script:
  - 10 starter presets with live speed-curve preview
  - output-duration calculation (integral of 1/speed)
  - experimental ramp apply (property-bag snapshot, restore on failure)
  - Undo last apply
  - read-only diagnostics report (clipboard + `~/lets-ramp-diagnostics.txt`)
  - quality toggles: optical flow, motion blur, audio mode
- Windows + macOS install guides and copy helpers
- Pure ramp engine (TypeScript): model + validation, easings, frame-map
  integrator, strategy planner (native / segments / fusion), mock Resolve
  adapter, transactional apply with rollback
- 53 unit tests covering the engine and adapter
- Spike harness `spikes/run_spikes.py` (S1-S9) + S10 signing checklist +
  S7 Workflow Integration panel scaffold

### Known limitations
- Ramp apply depends on undocumented Resolve API surface; may no-op on
  some versions (the diagnostics log records why)
- No installer, signing, licensing, or effects pack yet
- Free Resolve is not supported
