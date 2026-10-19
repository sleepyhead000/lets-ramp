# 07. Roadmap & Risks

## Phases
| Phase | Scope | Exit |
|---|---|---|
| 0. Spikes | S1 to S10 | Strategy + host chosen, results documented |
| 1. Core | Model, planner, adapter, chosen strategy, basic panel, undo | Ramp applied reliably on both OS |
| 2. Product | Preset library, curve editor, optical flow, motion blur | Feature-complete ramp |
| 3. Polish | Effects, transitions, rewards, onboarding | UX tests pass |
| 4. Commerce | Licensing, installers, signing, docs, sales page sync | End-to-end purchase to ramp |
| 5. Beta | Closed beta + fixes | Beta gates met |
| 6. Launch | Public release, support ready | v1.0 |
| 7. Post-launch | Beat sync, batch+, preset sharing | v1.1+ |

Dates: set after Phase 0 (estimates before spikes would be guesses).

## Risks
| Risk | Impact | Mitigation |
|---|---|---|
| API can't do native retime curves | Lower quality ramps | Strategies B/C, many segments |
| Resolve updates break API | Plugin breaks | Adapter layer, version tests, fast patch cadence |
| Motion blur/effects not scriptable | Promise gap | Fusion templates; adjust claims on page |
| Segment approach leaves cuts/artifacts | Bad UX | Validate S3, hide behind compound clip if possible |
| Notarization/signing delays | Launch slip | Start certs early |
| Refund abuse / piracy | Revenue | Signed tokens, clear policy |
| Sales page promises exceed tech | Refunds | Align copy with spike outcomes |
