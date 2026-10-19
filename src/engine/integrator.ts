import { evaluateEasing } from "./easing/index.js";
import { clampSpeed, type RampDefinition, type RampKeyframe } from "./model/ramp.js";

/**
 * Sample the speed multiplier at normalized clip position t in [0, 1].
 * Speed is interpolated from keyframe i to keyframe i+1 using keyframe i's ease.
 * A "hold" ease holds the previous speed until the next keyframe.
 */
export function sampleSpeed(ramp: RampDefinition, t: number): number {
  const tc = Math.min(1, Math.max(0, t));
  const kfs = ramp.keyframes;
  if (kfs.length === 0) {
    throw new Error("ramp has no keyframes");
  }
  if (tc <= kfs[0]!.t) {
    return clampSpeed(kfs[0]!.speed);
  }
  const last = kfs[kfs.length - 1]!;
  if (tc >= last.t) {
    return clampSpeed(last.speed);
  }
  let i = 0;
  while (i < kfs.length - 1 && kfs[i + 1]!.t <= tc) {
    i++;
  }
  const a = kfs[i]!;
  const b = kfs[i + 1]!;
  const span = b.t - a.t;
  if (span <= 0) {
    return clampSpeed(a.speed);
  }
  const u = (tc - a.t) / span;
  const eased = evaluateEasing(a.ease, u);
  return clampSpeed(a.speed + (b.speed - a.speed) * eased);
}

export interface FrameMapOptions {
  /** Source clip length in frames (timeline frames at 1x). */
  sourceFrames: number;
  /**
   * Number of output samples. Higher = smoother curve approximation,
   * more segments if strategy B is used. Default: one per source frame, min 64.
   */
  samples?: number;
}

export interface FrameMapEntry {
  /** Output frame index (0-based). */
  outFrame: number;
  /** Position on the source clip (timeline frames from clip start, fractional). */
  sourceFrame: number;
  /** Speed multiplier at this output frame. */
  speed: number;
}

export interface FrameMap {
  entries: FrameMapEntry[];
  /** Total output duration in frames (may be fractional; round for timeline use). */
  outputFrames: number;
  minSpeed: number;
  maxSpeed: number;
}

/**
 * Integrate the speed curve: output duration = integral of 1/speed over the clip.
 * Builds a frame map from output frames to source positions so the resulting
 * duration is predictable and can be shown to the user before applying.
 *
 * Discretization: each output step advances the source position by
 * (1 / speed) frames — i.e. at 2x speed a step consumes 2 source frames.
 */
export function buildFrameMap(ramp: RampDefinition, options: FrameMapOptions): FrameMap {
  const { sourceFrames } = options;
  if (!Number.isFinite(sourceFrames) || sourceFrames <= 0) {
    throw new Error("sourceFrames must be a positive number");
  }
  const samples = Math.max(64, options.samples ?? Math.ceil(sourceFrames));

  // Integrate 1/speed across normalized time to get output length.
  // ds = sourceFrames * dt; dOut = ds / speed.
  const dt = 1 / samples;
  let outTotal = 0;
  let minSpeed = Infinity;
  let maxSpeed = -Infinity;
  const speedsAtSamples: number[] = [];
  for (let s = 0; s < samples; s++) {
    const tMid = (s + 0.5) * dt;
    const speed = sampleSpeed(ramp, tMid);
    speedsAtSamples.push(speed);
    if (speed < minSpeed) minSpeed = speed;
    if (speed > maxSpeed) maxSpeed = speed;
    outTotal += (sourceFrames * dt) / speed;
  }

  const outFrames = Math.max(1, Math.round(outTotal));
  const entries: FrameMapEntry[] = [];
  let sourcePos = 0;
  for (let out = 0; out < outFrames; out++) {
    const tNorm = Math.min(1, sourcePos / sourceFrames);
    const speed = sampleSpeed(ramp, tNorm);
    entries.push({ outFrame: out, sourceFrame: sourcePos, speed });
    // Each output frame consumes `speed` source frames (speed = source
    // frames per output frame: 2x advances 2 source frames per frame out).
    sourcePos += speed;
    if (sourcePos >= sourceFrames) {
      // Clamp remaining frames to clip end.
      sourcePos = sourceFrames;
    }
  }

  return { entries, outputFrames: outFrames, minSpeed, maxSpeed };
}

/** Output duration in frames for a ramp applied to a clip of the given length. */
export function outputDurationFrames(ramp: RampDefinition, sourceFrames: number): number {
  return buildFrameMap(ramp, { sourceFrames }).outputFrames;
}
