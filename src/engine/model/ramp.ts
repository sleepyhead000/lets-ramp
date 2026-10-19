export type Easing = "linear" | "easeIn" | "easeOut" | "easeInOut" | "hold";

export interface RampKeyframe {
  /** Normalized clip position, 0..1. Must be non-decreasing. */
  t: number;
  /** Speed as a multiplier of normal (1 = normal, 0.2 = 20%, 4 = 400%). */
  speed: number;
  /** How speed interpolates FROM this keyframe toward the next. */
  ease: Easing;
}

export interface MotionBlurConfig {
  enabled: boolean;
  /** User multiplier on speed-derived blur, 0..2. */
  strength: number;
}

export interface RampQuality {
  opticalFlow: boolean;
  motionBlur: MotionBlurConfig;
}

export interface RampFx {
  id: string;
  /** Normalized position 0..1. */
  at: number;
  params: Record<string, number | string | boolean>;
}

export type AudioMode = "mute" | "keepPitch" | "followSpeed";

export interface RampDefinition {
  id: string;
  name: string;
  version: number;
  keyframes: RampKeyframe[];
  quality: RampQuality;
  fx: RampFx[];
  transition: { id: string; at: number; params: Record<string, number | string | boolean> } | null;
  audio: AudioMode;
}

export const SPEED_MIN = 0.01;
export const SPEED_MAX = 10.0;

export class RampValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "RampValidationError";
  }
}

export function clampSpeed(speed: number): number {
  if (!Number.isFinite(speed)) {
    throw new RampValidationError(`speed must be finite, got ${speed}`);
  }
  return Math.min(SPEED_MAX, Math.max(SPEED_MIN, speed));
}

export function validateRamp(unknownRamp: unknown): RampDefinition {
  if (typeof unknownRamp !== "object" || unknownRamp === null) {
    throw new RampValidationError("ramp must be an object");
  }
  const r = unknownRamp as Record<string, unknown>;

  if (typeof r.id !== "string" || r.id.length === 0) {
    throw new RampValidationError("id must be a non-empty string");
  }
  if (typeof r.name !== "string" || r.name.length === 0) {
    throw new RampValidationError("name must be a non-empty string");
  }
  if (typeof r.version !== "number" || !Number.isInteger(r.version) || r.version < 1) {
    throw new RampValidationError("version must be a positive integer");
  }
  if (!Array.isArray(r.keyframes) || r.keyframes.length < 2) {
    throw new RampValidationError("keyframes must be an array of at least 2 entries");
  }

  const easings: Easing[] = ["linear", "easeIn", "easeOut", "easeInOut", "hold"];
  let prevT = -Infinity;
  for (let i = 0; i < r.keyframes.length; i++) {
    const kf = r.keyframes[i] as Record<string, unknown>;
    if (typeof kf?.t !== "number" || !Number.isFinite(kf.t) || kf.t < 0 || kf.t > 1) {
      throw new RampValidationError(`keyframes[${i}].t must be in [0, 1]`);
    }
    if (kf.t < prevT) {
      throw new RampValidationError(`keyframes[${i}].t must be >= previous t (non-decreasing)`);
    }
    prevT = kf.t;
    if (typeof kf.speed !== "number") {
      throw new RampValidationError(`keyframes[${i}].speed must be a number`);
    }
    clampSpeed(kf.speed);
    if (typeof kf.ease !== "string" || !easings.includes(kf.ease as Easing)) {
      throw new RampValidationError(`keyframes[${i}].ease must be one of ${easings.join(", ")}`);
    }
  }
  const first = r.keyframes[0] as { t: number };
  const last = r.keyframes[r.keyframes.length - 1] as { t: number };
  if (first.t !== 0) {
    throw new RampValidationError("first keyframe must be at t=0");
  }
  if (last.t !== 1) {
    throw new RampValidationError("last keyframe must be at t=1");
  }

  if (typeof r.audio !== "string" || !["mute", "keepPitch", "followSpeed"].includes(r.audio)) {
    throw new RampValidationError("audio must be mute | keepPitch | followSpeed");
  }

  const quality = r.quality as Record<string, unknown> | undefined;
  if (typeof quality?.opticalFlow !== "boolean") {
    throw new RampValidationError("quality.opticalFlow must be a boolean");
  }
  const mb = quality.motionBlur as Record<string, unknown> | undefined;
  if (typeof mb?.enabled !== "boolean" || typeof mb.strength !== "number") {
    throw new RampValidationError("quality.motionBlur must have enabled:boolean and strength:number");
  }

  const fx = r.fx;
  if (!Array.isArray(fx)) {
    throw new RampValidationError("fx must be an array");
  }
  for (let i = 0; i < fx.length; i++) {
    const item = fx[i] as Record<string, unknown>;
    if (typeof item?.id !== "string" || typeof item.at !== "number" || item.at < 0 || item.at > 1) {
      throw new RampValidationError(`fx[${i}] must have id:string and at in [0,1]`);
    }
  }

  const transition = r.transition;
  if (transition !== null && transition !== undefined) {
    const tr = transition as Record<string, unknown>;
    if (typeof tr.id !== "string" || typeof tr.at !== "number") {
      throw new RampValidationError("transition must be null or {id, at, params}");
    }
  }

  return unknownRamp as RampDefinition;
}
