import type { PlanOp } from "../../engine/planner.js";
import type { AdapterCapabilities, ResolveAdapter, ResolveClipInfo } from "./contract.js";

export interface MockClipState {
  info: ResolveClipInfo;
  retimeCurve: { frame: number; speedPercent: number }[] | null;
  segments: { startFrame: number; endFrame: number; speedPercent: number }[] | null;
  retimeProcess: string | null;
  motionEstimation: string | null;
  motionBlurStrength: number | null;
  fusionTimeRemap: { outFrame: number; sourceFrame: number }[] | null;
  appliedFx: { fxId: string; atFrame: number; params: Record<string, number | string | boolean> }[];
  appliedTransitions: { transitionId: string; atFrame: number; params: Record<string, number | string | boolean> }[];
  audioMode: string | null;
}

export interface MockResolveOptions {
  capabilities?: Partial<AdapterCapabilities>;
  clips?: ResolveClipInfo[];
  /** When true, execute() throws after snapshot to test rollback. */
  failAfterSnapshot?: boolean;
}

const DEFAULT_CAPS: AdapterCapabilities = {
  nativeRetimeCurve: true,
  fusionTimeRemap: true,
  segmentSplit: true,
};

/**
 * In-memory fake Resolve for engine tests. Records every operation and
 * supports snapshot/restore so transactional rollback can be asserted.
 */
function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

export class MockResolveAdapter implements ResolveAdapter {
  readonly clips: Map<string, MockClipState> = new Map();
  readonly executedOps: PlanOp[] = [];
  private snapshots: Map<string, MockClipState> = new Map();
  private caps: AdapterCapabilities;
  private failAfterSnapshot: boolean;

  constructor(options: MockResolveOptions = {}) {
    this.caps = { ...DEFAULT_CAPS, ...options.capabilities };
    this.failAfterSnapshot = options.failAfterSnapshot ?? false;
    const clips = options.clips ?? [
      {
        id: "clip-1",
        name: "A001_C002_0615R2.mov",
        frames: 240,
        fps: 24,
        hasAudio: true,
      },
    ];
    for (const info of clips) {
      this.clips.set(info.id, {
        info,
        retimeCurve: null,
        segments: null,
        retimeProcess: null,
        motionEstimation: null,
        motionBlurStrength: null,
        fusionTimeRemap: null,
        appliedFx: [],
        appliedTransitions: [],
        audioMode: null,
      });
    }
  }

  getCapabilities(): AdapterCapabilities {
    return { ...this.caps };
  }

  getSelection(): ResolveClipInfo[] {
    return [...this.clips.values()].map((c) => c.info);
  }

  execute(op: PlanOp): void {
    this.executedOps.push(op);
    if (op.op === "snapshot") {
      const state = this.mustClip(op.clipId);
      this.snapshots.set(op.clipId, deepClone(state));
      if (this.failAfterSnapshot) {
        throw new Error("mock resolve failure after snapshot");
      }
      return;
    }
    const state = this.mustClip(op.clipId);
    switch (op.op) {
      case "setRetimeCurve":
        state.retimeCurve = op.keyframes;
        break;
      case "splitSegment":
        if (!state.segments) state.segments = [];
        state.segments.push({
          startFrame: op.startFrame,
          endFrame: op.endFrame,
          speedPercent: op.speedPercent,
        });
        break;
      case "setRetimeProcess":
        state.retimeProcess = op.mode;
        break;
      case "setMotionEstimation":
        state.motionEstimation = op.quality;
        break;
      case "setMotionBlur":
        state.motionBlurStrength = op.strength;
        break;
      case "applyFusionTimeRemap":
        state.fusionTimeRemap = op.frameMap;
        break;
      case "applyFx":
        state.appliedFx.push({ fxId: op.fxId, atFrame: op.atFrame, params: op.params });
        break;
      case "applyTransition":
        state.appliedTransitions.push({
          transitionId: op.transitionId,
          atFrame: op.atFrame,
          params: op.params,
        });
        break;
      case "setAudioMode":
        state.audioMode = op.mode;
        break;
      case "verify": {
        // Mock "succeeds" when the applied duration matches.
        // Segments strategy: output length = sum of (segment source length / speed).
        if (state.segments && state.segments.length > 0) {
          const totalOut = state.segments.reduce(
            (acc, s) => acc + ((s.endFrame - s.startFrame) * 100) / s.speedPercent,
            0,
          );
          // Segments approximate the curve; allow 2% tolerance like real world.
          if (Math.abs(totalOut - op.expectedOutputFrames) > op.expectedOutputFrames * 0.02) {
            throw new Error(
              `verify failed: segment output ${totalOut} vs expected ${op.expectedOutputFrames}`,
            );
          }
        }
        break;
      }
    }
  }

  restoreSnapshot(clipId: string): void {
    const snap = this.snapshots.get(clipId);
    if (!snap) {
      throw new Error(`no snapshot for clip ${clipId}`);
    }
    this.clips.set(clipId, deepClone(snap));
  }

  private mustClip(clipId: string): MockClipState {
    const state = this.clips.get(clipId);
    if (!state) {
      throw new Error(`unknown clip ${clipId}`);
    }
    return state;
  }
}
