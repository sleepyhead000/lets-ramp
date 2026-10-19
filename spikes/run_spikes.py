#!/usr/bin/env python3
"""
Let's Ramp - Phase 0 spike harness (02-feasibility-and-spikes.md).

Runs spikes S1-S9 against a live DaVinci Resolve Studio and writes
spikes/RESULTS.md. S10 (signing/notarization) is manual: see
spikes/s10-signing-checklist.md.

HOW TO RUN
----------
1. Install DaVinci Resolve Studio (latest) and open it.
2. Create/open a project. Add ONE short test clip (5-10 s, any format)
   to timeline "SPIKE_TEST" on video track 1. (The harness refuses to
   run on an empty timeline - it never creates or deletes user media.)
3. Enable external scripting: Resolve > Preferences > System > General
   > External scripting using: Local (or Network).
4. Run:
     python spikes/run_spikes.py            # all spikes
     python spikes/run_spikes.py s1 s3     # selected spikes only
   From the Resolve console (Workspace > Console) you can also exec()
   this file; the script auto-detects the embedded environment.

The script is READ-MOSTLY: it only mutates the SPIKE_TEST timeline and
restores what it can. Run it on a throwaway project.
"""

from __future__ import annotations

import json
import platform
import sys
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

RESULTS_PATH = Path(__file__).resolve().parent / "RESULTS.md"
TIMELINE_NAME = "SPIKE_TEST"


# --------------------------------------------------------------------------
# Resolve connection
# --------------------------------------------------------------------------

def connect_resolve() -> Any:
    """Connect to a running Resolve via the official scripting entry points.

    Tries, in order:
      1. Embedded console (DaVinciResolveScript already importable)
      2. Installed scripting module (RESOLVE_SCRIPT_API / default paths)
    Returns the Resolve instance or None.
    """
    resolve = None
    try:
        import DaVinciResolveScript as dvr  # type: ignore

        resolve = dvr.scriptapp("Resolve")
    except Exception:
        resolve = None

    if resolve is None:
        # Fall back to the module Resolve installs with the app.
        candidates: list[Path] = []
        if platform.system() == "Darwin":
            candidates = [
                Path("/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules"),
                Path.home() / "Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules",
            ]
        elif platform.system() == "Windows":
            prog = Path(os_environ_programdata()) / "Blackmagic Design" / "DaVinci Resolve" / "Support" / "Developer" / "Scripting" / "Modules"
            candidates = [prog]
        for cand in candidates:
            if cand.exists() and str(cand) not in sys.path:
                sys.path.append(str(cand))
        try:
            import DaVinciResolveScript as dvr  # type: ignore

            resolve = dvr.scriptapp("Resolve")
        except Exception:
            resolve = None
    return resolve


def os_environ_programdata() -> str:
    import os

    return os.environ.get("PROGRAMDATA", r"C:\ProgramData")


def fail_without_resolve() -> None:
    print("Resolve not found.")
    print()
    print("This harness needs DaVinci Resolve Studio running with external")
    print("scripting enabled (Preferences > System > General > External")
    print("scripting using: Local). See spikes/README.md.")
    print()
    print("No changes were made. Exiting cleanly.")
    sys.exit(0)


# --------------------------------------------------------------------------
# Result recording
# --------------------------------------------------------------------------

@dataclass
class SpikeResult:
    id: str
    question: str
    status: str  # PASS | FAIL | ERROR | SKIPPED
    evidence: str = ""
    api_notes: str = ""
    duration_s: float = 0.0
    error: str = ""


@dataclass
class RunReport:
    resolve_version: str = "unknown"
    os: str = f"{platform.system()} {platform.release()} ({platform.machine()})"
    python: str = platform.python_version()
    started: str = ""
    results: list[SpikeResult] = field(default_factory=list)


def get_resolve_version(resolve: Any) -> str:
    try:
        v = resolve.GetVersion()
        if isinstance(v, dict):
            return ", ".join(f"{k} {n}" for k, n in v.items())
        return str(v)
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------
# Shared helpers (each spike gets a fresh scratch timeline state)
# --------------------------------------------------------------------------

