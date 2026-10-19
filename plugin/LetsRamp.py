"""
Let's Ramp 0.1.0-alpha - speed-ramp utility for DaVinci Resolve Studio.

INSTALL: copy this file into Resolve's Scripts/Utility folder, restart
Resolve, then: Workspace > Scripts > Utility > LetsRamp.
See plugin/README.md for per-OS paths (or use install.ps1 / install.sh).

STATUS (alpha):
- Preset browser + speed-curve preview + output-duration math: WORK.
- Diagnostics: WORK (read-only API probe; paste results into a GitHub
  issue to help verify Resolve API capabilities).
- Ramp It: EXPERIMENTAL. Tries known property names, snapshots first,
  restores on failure. May do nothing on some Resolve versions - that
  result is itself spike data.

Runs inside Resolve's bundled Python + Qt. No extra installs needed.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets
    except ImportError:
        try:
            from PyQt5 import QtCore, QtGui, QtWidgets
        except ImportError:
            from PyQt6 import QtCore, QtGui, QtWidgets

VERSION = "0.1.1-alpha"
SPEED_MIN, SPEED_MAX = 0.01, 10.0

PRESETS = [
    {"id": "slow-in", "name": "Slow-In", "tag": "Cinematic",
     "keyframes": [(0, 1.0, "easeInOut"), (1, 0.3, "linear")]},
    {"id": "slow-out", "name": "Slow-Out", "tag": "Cinematic",
     "keyframes": [(0, 0.3, "linear"), (1, 1.0, "easeInOut")]},
    {"id": "hero-slowmo", "name": "Hero Slow-Mo", "tag": "Cinematic",
     "keyframes": [(0, 1.0, "easeIn"), (0.25, 0.2, "linear"), (0.75, 0.2, "easeOut"), (1, 1.0, "linear")]},
    {"id": "impact", "name": "Impact", "tag": "Sport",
     "keyframes": [(0, 1.0, "easeIn"), (0.5, 0.15, "linear"), (0.55, 0.15, "easeOut"), (1, 1.5, "linear")]},
    {"id": "whip-ramp", "name": "Whip Ramp", "tag": "Social",
     "keyframes": [(0, 1.0, "easeIn"), (0.5, 4.0, "easeOut"), (1, 1.0, "linear")]},
    {"id": "bullet-time", "name": "Bullet Time", "tag": "Cinematic",
     "keyframes": [(0, 1.0, "easeIn"), (0.3, 0.05, "linear"), (0.7, 0.05, "easeOut"), (1, 1.0, "linear")]},
    {"id": "pulse", "name": "Pulse", "tag": "Social",
     "keyframes": [(0, 1.0, "linear"), (0.25, 0.5, "linear"), (0.5, 1.0, "linear"), (0.75, 0.5, "linear"), (1, 1.0, "linear")]},
    {"id": "reverse-pop", "name": "Reverse Pop", "tag": "Social",
     "keyframes": [(0, 1.0, "easeIn"), (0.5, -1.0, "easeOut"), (1, 1.0, "linear")]},
    {"id": "car-launch", "name": "Car Launch", "tag": "Car",
     "keyframes": [(0, 0.5, "easeIn"), (1, 3.0, "linear")]},
    {"id": "drift-flow", "name": "Drift Flow", "tag": "Car",
     "keyframes": [(0, 1.0, "easeIn"), (0.4, 0.4, "easeOut"), (1, 1.2, "linear")]},
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
    return 0.0


def clamp_speed(v):
    return min(SPEED_MAX, max(SPEED_MIN, v))


def sample_speed(keyframes, t):
    tc = min(1.0, max(0.0, t))
    if tc <= keyframes[0][0]:
        return clamp_speed(keyframes[0][1])
    if tc >= keyframes[-1][0]:
        return clamp_speed(keyframes[-1][1])
    i = 0
    while i < len(keyframes) - 1 and keyframes[i + 1][0] <= tc:
        i += 1
    t0, s0, ease = keyframes[i]
    t1, s1, _ = keyframes[i + 1]
    span = t1 - t0
    if span <= 0:
        return clamp_speed(s0)
    u = (tc - t0) / span
    return clamp_speed(s0 + (s1 - s0) * ease_value(ease, u))


def integrate(keyframes, source_frames, samples=240):
    dt = 1.0 / samples
    total, min_s, max_s = 0.0, 999.0, -999.0
    for s in range(samples):
        sp = sample_speed(keyframes, (s + 0.5) * dt)
        total += (source_frames * dt) / sp
        min_s = min(min_s, sp)
        max_s = max(max_s, sp)
    return {"out_frames": max(1, int(round(total))), "min": min_s, "max": max_s}


def frames_to_tc(frames, fps):
    try:
        fpsf = float(fps)
    except (TypeError, ValueError):
        fpsf = 24.0
    total_s = frames / fpsf
    m, s = divmod(total_s, 60)
    h, m = divmod(int(m), 60)
    return "%d:%02d:%06.3f" % (h, int(m), s)


class CurveWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._kf = PRESETS[0]["keyframes"]
        self.setMinimumHeight(110)

    def set_keyframes(self, kf):
        self._kf = kf
        self.update()

    def paintEvent(self, _event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QtGui.QColor("#181818"))
        p.setPen(QtGui.QColor("#333333"))
        p.drawLine(0, h // 2, w, h // 2)
        speeds = [sample_speed(self._kf, i / 64.0) for i in range(65)]
        lo, hi = min(speeds), max(speeds)
        if hi - lo < 1e-6:
            hi = lo + 1.0
        path = QtGui.QPainterPath()
        for i, sp in enumerate(speeds):
            x = i / 64.0 * w
            y = h - 8 - ((sp - lo) / (hi - lo)) * (h - 16)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        p.setPen(QtGui.QPen(QtGui.QColor("#ffcc33"), 2))
        p.drawPath(path)
        for t, sp, _e in self._kf:
            x = t * w
            y = h - 8 - ((sp - lo) / (hi - lo)) * (h - 16)
            p.setBrush(QtGui.QColor("#ffcc33"))
            p.drawEllipse(QtCore.QPointF(x, y), 3.5, 3.5)
        p.setPen(QtGui.QColor("#888888"))
        p.drawText(6, 14, "%.0f%%" % (hi * 100))
        p.drawText(6, h - 4, "%.0f%%" % (lo * 100))


PROBE_PROPERTIES = [
    "Speed", "RetimeStyle", "RetimeProcess", "MotionEstimation",
    "MotionBlur", "RetimeSpeed", "RetimeKeyframes", "RetimeCurve",
    "StartFrame", "EndFrame", "Duration", "HasAudio", "AudioCodec",
    "RetimeProcessAudio", "PitchCorrection", "LeftOffset", "RightOffset",
]


class LetsRampDialog(QtWidgets.QWidget):
    def __init__(self, resolve):
        super().__init__(None)
        self.resolve = resolve
        self.snapshot = None
        self.last_report = ""
        self.setWindowTitle("Let's Ramp %s" % VERSION)
        self.setMinimumWidth(420)
        self.setStyleSheet(
            "QWidget { background: #1e1e1e; color: #dddddd; "
            "font-family: Segoe UI, sans-serif; font-size: 12px; }"
            "QPushButton { background: #2d2d2d; border: 1px solid #444; "
            "padding: 6px 10px; border-radius: 4px; }"
            "QPushButton:hover { background: #3a3a3a; }"
            "QPushButton#rampBtn { background: #ffcc33; color: #111; font-weight: bold; }"
            "QListWidget { background: #181818; border: 1px solid #333; }"
            "QListWidget::item:selected { background: #3a3a20; }"
            "QPlainTextEdit { background: #141414; border: 1px solid #333; font-family: Consolas; }"
            "QCheckBox { spacing: 6px; }"
        )
        self._build_ui()
        self.refresh_clip_info()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        header = QtWidgets.QLabel("Let's Ramp %s  -  alpha" % VERSION)
        header.setStyleSheet("color: #ffcc33; font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        self.clip_label = QtWidgets.QLabel("No clip detected")
        self.clip_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self.clip_label)

        split = QtWidgets.QHBoxLayout()
        self.preset_list = QtWidgets.QListWidget()
        self.preset_list.setMaximumWidth(160)
        for p in PRESETS:
            item = QtWidgets.QListWidgetItem("%s  [%s]" % (p["name"], p["tag"]))
            item.setData(QtCore.Qt.UserRole, p["id"])
            self.preset_list.addItem(item)
        self.preset_list.currentRowChanged.connect(self._on_preset)
        split.addWidget(self.preset_list)

        right = QtWidgets.QVBoxLayout()
        self.curve = CurveWidget()
        right.addWidget(self.curve)
        self.duration_label = QtWidgets.QLabel("output duration: -")
        self.duration_label.setStyleSheet("color: #aaa;")
        right.addWidget(self.duration_label)
        split.addLayout(right)
        layout.addLayout(split)

        quality = QtWidgets.QHBoxLayout()
        self.optical_flow = QtWidgets.QCheckBox("Optical flow")
        self.optical_flow.setChecked(True)
        self.motion_blur = QtWidgets.QCheckBox("Motion blur")
        self.motion_blur.setChecked(True)
        self.audio_combo = QtWidgets.QComboBox()
        self.audio_combo.addItems(["keepPitch", "mute", "followSpeed"])
        quality.addWidget(self.optical_flow)
        quality.addWidget(self.motion_blur)
        quality.addWidget(self.audio_combo)
        quality.addStretch(1)
        layout.addLayout(quality)

        buttons = QtWidgets.QHBoxLayout()
        ramp_btn = QtWidgets.QPushButton("Ramp It (experimental)")
        ramp_btn.setObjectName("rampBtn")
        ramp_btn.clicked.connect(self._on_ramp)
        undo_btn = QtWidgets.QPushButton("Undo last apply")
        undo_btn.clicked.connect(self._on_undo)
        diag_btn = QtWidgets.QPushButton("Run diagnostics")
        diag_btn.clicked.connect(self._on_diagnostics)
        buttons.addWidget(ramp_btn)
        buttons.addWidget(undo_btn)
        buttons.addWidget(diag_btn)
        layout.addLayout(buttons)

        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        layout.addWidget(self.log)

        if self.preset_list.count():
            self.preset_list.setCurrentRow(2)

    def log_line(self, text):
        self.log.appendPlainText(text)

    def current_preset(self):
        row = self.preset_list.currentRow()
        if row < 0:
            return None
        return PRESETS[row]

    def _on_preset(self, row):
        if row < 0:
            return
        p = PRESETS[row]
        self.curve.set_keyframes(p["keyframes"])
        info = self.get_clip_info()
        if info:
            r = integrate(p["keyframes"], info["frames"])
            self.duration_label.setText(
                "output: %s frames (%s)  |  speed %.0f%% - %.0f%%"
                % (r["out_frames"], frames_to_tc(r["out_frames"], info["fps"]),
                   r["min"] * 100, r["max"] * 100)
            )
        else:
            self.duration_label.setText("output: select a clip to compute")

    def get_timeline(self):
        try:
            pm = self.resolve.GetProjectManager()
            proj = pm.GetCurrentProject() if pm else None
            return proj.GetCurrentTimeline() if proj else None
        except Exception:
            return None

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
        fps = 24.0
        try:
            pm = self.resolve.GetProjectManager()
            proj = pm.GetCurrentProject()
            fps = float(proj.GetSetting("timelineFrameRate"))
        except Exception:
            pass
        name = "?"
        try:
            name = item.GetName()
        except Exception:
            pass
        return {"item": item, "name": name, "frames": frames, "fps": fps}

    def refresh_clip_info(self):
        info = self.get_clip_info()
        if info:
            self.clip_label.setText(
                "Clip: %s  |  %d frames @ %.3f fps  |  %s"
                % (info["name"], info["frames"], info["fps"],
                   frames_to_tc(info["frames"], info["fps"]))
            )
        else:
            self.clip_label.setText("No clip detected - select a clip on the timeline")
        self._on_preset(self.preset_list.currentRow())

    def _on_ramp(self):
        info = self.get_clip_info()
        preset = self.current_preset()
        if not info or preset is None:
            self.log_line("Select a timeline and a preset first.")
            return
        item = info["item"]
        self.log_line("--- Ramp It: %s on %s ---" % (preset["name"], info["name"]))

        self.snapshot = {}
        for prop in PROBE_PROPERTIES:
            try:
                self.snapshot[prop] = item.GetProperty(prop)
            except Exception:
                pass
        self.log_line("Snapshot stored for %d properties." % len(self.snapshot))

        result = integrate(preset["keyframes"], info["frames"])
        target_percent = round(sample_speed(preset["keyframes"], 0.5) * 100, 2)

        attempts = [
            ("Speed", target_percent),
            ("RetimeSpeed", target_percent),
            ("RetimeStyle", "RetimeSpeed"),
        ]
        keyframe_payload = [
            {"Frame": int(t * max(0, result["out_frames"] - 1)), "Speed": sp * 100}
            for t, sp, _e in preset["keyframes"]
        ]
        attempts.append(("RetimeKeyframes", keyframe_payload))
        attempts.append(("RetimeSpeed", keyframe_payload))

        applied = None
        for prop, value in attempts:
            try:
                ok = item.SetProperty(prop, value)
                readback = None
                try:
                    readback = item.GetProperty(prop)
                except Exception:
                    pass
                self.log_line("SetProperty(%s, %s...) -> %s; readback=%s"
                              % (prop, str(value)[:60], ok, str(readback)[:80]))
                if ok and applied is None:
                    applied = prop
            except Exception as e:
                self.log_line("SetProperty(%s) raised %s: %s" % (prop, type(e).__name__, e))

        if self.optical_flow.isChecked():
            for prop, value in (("RetimeProcess", "Optical Flow"), ("MotionEstimation", "Better")):
                try:
                    ok = item.SetProperty(prop, value)
                    self.log_line("SetProperty(%s, %r) -> %s" % (prop, value, ok))
                except Exception as e:
                    self.log_line("%s: %s" % (prop, e))
        if self.motion_blur.isChecked():
            try:
                ok = item.SetProperty("MotionBlur", True)
                self.log_line("SetProperty(MotionBlur, True) -> %s" % ok)
            except Exception as e:
                self.log_line("MotionBlur: %s" % e)
        try:
            ok = item.SetProperty("RetimeProcessAudio", self.audio_combo.currentText())
            self.log_line("SetProperty(RetimeProcessAudio, %r) -> %s"
                          % (self.audio_combo.currentText(), ok))
        except Exception as e:
            self.log_line("RetimeProcessAudio: %s" % e)

        if applied:
            self.log_line("Applied via '%s'. Check the timeline; use Undo if it looks wrong." % applied)
        else:
            self.log_line("No speed property accepted a write on this Resolve version.")
            self.log_line("Nothing was left applied - restoring snapshot.")
            self._restore_snapshot(item)

    def _restore_snapshot(self, item=None):
        if not self.snapshot:
            self.log_line("No snapshot to restore.")
            return
        if item is None:
            info = self.get_clip_info()
            item = info["item"] if info else None
        if item is None:
            self.log_line("No clip to restore onto.")
            return
        restored = 0
        for prop, value in self.snapshot.items():
            try:
                if value is not None:
                    item.SetProperty(prop, value)
                    restored += 1
            except Exception:
                pass
        self.log_line("Restored %d/%d properties." % (restored, len(self.snapshot)))

    def _on_undo(self):
        self._restore_snapshot()

    def _on_diagnostics(self):
        info = self.get_clip_info()
        lines = [
            "Let's Ramp diagnostics %s" % datetime.now().isoformat(timespec="seconds"),
            "Plugin: %s" % VERSION,
            "OS: %s %s (%s)" % (platform.system(), platform.release(), platform.machine()),
            "Python: %s" % platform.python_version(),
        ]
        try:
            lines.append("Resolve: %s" % json.dumps(self.resolve.GetVersion()))
        except Exception:
            pass
        lines.append("Clip: %s" % (info["name"] if info else "none"))
        lines.append("")
        lines.append("Property probe (read-only):")
        if info:
            for prop in PROBE_PROPERTIES:
                try:
                    val = info["item"].GetProperty(prop)
                    lines.append("  %s = %r" % (prop, val))
                except Exception as e:
                    lines.append("  %s -> %s: %s" % (prop, type(e).__name__, e))
            lines.append("")
            lines.append("Method probe:")
            for m in ("GetProperty", "SetProperty", "GetDuration", "GetName",
                      "GetMediaPoolItem", "AddFusionComp", "GetFlag"):
                lines.append("  hasattr(item, %r) = %s" % (m, hasattr(info["item"], m)))
            tl = self.get_timeline()
            for m in ("GetCurrentVideoItem", "GetItemListInTrack", "Blade", "DeleteClips"):
                lines.append("  hasattr(timeline, %r) = %s" % (m, hasattr(tl, m) if tl else False))
        report = "\n".join(lines)
        self.last_report = report
        self.log.setPlainText(report)
        out = Path.home() / "lets-ramp-diagnostics.txt"
        try:
            out.write_text(report, encoding="utf-8")
            self.log_line("Saved to %s" % out)
        except Exception as e:
            self.log_line("Could not save file: %s" % e)
        try:
            QtWidgets.QApplication.clipboard().setText(report)
            self.log_line("Also copied to clipboard - paste into a GitHub issue.")
        except Exception:
            pass


DIALOG = None


def main():
    global DIALOG
    resolve = get_resolve()
    if resolve is None:
        print("Let's Ramp: could not attach to Resolve. Run this from ")
        print("Workspace > Scripts > Utility INSIDE DaVinci Resolve Studio.")
        return
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    if DIALOG is not None:
        try:
            DIALOG.close()
        except Exception:
            pass
    DIALOG = LetsRampDialog(resolve)
    DIALOG.show()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        print("Let's Ramp crashed:\n%s" % err)
        try:
            (Path.home() / "lets-ramp-crash.txt").write_text(err, encoding="utf-8")
        except Exception:
            pass
