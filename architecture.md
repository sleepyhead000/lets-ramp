# Architecture

> Status: draft. Host and ramp strategy depend on spikes in `02-feasibility-and-spikes.md`.

## 1. Overview
Let's Ramp runs as a panel inside DaVinci Resolve Studio. The panel (UI) talks to a **Ramp Engine** that turns a ramp definition into Resolve operations through an **Adapter** layer. A **License module** gates features. A **Progress module** handles themes/trophies/cars.

```
+---------------- DaVinci Resolve Studio ----------------+
|                                                        |
|  Panel UI (Electron/HTML/JS)                           |
|   |-- Curve Editor  |-- Preset Browser  |-- Rewards    |
|   v                                                    |
|  App Core                                              |
|   |-- State store                                      |
|   |-- Ramp Engine (model -> plan)                      |
|   |-- Effects/Transitions Manager                      |
|   |-- License Manager   |-- Progress Manager           |
|   v                                                    |
|  Resolve Adapter  --> Strategy A / B / C               |
|   v                                                    |
|  Resolve Scripting API / Fusion API                    |
+--------------------------------------------------------+
         |  (HTTPS, only for activate/update/telemetry)
         v
   License + Update server
```

## 2. Host choice
**Primary (proposed): Workflow Integration plugin** (Electron + Node, runs inside Resolve Studio, native panel). `[VERIFY S7]`
**Fallback:** Python/Lua script in Resolve's Scripts menu with a small UI, plus optional helper app.

Reason for primary: real UI, one-click button inside Resolve, packaged install.

## 3. Modules

| Module | Responsibility |
|---|---|
| `ui/` | Panel screens, curve editor, theme system |
| `core/state` | Single store: selection, current ramp, settings |
| `engine/model` | Ramp definition: keyframes, easing, range |
| `engine/planner` | Converts ramp -> frame mapping -> operation plan |
| `engine/strategies/{native,fusion,segments}` | Executes plan in Resolve |
| `adapter/resolve` | Thin wrapper over Resolve API (mockable) |
| `fx/` | Effects, transitions, motion blur templates + applier |
| `presets/` | Built-in + user presets (JSON) |
| `license/` | Activate, verify, offline grace, deactivate |
| `progress/` | XP, trophies, unlocks, cosmetics |
| `telemetry/` | Opt-in anonymous usage + crash reports |
| `updater/` | Check version, download, verify signature |
| `installer/` | Mac pkg / Windows MSI |

## 4. Core data model
```json
{
  "id": "hero-slowmo",
  "name": "Hero Slow-Mo",
  "version": 1,
  "keyframes": [
    {"t": 0.0, "speed": 1.0, "ease": "easeIn"},
    {"t": 0.4, "speed": 0.2, "ease": "linear"},
    {"t": 0.7, "speed": 0.2, "ease": "easeOut"},
    {"t": 1.0, "speed": 1.0, "ease": "linear"}
  ],
  "quality": {"opticalFlow": true, "motionBlur": {"enabled": true, "strength": 0.5}},
  "fx": [{"id": "zoom-punch", "at": 0.4, "params": {}}],
  "transition": null,
  "audio": "mute|keepPitch|followSpeed"
}
```
`t` is normalized clip position (0 to 1) so one preset fits any clip length.

## 5. Ramp Engine pipeline
1. **Read** selected clip(s): frame rate, duration, in/out, linked audio.
2. **Resolve ramp**: normalized keyframes -> clip frames; clamp speed range.
3. **Integrate speed curve** -> output-frame to source-frame map (so total duration is predictable and shown to user).
4. **Snapshot** original (clip properties + duplicate hidden on a disabled track or saved marker data `[VERIFY S9]`) for undo.
5. **Execute** via chosen strategy:
   - **A. Native retime curve** (best)
   - **B. Segment split**: N constant-speed segments approximating the curve
   - **C. Fusion time-remap**: composition with animated speed
6. **Quality**: set optical flow / motion estimation, add motion blur.
7. **Apply fx/transition** at planned positions.
8. **Verify**: re-read clip, compare duration/map, report success or roll back.
9. **Award progress**, save history.

## 6. Resolve Adapter contract
All Resolve calls go through one interface so we can mock in tests and swap Resolve versions:
`getSelection()`, `getClipInfo()`, `setRetime(...)`, `splitClip(...)`, `setSpeed(...)`, `addFusionComp(...)`, `applyTemplate(...)`, `setMarker(...)`, `snapshot()/restore()`.
Adapter reports capabilities at startup; engine picks the strategy from capabilities.

## 7. Storage
- User data dir (per OS): presets, settings, license token, progress, logs.
- Format: JSON, versioned, migration functions on load.
- Never write into the user's project except the changes the ramp makes.

## 8. Error handling
- Every apply is transactional: on failure, restore snapshot and show a plain-language message + "copy diagnostic" button.
- Unsupported Resolve version -> clear banner, features disabled, nothing touched.

## 9. Performance
- Planner is pure functions (fast, testable).
- Batch operations queued, progress bar, cancelable.
- Targets: apply < 2 s per clip (excluding Resolve render/cache time) `[measure in S1 to S4]`.

## 10. Security & privacy
- License token signed (public-key verification offline).
- Only license/update calls hit the network; telemetry opt-in.
- Updates verified by signature.
- No user media leaves the machine.

## 11. Compatibility
Resolve Studio versions supported: define min version after spikes `[VERIFY]`. macOS (Intel + Apple Silicon) and Windows 10/11. Resolve Free: detect and show "Studio required" screen.

## 12. Tech stack (proposed)
TypeScript, Electron panel, Vitest/Jest, JSON schema validation, electron-builder (installers), a small license server (any serverless) + payment provider.