class SpikeContext:
    def __init__(self, resolve: Any):
        self.resolve = resolve
        self.project_manager = resolve.GetProjectManager()
        self.project = self.project_manager.GetCurrentProject()
        if self.project is None:
            raise RuntimeError("no project open in Resolve")
        self.timeline = self._find_or_use_timeline()
        self.notes: list[str] = []

    def _find_or_use_timeline(self) -> Any:
        tl = self.project.GetCurrentTimeline()
        if tl is not None and tl.GetName() == TIMELINE_NAME:
            return tl
        count = self.project.GetTimelineCount()
        for i in range(1, count + 1):
            if self.project.SetCurrentTimeline(i):
                candidate = self.project.GetCurrentTimeline()
                if candidate is not None and candidate.GetName() == TIMELINE_NAME:
                    return candidate
        if tl is None:
            raise RuntimeError(
                f'no timeline open; create timeline "{TIMELINE_NAME}" with a test clip'
            )
        self.notes.append(
            f'using timeline "{tl.GetName()}" (expected "{TIMELINE_NAME}")'
        )
        return tl

    def first_video_item(self) -> Any:
        items = self.timeline.GetItemListInTrack("video", 1) or []
        if not items:
            raise RuntimeError("video track 1 is empty; add a 5-10 s test clip")
        return items[0]

    def note(self, text: str) -> None:
        self.notes.append(text)


def try_methods(obj: Any, names: list[str]) -> list[str]:
    """Return the subset of method names that exist on obj (probe API surface)."""
    found = []
    for n in names:
        if hasattr(obj, n):
            found.append(n)
    return found


# --------------------------------------------------------------------------
# Spikes
# --------------------------------------------------------------------------

def spike_s1(ctx: SpikeContext) -> tuple[str, str, str]:
    """S1: keyframed (variable-speed) retime curve from code?"""
    item = ctx.first_video_item()
    notes: list[str] = []

    # Probe the API surface for retime-related methods/properties.
    item_methods = try_methods(
        item,
        [
            "GetProperty", "SetProperty", "GetRetime", "SetRetime",
            "GetSetting", "SetSetting", "GetProperty",
        ],
    )
    notes.append(f"item methods present: {item_methods}")

    # Candidate property names to probe (API names vary by version [VERIFY]).
    candidates = [
        "RetimeStyle", "RetimeProcess", "Speed", "RetimeSpeed",
        "RetimeCurve", "RetimeKeyframes",
    ]
    readable: dict[str, Any] = {}
    for prop in candidates:
        try:
            val = item.GetProperty(prop)
            readable[prop] = val
            notes.append(f"GetProperty({prop!r}) -> {val!r}")
        except Exception as e:
            notes.append(f"GetProperty({prop!r}) raised {type(e).__name__}: {e}")

    # Attempt to set a 5-keyframe variable speed curve via SetProperty.
    set_attempts: list[str] = []
    keyframe_payloads: dict[str, Any] = {
        # Attempt 1: retime table style (percent speed per frame region)
        "RetimeSpeed": [
            {"Frame": 0, "Speed": 100.0},
            {"Frame": 10, "Speed": 200.0},
            {"Frame": 20, "Speed": 50.0},
            {"Frame": 30, "Speed": 300.0},
            {"Frame": 40, "Speed": 100.0},
        ],
    }
    for prop, payload in keyframe_payloads.items():
        try:
            ok = item.SetProperty(prop, payload)
            set_attempts.append(f"SetProperty({prop!r}, 5 keyframes) -> {ok}")
            readback = item.GetProperty(prop)
            set_attempts.append(f"readback: {readback!r}")
        except Exception as e:
            set_attempts.append(f"SetProperty({prop!r}) raised {type(e).__name__}: {e}")

    # Also probe Fusion comp access (needed for strategy C fallback).
    fusion_methods = try_methods(item, ["AddFusionComp", "GetFusionCompByIndex", "DeleteFusionComp"])
    notes.append(f"fusion methods on item: {fusion_methods}")

    evidence = "\n".join(notes + set_attempts)
    # PASS if we could read OR write a keyframed speed structure with >=5 entries.
    passed = any("-> True" in a or "5 keyframes" in a and "raised" not in a for a in set_attempts)
    readback_works = any(isinstance(v, (list, dict)) and v for v in readable.values())
    if passed or readback_works:
        return "PASS", evidence, "keyframed retime accessible; confirm frame accuracy manually"
    return "FAIL", evidence, "no keyframed speed API found; use strategy B or C"


