import type { RampDefinition } from "../engine/model/ramp.js";

/**
 * Starter preset library (03-ramp-and-effects-spec.md).
 * t is normalized clip position so one preset fits any clip length.
 */
export const PRESETS: RampDefinition[] = [
  {
    id: "slow-in",
    name: "Slow-In",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeInOut" },
      { t: 1, speed: 0.3, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.5 } },
    fx: [],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "slow-out",
    name: "Slow-Out",
    version: 1,
    keyframes: [
      { t: 0, speed: 0.3, ease: "linear" },
      { t: 1, speed: 1, ease: "easeInOut" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.5 } },
    fx: [],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "hero-slowmo",
    name: "Hero Slow-Mo",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.25, speed: 0.2, ease: "linear" },
      { t: 0.75, speed: 0.2, ease: "easeOut" },
      { t: 1, speed: 1, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.6 } },
    fx: [],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "impact",
    name: "Impact",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.5, speed: 0.15, ease: "linear" },
      { t: 0.55, speed: 0.15, ease: "easeOut" },
      { t: 1, speed: 1.5, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.8 } },
    fx: [{ id: "zoom-punch", at: 0.5, params: { intensity: 0.7 } }],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "whip-ramp",
    name: "Whip Ramp",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.5, speed: 4, ease: "easeOut" },
      { t: 1, speed: 1, ease: "linear" },
    ],
    quality: { opticalFlow: false, motionBlur: { enabled: true, strength: 1 } },
    fx: [{ id: "whip-pan-blur", at: 0.5, params: {} }],
    transition: null,
    audio: "followSpeed",
  },
  {
    id: "bullet-time",
    name: "Bullet Time",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.3, speed: 0.05, ease: "linear" },
      { t: 0.7, speed: 0.05, ease: "easeOut" },
      { t: 1, speed: 1, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.4 } },
    fx: [{ id: "glow-pulse", at: 0.5, params: {} }],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "pulse",
    name: "Pulse",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "linear" },
      { t: 0.25, speed: 0.5, ease: "linear" },
      { t: 0.5, speed: 1, ease: "linear" },
      { t: 0.75, speed: 0.5, ease: "linear" },
      { t: 1, speed: 1, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: false, strength: 0 } },
    fx: [],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "reverse-pop",
    name: "Reverse Pop",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.5, speed: -1, ease: "easeOut" },
      { t: 1, speed: 1, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.5 } },
    fx: [],
    transition: null,
    audio: "mute",
  },
  {
    id: "car-launch",
    name: "Car Launch",
    version: 1,
    keyframes: [
      { t: 0, speed: 0.5, ease: "easeIn" },
      { t: 1, speed: 3, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.9 } },
    fx: [{ id: "speed-lines", at: 0.6, params: {} }],
    transition: null,
    audio: "keepPitch",
  },
  {
    id: "drift-flow",
    name: "Drift Flow",
    version: 1,
    keyframes: [
      { t: 0, speed: 1, ease: "easeIn" },
      { t: 0.4, speed: 0.4, ease: "easeOut" },
      { t: 1, speed: 1.2, ease: "linear" },
    ],
    quality: { opticalFlow: true, motionBlur: { enabled: true, strength: 0.7 } },
    fx: [],
    transition: null,
    audio: "keepPitch",
  },
];

export function getPreset(id: string): RampDefinition | undefined {
  return PRESETS.find((p) => p.id === id);
}
