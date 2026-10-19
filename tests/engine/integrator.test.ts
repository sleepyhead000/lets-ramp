import { describe, expect, it } from "vitest";
import {
  buildFrameMap,
  outputDurationFrames,
  sampleSpeed,
} from "../../src/engine/integrator.js";
import { validateRamp, RampValidationError } from "../../src/engine/model/ramp.js";
import { PRESETS } from "../../src/presets/index.js";

function rampWith(keyframes: { t: number; speed: number; ease: "linear" | "hold" | "easeIn" | "easeOut" | "easeInOut" }[]) {
  return validateRamp({
    id: "test",
    name: "Test",
    version: 1,
    keyframes,
    quality: { opticalFlow: false, motionBlur: { enabled: false, strength: 0 } },
    fx: [],
    transition: null,
    audio: "mute",
  });
}

describe("sampleSpeed", () => {
  it("returns endpoint speeds at t=0 and t=1", () => {
    const r = rampWith([
      { t: 0, speed: 1, ease: "linear" },
      { t: 1, speed: 2, ease: "linear" },
    ]);
    expect(sampleSpeed(r, 0)).toBe(1);
    expect(sampleSpeed(r, 1)).toBe(2);
  });

  it("interpolates linearly", () => {
    const r = rampWith([
      { t: 0, speed: 1, ease: "linear" },
      { t: 1, speed: 3, ease: "linear" },
    ]);
    expect(sampleSpeed(r, 0.5)).toBeCloseTo(2);
  });

  it("hold keeps previous speed until next keyframe", () => {
    const r = rampWith([
      { t: 0, speed: 1, ease: "hold" },
      { t: 0.5, speed: 2, ease: "linear" },
      { t: 1, speed: 2, ease: "linear" },
    ]);
    expect(sampleSpeed(r, 0.1)).toBe(1);
    expect(sampleSpeed(r, 0.49)).toBe(1);
    expect(sampleSpeed(r, 0.5)).toBe(2);
  });

  it("clamps speed into [SPEED_MIN, SPEED_MAX]", () => {
    const r = rampWith([
      { t: 0, speed: 0.001, ease: "linear" },
      { t: 1, speed: 100, ease: "linear" },
    ]);
    expect(sampleSpeed(r, 0)).toBeGreaterThanOrEqual(0.01);
    expect(sampleSpeed(r, 1)).toBeLessThanOrEqual(10);
  });
});

describe("buildFrameMap", () => {
  it("constant 1x speed yields output = source duration", () => {
    const r = rampWith([
      { t: 0, speed: 1, ease: "linear" },
      { t: 1, speed: 1, ease: "linear" },
    ]);
    const map = buildFrameMap(r, { sourceFrames: 100 });
    expect(map.outputFrames).toBe(100);
    expect(map.minSpeed).toBe(1);
    expect(map.maxSpeed).toBe(1);
  });

  it("constant 2x halves the output duration", () => {
    const r = rampWith([
      { t: 0, speed: 2, ease: "linear" },
      { t: 1, speed: 2, ease: "linear" },
    ]);
    expect(outputDurationFrames(r, 200)).toBe(100);
  });

  it("constant 0.5x doubles the output duration", () => {
    const r = rampWith([
      { t: 0, speed: 0.5, ease: "linear" },
      { t: 1, speed: 0.5, ease: "linear" },
    ]);
    expect(outputDurationFrames(r, 100)).toBe(200);
  });

  it("monotonic frame map never rewinds source position", () => {
    const r = rampWith([
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.5, speed: 0.2, ease: "easeOut" },
      { t: 1, speed: 1, ease: "linear" },
    ]);
    const map = buildFrameMap(r, { sourceFrames: 240 });
    for (let i = 1; i < map.entries.length; i++) {
      expect(map.entries[i]!.sourceFrame).toBeGreaterThanOrEqual(map.entries[i - 1]!.sourceFrame);
    }
  });

  it("source positions stay within clip bounds", () => {
    const r = rampWith([
      { t: 0, speed: 4, ease: "linear" },
      { t: 1, speed: 0.25, ease: "linear" },
    ]);
    const map = buildFrameMap(r, { sourceFrames: 120 });
    for (const e of map.entries) {
      expect(e.sourceFrame).toBeGreaterThanOrEqual(0);
      expect(e.sourceFrame).toBeLessThanOrEqual(120);
    }
  });

  it("rejects invalid sourceFrames", () => {
    const r = rampWith([
      { t: 0, speed: 1, ease: "linear" },
      { t: 1, speed: 1, ease: "linear" },
    ]);
    expect(() => buildFrameMap(r, { sourceFrames: 0 })).toThrow();
    expect(() => buildFrameMap(r, { sourceFrames: -5 })).toThrow();
  });
});

