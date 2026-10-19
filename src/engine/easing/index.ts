import type { Easing } from "../model/ramp.js";

/**
 * Evaluate an easing curve at normalized position u in [0, 1].
 * Returns the interpolation factor in [0, 1] used to blend
 * between the speed of keyframe i and keyframe i+1.
 */
export function evaluateEasing(ease: Easing, u: number): number {
  const x = Math.min(1, Math.max(0, u));
  switch (ease) {
    case "linear":
      return x;
    case "easeIn":
      return x * x;
    case "easeOut":
      return 1 - (1 - x) * (1 - x);
    case "easeInOut":
      return x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
    case "hold":
      return 0;
  }
}