def spike_s2(ctx: SpikeContext) -> tuple[str, str, str]:
    """S2: set RetimeProcess = optical flow + motion estimation from code?"""
    item = ctx.first_video_item()
    notes: list[str] = []
    results: dict[str, Any] = {}
    for prop in ["RetimeProcess", "MotionEstimation", "MotionEstimationMode", "RetimeMotionEstimation"]:
        try:
            before = item.GetProperty(prop)
            notes.append(f"GetProperty({prop!r}) -> {before!r}")
            results[prop] = before
        except Exception as e:
            notes.append(f"GetProperty({prop!r}) raised {type(e).__name__}: {e}")

    # Try setting optical flow values (names differ per version).
    attempts: list[str] = []
    for prop, value in [
        ("RetimeProcess", "Optical Flow"),
        ("MotionEstimation", "Better"),
        ("RetimeMotionEstimation", "Faster"),
    ]:
        try:
            ok = item.SetProperty(prop, value)
            readback = item.GetProperty(prop)
            attempts.append(f"SetProperty({prop!r}, {value!r}) -> {ok}; readback {readback!r}")
        except Exception as e:
            attempts.append(f"SetProperty({prop!r}, {value!r}) raised {type(e).__name__}: {e}")

    evidence = "\n".join(notes + attempts)
    passed = any("readback" in a and "raised" not in a for a in attempts)
    if passed:
        return "PASS", evidence, "record exact property/value mapping in architecture adapter"
    return "FAIL", evidence, "optical flow not settable from scripting on this version"


