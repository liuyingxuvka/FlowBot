# FlowBot Runtime Contracts

This document records the MVP runtime contracts implemented in Python.

The native startup intake is implemented at:

```text
flowbot/assets/ui/startup_intake/flowbot_startup_intake.ps1
```

It is a FlowPilot-style WPF bootloader cut down to the FlowBot MVP surface:
work request, background-agent toggle, confirm/cancel. Confirm writes the
FlowBot intake artifacts and invokes the existing runtime from that confirmed
intake.

The local Codex skill source lives at `skills/flowbot/SKILL.md` and is installed
to `C:\Users\liu_y\.codex\skills\flowbot`.

## Run Layout

```text
.flowbot/
  runs/
    run-YYYYMMDD-HHMMSS/
      intake/
        flowbot_intake_body.md
        flowbot_intake_result.json
        flowbot_intake_receipt.json
        flowbot_intake_envelope.json
      router_state.json
      controller_ledger.json
      pm/
        user_contract.md
        route_hypothesis.md
        flowguard_route_model.py
        flowguard_result.json
        model_findings.md
        route_topology.json
        linear_route.json
        node_acceptance_contracts.json
        route_package.json
        final_acceptance.json
      letters/
      checkins/
      reviews/
      artifacts/
      mermaid.mmd
```

## Intake

- `flowbot_intake_body.md`: sealed user request body.
- `flowbot_intake_result.json`: confirm/cancel result with `body_path`, `body_hash`, and startup options.
- `flowbot_intake_receipt.json`: user confirmation record.
- `flowbot_intake_envelope.json`: Controller-visible envelope. It sets `controller_may_read_body: false`.

Cancel behavior: cancelled intake does not create a run and does not start PM or Worker.

## Router State

`router_state.json` stores:

- `status`: one of `RUN_CREATED`, `ROLES_READY`, `ROUTE_ACCEPTED`, `NODE_DISPATCHED`, `WORKER_SUBMITTED`, `NODE_PASSED`, `NODE_RETRYING`, `PAUSED`, `DONE`.
- `current_node_id`: active linear-route node or null.
- `linear_route`: accepted PM route spine.
- `passed_node_ids`: nodes passed by PM evidence review.
- `retry_counts`: per-node retry counts.
- `events`: state transition log.

## Controller Ledger

`controller_ledger.json` stores relay events only:

- `roles_ready`
- `deliver_to_pm`
- `return_from_pm`
- `deliver_to_worker`
- `return_from_worker`

Controller is not allowed to write planning, execution, or review decisions.

## PM Route Package

`pm/route_package.json` must include:

- `user_contract`
- `route_hypothesis`
- `flowguard_route_model`
- `flowguard_result`
- `model_findings`
- `route_topology`
- `linear_route`
- `node_acceptance_contracts`

Router rejects a route package that is missing any required artifact or whose FlowGuard result is not ok.

## Letters

### route_model_request

Sent to PM through Controller. Contains body path/hash, required route artifacts, and `controller_may_read_body: false`.

### work_letter

Sent to Worker through Controller. Contains the active node, current scope, forbidden actions, completion criteria, and evidence requirements.

### worker_checkin

Returned by Worker. Contains completed action and evidence paths.

### pm_review

Returned by PM. Contains `pass`, `reject`, or `needs_user`, plus evidence checked and repair instruction when needed.

### repair_letter

Created when PM rejects a node and retry limit has not been exceeded.

## FlowGuard Models

- `flowbot_models/protocol_model.py`: FlowBot Router/Controller protocol safety.
- `flowbot_models/route_synthesis_model.py`: PM route synthesis through FlowGuard topology.

Runners:

```powershell
python scripts/run_flowbot_protocol_checks.py
python scripts/run_flowbot_route_synthesis_checks.py
python scripts/run_flowbot_smoke_checks.py
python scripts/run_flowbot_demo.py
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_flowbot_startup_intake_smoke.ps1
python scripts/check_flowbot_skill_install.py
```
