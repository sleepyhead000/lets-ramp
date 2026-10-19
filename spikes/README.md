# Spike Harness

Phase 0 feasibility tests for `02-feasibility-and-spikes.md`. Run these
**before** building against assumptions marked `[VERIFY]`.

## Prerequisites

1. **DaVinci Resolve Studio** (latest) installed. Free will not do —
   several capabilities require Studio.
2. A throwaway project with a timeline named **`SPIKE_TEST`** containing
   one 5–10 s test clip on video track 1 (include audio for S8).
3. External scripting enabled: **Resolve > Preferences > System >
   General > External scripting using: Local**.

## Run

```bash
python spikes/run_spikes.py           # all spikes S1–S9
python spikes/run_spikes.py s1 s3     # selected spikes
```

- Without Resolve running: prints a clear message and exits 0 — safe in CI.
- With Resolve: connects, runs each spike against `SPIKE_TEST`, writes
  `RESULTS.md` with pass/fail, evidence, and the Strategy A/B/C decision.
- S3 makes cuts on the timeline (undo with Ctrl/Cmd+Z or reopen the project).
- Run on **both macOS and Windows**; the report records OS + Resolve version.

## S10 (manual)

Signing/notarization needs real certificates — see
[`s10-signing-checklist.md`](s10-signing-checklist.md).

## S7 panel (manual step)

Automated part checks the scripting bridge; the UI load test needs the
scaffold in [`s7-panel/`](s7-panel/README.md) installed into Resolve's
Workflow Integrations folder.

## After the run

1. Commit `RESULTS.md` so the decision is recorded in history.
2. Update the decision section of `02-feasibility-and-spikes.md`.
3. Set the adapter's capability flags in `src/adapter/resolve/` to match.
