import { describe, expect, it } from "vitest";
import { planRamp, PlanError } from "../../src/engine/planner.js";
import { validateRamp } from "../../src/engine/model/ramp.js";
import { getPreset } from "../../src/presets/index.js";

const FULL_CAPS = { nativeRetimeCurve: true, fusionTimeRemap: true, segmentSplit: true };

function ctx(overrides: Partial<Parameters<typeof planRamp>[1]> = {}) {
  return {
    clipId: "clip-1",
    sourceFrames: 240,
    capabilities: FULL_CAPS,
    ...overrides,
  } as Parameters<typeof planRamp>[1];
}

const hero = getPreset("hero-slowmo")!;

describe("planRamp strategy selection", () => {
  it("prefers native when available", () => {
    expect(planRamp(hero, ctx()).strategy).toBe("native");
  });

  it("falls back to fusion when native missing", () => {
    const plan = planRamp(
      hero,
      ctx({ capabilities: { nativeRetimeCurve: false, fusionTimeRemap: true, segmentSplit: true } }),
    );
    expect(plan.strategy).toBe("fusion");
  });

  it("falls back to segments when native and fusion missing", () => {
    const plan = planRamp(
      hero,
      ctx({ capabilities: { nativeRetimeCurve: false, fusionTimeRemap: false, segmentSplit: true } }),
    );
    expect(plan.strategy).toBe("segments");
  });

  it("throws when nothing available", () => {
    expect(() =>
      planRamp(hero, ctx({ capabilities: { nativeRetimeCurve: false, fusionTimeRemap: false, segmentSplit: false } })),
    ).toThrow(PlanError);
  });

  it("honors forced strategy and validates capability", () => {
    expect(planRamp(hero, ctx({ strategy: "segments" })).strategy).toBe("segments");
    expect(() =>
      planRamp(
        hero,
        ctx({
          strategy: "native",
          capabilities: { nativeRetimeCurve: false, fusionTimeRemap: true, segmentSplit: true },
        }),
      ),
    ).toThrow(PlanError);
  });
});

describe("planRamp ops", () => {
  it("always snapshots first and verifies last", () => {
    const ops = planRamp(hero, ctx()).ops;
    expect(ops[0]!.op).toBe("snapshot");
    expect(ops[ops.length - 1]!.op).toBe("verify");
  });

  it("native strategy emits keyframed retime curve with frame positions", () => {
    const plan = planRamp(hero, ctx());
    const curve = plan.ops.find((o) => o.op === "setRetimeCurve");
    expect(curve).toBeDefined();
    if (curve?.op !== "setRetimeCurve") throw new Error("unreachable");
    expect(curve.keyframes.length).toBe(hero.keyframes.length);
    expect(curve.keyframes[0]!.frame).toBe(0);
    expect(curve.keyframes[curve.keyframes.length - 1]!.frame).toBe(plan.expectedOutputFrames - 1);
    // hero holds 20% in the middle
    const mid = curve.keyframes[1];
    expect(mid!.speedPercent).toBeCloseTo(20, 5);
  });

  it("segments strategy splits into constant-speed segments covering the clip", () => {
    const plan = planRamp(hero, ctx({ strategy: "segments" }));
    const segs = plan.ops.filter((o) => o.op === "splitSegment");
    expect(segs.length).toBeGreaterThanOrEqual(8);
    expect(segs.length).toBeLessThanOrEqual(48);
    if (segs[0]?.op !== "splitSegment") throw new Error("unreachable");
    expect(segs[0].startFrame).toBe(0);
    // Segments are contiguous: each starts where the previous roughly ended
    let prevEnd = 0;
    for (const s of segs) {
      if (s.op !== "splitSegment") continue;
      expect(s.startFrame).toBeLessThanOrEqual(s.endFrame);
      prevEnd = s.endFrame;
    }
    expect(prevEnd).toBeLessThanOrEqual(240);
  });

  it("fusion strategy embeds the frame map", () => {
    const plan = planRamp(hero, ctx({ strategy: "fusion" }));
    const remap = plan.ops.find((o) => o.op === "applyFusionTimeRemap");
    if (remap?.op !== "applyFusionTimeRemap") throw new Error("missing remap");
    expect(remap.frameMap.length).toBe(plan.expectedOutputFrames);
    expect(remap.frameMap[0]!.sourceFrame).toBeCloseTo(0, 5);
  });

  it("sets optical flow when enabled and nearest when not", () => {
    const withFlow = planRamp(hero, ctx());
    expect(withFlow.ops.some((o) => o.op === "setRetimeProcess" && o.mode === "opticalFlow")).toBe(true);
    const whip = getPreset("whip-ramp")!;
    const noFlow = planRamp(whip, ctx());
    expect(noFlow.ops.some((o) => o.op === "setRetimeProcess" && o.mode === "nearest")).toBe(true);
  });

  it("emits motion blur with strength when enabled", () => {
    const plan = planRamp(hero, ctx());
    const blur = plan.ops.find((o) => o.op === "setMotionBlur");
    if (blur?.op !== "setMotionBlur") throw new Error("missing blur");
    expect(blur.strength).toBeCloseTo(0.6, 5);
  });

  it("places fx at planned frame positions", () => {
    const impact = getPreset("impact")!;
    const plan = planRamp(impact, ctx());
    const fx = plan.ops.find((o) => o.op === "applyFx");
    if (fx?.op !== "applyFx") throw new Error("missing fx");
    expect(fx.fxId).toBe("zoom-punch");
    expect(fx.atFrame).toBe(Math.round(0.5 * (plan.expectedOutputFrames - 1)));
  });

  it("sets audio mode from ramp", () => {
    const plan = planRamp(hero, ctx());
    const audio = plan.ops.find((o) => o.op === "setAudioMode");
    if (audio?.op !== "setAudioMode") throw new Error("missing audio op");
    expect(audio.mode).toBe("keepPitch");
  });

  it("verify op carries expected output frames", () => {
    const plan = planRamp(hero, ctx());
    const v = plan.ops.find((o) => o.op === "verify");
    if (v?.op !== "verify") throw new Error("missing verify");
    expect(v.expectedOutputFrames).toBe(plan.expectedOutputFrames);
  });
});

describe("planRamp with custom ramp", () => {
  it("rejects a ramp that fails validation upstream of planning", () => {
    expect(() =>
      planRamp(
        validateRamp({
          id: "bad",
          name: "Bad",
          version: 1,
          keyframes: [
            { t: 0, speed: 1, ease: "linear" },
            { t: 1, speed: 1, ease: "linear" },
          ],
          quality: { opticalFlow: false, motionBlur: { enabled: false, strength: 0 } },
          fx: [],
          transition: { id: "flash-cut", at: 0.5, params: {} },
          audio: "mute",
        }),
        ctx(),
      ),
    ).not.toThrow();
  });
});
