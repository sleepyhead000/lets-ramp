import { describe, expect, it } from "vitest";
import { MockResolveAdapter } from "../../src/adapter/resolve/mock.js";
import { applyRamp, ApplyError } from "../../src/engine/apply.js";
import { getPreset } from "../../src/presets/index.js";

const hero = getPreset("hero-slowmo")!;

describe("MockResolveAdapter", () => {
  it("reports default capabilities and selection", () => {
    const adapter = new MockResolveAdapter();
    expect(adapter.getCapabilities()).toEqual({
      nativeRetimeCurve: true,
      fusionTimeRemap: true,
      segmentSplit: true,
    });
    expect(adapter.getSelection()).toHaveLength(1);
    expect(adapter.getSelection()[0]!.frames).toBe(240);
  });

  it("supports partial capabilities", () => {
    const adapter = new MockResolveAdapter({
      capabilities: { nativeRetimeCurve: false },
    });
    expect(adapter.getCapabilities().nativeRetimeCurve).toBe(false);
    expect(adapter.getCapabilities().segmentSplit).toBe(true);
  });
});

describe("applyRamp (transactional)", () => {
  it("applies native ramp end-to-end and marks clip as retimed", () => {
    const adapter = new MockResolveAdapter();
    const result = applyRamp(adapter, hero, "clip-1");
    expect(result.ok).toBe(true);
    const state = adapter.clips.get("clip-1")!;
    expect(state.retimeCurve).not.toBeNull();
    expect(state.retimeProcess).toBe("opticalFlow");
    expect(state.motionBlurStrength).toBeCloseTo(0.6, 5);
    expect(state.audioMode).toBe("keepPitch");
  });

  it("rolls back to snapshot when an op fails mid-plan", () => {
    const adapter = new MockResolveAdapter({ failAfterSnapshot: true });
    const result = applyRamp(adapter, hero, "clip-1");
    expect(result.ok).toBe(false);
    expect(result.error).toMatch(/mock resolve failure/);
    const state = adapter.clips.get("clip-1")!;
    // Fully restored: no partial state from the failed plan
    expect(state.retimeCurve).toBeNull();
    expect(state.retimeProcess).toBeNull();
    expect(state.motionBlurStrength).toBeNull();
    expect(state.audioMode).toBeNull();
  });

  it("snapshot precedes every mutating op", () => {
    const adapter = new MockResolveAdapter();
    applyRamp(adapter, hero, "clip-1");
    expect(adapter.executedOps[0]!.op).toBe("snapshot");
  });

  it("throws ApplyError for unknown clip", () => {
    const adapter = new MockResolveAdapter();
    expect(() => applyRamp(adapter, hero, "nope")).toThrow(ApplyError);
  });

  it("works when only segments capability exists", () => {
    const adapter = new MockResolveAdapter({
      capabilities: { nativeRetimeCurve: false, fusionTimeRemap: false, segmentSplit: true },
    });
    const result = applyRamp(adapter, hero, "clip-1");
    expect(result.plan.strategy).toBe("segments");
    expect(result.ok).toBe(true);
    expect(adapter.clips.get("clip-1")!.segments!.length).toBeGreaterThan(0);
  });

  it("works when only fusion capability exists", () => {
    const adapter = new MockResolveAdapter({
      capabilities: { nativeRetimeCurve: false, fusionTimeRemap: true, segmentSplit: false },
    });
    const result = applyRamp(adapter, hero, "clip-1");
    expect(result.plan.strategy).toBe("fusion");
    expect(result.ok).toBe(true);
    expect(adapter.clips.get("clip-1")!.fusionTimeRemap).not.toBeNull();
  });

  it("restoreSnapshot restores a pre-apply state", () => {
    const adapter = new MockResolveAdapter();
    adapter.execute({ op: "snapshot", clipId: "clip-1" });
    adapter.execute({
      op: "setRetimeCurve",
      clipId: "clip-1",
      keyframes: [{ frame: 0, speedPercent: 100 }],
    });
    expect(adapter.clips.get("clip-1")!.retimeCurve).not.toBeNull();
    adapter.restoreSnapshot("clip-1");
    expect(adapter.clips.get("clip-1")!.retimeCurve).toBeNull();
  });
});
