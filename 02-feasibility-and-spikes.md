# 02. Feasibility & Spikes (do these first)

The entire product depends on what Resolve lets a plugin do. These are **unverified**. Each spike is a 1 to 2 day test with a pass/fail result, run on Resolve Studio (latest) on both Mac and Windows.

| # | Question | Why it matters | Pass criteria |
|---|---|---|---|
| S1 | Can scripting/Workflow Integration set a **variable-speed retime curve** (keyframed speed) on a timeline item? | Decides ramp strategy A | Curve with 5+ keyframes created from code |
| S2 | Can a script set `RetimeProcess` = optical flow and motion estimation mode on a clip? | Optical flow built-in | Property reads back correctly `[VERIFY property names in current API docs]` |
| S3 | Segment-split: can we split a clip and set constant speed per segment cleanly? | Fallback strategy B | 12 segments, no gaps/overlaps, correct duration |
| S4 | Fusion composition with Time Stretcher/Speed Redirect driven by animated speed: frame-accurate and fast? | Fallback strategy C | Correct frame mapping, playback OK |
| S5 | Can we apply motion blur from code (ResolveFX, or Fusion blur node)? | Built-in motion blur | Visible blur tied to speed |
| S6 | Can we install Fusion templates (effects/transitions) and apply them to a clip from code? | Effects & transitions | Template appears and applies |
| S7 | Workflow Integration plugin: UI in an Electron panel, access to Resolve API, install paths on Mac/Win | Primary host choice | Panel loads, reads selected clip |
| S8 | Does speed change preserve audio sync, and what happens to linked audio? | Audio quality | Documented behavior |
| S9 | Can we undo cleanly? (Resolve API has no known undo hook `[VERIFY]`) | Safety | Original restorable via snapshot/duplicate |
| S10 | Code signing/notarization + plugin loading on macOS and Windows | Distribution | Installs on clean machine |

## Decision after spikes
- If S1 passes: **Strategy A** (native curve), the best result.
- Else if S4 passes: **Strategy C** (Fusion time-remap).
- Else: **Strategy B** (segments) with a high segment count.
- If S7 fails: fall back to Python/Lua script + external helper app.

Record every result in `spikes/RESULTS.md` with Resolve version and OS.
