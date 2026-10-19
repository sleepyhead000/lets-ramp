import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugin" / "LetsRamp.py"

spec = importlib.util.spec_from_file_location("lets_ramp_plugin", PLUGIN)
lr = importlib.util.module_from_spec(spec)
sys.modules["lets_ramp_plugin"] = lr
spec.loader.exec_module(lr)


class TestEasing(unittest.TestCase):
    def test_linear(self):
        for u in (0.0, 0.25, 0.5, 0.75, 1.0):
            self.assertAlmostEqual(lr.ease_value("linear", u), u)

    def test_ease_in(self):
        self.assertAlmostEqual(lr.ease_value("easeIn", 0.0), 0.0)
        self.assertAlmostEqual(lr.ease_value("easeIn", 1.0), 1.0)
        self.assertAlmostEqual(lr.ease_value("easeIn", 0.5), 0.25)
        self.assertLess(lr.ease_value("easeIn", 0.3), 0.3)

    def test_ease_out(self):
        self.assertAlmostEqual(lr.ease_value("easeOut", 0.0), 0.0)
        self.assertAlmostEqual(lr.ease_value("easeOut", 1.0), 1.0)
        self.assertGreater(lr.ease_value("easeOut", 0.7), 0.7)

    def test_ease_in_out_symmetry(self):
        a = lr.ease_value("easeInOut", 0.25)
        b = 1.0 - lr.ease_value("easeInOut", 0.75)
        self.assertAlmostEqual(a, b, places=6)
        self.assertAlmostEqual(lr.ease_value("easeInOut", 0.5), 0.5)

    def test_hold(self):
        self.assertAlmostEqual(lr.ease_value("hold", 0.9), 0.0)
        self.assertAlmostEqual(lr.ease_value("hold", 0.0), 0.0)

    def test_clamps_u(self):
        self.assertAlmostEqual(lr.ease_value("linear", -1.0), 0.0)
        self.assertAlmostEqual(lr.ease_value("linear", 2.0), 1.0)

    def test_unknown_easing_falls_back_linear(self):
        self.assertAlmostEqual(lr.ease_value("wat", 0.5), 0.5)


class TestClampSpeed(unittest.TestCase):
    def test_in_range_unchanged(self):
        self.assertEqual(lr.clamp_speed(1.0), 1.0)
        self.assertEqual(lr.clamp_speed(2.5), 2.5)

    def test_min_magnitude(self):
        self.assertEqual(lr.clamp_speed(0.0), lr.SPEED_MIN)
        self.assertEqual(lr.clamp_speed(0.001), lr.SPEED_MIN)

    def test_max_magnitude(self):
        self.assertEqual(lr.clamp_speed(99.0), lr.SPEED_MAX)

    def test_negative_sign_preserved(self):
        self.assertEqual(lr.clamp_speed(-1.0), -1.0)
        self.assertEqual(lr.clamp_speed(-0.001), -lr.SPEED_MIN)
        self.assertEqual(lr.clamp_speed(-99.0), -lr.SPEED_MAX)

    def test_non_finite(self):
        self.assertEqual(lr.clamp_speed(float("nan")), lr.SPEED_MIN)
        self.assertEqual(lr.clamp_speed(float("inf")), lr.SPEED_MIN)

    def test_garbage(self):
        self.assertEqual(lr.clamp_speed("x"), lr.SPEED_MIN)
        self.assertEqual(lr.clamp_speed(None), lr.SPEED_MIN)


