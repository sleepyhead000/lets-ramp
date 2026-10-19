"""
Let's Ramp 0.2.0-alpha - speed-ramp plugin for DaVinci Resolve Studio.

INSTALL: copy this file into either
  - Resolve's "Workflow Integration Plugins" root (shows under
    Workspace > Workflow Integrations), or
  - Resolve's "Editor Pages/Scripts/Utility" folder (shows under
    Workspace > Scripts > Utility).
Restart Resolve after installing. See plugin/INSTALL-WINDOWS.md or
plugin/INSTALL-MAC.md, or use Install-LetsRamp.cmd / .ps1.

STATUS (alpha):
- Full UI: preset grid, draggable curve editor, effects drawer,
  quality settings, custom presets, diagnostics.
- Ramp It: EXPERIMENTAL. Snapshots the clip first, tries known
  property paths in priority order, restores on failure. Works or
  not, the log tells you exactly what your Resolve accepted.
- Effects/transitions: EXPERIMENTAL. Attempts are logged and
  reversible; they may no-op on some Resolve versions.

Runs inside Resolve's bundled Python + Qt. No extra installs needed.
"""

from __future__ import annotations

import json
import math
import os
import platform
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

QtCore = QtGui = QtWidgets = None
try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets
        except ImportError:
            try:
                from PyQt6 import QtCore, QtGui, QtWidgets
            except ImportError:
                pass

VERSION = "0.2.0-alpha"
SPEED_MIN, SPEED_MAX = 0.01, 10.0
DATA_DIR = Path.home() / ".lets-ramp"
SETTINGS_PATH = DATA_DIR / "settings.json"
CUSTOM_PRESETS_PATH = DATA_DIR / "custom-presets.json"
EASINGS = ("linear", "easeIn", "easeOut", "easeInOut", "hold")
TAGS = ("All", "Cinematic", "Social", "Car", "Sport", "Custom")

