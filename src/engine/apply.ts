import type { ResolveAdapter } from "../adapter/resolve/contract.js";
import { planRamp, type OperationPlan } from "./planner.js";
import type { RampDefinition } from "./model/ramp.js";

export class ApplyError extends Error {
  constructor(
    message: string,
    readonly cause?: unknown,
  ) {
    super(message);
    this.name = "ApplyError";
  }
}

export interface ApplyResult {
  ok: boolean;
  plan: OperationPlan;
  error?: string;
}

/**
 * Apply a ramp transactionally (architecture.md §8): every apply snapshots
 * first; on any failure the snapshot is restored and a plain-language error
 * is returned. Nothing is left half-applied.
 */
export function applyRamp(
  adapter: ResolveAdapter,
  ramp: RampDefinition,
  clipId: string,
  strategy?: OperationPlan["strategy"],
): ApplyResult {
  const selection = adapter.getSelection();
  const clip = selection.find((c) => c.id === clipId);
  if (!clip) {
    throw new ApplyError(`clip ${clipId} is not in the current selection`);
  }

  const plan = planRamp(ramp, {
    clipId,
    sourceFrames: clip.frames,
    capabilities: adapter.getCapabilities(),
    ...(strategy ? { strategy } : {}),
  });

  try {
    for (const op of plan.ops) {
      adapter.execute(op);
    }
    return { ok: true, plan };
  } catch (err) {
    try {
      adapter.restoreSnapshot(clipId);
    } catch (restoreErr) {
      throw new ApplyError(
        `apply failed and snapshot restore also failed: ${String(restoreErr)}`,
        restoreErr,
      );
    }
    return {
      ok: false,
      plan,
      error: err instanceof Error ? err.message : String(err),
    };
  }
}
