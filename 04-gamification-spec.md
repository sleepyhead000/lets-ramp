# 04. Gamification: Themes, Trophies & Cars

Purpose: make ramping fun and encourage retention. **Cosmetic only; core features are never locked.**

## Progress
- XP per action: apply ramp (+10), custom curve (+25), save preset (+15), use effect/transition (+10), batch apply (+5 per clip, capped).
- Levels at XP thresholds; daily streak bonus (optional, can be disabled).
- Anti-abuse: XP capped per day; stored locally + signed.

## Cars (garage)
- Car appears on the progress bar/ramp animation, accelerating along the ramp curve.
- Unlock by level or trophy. Launch: 3 cars (e.g., Starter Hatch, Street Coupe, Hyper GT), all original designs (no real brands/trademarks).
- Equip one; animation speed mirrors the ramp.

## Trophies (launch 5)
First Ramp, 10 Ramps, Custom Curve Creator, Effects Explorer, Batch Boss.
Later: streaks, seasonal, preset-sharing milestones.

## Themes
Dark (default), Neon, Sunset at launch. Unlock by level; accent colors + panel art only.

## Data
`progress.json` (xp, level, unlocked[], trophies[], equipped, streak). Versioned and signed. Reset option in Settings.

## Rules
Toasts small and dismissible; can disable rewards; no dark patterns; no pay-to-unlock.

## Later ideas
Shareable ramp "cards," community presets, leaderboards (opt-in, needs server).
