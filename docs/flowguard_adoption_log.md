# FlowGuard Adoption Log

## 2026-05-14: FlowBot OpenSpec + FlowGuard Planning Baseline

- Why FlowGuard was used: FlowBot's core design is a stateful multi-agent workflow with Router, Controller, PM, Worker, route modeling, retries, evidence review, and pause/done states.
- Workflow modeled or scoped: This phase documented the architecture where PM uses FlowGuard as the runtime route-synthesis medium. No executable FlowGuard route model was created in this phase because the active work was OpenSpec and concept-document alignment.
- Checks run: `python -c "import flowguard; print(flowguard.SCHEMA_VERSION)"` passed with schema version `1.0`.
- Findings and next action: FlowGuard must appear in two later implementation tracks: a FlowBot protocol model for Router/Controller safety, and a PM route-synthesis sample model that extracts a linear route from model topology. Skipped executable modeling is not a pass for either future track.

## 2026-05-14: Headless MVP Runtime and Demo Verification

- Why FlowGuard was used: FlowBot's MVP runtime depends on ordered state transitions, relay-only Controller behavior, PM route synthesis, Worker evidence, PM review, and final completion evidence.
- Workflow modeled or scoped: `flowbot_models/protocol_model.py` models Router/Controller protocol safety; `flowbot_models/route_synthesis_model.py` models PM route synthesis from contract to topology to one-direction linear route.
- Checks run: `python -m compileall flowbot flowbot_models scripts`, `python scripts/run_flowbot_protocol_checks.py`, `python scripts/run_flowbot_route_synthesis_checks.py`, `python scripts/run_flowbot_smoke_checks.py`, `python scripts/run_flowbot_demo.py --request "用 FlowBot 把这个复杂请求整理成模型优先路线，并生成一个可验收的最终报告。"`, and `openspec validate flowbot-model-first-runtime` all passed.
- Findings and next action: The protocol model detects known-bad hazards including cancel creating a run, Controller doing planning work, dispatch before route acceptance, route acceptance without model artifacts, PM pass without evidence, and done after reject. The route-synthesis model detects linear route without topology, route package without model, and acceptance contracts before route. The demo completed run `run-20260514-135153` with final Router status `DONE`. Remaining product work is UI integration and real background-agent adapters; those are not claimed as complete by this MVP.

## 2026-05-14: FlowPilot Native Startup Intake Cut

- Why FlowGuard was used: The native startup intake now creates or cancels the first stateful boundary before Router/Controller/PM/Worker execution, so it must preserve cancel-before-run, confirmed intake artifacts, and model-backed completion.
- Workflow modeled or scoped: The existing protocol model covers confirmed/cancelled intake, Controller relay-only behavior, route acceptance, Worker evidence, PM review, and done/pause states. The existing route-synthesis model covers PM FlowGuard route topology and linear route extraction.
- Checks run: `python scripts/run_flowbot_protocol_checks.py`, `python scripts/run_flowbot_route_synthesis_checks.py`, `python scripts/run_flowbot_smoke_checks.py`, `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_flowbot_startup_intake_smoke.ps1`, `python scripts/run_flowbot_demo.py --request "用 FlowBot 跑一次最终 native UI 接入后的基线 demo。"`, and `openspec validate flowbot-model-first-runtime` all passed.
- Findings and next action: The WPF startup intake was cut down to the original plan's surface: work request, background-agent toggle, confirm/cancel. It writes FlowBot intake artifacts and invokes the existing runtime from that intake. No browser UI, HTTP server, Cockpit, heartbeat, scheduled continuation, or workbench surface is included.

## 2026-05-14: Local Skill Install and Initial Version

- Why FlowGuard was used: Installing a local Codex skill, recording version `0.1.0`, initializing git, and tagging the baseline are ordered side effects; completion should not be claimed before install validation, version recording, ignore rules, commit, and tag exist.
- Workflow modeled or scoped: `flowbot_models/install_release_model.py` models skill source, installed skill, validation, version file, `.gitignore`, git init, initial commit, and version tag ordering.
- Checks run: `python scripts/run_flowbot_install_release_checks.py`, `python scripts/check_flowbot_skill_install.py`, `openspec validate flowbot-model-first-runtime`, and `openspec validate install-flowbot-skill-initial-version` passed before the git baseline.
- Findings and next action: The installed skill at `C:\Users\liu_y\.codex\skills\flowbot\SKILL.md` matches repository source `skills/flowbot/SKILL.md` and points to this project. The initial version is `0.1.0`; after commit, tag the baseline as `v0.1.0`.