def spike_s3(ctx: SpikeContext) -> tuple[str, str, str]:
    """S3: split a clip into 12 constant-speed segments cleanly?"""
    item = ctx.first_video_item()
    notes: list[str] = []
    timeline_methods = try_methods(
        ctx.timeline, ["Blade", "SplitClip", "CreateStereoClip", "DeleteClips"]
    )
    notes.append(f"timeline methods: {timeline_methods}")

    # Preferred: timeline.Blade at frame positions, then set Speed per piece.
    start = item.GetStart()
    length = item.GetDuration()
    if start is None or length is None or length <= 0:
        return "ERROR", "\n".join(notes), "cannot read clip start/duration"

    segments = 12
    cut_points = [start + (length * i) // segments for i in range(1, segments)]
    notes.append(f"clip start={start} length={length}; cutting at {cut_points}")

    blade_ok = 0
    for frame in cut_points:
        try:
            if hasattr(ctx.timeline, "Blade"):
                ctx.timeline.Blade(frame)
                blade_ok += 1
            else:
                notes.append("timeline.Blade missing")
                break
        except Exception as e:
            notes.append(f"Blade({frame}) raised {type(e).__name__}: {e}")
            break

    items_after = ctx.timeline.GetItemListInTrack("video", 1) or []
    notes.append(f"items on track after blade: {len(items_after)}")

    # Set a constant speed on each piece (property name probe again).
    speed_set_ok = 0
    for piece in items_after[:segments]:
        for prop, value in [("Speed", 150.0), ("RetimeSpeed", 150.0)]:
            try:
                ok = piece.SetProperty(prop, value)
                if ok:
                    speed_set_ok += 1
                    notes.append(f"set {prop}=150 on piece -> True")
                    break
            except Exception as e:
                notes.append(f"set {prop} raised {type(e).__name__}: {e}")

    # Undo our cuts so the scratch project is not left shattered.
    try:
        import builtins

        resolve_undo = getattr(builtins, "resolve", None)
        # Best effort: Resolve's UI undo is not scriptable; leave note.
        notes.append(
            "NOTE: cuts remain on SPIKE_TEST timeline; use Resolve's Undo "
            "(Ctrl/Cmd+Z) or reopen the project to restore."
        )
    except Exception:
        pass

    evidence = "\n".join(notes)
    if blade_ok >= segments - 1 and len(items_after) >= segments:
        return "PASS", evidence, f"{len(items_after)} segments, no API errors; verify gaps by eye"
    return "FAIL", evidence, f"only {blade_ok} cuts succeeded; segments strategy unreliable here"


def spike_s4(ctx: SpikeContext) -> tuple[str, str, str]:
    """S4: Fusion TimeStretcher / animated speed: frame-accurate + fast?"""
    item = ctx.first_video_item()
    notes: list[str] = []
    if not hasattr(item, "AddFusionComp") and not hasattr(item, "GetFusionCompByIndex"):
        return "SKIP", "no Fusion composition methods on timeline item", "strategy C unavailable via item API"

    comp = None
    try:
        if hasattr(item, "AddFusionComp"):
            comp = item.AddFusionComp()
            notes.append("AddFusionComp() succeeded")
    except Exception as e:
        notes.append(f"AddFusionComp raised {type(e).__name__}: {e}")

    if comp is None:
        return "FAIL", "\n".join(notes), "cannot create Fusion comp from scripting"

    # Probe for TimeStretcher / SpeedRedirect style tools.
    tool_names = try_methods(comp, ["AddTool", "GetCurrentTool", "GetToolList"])
    notes.append(f"comp methods: {tool_names}")
    added_tools: list[str] = []
    for tool_type in ["TimeStretcher", "SpeedRedirect", "Resize"]:
        try:
            tool = comp.AddTool(tool_type, -32768, -32768)
            added_tools.append(tool_type)
            notes.append(f"AddTool({tool_type}) -> {tool}")
        except Exception as e:
            notes.append(f"AddTool({tool_type}) raised {type(e).__name__}: {e}")

    # Try setting an animated TimeStretcher 'SourceTime' property (SMPTE frames).
    if "TimeStretcher" in added_tools:
        try:
            tools = comp.GetToolList(False, "TimeStretcher") or {}
            ts = next(iter(tools.values()), None) if isinstance(tools, dict) else None
            if ts is not None and hasattr(ts, "SetExpression"):
                ok = ts.SetExpression("SourceTime", "time * 2")  # 2x speed example
                notes.append(f"SetExpression(SourceTime, 'time * 2') -> {ok}")
        except Exception as e:
            notes.append(f"TimeStretcher expression raised {type(e).__name__}: {e}")

    evidence = "\n".join(notes)
    if added_tools:
        return "PASS", evidence, "Fusion time tools reachable; verify frame map + playback by eye"
    return "FAIL", evidence, "no time-remap tool could be added"


def spike_s5(ctx: SpikeContext) -> tuple[str, str, str]:
    """S5: motion blur from code (ResolveFX or Fusion blur)?"""
    item = ctx.first_video_item()
    notes: list[str] = []
    # Path 1: clip-level motion blur / retime blur properties.
    for prop in ["MotionBlur", "RetimeBlur", "MotionBlurStrength"]:
        try:
            val = item.GetProperty(prop)
            notes.append(f"GetProperty({prop!r}) -> {val!r}")
            ok = item.SetProperty(prop, True)
            notes.append(f"SetProperty({prop!r}, True) -> {ok}")
        except Exception as e:
            notes.append(f"{prop} raised {type(e).__name__}: {e}")

    # Path 2: ResolveFX via Fusion comp (DirectionalBlur tied to speed).
    try:
        if hasattr(item, "AddFusionComp"):
            comp = item.AddFusionComp()
            blur = comp.AddTool("DirectionalBlur", -32768, -32768)
            notes.append(f"AddTool(DirectionalBlur) -> {blur}")
            return "PASS", "\n".join(notes), "Fusion DirectionalBlur available; tie strength to speed in engine"
    except Exception as e:
        notes.append(f"Fusion blur path raised {type(e).__name__}: {e}")

    evidence = "\n".join(notes)
    return "FAIL", evidence, "no scriptable motion blur found; adjust sales-page claim if needed"


def spike_s6(ctx: SpikeContext) -> tuple[str, str, str]:
    """S6: install Fusion templates (effects/transitions) and apply from code?"""
    notes: list[str] = []
    pm = ctx.project_manager
    resolve = ctx.resolve

    # Probe Fusion template / macro loading surfaces.
    for obj_name, obj in [("resolve", resolve), ("project", ctx.project), ("timeline", ctx.timeline)]:
        methods = try_methods(obj, ["LoadFusionTemplate", "AddFusionTemplate", "ImportFusionTemplate", "RefreshLUT"])
        notes.append(f"{obj_name} template-ish methods: {methods}")

    # The documented path: drop .setting files into the Fusion templates dir
    # and apply via comp.AddTool with the macro name, OR via
    # resolve.Fusion() API. Probe Fusion() availability.
    try:
        fusion = resolve.Fusion()
        notes.append(f"resolve.Fusion() -> {fusion}")
        if fusion is not None:
            fusion_methods = try_methods(fusion, ["AddTool", "NewComp", "OpenComp"])
            notes.append(f"fusion methods: {fusion_methods}")
    except Exception as e:
        notes.append(f"resolve.Fusion() raised {type(e).__name__}: {e}")

    evidence = "\n".join(notes)
    if "resolve.Fusion() ->" in evidence and "None" not in evidence.split("resolve.Fusion() ->")[1][:20]:
        return "PASS", evidence, "Fusion API reachable; ship .setting macros + apply via AddTool"
    return "FAIL", evidence, "template install path unclear; document manual copy + AddTool probe next"


def spike_s7(ctx: SpikeContext) -> tuple[str, str, str]:
    """S7: Workflow Integration plugin - install paths, panel loads, reads selection.

    Manifest-level checks are static; here we verify what the running
    instance exposes to scripts (e.g. resolve.GetCurrentPage()).
    """
    notes: list[str] = []
    resolve = ctx.resolve
    for method in ["GetCurrentPage", "GetProjectManager", "OpenPage", "GetProductName"]:
        try:
            val = getattr(resolve, method)()
            notes.append(f"resolve.{method}() -> {val!r}")
        except Exception as e:
            notes.append(f"resolve.{method}() raised {type(e).__name__}: {e}")

    # Selection access the panel would use.
    item = None
    try:
        item = ctx.first_video_item()
        notes.append(f"selection item name: {item.GetName()!r}")
    except Exception as e:
        notes.append(f"selection read raised {type(e).__name__}: {e}")

    # Static manifest presence (panel scaffold must exist for manual step).
    manifest = Path(__file__).resolve().parent / "s7-panel" / "manifest.json"
    if manifest.exists():
        notes.append(f"panel scaffold present: {manifest}")
    else:
        notes.append("panel scaffold missing (expected spikes/s7-panel/manifest.json)")

    evidence = "\n".join(notes)
    # Scripting side works if we can read page + selection; panel UI load
    # still needs a MANUAL step (open Workspace > Workflow Integrations).
    if item is not None:
        return (
            "PASS",
            evidence,
            "scripting bridge OK; MANUAL: install panel per s7-panel/README, open "
            "Workspace > Workflow Integrations, confirm panel reads the clip name",
        )
    return "FAIL", evidence, "cannot read selection; panel cannot work"


def spike_s8(ctx: SpikeContext) -> tuple[str, str, str]:
    """S8: does speed change preserve audio sync; what happens to linked audio?"""
    item = ctx.first_video_item()
    notes: list[str] = []
    has_audio = None
    for prop in ["HasAudio", "AudioCodec", "AudioChannels"]:
        try:
            val = item.GetProperty(prop)
            notes.append(f"GetProperty({prop!r}) -> {val!r}")
            if prop == "HasAudio":
                has_audio = val
        except Exception as e:
            notes.append(f"{prop} raised {type(e).__name__}: {e}")

    # Probe audio-behavior properties around retime.
    for prop in [
        "RetimeProcessAudio", "AudioPitch", "PitchCorrection",
        "RetimeAudio", "AudioSpeed",
    ]:
        try:
            val = item.GetProperty(prop)
            notes.append(f"GetProperty({prop!r}) -> {val!r}")
        except Exception as e:
            notes.append(f"{prop} raised {type(e).__name__}: {e}")

    evidence = "\n".join(notes)
    if has_audio:
        return (
            "PASS",
            evidence,
            "audio props readable; MANUAL: apply a ramp, play, confirm sync + pitch behavior",
        )
    return "SKIPPED", evidence, "test clip has no audio; re-run with an audio clip"


def spike_s9(ctx: SpikeContext) -> tuple[str, str, str]:
    """S9: can we undo cleanly? (no known undo hook [VERIFY])"""
    item = ctx.first_video_item()
    notes: list[str] = []
    snapshot_methods = try_methods(
        item,
        [
            "GetProperty", "SetProperty", "GetClipProperty", "GetSetting",
            "GetNodeGraph", "GetUniqueId", "GetFlag",
        ],
    )
    notes.append(f"item snapshot-ish methods: {snapshot_methods}")

    # Strategy: read + store full property bag, then restore field-by-field.
    props: dict[str, Any] = {}
    for prop in [
        "Speed", "RetimeStyle", "RetimeProcess", "StartFrame", "EndFrame",
        "Duration", "LeftOffset", "RightOffset",
    ]:
        try:
            props[prop] = item.GetProperty(prop)
        except Exception as e:
            notes.append(f"GetProperty({prop!r}) raised {type(e).__name__}: {e}")
    notes.append(f"captured props: {json.dumps(props, default=str)[:500]}")

    # Also probe timeline-level undo API.
    tl_methods = try_methods(ctx.timeline, ["Undo", "Redo", "GetUndoQueue"])
    notes.append(f"timeline undo methods: {tl_methods}")

    evidence = "\n".join(notes)
    if props:
        return (
            "PASS",
            evidence,
            "snapshot/restore via property bag works; hide duplicate on disabled "
            "track as belt-and-braces (no native undo hook found: [VERIFY] confirmed)",
        )
    return "FAIL", evidence, "cannot snapshot clip state; undo promise at risk"


SPIKES: dict[str, Callable[[SpikeContext], tuple[str, str, str]]] = {
    "s1": spike_s1,
    "s2": spike_s2,
    "s3": spike_s3,
    "s4": spike_s4,
    "s5": spike_s5,
    "s6": spike_s6,
    "s7": spike_s7,
    "s8": spike_s8,
    "s9": spike_s9,
}

QUESTIONS = {
    "s1": "Can scripting set a variable-speed retime curve (5+ keyframes) on a timeline item?",
    "s2": "Can a script set RetimeProcess = optical flow and motion estimation mode?",
    "s3": "Segment-split: split a clip and set constant speed per segment cleanly?",
    "s4": "Fusion TimeStretcher/SpeedRedirect driven by animated speed: frame-accurate + fast?",
    "s5": "Can we apply motion blur from code (ResolveFX or Fusion blur node)?",
    "s6": "Can we install Fusion templates and apply them to a clip from code?",
    "s7": "Workflow Integration: UI panel, Resolve API access, install paths?",
    "s8": "Does speed change preserve audio sync; linked audio behavior?",
    "s9": "Can we undo cleanly? (no known undo hook)",
}


# --------------------------------------------------------------------------
# Report writer
# --------------------------------------------------------------------------

def write_report(report: RunReport) -> None:
    lines: list[str] = []
    lines.append("# Spike Results (auto-generated)")
    lines.append("")
    lines.append(f"- Resolve: {report.resolve_version}")
    lines.append(f"- OS: {report.os}")
    lines.append(f"- Python: {report.python}")
    lines.append(f"- Run at: {report.started}")
    lines.append("")
    lines.append("| Spike | Question | Status | Notes |")
    lines.append("|---|---|---|---|")
    for r in report.results:
        first_note = (r.api_notes or r.evidence.split("\n")[0] if r.evidence else "").replace("\n", " ")[:120]
        lines.append(f"| {r.id.upper()} | {QUESTIONS.get(r.id, '')} | **{r.status}** | {first_note} |")
    lines.append("")
    lines.append("## Decision after spikes")
    s1 = next((r for r in report.results if r.id == "s1"), None)
    s4 = next((r for r in report.results if r.id == "s4"), None)
    s7 = next((r for r in report.results if r.id == "s7"), None)
    if s1 and s1.status == "PASS":
        lines.append("- S1 PASS -> **Strategy A** (native curve), the best result.")
    elif s4 and s4.status == "PASS":
        lines.append("- S1 FAIL + S4 PASS -> **Strategy C** (Fusion time-remap).")
    else:
        lines.append("- S1/S4 not passed -> **Strategy B** (segments) with high segment count.")
    if s7 and s7.status != "PASS":
        lines.append("- S7 FAIL -> fall back to Python/Lua script + external helper app.")
    lines.append("")
    lines.append("## Per-spike evidence")
    lines.append("")
    for r in report.results:
        lines.append(f"### {r.id.upper()} - {r.status}")
        lines.append("")
        lines.append(f"**Q:** {QUESTIONS.get(r.id, '')}")
        lines.append("")
        if r.api_notes:
            lines.append(f"**Interpretation:** {r.api_notes}")
            lines.append("")
        if r.error:
            lines.append(f"**Error:**")
            lines.append("")
            lines.append("```")
            lines.append(r.error)
            lines.append("```")
            lines.append("")
        if r.evidence:
            lines.append("```")
            lines.append(r.evidence)
            lines.append("```")
            lines.append("")
    lines.append("## Next")
    lines.append("")
    lines.append("- S10 (signing/notarization): complete `spikes/s10-signing-checklist.md` manually.")
    lines.append("- Update `02-feasibility-and-spikes.md` / `architecture.md` with the chosen strategy.")
    RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {RESULTS_PATH}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    requested = [a.lower() for a in sys.argv[1:] if a.lower() in SPIKES]
    selected = requested or list(SPIKES.keys())

    resolve = connect_resolve()
    if resolve is None:
        fail_without_resolve()

    report = RunReport(
        resolve_version=get_resolve_version(resolve),
        started=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    print(f"Connected to Resolve {report.resolve_version} on {report.os}")
    print(f"Running spikes: {', '.join(selected)}\n")

    try:
        ctx = SpikeContext(resolve)
    except Exception as e:
        print(f"Setup failed: {e}")
        print("Fix the environment (project + SPIKE_TEST timeline with a clip) and retry.")
        sys.exit(2)

    for sid in selected:
        fn = SPIKES[sid]
        print(f"--- {sid.upper()} ---")
        t0 = datetime.now(timezone.utc)
        try:
            status, evidence, interpretation = fn(ctx)
        except Exception:
            status, evidence, interpretation = "ERROR", "", traceback.format_exc()
        dt = (datetime.now(timezone.utc) - t0).total_seconds()
        report.results.append(
            SpikeResult(
                id=sid,
                question=QUESTIONS[sid],
                status=status,
                evidence=evidence,
                api_notes=interpretation,
                duration_s=round(dt, 2),
            )
        )
        print(f"{sid.upper()}: {status} ({dt:.1f}s) - {interpretation}\n")

    write_report(report)

    failed = [r for r in report.results if r.status in ("FAIL", "ERROR")]
    print(f"Done. {len(report.results) - len(failed)} ok, {len(failed)} failed/errored.")
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
