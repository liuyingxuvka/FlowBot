## Context

FlowBot starts as a concept folder, not an implemented runtime. The user wants a smaller system extracted from FlowPilot: keep the startup intake, Router discipline, Controller relay, packet/letter ideas, FlowGuard modeling, and Mermaid progress, but remove FlowPilot's Cockpit, heartbeat, six-role crew, long-term autonomous driving, and heavy route machinery.

The most important design correction is that FlowGuard is not only a development-time checker and not only a post-plan validator. In FlowBot runtime, PM uses FlowGuard as the planning medium: PM starts from a vague user request, builds and refines a FlowGuard route model, then derives a one-direction linear route from the model topology.

OpenSpec and FlowGuard have different jobs:

- OpenSpec captures FlowBot product requirements, design, and implementation tasks.
- FlowGuard is part of FlowBot's runtime: PM uses it to synthesize each user task route before Worker execution begins.

## Goals / Non-Goals

**Goals:**

- Reuse the FlowPilot startup intake shape as a minimal FlowBot bootloader UI.
- Keep Controller as the only component that creates/connects background agents and relays envelopes.
- Keep PM as the only cognitive route owner: PM plans, models, extracts the route, reviews Worker evidence, and performs final acceptance.
- Keep Worker focused on the current letter only.
- Keep Router deterministic: it gates legal state transitions and never plans or performs task work.
- Require a PM-owned FlowGuard route model before the Router accepts a linear route.
- Make the user-visible progress simple, mainly Mermaid and run state files.

**Non-Goals:**

- No FlowPilot Cockpit in MVP.
- No scheduled continuation or heartbeat in MVP.
- No six-role crew, officers, or full FlowPilot automation.
- No Controller-authored route plans, project evidence, task execution, or review decisions.
- No pre-generation of every future prompt. Current letters are instantiated by Router at dispatch time.
- No claim that FlowGuard proves real-world success; it models route structure, hazards, and completion logic.

## Decisions

### Decision: Keep FlowPilot-style startup intake, but cut it down

FlowBot SHALL begin with a bootloader UI similar to FlowPilot's native startup intake: a large work request field, a minimal background-agent toggle, and a confirm/cancel boundary. The UI writes intake body, result, receipt, and envelope files. It does not create routes or start work itself.

Alternative considered: build a two-panel FlowBot workbench. Rejected for MVP because the actual FlowPilot startup surface is simpler and the user wants FlowBot to stay light.

### Decision: Preserve Controller, but make it relay-only

Controller remains required because it is the bridge to live background agents. Controller creates/connects PM and Worker, delivers Router-authorized envelopes, records delivery/return receipts, and reports role liveness problems.

Controller MUST NOT read sealed task bodies unless a contract explicitly permits it, plan routes, execute work, review evidence, infer next steps from chat, or bypass Router.

Alternative considered: remove Controller and let Router or PM talk directly to agents. Rejected because it loses FlowPilot's core relay/control-plane separation.

### Decision: Collapse planning and review into PM

FlowBot uses two background roles: PM and Worker. PM is Project Manager, combining Planner and Reviewer. PM owns user-contract extraction, FlowGuard route synthesis, linear route extraction, node acceptance contracts, per-node review, repair instructions, and final acceptance.

Alternative considered: separate Planner and Reviewer. Rejected for MVP because two background roles are enough and the user explicitly accepts PM combining those duties.

### Decision: Use FlowGuard as route synthesis, not only validation

PM does not first write a normal AI plan and then ask FlowGuard to approve it. PM uses FlowGuard as the intermediate model artifact:

1. Extract user contract.
2. Draft a route hypothesis.
3. Build a FlowGuard route model.
4. Inspect model findings/counterexamples.
5. Refine the model and route topology.
6. Extract a one-direction linear route spine.
7. Submit the route package to Router.

The final route plan is derived from the model topology and includes node-level acceptance contracts.

Alternative considered: use FlowGuard only to validate a finished PM plan. Rejected because it makes FlowGuard secondary and weakens FlowBot's product identity.

### Decision: Router executes a linear spine with local failure exits

Router accepts a one-direction route:

```text
Node 1 -> Node 2 -> Node 3 -> Done
```

Each node may have local exits:

- reject -> repair current node
- retry exceeded -> pause
- ambiguity -> ask user

The main route remains linear so Router can stay simple and Worker receives only one current letter at a time.

### Decision: Current letters are generated just in time

PM creates route topology and node contracts. Router instantiates the current work letter at dispatch time from the active node, state, evidence requirements, and prior accepted outputs. FlowBot MUST NOT pre-generate hundreds or thousands of prompts at startup.

## Risks / Trade-offs

- [Risk] PM may create a FlowGuard model that is too abstract to protect user intent. -> Mitigation: require user_contract, model_findings, route_topology, linear_route_spine, and node_acceptance_contracts as separate PM artifacts.
- [Risk] Controller may accidentally become a cognitive agent. -> Mitigation: Controller contract says relay-only; Router state gates every delivery and return.
- [Risk] FlowGuard route synthesis could be too slow for small tasks. -> Mitigation: FlowBot only starts on explicit user request in MVP.
- [Risk] A linear route may hide natural loops or batches. -> Mitigation: represent batches inside nodes while keeping the outer route spine one-directional.
- [Risk] Worker may act on too much context and drift. -> Mitigation: Worker receives only the current work letter, bounded inputs, and required evidence list.
- [Risk] PM review may rely on Worker self-report. -> Mitigation: PM review contracts require evidence paths, logs, diffs, tests, or other concrete artifacts.
