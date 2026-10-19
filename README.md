# Let's Ramp

One-click speed ramps for **DaVinci Resolve Studio** (macOS + Windows).
Pick a preset, see the curve and new duration, hit **Ramp It**. Tweak
every keyframe in the curve editor, stack experimental effects, undo
anything.

> **Status: alpha (v0.2.0-alpha).** The installable piece today is a
> Resolve **plugin panel** with preset grid, draggable curve editor,
> effects drawer, quality settings, custom presets, diagnostics, and an
> *experimental* ramp apply. Motion blur strength mapping, the full
> Fusion effects pack, licensing and rewards are planned - see the
> [roadmap](07-roadmap.md). The apply step depends on what the Resolve
> scripting API actually allows; we collect that data via diagnostics
> ([feasibility spikes](02-feasibility-and-spikes.md)).

## Install (30 seconds, no Python needed)

Resolve ships its own Python - you do **not** install anything extra.

### Windows
1. Download **lets-ramp-plugin.zip** from the
   [latest release](../../releases/latest) and extract it.
2. Double-click **Install-LetsRamp.cmd** (accept the UAC prompt).
3. Open (or restart) Resolve Studio.
4. Menu: **Workspace > Workflow Integrations > LetsRamp**
   (fallback: **Workspace > Scripts > Utility > LetsRamp**).

Details, uninstall, troubleshooting: [plugin/INSTALL-WINDOWS.md](plugin/INSTALL-WINDOWS.md)

### macOS
1. Download and extract the release zip.
2. In Terminal, from the extracted folder:
   ```bash
   sudo mkdir -p "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins"
   sudo cp LetsRamp.py "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/"
   ```
3. Restart Resolve Studio.
4. Menu: **Workspace > Workflow Integrations > LetsRamp**.

Details: [plugin/INSTALL-MAC.md](plugin/INSTALL-MAC.md)

## Use

1. Select a clip on the timeline (video track 1).
2. Open the panel: **Workspace > Workflow Integrations > LetsRamp**.
3. The **Ramp** tab shows clip name, length and fps, plus a preset
   grid (Slow-In, Hero Slow-Mo, Impact, Whip Ramp, Bullet Time, Pulse,
   Reverse Pop, Car Launch, Drift Flow...). Each card draws its curve;
   the output duration updates live.
4. Click a preset, then **Ramp It**. The panel snapshots the clip
   first, tries known speed-property paths in priority order (keyframed
   retime first, single-speed fallback), applies quality settings
   (optical flow, motion blur, audio mode), and restores everything if
   nothing sticks. A log dialog shows exactly which properties your
   Resolve accepted.
5. **Undo** restores the snapshot and removes any Fusion comps the
   plugin added.
6. Fine-tune on the **Editor** tab: drag keyframes, set exact time and
   speed percentages, pick per-segment easing, add a keyframe at the
   playhead, save your curve as a custom preset.
7. Stack **Effects** and **Transitions** (experimental) from their tab:
   check what you want, set intensity and placement, then Ramp It. They
   ride along with snapshot/undo protection and may no-op on some
   Resolve versions - the log always says what happened.
8. **Settings > Run diagnostics** produces a read-only API probe, saved
   to your home folder and copied to the clipboard. Pasting it into a
   GitHub issue helps us support your Resolve version.

Quality toggles (Optical Flow + Faster/Better mode, Motion Blur +
strength, audio mode, Keep duration) are sent along with the apply;
whether they take effect depends on your Resolve version.

## What works today

| Feature | State |
|---|---|
| Preset grid with curve cards (10 ramps + custom) | works |
| Draggable curve editor, exact numeric control | works |
| Output duration calculation (integral of 1/speed) | works |
| Keep-duration scaling | works |
| Quality settings (optical flow, motion blur, audio) | sent with apply |
| Custom preset save/load | works |
| Experimental ramp apply + snapshot/undo | works on some Resolve versions - tell us yours |
| Effects / transitions (experimental, snapshot-protected) | may no-op - log tells you |
| Diagnostics report | works |
| Rewards / licensing | not yet |

## Requirements

- DaVinci Resolve **Studio** (Free is not supported)
- Windows 10/11 or macOS (Intel / Apple Silicon)

## Building from source

```bash
npm install
npm test        # 53 engine tests
python -m unittest discover -s tests/plugin   # 45 plugin engine tests
```

The pure ramp engine lives in [`src/engine`](src/engine) (TypeScript);
the same math ships inside the plugin. The spike harness for Resolve
API research is in [`spikes`](spikes).

## Contributing your diagnostics

The fastest way to help: install the plugin, open **Settings > Run
diagnostics**, and open an issue with the report attached (or paste
it). If **Ramp It** worked on your machine, say so - we will prioritize
that API path.

## Docs

| Doc | What it is |
|---|---|
| [01-product-requirements](01-product-requirements.md) | users, stories, scope |
| [02-feasibility-and-spikes](02-feasibility-and-spikes.md) | open API questions + tests |
| [architecture](architecture.md) | system design |
| [design](design.md) | UX / UI |
| [03-ramp-and-effects-spec](03-ramp-and-effects-spec.md) | ramp model, presets, effects |
| [04-gamification-spec](04-gamification-spec.md) | themes, trophies, cars |
| [05-licensing-and-distribution](05-licensing-and-distribution.md) | licensing, installers |
| [06-testing-and-qa](06-testing-and-qa.md) | test matrix |
| [07-roadmap](07-roadmap.md) | phases and risks |

## License

Source available; all rights reserved unless a LICENSE file says otherwise.
Original assets only - no Blackmagic trademarks beyond factual
compatibility statements.
