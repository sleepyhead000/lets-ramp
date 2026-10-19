# 03. Ramp, Effects & Transitions Spec

## Ramp rules
- Speed is a percentage of normal (100% = normal). Reverse = negative `[VERIFY support]`.
- Easing: linear, easeIn, easeOut, easeInOut, hold (step).
- Ramp output duration = integral of 1/speed over the clip; always show it before applying.
- Option: **Keep duration** (trim/extend to fit) vs **Let duration change**.
- Frame-rate aware: avoid sub-frame artifacts; optical flow recommended below ~50% speed.

## Starter presets (v1)
| Name | Shape | Use |
|---|---|---|
| Slow-In | 100 -> 30 | Subject reveal |
| Slow-Out | 30 -> 100 | Land the action |
| Hero Slow-Mo | 100 -> 20 hold -> 100 | Cinematic |
| Impact | 100 -> 15 at hit -> 150 | Sports/action |
| Whip Ramp | 100 -> 400 -> 100 | Fast transitions |
| Bullet Time | 100 -> 5 hold -> 100 | Hero moment |
| Pulse | repeating 100/50 | Beat-style |
| Reverse Pop | 100 -> -100 -> 100 | Social punch |
| Car Launch | 50 -> 300 | Cars |
| Drift Flow | 100 -> 40 -> 120 | Cars |
(+10 more before launch)

## Motion blur
- Tie blur strength to speed change (faster = more blur) with a user multiplier.
- Implementation depends on spike S5 (ResolveFX vs Fusion blur node).

## Optical flow
- Default on for speeds < 100%.
- Offer mode choice (Faster / Better) mapped to Resolve motion estimation `[VERIFY mapping]`.
- Warn about artifacts on fast, busy motion.

## Effects pack (v1, 10)
Zoom Punch, Flash, Shake, RGB Split, Glow Pulse, Speed Lines, Vignette Pulse, Whip Pan Blur, Freeze Pop, Color Snap.

## Transitions pack (v1, 10)
Zoom Through, Whip Left/Right, Spin Blur, Flash Cut, Glitch, Film Burn, Shake Cut, Slide Push, Light Leak.

All implemented as Fusion templates/macros `[VERIFY S6]`, parameterized (intensity, direction, duration), with licensed-only access. Original assets only; no third-party copyrighted content.

## Audio
Options: mute during ramp, keep pitch, follow speed. Default: keep pitch `[VERIFY S8]`.

## Edge cases
Very short clips; clips with existing retime; already-ramped clips; speed changes beyond limits; mixed frame rates; clips with transitions at edges; compound/nested clips.