describe("golden preset durations (03 starter presets)", () => {
  const clipFrames = 240;

  it("every preset produces a valid positive output duration", () => {
    for (const preset of PRESETS) {
      const out = outputDurationFrames(preset, clipFrames);
      expect(out, preset.id).toBeGreaterThan(0);
    }
  });

  it("slow-in (ends at 30%) is longer than source", () => {
    const slowIn = PRESETS.find((p) => p.id === "slow-in")!;
    // Integral of 1/speed with speed 1->0.3 easeInOut: average of 1/speed > 1
    expect(outputDurationFrames(slowIn, clipFrames)).toBeGreaterThan(clipFrames);
  });

  it("hero-slow-mo hold at 20% roughly triples duration", () => {
    const hero = PRESETS.find((p) => p.id === "hero-slowmo")!;
    const out = outputDurationFrames(hero, clipFrames);
    // Half the clip at 1x-approach, long stretch at 0.2x: expect 2.5x..4.5x
    expect(out).toBeGreaterThan(clipFrames * 2.5);
    expect(out).toBeLessThan(clipFrames * 4.5);
  });

  it("whip-ramp peaks at 400%", () => {
    const whip = PRESETS.find((p) => p.id === "whip-ramp")!;
    const map = buildFrameMap(whip, { sourceFrames: clipFrames });
    // Midpoint sampling approximates the peak; allow small discretization error.
    expect(map.maxSpeed).toBeGreaterThan(3.9);
    expect(map.maxSpeed).toBeLessThanOrEqual(4);
    expect(map.minSpeed).toBeCloseTo(1, 2);
  });

  it("bullet-time bottoms out at 5%", () => {
    const bt = PRESETS.find((p) => p.id === "bullet-time")!;
    const map = buildFrameMap(bt, { sourceFrames: clipFrames });
    expect(map.minSpeed).toBeCloseTo(0.05, 5);
    expect(outputDurationFrames(bt, clipFrames)).toBeGreaterThan(clipFrames * 3);
  });

  it("pulse alternates 100/50 with output longer than source", () => {
    const pulse = PRESETS.find((p) => p.id === "pulse")!;
    const out = outputDurationFrames(pulse, clipFrames);
    // Average speed 0.75x -> ~1.33x duration; just assert direction
    expect(out).toBeGreaterThan(clipFrames);
    expect(out).toBeLessThan(clipFrames * 2);
  });

  it("car-launch accelerates 50% to 300%", () => {
    const car = PRESETS.find((p) => p.id === "car-launch")!;
    const map = buildFrameMap(car, { sourceFrames: clipFrames });
    // Midpoint sampling approximates endpoints; allow small discretization error.
    expect(map.minSpeed).toBeGreaterThan(0.49);
    expect(map.minSpeed).toBeLessThan(0.51);
    expect(map.maxSpeed).toBeGreaterThan(2.9);
    expect(map.maxSpeed).toBeLessThanOrEqual(3.01);
    // easeIn dwells at 50% first, so output is slightly longer than source.
    expect(map.outputFrames).toBeGreaterThan(clipFrames);
    expect(map.outputFrames).toBeLessThan(clipFrames * 1.2);
  });

  it("all presets validate against the ramp schema", () => {
    for (const preset of PRESETS) {
      expect(() => validateRamp(preset), preset.id).not.toThrow();
    }
  });
});

describe("validateRamp", () => {
  const base = {
    id: "x",
    name: "X",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "linear" },
      { t: 1, speed: 1, ease: "linear" },
    ],
    quality: { opticalFlow: false, motionBlur: { enabled: false, strength: 0 } },
    fx: [],
    transition: null,
    audio: "mute" as const,
  };

  it("accepts a minimal valid ramp", () => {
    expect(() => validateRamp(base)).not.toThrow();
  });

  it("requires first keyframe at t=0 and last at t=1", () => {
    expect(() =>
      validateRamp({ ...base, keyframes: [{ t: 0.1, speed: 1, ease: "linear" }, { t: 1, speed: 1, ease: "linear" }] }),
    ).toThrow(RampValidationError);
    expect(() =>
      validateRamp({ ...base, keyframes: [{ t: 0, speed: 1, ease: "linear" }, { t: 0.9, speed: 1, ease: "linear" }] }),
    ).toThrow(RampValidationError);
  });

  it("requires non-decreasing t", () => {
    expect(() =>
      validateRamp({
        ...base,
        keyframes: [
          { t: 0, speed: 1, ease: "linear" },
          { t: 0.6, speed: 1, ease: "linear" },
          { t: 0.3, speed: 1, ease: "linear" },
          { t: 1, speed: 1, ease: "linear" },
        ],
      }),
    ).toThrow(/non-decreasing/);
  });

  it("rejects unknown easing", () => {
    expect(() =>
      validateRamp({
        ...base,
        keyframes: [
          { t: 0, speed: 1, ease: "bouncy" },
          { t: 1, speed: 1, ease: "linear" },
        ],
      }),
    ).toThrow(/ease/);
  });

  it("rejects bad audio mode", () => {
    expect(() => validateRamp({ ...base, audio: "loud" })).toThrow(/audio/);
  });
});
