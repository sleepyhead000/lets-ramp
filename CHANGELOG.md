# Changelog

## 0.2.0-alpha

The plugin becomes a real panel: full-screen UI, precise curve editing,
effects drawer, and registration under Workflow Integrations.

### Added
- Full panel UI (`plugin/LetsRamp.py` rewrite):
  - sidebar navigation: Ramp / Effects / Editor / Settings
  - preset grid with per-preset curve cards, tag filter chips, search
  - draggable curve editor: drag keyframes, double-click to add, Del to
    remove, exact time/speed spin boxes, per-segment easing, add
    keyframe at playhead, save curve as custom preset
  - effects + transitions drawer (10 + 10) with enable / intensity /
    placement; applied with snapshot protection, may no-op per version
  - quality row: Optical Flow + Faster/Better mode, Motion Blur +
    strength slider, audio mode, Keep duration
  - Keep-duration scaling (speeds scaled so output length matches source)
  - toast status messages, log dialogs, Studio-edition detection
  - custom presets + settings persisted to `~/.lets-ramp/`
- Workflow Integration install: copies `LetsRamp.py` into Resolve's
  `Workflow Integration Plugins` root so the panel appears under
  **Workspace > Workflow Integrations** (Scripts > Utility kept as
  fallback); installer and guides updated for Windows + macOS
- 45 Python unit tests for the plugin's pure engine
  (`tests/plugin/test_engine.py`)

### Fixed
- Negative speeds (Reverse Pop) no longer clamp to +1%; magnitude is
  clamped but the sign is preserved, and the duration integral uses
  |speed|
- Multi-keyframe ramps now try keyframed retime properties first;
  the single-speed fallback is only used for constant curves (v0.1
  could leave a mid-point scalar speed on a keyframed ramp)
- `hold` easing implemented in the plugin engine
- Invalid/garbage speeds and non-finite values sanitize instead of
  producing broken integrals

## 0.1.1-alpha

- One-click Windows installer: `Install-LetsRamp.cmd` (double-click),
  `Install-LetsRamp.ps1` with `-Uninstall` support
- Install guides rewritten around the installer
- Same plugin features as 0.1.0-alpha

## 0.1.0-alpha

First public release. Installable Resolve script + engine + spike harness.

### Added
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
- No signing, licensing, or effects pack yet
- Free Resolve is not supported
