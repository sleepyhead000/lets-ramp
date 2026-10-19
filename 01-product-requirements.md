# 01. Product Requirements

## Promise (from the sales page)
One-click speed ramp, built-in motion blur + optical flow, built-in effects & transitions, unlockable themes/trophies/cars, fully customizable. Studio only. Mac + Windows. Refund guarantee. Lifetime updates.

## Users
| Persona | Goal | Pain today |
|---|---|---|
| Social editor (Reels/TikTok/Shorts) | Punchy ramp in seconds | Retime curve is fiddly, many clicks |
| Car / sports / action editor | Cinematic slow-fast-slow | Smoothness, blur, matching beats |
| Beginner | Looks pro with zero learning | Doesn't know retime curves or optical flow |
| Pro colorist/editor | Control + repeatability | Wants exact curves, presets, batch |

## Core user stories
1. Select a clip, click a preset, ramp applied. (**One-click**)
2. See a live preview of the speed curve before applying.
3. Drag curve handles to customize; save as my own preset.
4. Optical flow and motion blur on by default; toggle per ramp.
5. Add a transition or effect (zoom punch, flash, shake) at the ramp peak with one click.
6. Apply to many clips at once.
7. Undo a ramp and restore the original clip.
8. Match ramp to a marker or beat.
9. Unlock themes/trophies/cars by using the plugin.
10. Activate license once; works offline afterward.

## Feature list
**MVP (v1.0)**
- Preset library (20+ ramps): slow-in, slow-out, hero slow-mo, impact, whip, bullet time, reverse ramp, pulse
- Curve editor (keyframes, ease handles, speed range 1% to 1000% `[VERIFY limits]`)
- Apply to selected clip(s) in timeline
- Optical flow + motion blur toggles
- Effects pack (10) and transitions pack (10)
- Undo / restore
- License activation, offline grace period
- 3 themes, 5 trophies, 3 cars at launch
- Mac + Windows installer

**v1.1+**
- Marker-driven ramps, beat detection
- Batch apply, preset import/export
- Audio pitch handling options
- More themes/cars, seasonal unlocks

## Non-goals (v1)
Free Resolve support, Premiere/FCP ports, cloud project sync, AI auto-ramp.

## Success metrics
- Time from install to first ramp < 3 min
- First-ramp success rate > 95%
- Refund rate < 5%
- Support tickets per 100 sales < 10
- Preset applied per active user per week

## Constraints
- Resolve Studio required `[VERIFY: which integration types require Studio]`
- Must not corrupt user timelines: every apply is reversible