class TestSampleSpeed(unittest.TestCase):
    def test_endpoints(self):
        kf = [(0, 1.0, "linear"), (1, 0.5, "linear")]
        self.assertAlmostEqual(lr.sample_speed(kf, 0.0), 1.0)
        self.assertAlmostEqual(lr.sample_speed(kf, 1.0), 0.5)

    def test_linear_midpoint(self):
        kf = [(0, 1.0, "linear"), (1, 0.5, "linear")]
        self.assertAlmostEqual(lr.sample_speed(kf, 0.5), 0.75)

    def test_clamps_outside(self):
        kf = [(0, 1.0, "linear"), (1, 0.5, "linear")]
        self.assertAlmostEqual(lr.sample_speed(kf, -0.5), 1.0)
        self.assertAlmostEqual(lr.sample_speed(kf, 1.5), 0.5)

    def test_negative_speed_round_trip(self):
        kf = [(0, 1.0, "linear"), (0.5, -1.0, "linear"), (1, 1.0, "linear")]
        self.assertAlmostEqual(lr.sample_speed(kf, 0.5), -1.0)
        sp = lr.sample_speed(kf, 0.25)
        self.assertGreater(sp, 0.0)
        self.assertLessEqual(sp, lr.SPEED_MIN)

    def test_hold_ease(self):
        kf = [(0, 1.0, "hold"), (1, 0.2, "linear")]
        self.assertAlmostEqual(lr.sample_speed(kf, 0.9), 1.0)
        self.assertAlmostEqual(lr.sample_speed(kf, 1.0), 0.2)

    def test_unsorted_input_sorted(self):
        kf = [(1, 0.5, "linear"), (0, 1.0, "linear")]
        self.assertAlmostEqual(lr.sample_speed(kf, 0.0), 1.0)

    def test_empty_returns_unity(self):
        self.assertEqual(lr.sample_speed([], 0.5), 1.0)


class TestIntegrate(unittest.TestCase):
    def test_constant_1x(self):
        kf = [(0, 1.0, "linear"), (1, 1.0, "linear")]
        r = lr.integrate(kf, 240)
        self.assertEqual(r["out_frames"], 240)
        self.assertAlmostEqual(r["min"], 1.0)
        self.assertAlmostEqual(r["max"], 1.0)

    def test_constant_2x_halves(self):
        kf = [(0, 2.0, "linear"), (1, 2.0, "linear")]
        r = lr.integrate(kf, 240)
        self.assertEqual(r["out_frames"], 120)

    def test_constant_half_speed_doubles(self):
        kf = [(0, 0.5, "linear"), (1, 0.5, "linear")]
        r = lr.integrate(kf, 120)
        self.assertEqual(r["out_frames"], 240)

    def test_negative_speed_uses_magnitude(self):
        kf = [(0, 1.0, "linear"), (1, -1.0, "linear")]
        r = lr.integrate(kf, 100)
        self.assertGreater(r["out_frames"], 100)
        self.assertLess(r["min"], 0)
        self.assertGreater(r["max"], 0)

    def test_zero_frames(self):
        kf = [(0, 1.0, "linear"), (1, 1.0, "linear")]
        self.assertEqual(lr.integrate(kf, 0)["out_frames"], 0)

    def test_empty_keyframes(self):
        self.assertEqual(lr.integrate([], 100)["out_frames"], 0)

    def test_min_max_reported(self):
        kf = [(0, 1.0, "linear"), (0.5, 0.1, "linear"), (1, 4.0, "linear")]
        r = lr.integrate(kf, 300)
        self.assertLess(r["min"], 0.2)
        self.assertGreater(r["max"], 3.0)


class TestKeepDuration(unittest.TestCase):
    def test_scale_makes_output_equal_source(self):
        kf = [(0, 1.0, "linear"), (0.5, 0.2, "linear"), (1, 1.0, "linear")]
        scaled = lr.apply_keep_duration(kf)
        src = 480
        r = lr.integrate(scaled, src)
        self.assertAlmostEqual(r["out_frames"], src, delta=max(2, src * 0.01))

    def test_already_1x_unchanged(self):
        kf = [(0, 1.0, "linear"), (1, 1.0, "linear")]
        self.assertAlmostEqual(lr.keep_duration_scale(kf), 1.0, places=2)

    def test_empty_returns_unity_scale(self):
        self.assertEqual(lr.keep_duration_scale([]), 1.0)


