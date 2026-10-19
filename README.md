# Let's Ramp

One-click speed ramps for **DaVinci Resolve Studio** (macOS + Windows).
Pick a preset, see the curve and new duration, hit **Ramp It**.

> **Status: early alpha (v0.1.0-alpha).** The installable piece today is a
> Resolve **script** with preset browser, curve preview, duration math,
> diagnostics, and an *experimental* ramp apply. The full panel plugin,
> motion blur, effects pack, licensing and rewards are planned - see the
> [roadmap](07-roadmap.md). The apply step depends on what the Resolve
> scripting API actually allows; we are collecting that data via
> diagnostics ([feasibility spikes](02-feasibility-and-spikes.md)).

## Install (30 seconds, no Python needed)

Resolve ships its own Python - you do **not** install anything extra.

### Windows
1. Download **lets-ramp-plugin.zip** from the
   [latest release](../../releases/latest) and extract it.
2. Double-click **Install-LetsRamp.cmd** (accept the UAC prompt).
3. Open (or restart) Resolve Studio.
4. Menu: **Workspace > Scripts > Utility > LetsRamp**.

Details, uninstall, troubleshooting: [plugin/INSTALL-WINDOWS.md](plugin/INSTALL-WINDOWS.md)

### macOS
1. Download and extract the release zip.
2. In Terminal, from the extracted folder:
   ```bash
   sudo mkdir -p "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility"
   sudo cp LetsRamp.py "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Support/Editor Pages/Scripts/Utility/"
   ```
3. Restart Resolve Studio.
4. Menu: **Workspace > Scripts > Utility > LetsRamp**.

Details: [plugin/INSTALL-MAC.md](plugin/INSTALL-MAC.md)

## Use

1. Select a clip on the timeline (video track 1).
2. The panel shows clip name, length and fps.
3. Click a preset (Slow-In, Hero Slow-Mo, Impact, Whip, Bullet Time,
   Pulse, Reverse Pop, Car Launch, Drift Flow...) - the curve preview and
   the **output duration** update instantly.
4. **Ramp It (experimental)** tries to apply the speed change. It
   snapshots the clip first and restores it if nothing sticks. Works or
   not, the log tells you exactly which properties your Resolve accepted
   - that feedback is valuable.
5. **Undo last apply** restores the snapshot.
6. **Run diagnostics** produces a read-only API probe, saved to your
   home folder and copied to the clipboard. Pasting it into a GitHub
   issue helps us support your Resolve version.

Quality toggles (Optical flow, Motion blur, audio mode) are sent along
with the apply; whether they take effect depends on your Resolve version.

## What works today

| Feature | State |
|---|---|
| Preset browser (10 ramps) + curve preview | works |
| Output duration calculation | works |
| Diagnostics report | works |
| Experimental ramp apply + snapshot/undo | works on some Resolve versions - tell us yours |
| Motion blur / effects / transitions / rewards / licensing | not yet |

## Requirements

- DaVinci Resolve **Studio** (Free is not supported)
- Windows 10/11 or macOS (Intel / Apple Silicon)

## Building from source

```bash
npm install
npm test        # 53 engine tests
```

The pure ramp engine lives in [`src/engine`](src/engine) (TypeScript).
The spike harness for Resolve API research is in [`spikes`](spikes).

## Contributing your diagnostics

The fastest way to help: install the script, click **Run diagnostics**,
and open an issue with the report attached (or paste it). If **Ramp It**
worked on your machine, say so - we will prioritize that API path.

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
