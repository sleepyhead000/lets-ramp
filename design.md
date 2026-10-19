# Design Doc (UX / UI)

Think from the user: they are mid-edit, in a hurry, and want a result that looks good immediately.

## Principles
1. **One click to a good result.** Defaults must be great.
2. **Show, don't tell.** Every preset shows its curve and an animated preview.
3. **Never lose work.** Undo always visible.
4. **Depth on demand.** Simple view first, advanced one toggle away.
5. **Fun, not childish.** Rewards stay out of the way.

## Primary flow (happy path)
1. User selects a clip on the timeline.
2. Opens Let's Ramp panel (Workspace > Workflow Integrations).
3. Panel shows clip name + duration; preset grid is active.
4. Hover a preset: curve animates, "new duration" shown.
5. Click preset: ramp applied, toast: "Applied. Undo".
6. Optional: tweak in the editor, add effect/transition, Apply again.

## Screens
**1. Main panel**
- Header: logo, theme/rewards button, settings
- Clip bar: selected clip(s), duration, fps
- Preset grid (cards with mini curve + name + tag: Cinematic, Social, Car, Sport)
- Search + filter + favorites
- Big **Ramp It** button (applies selected preset)
- Quality row: Optical Flow, Motion Blur (toggle + strength)
- Undo / Restore original

**2. Curve editor**
- Speed (Y) vs clip time (X), draggable keyframes and ease handles
- Numeric fields (time, speed %), snap to markers/playhead
- Live readout: output duration, min/max speed
- Save as preset, reset

**3. Effects & Transitions drawer**
- Tabs: Effects, Transitions; thumbnails with hover preview
- Placement: "at peak", "at start", "at marker"
- Intensity slider

**4. Rewards (Themes, Trophies, Cars)**
- Garage: cars list (locked/unlocked), equip one; car animates on ramp progress bar
- Trophy shelf with progress bars
- Theme picker

**5. License / onboarding**
- First run: 3-step tour (select clip, pick preset, Ramp It), then activation field
- Offline activation option
- Studio-required screen if Resolve Free detected

**6. Settings**
Default quality, audio behavior, telemetry opt-in, preset folder, updates, diagnostics export.

## States to design
Empty (no clip selected), multiple clips, unsupported clip (still image, nested?) `[VERIFY]`, applying (progress), success, error with recovery, license expired/offline, update available.

## Copy tone
Short, confident, friendly. Buttons are verbs: "Ramp It", "Undo", "Save Preset".

## Visual system
- Dark UI matching Resolve; accent color per theme
- 8px grid, 12/14/16px type scale, system font stack
- Motion: 150 to 250 ms easing; reduce-motion setting respected
- Accessibility: keyboard navigation, contrast >= 4.5:1, labels on all controls

## Rewards UX rules
Never block features behind rewards (cosmetic only). Unlock toasts are small and dismissible. Can disable rewards entirely in Settings.

## Usability tests
5 users per persona: time to first ramp, number of errors, "would you pay" signal. Iterate before launch.