class TestNormalizeKeyframes(unittest.TestCase):
    def test_sorts(self):
        kf = lr.normalize_keyframes([(1, 1.0, "linear"), (0, 2.0, "linear")])
        self.assertEqual(kf[0][0], 0.0)
        self.assertEqual(kf[-1][0], 1.0)

    def test_clamps_t(self):
        kf = lr.normalize_keyframes([(-0.5, 1.0, "linear"), (1.5, 1.0, "linear")])
        self.assertEqual(kf[0][0], 0.0)
        self.assertEqual(kf[-1][0], 1.0)

    def test_invalid_ease_replaced(self):
        kf = lr.normalize_keyframes([(0, 1.0, "wat"), (1, 1.0, "linear")])
        self.assertEqual(kf[0][2], "linear")

    def test_single_keyframe_expands(self):
        kf = lr.normalize_keyframes([(0.3, 2.0, "linear")])
        self.assertGreaterEqual(len(kf), 2)
        self.assertEqual(kf[0][0], 0.0)

    def test_empty_defaults(self):
        kf = lr.normalize_keyframes([])
        self.assertEqual(len(kf), 2)
        self.assertEqual(kf[0][1], 1.0)

    def test_dedup_nearby(self):
        kf = lr.normalize_keyframes([(0, 1.0, "linear"), (0.001, 2.0, "linear"), (1, 1.0, "linear")])
        self.assertEqual(len(kf), 2)
        self.assertEqual(kf[0][1], 2.0)


class TestTimecode(unittest.TestCase):
    def test_frames_to_tc(self):
        self.assertEqual(lr.frames_to_tc(24, 24.0), "0:00:01.000")
        self.assertEqual(lr.frames_to_tc(0, 24.0), "0:00:00.000")

    def test_frames_to_tc_bad_fps(self):
        self.assertEqual(lr.frames_to_tc(24, None), "0:00:01.000")

    def test_tc_to_frames(self):
        self.assertEqual(lr.tc_to_frames("0:00:01:00", 24.0), 24)
        self.assertEqual(lr.tc_to_frames("0:01:00:00", 24.0), 1440)

    def test_tc_to_frames_garbage(self):
        self.assertIsNone(lr.tc_to_frames("nope", 24.0))


class TestPresets(unittest.TestCase):
    def test_ten_builtin_presets(self):
        self.assertEqual(len(lr.PRESETS), 10)

    def test_all_presets_normalize_cleanly(self):
        for p in lr.PRESETS:
            kf = lr.normalize_keyframes(p["keyframes"])
            self.assertGreaterEqual(len(kf), 2, p["id"])
            self.assertAlmostEqual(kf[0][0], 0.0)
            self.assertAlmostEqual(kf[-1][0], 1.0)
            r = lr.integrate(kf, 240)
            self.assertGreater(r["out_frames"], 0, p["id"])

    def test_reverse_pop_has_negative(self):
        p = dict((x["id"], x) for x in lr.PRESETS)["reverse-pop"]
        self.assertTrue(any(k[1] < 0 for k in p["keyframes"]))

    def test_effects_and_transitions_catalogs(self):
        self.assertEqual(len(lr.EFFECTS), 10)
        self.assertEqual(len(lr.TRANSITIONS), 10)
        fx_ids = [e["id"] for e in lr.EFFECTS]
        self.assertEqual(len(set(fx_ids)), 10)
        tr_ids = [e["id"] for e in lr.TRANSITIONS]
        self.assertEqual(len(set(tr_ids)), 10)

    def test_preset_fx_reference_known_effects(self):
        known = set(e["id"] for e in lr.EFFECTS) | set(e["id"] for e in lr.TRANSITIONS)
        for p in lr.PRESETS:
            for fx in p.get("fx", []):
                self.assertIn(fx, known, "%s references unknown fx %s" % (p["id"], fx))


if __name__ == "__main__":
    unittest.main()
