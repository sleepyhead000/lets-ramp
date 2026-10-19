import type { RampDefinition } from "./model/ramp.js";
import { buildFrameMap, type FrameMap } from "./integrator.js";

export type StrategyId = "native" | "segments" | "fusion";

export type PlanOp =
  | { op: "snapshot"; clipId: string }
  | {
      op: "setRetimeCurve";
      clipId: string;
      /** Keyframed speed in percent at timeline frame positions. */
      keyframes: { frame: number; speedPercent: number }[];
    }
  | {
      op: "splitSegment";
      clipId: string;
      /** Source range on the original clip, in frames. */
      startFrame: number;
      endFrame: number;
      /** Constant speed percent for this segment. */
      speedPercent: number;
    }
  | { op: "setRetimeProcess"; clipId: string; mode: "opticalFlow" | "nearest" | "frameBlend" }
  | { op: "setMotionEstimation"; clipId: string; quality: "faster" | "better" }
  | { op: "setMotionBlur"; clipId: string; strength: number }
  | { op: "applyFusionTimeRemap"; clipId: string; frameMap: { outFrame: number; sourceFrame: number }[] }
  | { op: "applyFx"; clipId: string; fxId: string; atFrame: number; params: Record<string, number | string | boolean> }
  | { op: "applyTransition"; clipId: string; transitionId: string; atFrame: number; params: Record<string, number | string | boolean> }
  | { op: "setAudioMode"; clipId: string; mode: RampDefinition["audio"] }
  | { op: "verify"; clipId: string; expectedOutputFrames: number };

export interface PlanContext {
  clipId: string;
  /** Source clip length in timeline frames at 1x speed. */
  sourceFrames: number;
  /** Strategies the adapter reported as available. */
  capabilities: { nativeRetimeCurve: boolean; fusionTimeRemap: boolean; segmentSplit: boolean };
  /** Force a strategy (tests); otherwise first available of native > fusion > segments. */
  strategy?: StrategyId;
}

export interface OperationPlan {
  strategy: StrategyId;
  frameMap: FrameMap;
  expectedOutputFrames: number;
  ops: PlanOp[];
}

export class PlanError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PlanError";
  }
}

/**
 * Convert a ramp into an ordered list of Resolve operations.
 * Pure function: no Resolve calls, fully unit-testable.
 */
export function planRamp(ramp: RampDefinition, context: PlanContext): OperationPlan {
  const { clipId, sourceFrames, capabilities } = context;

  let strategy: StrategyId;
  if (context.strategy) {
    strategy = context.strategy;
  } else if (capabilities.nativeRetimeCurve) {
    strategy = "native";
  } else if (capabilities.fusionTimeRemap) {
    strategy = "fusion";
  } else if (capabilities.segmentSplit) {
    strategy = "segments";
  } else {
    throw new PlanError("no retime strategy available on this adapter");
  }

  if (strategy === "native" && !capabilities.nativeRetimeCurve) {
    throw new PlanError("strategy native requested but adapter reports no nativeRetimeCurve");
  }
  if (strategy === "fusion" && !capabilities.fusionTimeRemap) {
    throw new PlanError("strategy fusion requested but adapter reports no fusionTimeRemap");
  }
  if (strategy === "segments" && !capabilities.segmentSplit) {
    throw new PlanError("strategy segments requested but adapter reports no segmentSplit");
  }

  const frameMap = buildFrameMap(ramp, { sourceFrames });
  const ops: PlanOp[] = [{ op: "snapshot", clipId }];

  if (strategy === "native") {
    // Convert normalized keyframes to timeline frames + speed percent.
    const keyframes = ramp.keyframes.map((kf) => ({
      frame: Math.round(kf.t * (frameMap.outputFrames - 1)),
      speedPercent: Math.round(kf.speed * 100 * 100) / 100,
    }));
    ops.push({ op: "setRetimeCurve", clipId, keyframes });
  } else if (strategy === "segments") {
    // Approximate the curve with constant-speed segments sampled from the frame map.
    const segmentCount = Math.min(48, Math.max(8, Math.round(frameMap.entries.length / 8)));
    const perSegment = Math.ceil(frameMap.entries.length / segmentCount);
    for (let i = 0; i < frameMap.entries.length; i += perSegment) {
      const slice = frameMap.entries.slice(i, i + perSegment);
      const start = slice[0]!;
      const end = slice[slice.length - 1]!;
      // Constant-speed equivalent for this slice: each output frame
      // consumes `speed` source frames, so v = sourceLen/outputLen =
      // sum(s_i)/n (arithmetic mean).
      const avgSpeed = slice.reduce((acc, e) => acc + e.speed, 0) / slice.length;
      ops.push({
        op: "splitSegment",
        clipId,
        // Fractional source boundaries: rounding here loses accuracy at
        // slow speeds (1 source frame can be many output frames). The
        // adapter rounds when executing against a real timeline.
        startFrame: start.sourceFrame,
        endFrame: Math.min(sourceFrames, end.sourceFrame + end.speed),
        speedPercent: Math.round(avgSpeed * 100 * 100) / 100,
      });
    }
  } else {
    ops.push({
      op: "applyFusionTimeRemap",
      clipId,
      frameMap: frameMap.entries.map((e) => ({ outFrame: e.outFrame, sourceFrame: e.sourceFrame })),
    });
  }

  // Quality: optical flow + motion estimation.
  if (ramp.quality.opticalFlow) {
    ops.push({ op: "setRetimeProcess", clipId, mode: "opticalFlow" });
    ops.push({ op: "setMotionEstimation", clipId, quality: ramp.quality.opticalFlow ? "better" : "faster" });
  } else {
    ops.push({ op: "setRetimeProcess", clipId, mode: "nearest" });
  }

  if (ramp.quality.motionBlur.enabled && ramp.quality.motionBlur.strength > 0) {
    ops.push({ op: "setMotionBlur", clipId, strength: ramp.quality.motionBlur.strength });
  }

  for (const fx of ramp.fx) {
    ops.push({
      op: "applyFx",
      clipId,
      fxId: fx.id,
      atFrame: Math.round(fx.at * (frameMap.outputFrames - 1)),
      params: fx.params,
    });
  }

  if (ramp.transition) {
    ops.push({
      op: "applyTransition",
      clipId,
      transitionId: ramp.transition.id,
      atFrame: Math.round(ramp.transition.at * (frameMap.outputFrames - 1)),
      params: ramp.transition.params,
    });
  }

  ops.push({ op: "setAudioMode", clipId, mode: ramp.audio });
  ops.push({ op: "verify", clipId, expectedOutputFrames: frameMap.outputFrames });

  return { strategy, frameMap, expectedOutputFrames: frameMap.outputFrames, ops };
}