PRESETS = [
    {"id": "slow-in", "name": "Slow-In", "tag": "Cinematic",
     "keyframes": [(0, 1.0, "easeInOut"), (1, 0.3, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.5},
     "audio": "keepPitch", "fx": []},
    {"id": "slow-out", "name": "Slow-Out", "tag": "Cinematic",
     "keyframes": [(0, 0.3, "linear"), (1, 1.0, "easeInOut")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.5},
     "audio": "keepPitch", "fx": []},
    {"id": "hero-slowmo", "name": "Hero Slow-Mo", "tag": "Cinematic",
     "keyframes": [(0, 1.0, "easeIn"), (0.25, 0.2, "linear"), (0.75, 0.2, "easeOut"), (1, 1.0, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.6},
     "audio": "keepPitch", "fx": []},
    {"id": "impact", "name": "Impact", "tag": "Sport",
     "keyframes": [(0, 1.0, "easeIn"), (0.5, 0.15, "linear"), (0.55, 0.15, "easeOut"), (1, 1.5, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.8},
     "audio": "keepPitch", "fx": ["zoom-punch"]},
    {"id": "whip-ramp", "name": "Whip Ramp", "tag": "Social",
     "keyframes": [(0, 1.0, "easeIn"), (0.5, 4.0, "easeOut"), (1, 1.0, "linear")],
     "quality": {"opticalFlow": False, "ofMode": "Faster", "motionBlur": True, "mbStrength": 1.0},
     "audio": "followSpeed", "fx": ["whip-pan-blur"]},
    {"id": "bullet-time", "name": "Bullet Time", "tag": "Cinematic",
     "keyframes": [(0, 1.0, "easeIn"), (0.3, 0.05, "linear"), (0.7, 0.05, "easeOut"), (1, 1.0, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.4},
     "audio": "keepPitch", "fx": ["glow-pulse"]},
    {"id": "pulse", "name": "Pulse", "tag": "Social",
     "keyframes": [(0, 1.0, "linear"), (0.25, 0.5, "linear"), (0.5, 1.0, "linear"),
                   (0.75, 0.5, "linear"), (1, 1.0, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Faster", "motionBlur": False, "mbStrength": 0.0},
     "audio": "keepPitch", "fx": []},
    {"id": "reverse-pop", "name": "Reverse Pop", "tag": "Social",
     "keyframes": [(0, 1.0, "easeIn"), (0.5, -1.0, "easeOut"), (1, 1.0, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.5},
     "audio": "mute", "fx": []},
    {"id": "car-launch", "name": "Car Launch", "tag": "Car",
     "keyframes": [(0, 0.5, "easeIn"), (1, 3.0, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.9},
     "audio": "keepPitch", "fx": ["speed-lines"]},
    {"id": "drift-flow", "name": "Drift Flow", "tag": "Car",
     "keyframes": [(0, 1.0, "easeIn"), (0.4, 0.4, "easeOut"), (1, 1.2, "linear")],
     "quality": {"opticalFlow": True, "ofMode": "Better", "motionBlur": True, "mbStrength": 0.7},
     "audio": "keepPitch", "fx": []},
]

EFFECTS = [
    {"id": "zoom-punch", "name": "Zoom Punch", "desc": "Quick scale punch at the hit", "tool": "Transform"},
    {"id": "flash", "name": "Flash", "desc": "Bright one-beat flash", "tool": "BrightnessContrast"},
    {"id": "shake", "name": "Shake", "desc": "Camera shake burst", "tool": "Transform"},
    {"id": "rgb-split", "name": "RGB Split", "desc": "Chromatic aberration split", "tool": "Displace"},
    {"id": "glow-pulse", "name": "Glow Pulse", "desc": "Soft glow swell", "tool": "Glow"},
    {"id": "speed-lines", "name": "Speed Lines", "desc": "Directional speed streaks", "tool": "DirectionalBlur"},
    {"id": "vignette-pulse", "name": "Vignette Pulse", "desc": "Vignette breathes in", "tool": "Vignette"},
    {"id": "whip-pan-blur", "name": "Whip Pan Blur", "desc": "Horizontal whip blur", "tool": "DirectionalBlur"},
    {"id": "freeze-pop", "name": "Freeze Pop", "desc": "Freeze then pop back", "tool": "TimeStretcher"},
    {"id": "color-snap", "name": "Color Snap", "desc": "Instant grade snap", "tool": "ColorCorrector"},
]

TRANSITIONS = [
    {"id": "zoom-through", "name": "Zoom Through", "desc": "Zoom into the next shot", "tool": "Transform"},
    {"id": "whip-left", "name": "Whip Left", "desc": "Whip pan to the left", "tool": "DirectionalBlur"},
    {"id": "whip-right", "name": "Whip Right", "desc": "Whip pan to the right", "tool": "DirectionalBlur"},
    {"id": "spin-blur", "name": "Spin Blur", "desc": "Rotational blur cut", "tool": "Blur"},
    {"id": "flash-cut", "name": "Flash Cut", "desc": "White flash on the cut", "tool": "BrightnessContrast"},
    {"id": "glitch", "name": "Glitch", "desc": "Digital glitch tear", "tool": "Displace"},
    {"id": "film-burn", "name": "Film Burn", "desc": "Warm burn-through", "tool": "Glow"},
    {"id": "shake-cut", "name": "Shake Cut", "desc": "Impact shake on the cut", "tool": "Transform"},
    {"id": "slide-push", "name": "Slide Push", "desc": "Slide the frame away", "tool": "Transform"},
    {"id": "light-leak", "name": "Light Leak", "desc": "Soft light wash", "tool": "Glow"},
]

PROBE_PROPERTIES = [
    "Speed", "RetimeStyle", "RetimeProcess", "MotionEstimation",
    "MotionBlur", "RetimeSpeed", "RetimeKeyframes", "RetimeCurve",
    "StartFrame", "EndFrame", "Duration", "HasAudio", "AudioCodec",
    "RetimeProcessAudio", "PitchCorrection", "LeftOffset", "RightOffset",
]


def get_resolve():
    for mod_name in ("DaVinciResolveScript", "bmd"):
        try:
            mod = __import__(mod_name)
            resolve = mod.scriptapp("Resolve")
            if resolve is not None:
                return resolve
        except Exception:
            pass
    return None


def ease_value(kind, u):
    u = min(1.0, max(0.0, u))
    if kind == "linear":
        return u
    if kind == "easeIn":
        return u * u
    if kind == "easeOut":
        return 1.0 - (1.0 - u) ** 2
    if kind == "easeInOut":
        return 2.0 * u * u if u < 0.5 else 1.0 - (-2.0 * u + 2.0) ** 2 / 2.0
    if kind == "hold":
        return 0.0
    return u


def clamp_speed(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return SPEED_MIN
    if not math.isfinite(v):
        return SPEED_MIN
    mag = min(SPEED_MAX, max(SPEED_MIN, abs(v)))
    return -mag if v < 0 else mag


def sample_speed(keyframes, t):
    if not keyframes:
        return 1.0
    kfs = sorted(keyframes, key=lambda k: k[0])
    tc = min(1.0, max(0.0, t))
    if tc <= kfs[0][0]:
        return clamp_speed(kfs[0][1])
    if tc >= kfs[-1][0]:
        return clamp_speed(kfs[-1][1])
    i = 0
    while i < len(kfs) - 1 and kfs[i + 1][0] <= tc:
        i += 1
    t0, s0, ease = kfs[i]
    t1, s1, _ = kfs[i + 1]
    span = t1 - t0
    if span <= 0:
        return clamp_speed(s0)
    u = (tc - t0) / span
    return clamp_speed(s0 + (s1 - s0) * ease_value(ease, u))


def integrate(keyframes, source_frames, samples=240):
    if not keyframes or source_frames <= 0:
        return {"out_frames": 0, "min": 1.0, "max": 1.0}
    dt = 1.0 / samples
    total, min_s, max_s = 0.0, 999.0, -999.0
    for s in range(samples):
        sp = sample_speed(keyframes, (s + 0.5) * dt)
        total += (source_frames * dt) / abs(sp)
        min_s = min(min_s, sp)
        max_s = max(max_s, sp)
    return {"out_frames": max(1, int(round(total))), "min": min_s, "max": max_s}


def keep_duration_scale(keyframes):
    if not keyframes:
        return 1.0
    samples = 240
    dt = 1.0 / samples
    integral = 0.0
    for s in range(samples):
        integral += dt / abs(sample_speed(keyframes, (s + 0.5) * dt))
    return integral if integral > 1e-9 else 1.0


def apply_keep_duration(keyframes):
    k = keep_duration_scale(keyframes)
    return [(t, clamp_speed(spd * k), e) for t, spd, e in keyframes]


def normalize_keyframes(keyframes, min_gap=0.005):
    cleaned = []
    for t, spd, ease in keyframes:
        try:
            t = min(1.0, max(0.0, float(t)))
            spd = float(spd)
        except (TypeError, ValueError):
            continue
        if ease not in EASINGS:
            ease = "linear"
        cleaned.append([t, spd, ease])
    cleaned.sort(key=lambda k: k[0])
    deduped = []
    for kf in cleaned:
        if deduped and abs(kf[0] - deduped[-1][0]) < min_gap:
            deduped[-1] = kf
        else:
            deduped.append(kf)
    if not deduped:
        return [(0.0, 1.0, "linear"), (1.0, 1.0, "linear")]
    if len(deduped) == 1:
        t = deduped[0][0]
        deduped = [[t, deduped[0][1], deduped[0][2]], [min(1.0, t + 0.5), deduped[0][1], "linear"]]
    deduped[0][0] = 0.0
    deduped[-1][0] = 1.0
    return [(t, spd, e) for t, spd, e in deduped]


def frames_to_tc(frames, fps):
    try:
        fpsf = float(fps)
    except (TypeError, ValueError):
        fpsf = 24.0
    if fpsf <= 0:
        fpsf = 24.0
    total_s = frames / fpsf
    m, s = divmod(total_s, 60)
    h, m = divmod(int(m), 60)
    return "%d:%02d:%06.3f" % (h, int(m), s)


def tc_to_frames(tc, fps):
    try:
        fpsf = float(fps)
    except (TypeError, ValueError):
        fpsf = 24.0
    if fpsf <= 0:
        fpsf = 24.0
    m = re.match(r"^(\d+):(\d+):(\d+)[:;.](\d+)$", str(tc).strip())
    if not m:
        return None
    h, mi, s, f = (int(x) for x in m.groups())
    return ((h * 60 + mi) * 60 + s) * int(round(fpsf)) + f


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


if QtWidgets is not None:

    class CurvePreviewWidget(QtWidgets.QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self._kf = [(0, 1.0, "linear"), (1, 1.0, "linear")]
            self.setMinimumHeight(44)

        def set_keyframes(self, kf):
            self._kf = kf
            self.update()

        def paintEvent(self, _event):
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.Antialiasing)
            w, h = self.width(), self.height()
            speeds = [sample_speed(self._kf, i / 48.0) for i in range(49)]
            lo, hi = min(speeds), max(speeds)
            if hi - lo < 1e-6:
                hi = lo + 1.0
            path = QtGui.QPainterPath()
            for i, sp in enumerate(speeds):
                x = i / 48.0 * (w - 6) + 3
                y = h - 4 - ((sp - lo) / (hi - lo)) * (h - 8)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            p.setPen(QtGui.QPen(QtGui.QColor("#ffcc33"), 1.6))
            p.drawPath(path)

    class PresetCardWidget(QtWidgets.QWidget):
        def __init__(self, preset, on_click, parent=None):
            super().__init__(parent)
            self.preset = preset
            self.on_click = on_click
            self.selected = False
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor) if hasattr(QtCore.Qt, "PointingHandCursor")
                           else QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            self.setMinimumSize(150, 108)
            self.setMaximumHeight(116)

        def paintEvent(self, _event):
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.Antialiasing)
            r = self.rect().adjusted(1, 1, -2, -2)
            bg = "#3a3a20" if self.selected else "#242424"
            border = "#ffcc33" if self.selected else "#3a3a3a"
            p.setBrush(QtGui.QColor(bg))
            p.setPen(QtGui.QPen(QtGui.QColor(border), 1.5 if self.selected else 1))
            p.drawRoundedRect(r, 6, 6)
            p.setPen(QtGui.QColor("#eeeeee"))
            f = p.font()
            f.setBold(True)
            f.setPointSize(9)
            p.setFont(f)
            p.drawText(r.adjusted(8, 6, -8, 0), QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, self.preset["name"])
            tag = self.preset.get("tag", "")
            if tag:
                p.setPen(QtGui.QColor("#999999"))
                f.setBold(False)
                f.setPointSize(7)
                p.setFont(f)
                p.drawText(r.adjusted(8, 6, -8, 0), QtCore.Qt.AlignRight | QtCore.Qt.AlignTop, tag)
            speeds = [sample_speed(self.preset["keyframes"], i / 40.0) for i in range(41)]
            lo, hi = min(speeds), max(speeds)
            if hi - lo < 1e-6:
                hi = lo + 1.0
            cr = QtCore.QRectF(r.left() + 8, r.top() + 34, r.width() - 16, r.height() - 42)
            path = QtGui.QPainterPath()
            for i, sp in enumerate(speeds):
                x = cr.left() + i / 40.0 * cr.width()
                y = cr.bottom() - ((sp - lo) / (hi - lo)) * cr.height()
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            p.setPen(QtGui.QPen(QtGui.QColor("#ffcc33"), 1.6))
            p.drawPath(path)
            if any(k[1] < 0 for k in self.preset["keyframes"]):
                p.setPen(QtGui.QColor("#66aaff"))
                p.drawText(r.adjusted(8, -14, -8, 0), QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight, "REV")

        def mousePressEvent(self, event):
            self.on_click(self)
            super().mousePressEvent(event)

    class CurveEditorWidget(QtWidgets.QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.keyframes = [(0.0, 1.0, "linear"), (1.0, 1.0, "linear")]
            self.selected_index = 0
            self.dragging = False
            self.onChange = None
            self.onSelect = None
            self.setMinimumHeight(240)
            self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            self.setMouseTracking(False)

        def set_keyframes(self, kf, keep_selection=False):
            self.keyframes = normalize_keyframes(kf)
            if not keep_selection:
                self.selected_index = 0
            self._emit()
            self.update()

        def get_keyframes(self):
            return list(self.keyframes)

        def selected_keyframe(self):
            if 0 <= self.selected_index < len(self.keyframes):
                return self.keyframes[self.selected_index]
            return None

        def select_index(self, idx):
            idx = max(0, min(len(self.keyframes) - 1, idx))
            changed = idx != self.selected_index
            self.selected_index = idx
            if changed and self.onSelect:
                self.onSelect(idx)
            self.update()

        def add_keyframe(self, t, speed):
            t = min(1.0, max(0.0, t))
            speed = clamp_speed(speed)
            ease = "linear"
            self.keyframes = normalize_keyframes(list(self.keyframes) + [(t, speed, ease)])
            best = min(range(len(self.keyframes)), key=lambda i: abs(self.keyframes[i][0] - t))
            self.selected_index = best
            self._emit()
            self.update()

        def remove_selected(self):
            if len(self.keyframes) <= 2:
                return False
            del self.keyframes[self.selected_index]
            self.keyframes = normalize_keyframes(self.keyframes)
            self.selected_index = min(self.selected_index, len(self.keyframes) - 1)
            self._emit()
            self.update()
            return True

        def set_selected_time(self, t):
            kf = self.selected_keyframe()
            if kf is None:
                return
            self.keyframes[self.selected_index] = [min(1.0, max(0.0, t)), kf[1], kf[2]]
            self.keyframes = normalize_keyframes(self.keyframes)
            self._emit()
            self.update()

        def set_selected_speed(self, speed):
            kf = self.selected_keyframe()
            if kf is None:
                return
            self.keyframes[self.selected_index] = [kf[0], clamp_speed(speed), kf[2]]
            self._emit()
            self.update()

        def set_selected_ease(self, ease):
            kf = self.selected_keyframe()
            if kf is None or ease not in EASINGS:
                return
            self.keyframes[self.selected_index] = [kf[0], kf[1], ease]
            self._emit()
            self.update()

        def _emit(self):
            if self.onChange:
                self.onChange()

        def _plot_rect(self):
            return QtCore.QRectF(46, 10, max(10, self.width() - 56), max(10, self.height() - 34))

        def _speed_range(self):
            speeds = [sample_speed(self.keyframes, i / 64.0) for i in range(65)]
            lo, hi = min(speeds), max(speeds)
            span = hi - lo
            pad = max(0.25, span * 0.15)
            lo -= pad
            hi += pad
            if lo > 0:
                lo = 0
            if hi < 1.0:
                hi = max(hi, 1.0)
            if hi - lo < 1.0:
                hi = lo + 1.0
            return lo, hi

        def _to_widget(self, t, speed, lo, hi):
            r = self._plot_rect()
            x = r.left() + t * r.width()
            y = r.bottom() - ((speed - lo) / (hi - lo)) * r.height()
            return QtCore.QPointF(x, y)

        def _to_curve(self, pos):
            r = self._plot_rect()
            lo, hi = self._speed_range()
            t = (pos.x() - r.left()) / r.width() if r.width() > 0 else 0.0
            speed = lo + (r.bottom() - pos.y()) / r.height() * (hi - lo) if r.height() > 0 else 1.0
            return min(1.0, max(0.0, t)), speed

        def paintEvent(self, _event):
            p = QtGui.QPainter(self)
            p.setRenderHint(QtGui.QPainter.Antialiasing)
            p.fillRect(self.rect(), QtGui.QColor("#141414"))
            r = self._plot_rect()
            lo, hi = self._speed_range()
            p.setPen(QtGui.QColor("#2a2a2a"))
            for i in range(5):
                t = i / 4.0
                x = r.left() + t * r.width()
                p.drawLine(QtCore.QPointF(x, r.top()), QtCore.QPointF(x, r.bottom()))
                p.setPen(QtGui.QColor("#666666"))
                p.drawText(QtCore.QPointF(x - 8, self.height() - 8), "%.0f%%" % (t * 100))
                p.setPen(QtGui.QColor("#2a2a2a"))
            speed_ticks = []
            for cand in (0, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, -0.5, -1.0):
                if lo <= cand <= hi:
                    speed_ticks.append(cand)
            for sp in speed_ticks:
                y = r.bottom() - ((sp - lo) / (hi - lo)) * r.height()
                p.setPen(QtGui.QColor("#553300" if abs(sp - 1.0) < 1e-6 else "#2a2a2a"))
                p.drawLine(QtCore.QPointF(r.left(), y), QtCore.QPointF(r.right(), y))
                p.setPen(QtGui.QColor("#777777"))
                p.drawText(QtCore.QPointF(4, y + 4), "%d%%" % round(sp * 100))
                p.setPen(QtGui.QColor("#2a2a2a"))
            if lo <= 0 <= hi:
                y0 = r.bottom() - ((0 - lo) / (hi - lo)) * r.height()
                p.setPen(QtGui.QPen(QtGui.QColor("#444444"), 1))
                p.drawLine(QtCore.QPointF(r.left(), y0), QtCore.QPointF(r.right(), y0))
            path = QtGui.QPainterPath()
            steps = max(64, int(r.width() // 2))
            for i in range(steps + 1):
                t = i / steps
                pt = self._to_widget(t, sample_speed(self.keyframes, t), lo, hi)
                if i == 0:
                    path.moveTo(pt)
                else:
                    path.lineTo(pt)
            p.setPen(QtGui.QPen(QtGui.QColor("#ffcc33"), 2))
            p.drawPath(path)
            for idx, (t, spd, _e) in enumerate(self.keyframes):
                pt = self._to_widget(t, spd, lo, hi)
                if idx == self.selected_index:
                    p.setBrush(QtGui.QColor("#ffcc33"))
                    p.setPen(QtGui.QPen(QtGui.QColor("#ffffff"), 1.5))
                    p.drawEllipse(pt, 6, 6)
                else:
                    p.setBrush(QtGui.QColor("#cc9900"))
                    p.setPen(QtGui.QPen(QtGui.QColor("#111111"), 1))
                    p.drawEllipse(pt, 4, 4)
            p.setPen(QtGui.QColor("#555555"))
            p.drawText(QtCore.QRectF(0, 0, self.width(), self.height() - 20),
                       QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight,
                       "drag keyframes - double-click to add - Del to remove")

        def _hit_test(self, pos):
            lo, hi = self._speed_range()
            for idx, (t, spd, _e) in enumerate(self.keyframes):
                pt = self._to_widget(t, spd, lo, hi)
                dx = pt.x() - pos.x()
                dy = pt.y() - pos.y()
                if dx * dx + dy * dy <= 100:
                    return idx
            return -1

        def mousePressEvent(self, event):
            pos = event.position() if hasattr(event, "position") else event.pos()
            idx = self._hit_test(pos)
            if idx >= 0:
                self.select_index(idx)
                self.dragging = True
            elif event.button() == QtCore.Qt.LeftButton if hasattr(QtCore.Qt, "LeftButton") else event.button() == QtCore.Qt.MouseButton.LeftButton:
                t, speed = self._to_curve(pos)
                self.add_keyframe(t, speed)
                self.dragging = True
            super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if self.dragging and 0 <= self.selected_index < len(self.keyframes):
                pos = event.position() if hasattr(event, "position") else event.pos()
                t, speed = self._to_curve(pos)
                self.keyframes[self.selected_index] = [t, clamp_speed(speed), self.keyframes[self.selected_index][2]]
                self._emit()
                self.update()
            super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self.dragging = False
            self.keyframes = normalize_keyframes(self.keyframes)
            self._emit()
            self.update()
            super().mouseReleaseEvent(event)

        def mouseDoubleClickEvent(self, event):
            pos = event.position() if hasattr(event, "position") else event.pos()
            if self._hit_test(pos) < 0:
                t, speed = self._to_curve(pos)
                self.add_keyframe(t, speed)
            super().mouseDoubleClickEvent(event)

        def keyPressEvent(self, event):
            key = event.key()
            delete_key = getattr(QtCore.Qt, "Key_Delete", None)
            if delete_key is None:
                delete_key = getattr(QtCore.Qt, "Key.Key_Delete", None)
            backspace = getattr(QtCore.Qt, "Key_Backspace", None)
            if key == delete_key or key == backspace:
                if self.remove_selected():
                    return
            super().keyPressEvent(event)


class ResolveBridge(object):
    def __init__(self, resolve):
        self.resolve = resolve
        self.snapshot = None
        self.snapshot_item = None
        self.added_fusion_comps = []
        self.last_apply_report = []

    def log(self, msg):
        self.last_apply_report.append(msg)
        return msg

    def get_project(self):
        try:
            pm = self.resolve.GetProjectManager()
            return pm.GetCurrentProject() if pm else None
        except Exception:
            return None

    def get_timeline(self):
        try:
            proj = self.get_project()
            return proj.GetCurrentTimeline() if proj else None
        except Exception:
            return None

    def get_fps(self):
        try:
            proj = self.get_project()
            fps = float(proj.GetSetting("timelineFrameRate"))
            return fps if fps > 0 else 24.0
        except Exception:
            return 24.0

    def is_studio(self):
        try:
            name = self.resolve.GetProductName() or ""
            return "studio" in str(name).lower()
        except Exception:
            return True

    def resolve_version(self):
        try:
            v = self.resolve.GetVersion()
            if isinstance(v, dict):
                return ", ".join("%s %s" % (k, n) for k, n in v.items())
            return str(v)
        except Exception:
            return "unknown"

    def get_clip_info(self):
        tl = self.get_timeline()
        if tl is None:
            return None
        try:
            item = tl.GetCurrentVideoItem()
        except Exception:
            item = None
        if item is None:
            try:
                items = tl.GetItemListInTrack("video", 1) or []
            except Exception:
                items = []
            item = items[0] if items else None
        if item is None:
            return None
        try:
            frames = int(item.GetDuration())
        except Exception:
            try:
                frames = int(item.GetProperty("EndFrame")) - int(item.GetProperty("StartFrame"))
            except Exception:
                frames = 0
        try:
            start = int(item.GetStart())
        except Exception:
            try:
                start = int(item.GetProperty("StartFrame"))
            except Exception:
                start = 0
        fps = self.get_fps()
        name = "?"
        try:
            name = item.GetName()
        except Exception:
            pass
        return {"item": item, "name": name, "frames": frames, "fps": fps, "start": start, "timeline": tl}

    def get_playhead_t(self, info):
        if not info:
            return None
        try:
            tc = info["timeline"].GetCurrentTimecode()
        except Exception:
            return None
        frame = tc_to_frames(tc, info["fps"])
        if frame is None or info["frames"] <= 0:
            return None
        return min(1.0, max(0.0, (frame - info["start"]) / float(info["frames"])))

    def take_snapshot(self, item):
        snap = {}
        for prop in PROBE_PROPERTIES:
            try:
                snap[prop] = item.GetProperty(prop)
            except Exception:
                pass
        self.snapshot = snap
        self.snapshot_item = item
        return len(snap)

    def restore_snapshot(self, item=None):
        if not self.snapshot:
            return 0
        item = item or self.snapshot_item
        if item is None:
            info = self.get_clip_info()
            item = info["item"] if info else None
        if item is None:
            return 0
        restored = 0
        for prop, value in self.snapshot.items():
            try:
                if value is not None:
                    item.SetProperty(prop, value)
                    restored += 1
            except Exception:
                pass
        self._remove_added_comps(item)
        return restored

    def _remove_added_comps(self, item):
        removed = 0
        for comp_name in list(self.added_fusion_comps):
            try:
                if hasattr(item, "DeleteFusionCompByName"):
                    if item.DeleteFusionCompByName(comp_name):
                        removed += 1
            except Exception:
                pass
        self.added_fusion_comps = []
        return removed

    def apply_ramp(self, info, keyframes, quality, audio_mode, keep_duration=False):
        self.last_apply_report = []
        item = info["item"]
        kf = normalize_keyframes(keyframes)
        if keep_duration:
            kf = apply_keep_duration(kf)
            self.log("Keep-duration: speeds scaled so output length matches the source.")
        n = self.take_snapshot(item)
        self.log("Snapshot stored for %d properties." % n)
        result = integrate(kf, info["frames"])
        constant = all(abs(k[1] - kf[0][1]) < 1e-6 for k in kf)

        keyframe_payload = [
            {"Frame": int(round(t * max(0, info["frames"] - 1))), "Speed": round(spd * 100.0, 3)}
            for t, spd, _e in kf
        ]
        applied = None
        if not constant:
            for prop in ("RetimeKeyframes", "RetimeSpeed"):
                try:
                    ok = item.SetProperty(prop, keyframe_payload)
                    readback = None
                    try:
                        readback = item.GetProperty(prop)
                    except Exception:
                        pass
                    self.log("SetProperty(%s, %d keyframes) -> %s; readback=%s"
                             % (prop, len(keyframe_payload), ok, str(readback)[:80]))
                    if ok and applied is None:
                        applied = prop
                        break
                except Exception as e:
                    self.log("SetProperty(%s) raised %s: %s" % (prop, type(e).__name__, e))
        if applied is None:
            mid = sample_speed(kf, 0.5)
            target_percent = round(mid * 100.0, 2)
            for prop in ("Speed", "RetimeSpeed"):
                try:
                    ok = item.SetProperty(prop, target_percent)
                    readback = None
                    try:
                        readback = item.GetProperty(prop)
                    except Exception:
                        pass
                    self.log("SetProperty(%s, %s%%) -> %s; readback=%s"
                             % (prop, target_percent, ok, str(readback)[:80]))
                    if ok and applied is None:
                        applied = prop
                        break
                except Exception as e:
                    self.log("SetProperty(%s) raised %s: %s" % (prop, type(e).__name__, e))
            if applied:
                self.log("Note: only the mid-point speed could be applied on this "
                         "Resolve version (single-speed fallback).")
        try:
            ok = item.SetProperty("RetimeStyle", "RetimeSpeed")
            self.log("SetProperty(RetimeStyle, 'RetimeSpeed') -> %s" % ok)
        except Exception as e:
            self.log("RetimeStyle: %s" % e)

        if quality.get("opticalFlow"):
            mode = quality.get("ofMode", "Better")
            for prop, value in (("RetimeProcess", "Optical Flow"), ("MotionEstimation", mode),
                                ("RetimeMotionEstimation", mode)):
                try:
                    ok = item.SetProperty(prop, value)
                    self.log("SetProperty(%s, %r) -> %s" % (prop, value, ok))
                except Exception as e:
                    self.log("%s: %s" % (prop, e))
        if quality.get("motionBlur"):
            try:
                ok = item.SetProperty("MotionBlur", True)
                self.log("SetProperty(MotionBlur, True) -> %s" % ok)
            except Exception as e:
                self.log("MotionBlur: %s" % e)
            strength = float(quality.get("mbStrength", 0.5))
            for prop in ("MotionBlurStrength", "RetimeBlur"):
                try:
                    ok = item.SetProperty(prop, round(strength, 3))
                    self.log("SetProperty(%s, %.2f) -> %s" % (prop, strength, ok))
                    if ok:
                        break
                except Exception as e:
                    self.log("%s: %s" % (prop, e))
        if audio_mode:
            try:
                ok = item.SetProperty("RetimeProcessAudio", audio_mode)
                self.log("SetProperty(RetimeProcessAudio, %r) -> %s" % (audio_mode, ok))
            except Exception as e:
                self.log("RetimeProcessAudio: %s" % e)

        if not applied:
            self.log("No speed property accepted a write - restoring snapshot.")
            self.restore_snapshot(item)
            return {"ok": False, "applied": None, "result": result, "kf": kf}
        return {"ok": True, "applied": applied, "result": result, "kf": kf}

    def apply_effects(self, info, fx_selections):
        self.last_apply_report = self.last_apply_report
        item = info["item"]
        applied_effects = []
        fusion = None
        try:
            fusion = self.resolve.Fusion()
        except Exception as e:
            self.log("resolve.Fusion() raised %s: %s" % (type(e).__name__, e))
        for fx_id, sel in fx_selections:
            if not sel.get("enabled"):
                continue
            catalog = dict((e["id"], e) for e in EFFECTS)
            meta = catalog.get(fx_id) or dict((e["id"], e) for e in TRANSITIONS).get(fx_id)
            if not meta:
                continue
            intensity = float(sel.get("intensity", 0.5))
            done = False
            for prop in ("FX_" + fx_id.replace("-", "_").title(), fx_id):
                try:
                    ok = item.SetProperty(prop, round(intensity, 3))
                    if ok:
                        self.log("Effect %s applied via SetProperty(%s, %.2f)." % (fx_id, prop, intensity))
                        done = True
                        break
                except Exception:
                    pass
            if not done and fusion is not None and hasattr(item, "AddFusionComp"):
                try:
                    comp = item.AddFusionComp()
                    if comp is not None:
                        comp_name = "LetsRamp_%s" % fx_id
                        try:
                            comp.SetName(comp_name)
                        except Exception:
                            pass
                        self.added_fusion_comps.append(comp_name)
                        tool = comp.AddTool(meta["tool"], -32768, -32768)
                        if tool is not None:
                            for inp, val in (("Blend", round(intensity, 3)),):
                                try:
                                    tool.SetInput(inp, val, 0)
                                except Exception:
                                    pass
                            self.log("Effect %s: Fusion %s tool added (comp %s)."
                                     % (fx_id, meta["tool"], comp_name))
                            done = True
                        else:
                            self.log("Effect %s: AddTool(%s) returned None." % (fx_id, meta["tool"]))
                except Exception as e:
                    self.log("Effect %s Fusion path raised %s: %s" % (fx_id, type(e).__name__, e))
            if done:
                applied_effects.append(fx_id)
            else:
                self.log("Effect %s: not supported on this Resolve version (no-op)." % fx_id)
        return applied_effects

    def diagnostics(self, info):
        lines = [
            "Let's Ramp diagnostics %s" % datetime.now().isoformat(timespec="seconds"),
            "Plugin: %s" % VERSION,
            "OS: %s %s (%s)" % (platform.system(), platform.release(), platform.machine()),
            "Python: %s" % platform.python_version(),
            "Resolve: %s" % self.resolve_version(),
            "Product studio: %s" % self.is_studio(),
            "Clip: %s" % (info["name"] if info else "none"),
            "",
            "Property probe (read-only):",
        ]
        if info:
            for prop in PROBE_PROPERTIES:
                try:
                    val = info["item"].GetProperty(prop)
                    lines.append("  %s = %r" % (prop, val))
                except Exception as e:
                    lines.append("  %s -> %s: %s" % (prop, type(e).__name__, e))
            lines.append("")
            lines.append("Method probe:")
            for m in ("GetProperty", "SetProperty", "GetDuration", "GetName", "GetStart",
                      "GetFusionCompByIndex", "AddFusionComp", "DeleteFusionCompByName", "GetFlag"):
                lines.append("  hasattr(item, %r) = %s" % (m, hasattr(info["item"], m)))
            tl = info.get("timeline") or self.get_timeline()
            for m in ("GetCurrentVideoItem", "GetItemListInTrack", "Blade", "DeleteClips", "GetCurrentTimecode"):
                lines.append("  hasattr(timeline, %r) = %s" % (m, hasattr(tl, m) if tl else False))
            try:
                fusion = self.resolve.Fusion()
                lines.append("resolve.Fusion() = %r" % (fusion is not None,))
            except Exception as e:
                lines.append("resolve.Fusion() raised %s: %s" % (type(e).__name__, e))
        return "\n".join(lines)


if QtWidgets is not None:

    class RampScreen(QtWidgets.QWidget):
        def __init__(self, window):
            super().__init__(window)
            self.window = window
            self.cards = []
            self._build()

        def _build(self):
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(8)

            clip_row = QtWidgets.QHBoxLayout()
            self.clip_label = QtWidgets.QLabel("No clip detected")
            self.clip_label.setStyleSheet("color: #aaaaaa;")
            clip_row.addWidget(self.clip_label, 1)
            refresh_btn = QtWidgets.QPushButton("Refresh")
            refresh_btn.clicked.connect(self.window.refresh_clip_info)
            clip_row.addWidget(refresh_btn)
            layout.addLayout(clip_row)

            filter_row = QtWidgets.QHBoxLayout()
            self.search = QtWidgets.QLineEdit()
            self.search.setPlaceholderText("Search presets...")
            self.search.textChanged.connect(self._rebuild_grid)
            filter_row.addWidget(self.search, 1)
            layout.addLayout(filter_row)

            chip_row = QtWidgets.QHBoxLayout()
            self.chip_group = QtWidgets.QButtonGroup(self)
            self.chip_group.setExclusive(True)
            for i, tag in enumerate(TAGS):
                btn = QtWidgets.QPushButton(tag)
                btn.setCheckable(True)
                btn.setMinimumWidth(64)
                if i == 0:
                    btn.setChecked(True)
                self.chip_group.addButton(btn, i)
                chip_row.addWidget(btn)
            chip_row.addStretch(1)
            self.chip_group.buttonClicked.connect(lambda _b: self._rebuild_grid())
            layout.addLayout(chip_row)

            self.grid_scroll = QtWidgets.QScrollArea()
            self.grid_scroll.setWidgetResizable(True)
            self.grid_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.grid_container = QtWidgets.QWidget()
            self.grid = QtWidgets.QGridLayout(self.grid_container)
            self.grid.setContentsMargins(4, 4, 4, 4)
            self.grid.setSpacing(8)
            self.grid.setAlignment(QtCore.Qt.AlignTop)
            self.grid_scroll.setWidget(self.grid_container)
            layout.addWidget(self.grid_scroll, 1)

            quality_box = QtWidgets.QHBoxLayout()
            self.optical_flow = QtWidgets.QCheckBox("Optical Flow")
            self.optical_flow.setChecked(True)
            self.of_mode = QtWidgets.QComboBox()
            self.of_mode.addItems(["Faster", "Better"])
            self.of_mode.setCurrentText("Better")
            self.motion_blur = QtWidgets.QCheckBox("Motion Blur")
            self.motion_blur.setChecked(True)
            self.mb_strength = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.mb_strength.setRange(0, 100)
            self.mb_strength.setValue(50)
            self.mb_strength.setFixedWidth(110)
            self.audio_combo = QtWidgets.QComboBox()
            self.audio_combo.addItems(["keepPitch", "mute", "followSpeed"])
            self.keep_duration = QtWidgets.QCheckBox("Keep duration")
            quality_box.addWidget(self.optical_flow)
            quality_box.addWidget(self.of_mode)
            quality_box.addWidget(self.motion_blur)
            quality_box.addWidget(self.mb_strength)
            quality_box.addWidget(QtWidgets.QLabel("Audio:"))
            quality_box.addWidget(self.audio_combo)
            quality_box.addWidget(self.keep_duration)
            quality_box.addStretch(1)
            layout.addLayout(quality_box)

            self.duration_label = QtWidgets.QLabel("output duration: -")
            self.duration_label.setStyleSheet("color: #aaaaaa;")
            layout.addWidget(self.duration_label)

            btn_row = QtWidgets.QHBoxLayout()
            self.ramp_btn = QtWidgets.QPushButton("Ramp It")
            self.ramp_btn.setObjectName("rampBtn")
            self.ramp_btn.setMinimumHeight(40)
            self.ramp_btn.clicked.connect(self.window.on_ramp_it)
            undo_btn = QtWidgets.QPushButton("Undo")
            undo_btn.clicked.connect(self.window.on_undo)
            btn_row.addWidget(self.ramp_btn, 2)
            btn_row.addWidget(undo_btn, 1)
            layout.addLayout(btn_row)

            self._rebuild_grid()

        def _active_tag(self):
            btn = self.chip_group.checkedButton()
            return btn.text() if btn else "All"

        def _visible_presets(self):
            tag = self._active_tag()
            needle = self.search.text().strip().lower()
            out = []
            for p in self.window.all_presets():
                if tag == "Custom" and not p.get("custom"):
                    continue
                if tag not in ("All", "Custom") and p.get("tag") != tag:
                    continue
                if needle and needle not in p["name"].lower():
                    continue
                out.append(p)
            return out

        def _rebuild_grid(self, *_args):
            while self.grid.count():
                item = self.grid.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
            self.cards = []
            presets = self._visible_presets()
            cols = 3
            for i, p in enumerate(presets):
                card = PresetCardWidget(p, self.window.on_preset_clicked)
                card.selected = p["id"] == self.window.selected_preset_id
                self.grid.addWidget(card, i // cols, i % cols)
                self.cards.append(card)
            if not presets:
                lbl = QtWidgets.QLabel("No presets match.")
                lbl.setStyleSheet("color: #777;")
                self.grid.addWidget(lbl, 0, 0)

        def sync_selection(self):
            for card in self.cards:
                card.selected = card.preset["id"] == self.window.selected_preset_id
                card.update()

        def update_duration(self):
            info = self.window.bridge.get_clip_info()
            kfs = self.window.current_keyframes()
            if info and kfs:
                r = integrate(kfs, info["frames"])
                self.duration_label.setText(
                    "output: %s frames (%s)  |  speed %.0f%% to %.0f%%  |  source %d frames"
                    % (r["out_frames"], frames_to_tc(r["out_frames"], info["fps"]),
                       r["min"] * 100, r["max"] * 100, info["frames"])
                )
            else:
                self.duration_label.setText("output duration: select a clip to compute")

        def update_clip(self, info):
            if info:
                self.clip_label.setText(
                    "Clip: %s  |  %d frames @ %.3f fps  |  %s"
                    % (info["name"], info["frames"], info["fps"],
                       frames_to_tc(info["frames"], info["fps"]))
                )
            else:
                self.clip_label.setText("No clip detected - select a clip on the timeline")

        def load_quality_from_preset(self, preset):
            q = preset.get("quality", {})
            self.optical_flow.setChecked(bool(q.get("opticalFlow", True)))
            self.of_mode.setCurrentText(q.get("ofMode", "Better"))
            self.motion_blur.setChecked(bool(q.get("motionBlur", True)))
            self.mb_strength.setValue(int(round(float(q.get("mbStrength", 0.5)) * 100)))
            self.audio_combo.setCurrentText(preset.get("audio", "keepPitch"))

        def current_quality(self):
            return {
                "opticalFlow": self.optical_flow.isChecked(),
                "ofMode": self.of_mode.currentText(),
                "motionBlur": self.motion_blur.isChecked(),
                "mbStrength": self.mb_strength.value() / 100.0,
            }

    class EffectsScreen(QtWidgets.QWidget):
        def __init__(self, window):
            super().__init__(window)
            self.window = window
            self.tabs = QtWidgets.QTabWidget()
            self.fx_list = self._make_list(EFFECTS)
            self.tr_list = self._make_list(TRANSITIONS)
            self.tabs.addTab(self.fx_list, "Effects")
            self.tabs.addTab(self.tr_list, "Transitions")
            self.tabs.currentChanged.connect(self._on_tab)

            detail = QtWidgets.QVBoxLayout()
            self.detail_title = QtWidgets.QLabel("Select an effect")
            self.detail_title.setStyleSheet("color: #ffcc33; font-weight: bold; font-size: 13px;")
            self.detail_desc = QtWidgets.QLabel("")
            self.detail_desc.setWordWrap(True)
            self.detail_desc.setStyleSheet("color: #999;")
            self.enable_check = QtWidgets.QCheckBox("Enable on Ramp It")
            self.intensity = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.intensity.setRange(0, 100)
            self.intensity.setValue(50)
            self.intensity_label = QtWidgets.QLabel("Intensity: 50%")
            self.intensity.valueChanged.connect(
                lambda v: self.intensity_label.setText("Intensity: %d%%" % v))
            self.placement = QtWidgets.QComboBox()
            self.placement.addItems(["at peak", "at start", "at end", "at playhead"])
            self.warning = QtWidgets.QLabel(
                "Experimental: effects are attempted with snapshot/undo protection.\n"
                "They may no-op on some Resolve versions - the log always says what happened.")
            self.warning.setWordWrap(True)
            self.warning.setStyleSheet("color: #cc8800;")
            detail.addWidget(self.detail_title)
            detail.addWidget(self.detail_desc)
            detail.addWidget(self.enable_check)
            detail.addWidget(self.intensity_label)
            detail.addWidget(self.intensity)
            detail.addWidget(QtWidgets.QLabel("Placement:"))
            detail.addWidget(self.placement)
            detail.addWidget(self.warning)
            detail.addStretch(1)

            body = QtWidgets.QHBoxLayout()
            body.addWidget(self.tabs, 3)
            body.addLayout(detail, 2)

            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)
            hint = QtWidgets.QLabel(
                "Effects and transitions ride along with the ramp. "
                "Check what you want, set intensity, then hit Ramp It on the Ramp tab.")
            hint.setStyleSheet("color: #888;")
            layout.addWidget(hint)
            layout.addLayout(body)

        def _make_list(self, catalog):
            lw = QtWidgets.QListWidget()
            lw.itemSelectionChanged.connect(self._on_select)
            for meta in catalog:
                item = QtWidgets.QListWidgetItem("%s  -  %s" % (meta["name"], meta["desc"]))
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                item.setData(QtCore.Qt.UserRole, meta["id"])
                lw.addItem(item)
            return lw

        def _current_catalog(self):
            return TRANSITIONS if self.tabs.currentIndex() == 1 else EFFECTS

        def _current_list(self):
            return self.tr_list if self.tabs.currentIndex() == 1 else self.fx_list

        def _on_tab(self, _idx):
            self._on_select()

        def _on_select(self):
            lw = self._current_list()
            item = lw.currentItem()
            if item is None:
                self.detail_title.setText("Select an %s" %
                                          ("transition" if self.tabs.currentIndex() == 1 else "effect"))
                self.detail_desc.setText("")
                return
            fx_id = item.data(QtCore.Qt.UserRole)
            meta = dict((m["id"], m) for m in self._current_catalog()).get(fx_id, {})
            self.detail_title.setText(meta.get("name", fx_id))
            self.detail_desc.setText(meta.get("desc", ""))
            state = self.window.effect_state.get(fx_id, {})
            self.enable_check.setChecked(bool(state.get("enabled")))
            self.intensity.setValue(int(round(float(state.get("intensity", 0.5)) * 100)))
            if "placement" in state:
                idx = self.placement.findText(state["placement"])
                if idx >= 0:
                    self.placement.setCurrentIndex(idx)
            self.enable_check.toggled.connect(lambda _c, fid=fx_id: self._persist(fid))
            self.intensity.valueChanged.connect(lambda _v, fid=fx_id: self._persist(fid))
            self.placement.currentTextChanged.connect(lambda _t, fid=fx_id: self._persist(fid))

        def _persist(self, fx_id):
            self.window.effect_state[fx_id] = {
                "enabled": self.enable_check.isChecked(),
                "intensity": self.intensity.value() / 100.0,
                "placement": self.placement.currentText(),
            }
            lw = self._current_list()
            item = lw.currentItem()
            if item and item.data(QtCore.Qt.UserRole) == fx_id:
                item.setCheckState(QtCore.Qt.Checked if self.enable_check.isChecked() else QtCore.Qt.Unchecked)

        def sync_from_preset(self, preset):
            for lw in (self.fx_list, self.tr_list):
                for i in range(lw.count()):
                    it = lw.item(i)
                    it.setCheckState(QtCore.Qt.Unchecked)
            for fx_id in preset.get("fx", []):
                for i in range(self.fx_list.count()):
                    it = self.fx_list.item(i)
                    if it.data(QtCore.Qt.UserRole) == fx_id:
                        it.setCheckState(QtCore.Qt.Checked)
                        self.window.effect_state[fx_id] = {
                            "enabled": True,
                            "intensity": self.window.effect_state.get(fx_id, {}).get("intensity", 0.5),
                            "placement": self.window.effect_state.get(fx_id, {}).get("placement", "at peak"),
                        }

        def enabled_effects(self):
            out = []
            for lw, catalog in ((self.fx_list, EFFECTS), (self.tr_list, TRANSITIONS)):
                for i in range(lw.count()):
                    it = lw.item(i)
                    if it.checkState() == QtCore.Qt.Checked:
                        fx_id = it.data(QtCore.Qt.UserRole)
                        state = self.window.effect_state.get(fx_id, {"enabled": True, "intensity": 0.5})
                        state = dict(state)
                        state["enabled"] = True
                        meta = dict((m["id"], m) for m in catalog)
                        out.append((fx_id, state, meta.get(fx_id, {}).get("name", fx_id)))
            return out

    class EditorScreen(QtWidgets.QWidget):
        def __init__(self, window):
            super().__init__(window)
            self.window = window
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)
            layout.setSpacing(8)

            top = QtWidgets.QHBoxLayout()
            self.title = QtWidgets.QLabel("Curve Editor")
            self.title.setStyleSheet("color: #ffcc33; font-weight: bold; font-size: 13px;")
            top.addWidget(self.title)
            top.addStretch(1)
            layout.addLayout(top)

            self.editor = CurveEditorWidget()
            self.editor.onChange = self._on_curve_change
            self.editor.onSelect = lambda _i: self._sync_fields()
            layout.addWidget(self.editor, 1)

            fields = QtWidgets.QHBoxLayout()
            fields.addWidget(QtWidgets.QLabel("Keyframe"))
            self.kf_index = QtWidgets.QSpinBox()
            self.kf_index.setMinimum(1)
            self.kf_index.valueChanged.connect(self._on_index)
            fields.addWidget(self.kf_index)
            fields.addWidget(QtWidgets.QLabel("Time %"))
            self.time_spin = QtWidgets.QDoubleSpinBox()
            self.time_spin.setRange(0.0, 100.0)
            self.time_spin.setDecimals(2)
            self.time_spin.setSingleStep(1.0)
            self.time_spin.valueChanged.connect(self._on_time)
            fields.addWidget(self.time_spin)
            fields.addWidget(QtWidgets.QLabel("Speed %"))
            self.speed_spin = QtWidgets.QDoubleSpinBox()
            self.speed_spin.setRange(-1000.0, 1000.0)
            self.speed_spin.setDecimals(1)
            self.speed_spin.setSingleStep(5.0)
            self.speed_spin.valueChanged.connect(self._on_speed)
            fields.addWidget(self.speed_spin)
            fields.addWidget(QtWidgets.QLabel("Ease"))
            self.ease_combo = QtWidgets.QComboBox()
            self.ease_combo.addItems(list(EASINGS))
            self.ease_combo.currentTextChanged.connect(self._on_ease)
            fields.addWidget(self.ease_combo)
            layout.addLayout(fields)

            btns = QtWidgets.QHBoxLayout()
            add_btn = QtWidgets.QPushButton("Add keyframe at playhead")
            add_btn.clicked.connect(self._on_add_at_playhead)
            del_btn = QtWidgets.QPushButton("Remove keyframe")
            del_btn.clicked.connect(self._on_remove)
            reset_btn = QtWidgets.QPushButton("Reset to linear")
            reset_btn.clicked.connect(self._on_reset)
            save_btn = QtWidgets.QPushButton("Save as preset")
            save_btn.clicked.connect(self._on_save_preset)
            btns.addWidget(add_btn)
            btns.addWidget(del_btn)
            btns.addWidget(reset_btn)
            btns.addStretch(1)
            btns.addWidget(save_btn)
            layout.addLayout(btns)

            self.readout = QtWidgets.QLabel("output: -")
            self.readout.setStyleSheet("color: #aaa;")
            layout.addWidget(self.readout)
            self._sync_fields()

        def load_keyframes(self, kf):
            self.editor.set_keyframes(kf)
            self._sync_fields()

        def _sync_fields(self):
            n = len(self.editor.keyframes)
            self.kf_index.blockSignals(True)
            self.kf_index.setMaximum(max(1, n))
            self.kf_index.setValue(self.editor.selected_index + 1)
            self.kf_index.blockSignals(False)
            kf = self.editor.selected_keyframe()
            if kf:
                self.time_spin.blockSignals(True)
                self.speed_spin.blockSignals(True)
                self.ease_combo.blockSignals(True)
                self.time_spin.setValue(round(kf[0] * 100.0, 2))
                self.speed_spin.setValue(round(kf[1] * 100.0, 1))
                idx = self.ease_combo.findText(kf[2])
                self.ease_combo.setCurrentIndex(max(0, idx))
                self.time_spin.blockSignals(False)
                self.speed_spin.blockSignals(False)
                self.ease_combo.blockSignals(False)
            self.readout.setText(self.window.duration_text())

        def _on_curve_change(self):
            self.window.on_editor_changed()
            self._sync_fields()

        def _on_index(self, val):
            self.editor.select_index(val - 1)
            self._sync_fields()

        def _on_time(self, val):
            self.editor.set_selected_time(val / 100.0)

        def _on_speed(self, val):
            self.editor.set_selected_speed(val / 100.0)

        def _on_ease(self, text):
            self.editor.set_selected_ease(text)

        def _on_add_at_playhead(self):
            info = self.window.bridge.get_clip_info()
            t = self.window.bridge.get_playhead_t(info) if info else None
            if t is None:
                t = 0.5
            kf = self.editor.selected_keyframe()
            speed = kf[1] if kf else 1.0
            self.editor.add_keyframe(t, speed)
            self._sync_fields()

        def _on_remove(self):
            self.editor.remove_selected()
            self._sync_fields()

        def _on_reset(self):
            self.editor.set_keyframes([(0.0, 1.0, "linear"), (1.0, 1.0, "linear")])
            self.window.on_editor_changed()

        def _on_save_preset(self):
            name, ok = QtWidgets.QInputDialog.getText(self, "Save preset", "Preset name:")
            if not ok or not name.strip():
                return
            self.window.save_custom_preset(name.strip(), self.editor.get_keyframes())

    class SettingsScreen(QtWidgets.QWidget):
        def __init__(self, window):
            super().__init__(window)
            self.window = window
            layout = QtWidgets.QVBoxLayout(self)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(10)

            title = QtWidgets.QLabel("Settings")
            title.setStyleSheet("color: #ffcc33; font-weight: bold; font-size: 14px;")
            layout.addWidget(title)

            self.def_of = QtWidgets.QCheckBox("Default: Optical Flow")
            self.def_of.setChecked(True)
            self.def_of_mode = QtWidgets.QComboBox()
            self.def_of_mode.addItems(["Faster", "Better"])
            self.def_mb = QtWidgets.QCheckBox("Default: Motion Blur")
            self.def_mb.setChecked(True)
            self.def_mb_strength = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            self.def_mb_strength.setRange(0, 100)
            self.def_mb_strength.setValue(50)
            self.def_audio = QtWidgets.QComboBox()
            self.def_audio.addItems(["keepPitch", "mute", "followSpeed"])

            form = QtWidgets.QFormLayout()
            form.addRow(self.def_of, self.def_of_mode)
            mb_row = QtWidgets.QHBoxLayout()
            mb_row.addWidget(self.def_mb)
            mb_row.addWidget(self.def_mb_strength)
            mb_row.addStretch(1)
            form.addRow("Motion blur:", mb_row)
            form.addRow("Default audio:", self.def_audio)
            layout.addLayout(form)

            save_btn = QtWidgets.QPushButton("Save defaults")
            save_btn.clicked.connect(self._save)
            layout.addWidget(save_btn)

            diag_btn = QtWidgets.QPushButton("Run diagnostics (read-only)")
            diag_btn.clicked.connect(window.on_diagnostics)
            layout.addWidget(diag_btn)

            info = QtWidgets.QLabel(
                "Let's Ramp %s\n"
                "Data folder: %s\n"
                "github.com/sleepyhead000/lets-ramp\n"
                "Alpha: ramp apply + effects are experimental and reversible." % (VERSION, DATA_DIR)
            )
            info.setStyleSheet("color: #888;")
            layout.addWidget(info)
            layout.addStretch(1)
            self._load()

        def _load(self):
            s = self.window.settings
            self.def_of.setChecked(bool(s.get("opticalFlow", True)))
            self.def_of_mode.setCurrentText(s.get("ofMode", "Better"))
            self.def_mb.setChecked(bool(s.get("motionBlur", True)))
            self.def_mb_strength.setValue(int(round(float(s.get("mbStrength", 0.5)) * 100)))
            self.def_audio.setCurrentText(s.get("audio", "keepPitch"))

        def _save(self):
            self.window.settings = {
                "opticalFlow": self.def_of.isChecked(),
                "ofMode": self.def_of_mode.currentText(),
                "motionBlur": self.def_mb.isChecked(),
                "mbStrength": self.def_mb_strength.value() / 100.0,
                "audio": self.def_audio.currentText(),
            }
            save_json(SETTINGS_PATH, self.window.settings)
            self.window.show_toast("Defaults saved.")

    class LetsRampWindow(QtWidgets.QWidget):
        def __init__(self, resolve):
            super().__init__(None)
            self.bridge = ResolveBridge(resolve)
            self.settings = load_json(SETTINGS_PATH, {})
            self.custom_presets = load_json(CUSTOM_PRESETS_PATH, [])
            self.effect_state = {}
            self.selected_preset_id = "hero-slowmo"
            self.current_kf = None
            self._toast_timer = None

            self.setWindowTitle("Let's Ramp %s" % VERSION)
            self.setMinimumSize(920, 640)
            self.resize(1000, 700)
            self.setStyleSheet(
                "QWidget { background: #1e1e1e; color: #dddddd; "
                "font-family: Segoe UI, sans-serif; font-size: 12px; }"
                "QPushButton { background: #2d2d2d; border: 1px solid #444; "
                "padding: 6px 12px; border-radius: 4px; }"
                "QPushButton:hover { background: #3a3a3a; }"
                "QPushButton:checked { background: #3a3a20; border-color: #ffcc33; color: #ffcc33; }"
                "QPushButton#navBtn { text-align: left; padding: 10px 14px; border: none; "
                "background: transparent; border-radius: 6px; font-size: 13px; }"
                "QPushButton#navBtn:hover { background: #2a2a2a; }"
                "QPushButton#navBtn:checked { background: #33301a; color: #ffcc33; font-weight: bold; }"
                "QPushButton#rampBtn { background: #ffcc33; color: #111; font-weight: bold; "
                "font-size: 14px; border: none; }"
                "QPushButton#rampBtn:hover { background: #ffd966; }"
                "QPushButton#rampBtn:disabled { background: #555; color: #999; }"
                "QListWidget { background: #181818; border: 1px solid #333; border-radius: 4px; }"
                "QListWidget::item { padding: 6px; }"
                "QListWidget::item:selected { background: #3a3a20; }"
                "QPlainTextEdit { background: #141414; border: 1px solid #333; "
                "font-family: Consolas; border-radius: 4px; }"
                "QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #141414; "
                "border: 1px solid #3a3a3a; border-radius: 4px; padding: 4px 6px; }"
                "QTabWidget::pane { border: 1px solid #333; }"
                "QTabBar::tab { background: #242424; padding: 6px 16px; border: 1px solid #333; "
                "border-bottom: none; }"
                "QTabBar::tab:selected { background: #1e1e1e; color: #ffcc33; }"
                "QScrollArea { border: none; }"
                "QCheckBox { spacing: 6px; }"
                "QStatusBar { background: #141414; color: #aaa; }"
            )
            self._build()
            self.refresh_clip_info()
            preset = self._preset_by_id(self.selected_preset_id)
            if preset:
                self._load_preset(preset)

        def _build(self):
            root = QtWidgets.QHBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            nav = QtWidgets.QVBoxLayout()
            nav.setContentsMargins(8, 12, 8, 12)
            nav.setSpacing(4)
            logo = QtWidgets.QLabel("LET'S RAMP")
            logo.setStyleSheet("color: #ffcc33; font-weight: bold; font-size: 16px; letter-spacing: 1px;")
            nav.addWidget(logo)
            ver = QtWidgets.QLabel("v%s" % VERSION)
            ver.setStyleSheet("color: #666; font-size: 10px;")
            nav.addWidget(ver)
            nav.addSpacing(12)
            self.nav_group = QtWidgets.QButtonGroup(self)
            self.nav_group.setExclusive(True)
            self.pages = QtWidgets.QStackedWidget()
            self.ramp_screen = RampScreen(self)
            self.effects_screen = EffectsScreen(self)
            self.editor_screen = EditorScreen(self)
            self.settings_screen = SettingsScreen(self)
            for i, (label, page) in enumerate([
                ("Ramp", self.ramp_screen),
                ("Effects", self.effects_screen),
                ("Editor", self.editor_screen),
                ("Settings", self.settings_screen),
            ]):
                btn = QtWidgets.QPushButton(label)
                btn.setObjectName("navBtn")
                btn.setCheckable(True)
                btn.setMinimumHeight(36)
                self.nav_group.addButton(btn, i)
                nav.addWidget(btn)
                self.pages.addWidget(page)
            self.nav_group.buttonClicked.connect(self._on_nav)
            self.nav_group.button(0).setChecked(True)
            nav.addStretch(1)
            nav_widget = QtWidgets.QWidget()
            nav_widget.setFixedWidth(150)
            nav_widget.setLayout(nav)
            nav_widget.setStyleSheet("QWidget { background: #171717; border-right: 1px solid #2a2a2a; }")

            right = QtWidgets.QVBoxLayout()
            right.setContentsMargins(0, 0, 0, 0)
            right.setSpacing(0)
            right.addWidget(self.pages, 1)
            self.toast = QtWidgets.QLabel("")
            self.toast.setAlignment(QtCore.Qt.AlignCenter)
            self.toast.setMinimumHeight(30)
            self.toast.setStyleSheet(
                "QLabel { background: #2a2a1a; color: #ffcc33; border-top: 1px solid #444; "
                "padding: 4px; }")
            self.toast.hide()
            right.addWidget(self.toast)
            right_widget = QtWidgets.QWidget()
            right_widget.setLayout(right)

            root.addWidget(nav_widget)
            root.addWidget(right_widget, 1)

        def _on_nav(self, button):
            idx = self.nav_group.id(button)
            self.pages.setCurrentIndex(idx)
            if idx == 0:
                self.ramp_screen.update_duration()

        def all_presets(self):
            out = list(PRESETS)
            for cp in self.custom_presets:
                p = dict(cp)
                p["custom"] = True
                p["tag"] = "Custom"
                out.append(p)
            return out

        def _preset_by_id(self, pid):
            for p in self.all_presets():
                if p["id"] == pid:
                    return p
            return None

        def on_preset_clicked(self, card):
            self.selected_preset_id = card.preset["id"]
            self.ramp_screen.sync_selection()
            self._load_preset(card.preset)

        def _load_preset(self, preset):
            self.current_kf = normalize_keyframes(preset["keyframes"])
            self.ramp_screen.load_quality_from_preset(preset)
            self.effects_screen.sync_from_preset(preset)
            self.editor_screen.load_keyframes(self.current_kf)
            self.ramp_screen.update_duration()

        def current_keyframes(self):
            if self.current_kf is None:
                return [(0.0, 1.0, "linear"), (1.0, 1.0, "linear")]
            return normalize_keyframes(self.current_kf)

        def on_editor_changed(self):
            self.current_kf = self.editor_screen.editor.get_keyframes()
            self.selected_preset_id = None
            self.ramp_screen.sync_selection()
            self.ramp_screen.update_duration()
            self.toast.hide()

        def duration_text(self):
            info = self.bridge.get_clip_info()
            kfs = self.current_keyframes()
            if not info:
                return "output: select a clip"
            r = integrate(kfs, info["frames"])
            return ("output: %s frames (%s)  |  speed %.0f%% to %.0f%%"
                    % (r["out_frames"], frames_to_tc(r["out_frames"], info["fps"]),
                       r["min"] * 100, r["max"] * 100))

        def refresh_clip_info(self):
            info = self.bridge.get_clip_info()
            self.ramp_screen.update_clip(info)
            self.ramp_screen.update_duration()
            self.editor_screen.readout.setText(self.duration_text())
            studio = self.bridge.is_studio()
            self.ramp_screen.ramp_btn.setEnabled(studio)
            if not studio:
                self.show_toast("Free Resolve detected - Let's Ramp needs Studio.")

        def show_toast(self, message, ms=5000):
            self.toast.setText(message)
            self.toast.show()
            if self._toast_timer is not None:
                self._toast_timer.stop()
            self._toast_timer = QtCore.QTimer(self)
            self._toast_timer.setSingleShot(True)
            self._toast_timer.timeout.connect(self.toast.hide)
            self._toast_timer.start(ms)

        def save_custom_preset(self, name, keyframes):
            pid = "custom-%s" % re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            preset = {
                "id": pid,
                "name": name,
                "tag": "Custom",
                "keyframes": [[t, s, e] for t, s, e in normalize_keyframes(keyframes)],
                "quality": self.ramp_screen.current_quality(),
                "audio": self.ramp_screen.audio_combo.currentText(),
                "fx": [],
            }
            self.custom_presets = [p for p in self.custom_presets if p["id"] != pid]
            self.custom_presets.append(preset)
            save_json(CUSTOM_PRESETS_PATH, self.custom_presets)
            self.ramp_screen._rebuild_grid()
            self.show_toast("Saved preset '%s'." % name)

        def _open_log_dialog(self, title, text):
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle(title)
            dlg.setMinimumSize(640, 420)
            layout = QtWidgets.QVBoxLayout(dlg)
            edit = QtWidgets.QPlainTextEdit()
            edit.setReadOnly(True)
            edit.setPlainText(text)
            layout.addWidget(edit)
            copy_btn = QtWidgets.QPushButton("Copy to clipboard")
            copy_btn.clicked.connect(lambda: QtWidgets.QApplication.clipboard().setText(text))
            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dlg.accept)
            row = QtWidgets.QHBoxLayout()
            row.addStretch(1)
            row.addWidget(copy_btn)
            row.addWidget(close_btn)
            layout.addLayout(row)
            dlg.exec_() if hasattr(dlg, "exec_") else dlg.exec()

        def on_ramp_it(self):
            info = self.bridge.get_clip_info()
            if not info:
                self.show_toast("Select a clip on the timeline first.")
                return
            kfs = self.current_keyframes()
            quality = self.ramp_screen.current_quality()
            audio = self.ramp_screen.audio_combo.currentText()
            keep_dur = self.ramp_screen.keep_duration.isChecked()
            preset_name = "custom curve"
            preset = self._preset_by_id(self.selected_preset_id) if self.selected_preset_id else None
            if preset:
                preset_name = preset["name"]
            self.ramp_screen.ramp_btn.setEnabled(False)
            try:
                outcome = self.bridge.apply_ramp(info, kfs, quality, audio, keep_duration=keep_dur)
                fx = self.effects_screen.enabled_effects()
                applied_fx = []
                if fx and outcome["ok"]:
                    applied_fx = self.bridge.apply_effects(info, fx)
                report = "\n".join(self.bridge.last_apply_report)
                if outcome["ok"]:
                    r = outcome["result"]
                    msg = "Applied %s -> %s frames." % (preset_name, r["out_frames"])
                    if applied_fx:
                        msg += " Effects: %s." % ", ".join(applied_fx)
                    msg += " Undo restores the clip."
                    self.show_toast(msg, 7000)
                    self._open_log_dialog("Ramp applied - log", report)
                else:
                    self.show_toast("Apply failed on this Resolve version - clip restored. "
                                    "See log for details.", 7000)
                    self._open_log_dialog("Ramp failed - log (clip restored)", report)
            except Exception:
                err = traceback.format_exc()
                self.bridge.restore_snapshot(info["item"])
                self.show_toast("Unexpected error - clip restored. See log.")
                self._open_log_dialog("Ramp crashed (restored)", err)
            finally:
                self.ramp_screen.ramp_btn.setEnabled(True)
                self.refresh_clip_info()

        def on_undo(self):
            n = self.bridge.restore_snapshot()
            if n:
                self.show_toast("Restored %d properties + removed added comps." % n)
            else:
                self.show_toast("Nothing to undo yet - apply a ramp first.")

        def on_diagnostics(self):
            info = self.bridge.get_clip_info()
            report = self.bridge.diagnostics(info)
            out = Path.home() / "lets-ramp-diagnostics.txt"
            try:
                out.write_text(report, encoding="utf-8")
                saved = "Saved to %s" % out
            except Exception as e:
                saved = "Could not save file: %s" % e
            try:
                QtWidgets.QApplication.clipboard().setText(report)
                clipped = "Copied to clipboard."
            except Exception:
                clipped = ""
            self._open_log_dialog("Diagnostics", "%s\n%s\n\n%s" % (report, saved, clipped))


DIALOG = None


def main():
    global DIALOG
    resolve = globals().get("resolve")
    if resolve is None:
        resolve = get_resolve()
    if resolve is None:
        print("Let's Ramp: could not attach to Resolve. Run this from")
        print("Workspace > Workflow Integrations or Workspace > Scripts > Utility")
        print("INSIDE DaVinci Resolve Studio.")
        return
    if QtWidgets is None:
        print("Let's Ramp: no Qt bindings found inside Resolve's Python.")
        return
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    if DIALOG is not None:
        try:
            DIALOG.close()
        except Exception:
            pass
    DIALOG = LetsRampWindow(resolve)
    DIALOG.show()


def _should_autorun():
    if os.environ.get("LETS_RAMP_NO_AUTORUN"):
        return False
    if globals().get("resolve") is not None:
        return True
    try:
        import builtins
        if getattr(builtins, "resolve", None) is not None:
            return True
    except Exception:
        pass
    return False


if __name__ == "__main__" or _should_autorun():
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        print("Let's Ramp crashed:\n%s" % err)
        try:
            (Path.home() / "lets-ramp-crash.txt").write_text(err, encoding="utf-8")
        except Exception:
            pass
