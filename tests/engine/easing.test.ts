import { describe, expect, it } from "vitest";
import { evaluateEasing } from "../../src/engine/easing/index.js";

describe("evaluateEasing", () => {
  it("linear is identity", () => {
    expect(evaluateEasing("linear", 0)).toBe(0);
    expect(evaluateEasing("linear", 0.5)).toBe(0.5);
    expect(evaluateEasing("linear", 1)).toBe(1);
  });

  it("easeIn is slow at start, fast at end", () => {
    expect(evaluateEasing("easeIn", 0)).toBe(0);
    expect(evaluateEasing("easeIn", 0.5)).toBeCloseTo(0.25);
    expect(evaluateEasing("easeIn", 1)).toBe(1);
    expect(evaluateEasing("easeIn", 0.25)).toBeLessThan(0.25);
  });

  it("easeOut is fast at start, slow at end", () => {
    expect(evaluateEasing("easeOut", 0)).toBe(0);
    expect(evaluateEasing("easeOut", 0.5)).toBeCloseTo(0.75);
    expect(evaluateEasing("easeOut", 1)).toBe(1);
    expect(evaluateEasing("easeOut", 0.25)).toBeGreaterThan(0.25);
  });

  it("easeInOut is symmetric around midpoint", () => {
    expect(evaluateEasing("easeInOut", 0)).toBe(0);
    expect(evaluateEasing("easeInOut", 0.5)).toBeCloseTo(0.5);
    expect(evaluateEasing("easeInOut", 1)).toBe(1);
    expect(evaluateEasing("easeInOut", 0.25)).toBeCloseTo(1 - evaluateEasing("easeInOut", 0.75));
  });

  it("hold stays at 0 until the next keyframe", () => {
    expect(evaluateEasing("hold", 0)).toBe(0);
    expect(evaluateEasing("hold", 0.99)).toBe(0);
    expect(evaluateEasing("hold", 1)).toBe(0);
  });

  it("clamps out-of-range u", () => {
    expect(evaluateEasing("linear", -1)).toBe(0);
    expect(evaluateEasing("linear", 2)).toBe(1);
  });
});
