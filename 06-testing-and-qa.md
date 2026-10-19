# 06. Testing & QA

## Layers
- **Unit:** ramp model, easing, integration, planner (pure functions, golden tests).
- **Adapter mock tests:** engine against a fake Resolve.
- **Integration:** real Resolve Studio, scripted scenarios, read back results.
- **Manual/UX:** persona-based scenarios.
- **Install tests:** clean Mac (Intel/ARM) and Windows 10/11 VMs/machines.

## Matrix
| Axis | Values |
|---|---|
| OS | macOS (Intel, Apple Silicon), Windows 10/11 |
| Resolve Studio | min supported, current, latest |
| Frame rates | 23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120 |
| Clip types | H.264/H.265, ProRes, BRAW, image sequence, speed-already-changed, nested |
| Length | 1 s, 10 s, 5 min |

## Critical scenarios
Apply/undo 50 times; batch 100 clips; cancel mid-apply; license offline; update install; Resolve restart; project reopen; ramp then render and compare to expected frame map; audio sync check.

## Performance gates
Apply time, UI frame rate, memory, no leaks across 100 applies.

## Release checklist
All spikes documented, matrix passed, installers signed, refund + license flows tested end-to-end, docs ready, rollback plan, beta feedback addressed.

## Beta
10 to 30 testers across personas; collect crash logs, time-to-first-ramp, preset popularity.
