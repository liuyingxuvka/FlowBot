## Why

FlowBot needs a clear MVP contract before implementation: it should reuse the simple FlowPilot startup intake surface while adding a lighter runtime where PM uses FlowGuard as the route-synthesis medium, not merely as a post-plan validator. This prevents FlowBot from becoming either ordinary AI planning or a smaller copy of full FlowPilot.

## What Changes

- Introduce a FlowPilot-derived startup intake for FlowBot with one work request field and a minimal background-agent option.
- Define a three-role runtime core: Router, Controller, PM, and Worker, where Controller relays envelopes and PM owns planning/review.
- Require PM to use FlowGuard during runtime planning to evolve a vague user request into a model topology and then extract a one-direction linear route.
- Require Router to execute only the accepted linear route, dispatching one current letter at a time through Controller.
- Preserve FlowBot's lightweight scope by excluding FlowPilot heartbeat, Cockpit, six-role crew, long-term recovery, and broad autonomous driving.
- Preserve OpenSpec as the requirement/design/task layer for FlowBot itself, while FlowGuard is the PM's task-route modeling substrate inside FlowBot runs.

## Capabilities

### New Capabilities

- `startup-intake`: FlowBot's bootloader UI, intake records, and initial run creation boundary.
- `model-first-route-planning`: PM-owned FlowGuard route modeling, topology refinement, and linear route extraction.
- `controller-letter-execution`: Router-gated Controller relay, Worker execution, PM review, retry, pause, completion, and progress records.

### Modified Capabilities

- None.

## Impact

- Affects FlowBot's concept documents, future `.flowbot/runs/` layout, Router state machine, Controller relay contract, PM prompt/role contract, Worker prompt/role contract, FlowGuard runtime integration, and Mermaid progress generation.
- Requires reusing/cutting down FlowPilot startup intake UI assets and packet/card ideas without inheriting FlowPilot heartbeat, Cockpit, multi-officer, or long-term automation behavior.
