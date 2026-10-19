import type { PlanOp } from "../../engine/planner.js";

export interface ResolveClipInfo {
  id: string;
  name: string;
  /** Length in timeline frames at 1x speed. */
  frames: number;
  fps: number;
  hasAudio: boolean;
}

export interface AdapterCapabilities {
  nativeRetimeCurve: boolean;
  fusionTimeRemap: boolean;
  segmentSplit: boolean;
}

/**
 * Thin wrapper over the Resolve scripting API. Every Resolve call goes
 * through this interface so the engine can be tested against a mock and
 * swapped across Resolve versions (architecture.md §6).
 */
export interface ResolveAdapter {
  getCapabilities(): AdapterCapabilities;
  getSelection(): ResolveClipInfo[];
  execute(op: PlanOp): void;
  /** Restore everything the plan's snapshot op recorded. */
  restoreSnapshot(clipId: string): void;
}
