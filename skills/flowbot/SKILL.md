---
name: flowbot
description: Opt-in only. Use this skill only when the user explicitly asks to use FlowBot or the flowbot skill, for example "Use FlowBot" or "使用 FlowBot". Runs the local FlowBot MVP from C:\Users\liu_y\Documents\FlowBot_20260514 with native startup intake, Router/Controller/PM/Worker letters, and PM-owned FlowGuard route synthesis. Do not activate implicitly for large tasks, generic planning, FlowPilot requests, repository work, or existing .flowbot directories.
---

# FlowBot

FlowBot is a local model-first task runner. It turns an explicit user request into a FlowGuard-backed linear route, then executes it through Router, relay-only Controller, PM, Worker, letters, evidence, and review.

## Activation Boundary

Use FlowBot only after an explicit request in the current thread. If the user is editing, auditing, installing, versioning, or repairing FlowBot itself, treat that as ordinary repository work unless they ask to run a formal FlowBot task.

Do not infer activation from task size, long plans, generic automation language, `.flowbot/` directories, or FlowPilot requests.

## Local Project

Canonical local project root:

```powershell
C:\Users\liu_y\Documents\FlowBot_20260514
```

Initial version:

```text
0.1.0
```

Before a formal run, verify the root exists and the real FlowGuard package is importable:

```powershell
python -c "import flowguard; print(flowguard.SCHEMA_VERSION)"
```

## Run FlowBot

For an interactive user-facing run, open the native startup intake:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\liu_y\Documents\FlowBot_20260514\flowbot\assets\ui\startup_intake\flowbot_startup_intake.ps1
```

The startup intake is the authority for activation. It writes the sealed FlowBot intake body/result/receipt/envelope and starts the existing runtime from the confirmed intake. If the user cancels the intake, do not create a run and do not continue.

For an explicit headless run or smoke-style check:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\liu_y\Documents\FlowBot_20260514\flowbot\assets\ui\startup_intake\flowbot_startup_intake.ps1 -HeadlessConfirmText "<user request>"
```

After a run, inspect the latest `.flowbot/runs/<run-id>/router_state.json`. A successful MVP run ends with `status: DONE` and has `artifacts/final_report.md`.

## Runtime Boundaries

- Router is a deterministic state machine.
- Controller is relay-only: it creates/connects PM and Worker, delivers Router-authorized envelopes, records receipts, and does not plan, execute, or review.
- PM owns user-contract extraction, FlowGuard route modeling, topology refinement, linear route extraction, evidence review, and final acceptance.
- Worker executes only the current work letter or repair letter.
- FlowGuard is part of PM route synthesis, not merely a post-plan validator.

## Verification

Use these commands from the project root when validating FlowBot itself:

```powershell
openspec validate flowbot-model-first-runtime
python scripts/run_flowbot_protocol_checks.py
python scripts/run_flowbot_route_synthesis_checks.py
python scripts/run_flowbot_smoke_checks.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_flowbot_startup_intake_smoke.ps1
```

Do not add browser UI, HTTP server, Cockpit, heartbeat, scheduled continuation, six-role crew, or a new product surface unless the user explicitly approves a new plan.
