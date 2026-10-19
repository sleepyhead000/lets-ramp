# Changelog

## 0.2.3-alpha

Fix: the UIManager is now obtained the way Blackmagic documents it.

### Fixed
- On Resolve 18.6 the injected `fusion` object exposes `UIManager` as
  a **property** (`ui = fu.UIManager`), but the probe *called* it
  (`fusion.UIManager()`) and got `None` back - the cause of
  "could not create a UI". The probe now tries the attribute
  **without calling first** (documented pattern), falls back to the
  call form for builds where it is a method, and accepts a candidate
  only after a real usability check (`Label({...})` factory returns
  an element). Every attempt is logged with its outcome
- Event wiring used a non-existent form
  (`win.On[id].Event = fn`). It now uses the documented element form
  (`elm.On.Clicked = fn`) first, then the window form
  (`win.On[id].Event.Close = fn`), logging any failure per event
- Failure now prints a `dir(fusion)` hint listing UI/Window members so
  a future version mismatch identifies itself immediately

### Added
- 4 more probe tests (property manager, method manager, unusable
  manager, failing Label factory) - 55 total

## 0.2.2-alpha

Diagnostics release: the silent UI-probe failure is impossible now.

### Fixed
- `fusion_ui_context()` could return "could not create a UI" with an
  **empty error list** when `fusion.UIManager()` returned `None`
  without raising - the exact failure seen on Resolve 18.6. It now
  records every probe step (globals, import, scriptapp, Fusion(),
  UIManager attribute/call, UIDispatcher) with type/repr results and
  explicit FAIL/EXIT markers, so a failure always names the step that
  died

### Added
- Full probe trail printed to the console and written to
  `~/lets-ramp-ui-log.txt` on **every** run (success or failure);
  failures also append it to `~/lets-ramp-crash.txt` with traceback if
  the probe itself raised

## 0.2.1-alpha

Fix: the panel now opens on Resolve builds without Python Qt bindings
(e.g. Resolve 18.6 Windows).

### Added
- **Fusion UIManager backend**: when PySide/PyQt is not importable
  inside Resolve's Python (Resolve 18.x ships none), the panel now
  builds itself with Resolve's built-in UIManager instead - the same
  toolkit Blackmagic's own Workflow Integration sample uses. Same
  features: preset combo with live curve sparkline, duration math,
  numeric keyframe editor (index/time/speed/ease), add at playhead,
  custom preset save, quality controls, effects + transitions
  selectors, Ramp It / Undo / Refresh / Diagnostics, log pane
- Backend selection is automatic: Qt window when bindings exist,
  UIManager window otherwise; failure logs exactly which UI object
  was missing (also written to `~/lets-ramp-crash.txt`)
- 51 plugin engine tests (sparkline renderer + UI context probe)

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
