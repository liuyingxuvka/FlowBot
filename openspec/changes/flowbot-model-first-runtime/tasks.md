## 1. Documented Architecture Baseline

- [x] 1.1 Update the root FlowBot documents to reflect the OpenSpec + FlowGuard model-first runtime.
- [x] 1.2 Replace `Reviewer/Planner` wording with `PM (Project Manager)` where the combined role is intended.
- [x] 1.3 Document Controller as relay-only and background-role owner, not a planning or execution agent.
- [x] 1.4 Document FlowGuard as PM's route-synthesis medium, not only a post-plan validator.

## 2. Startup Intake MVP

- [x] 2.1 Inspect the reusable FlowPilot startup intake UI asset and identify the smallest FlowBot-specific copy/cut.
- [x] 2.2 Define FlowBot intake output files: body, result, receipt, and envelope.
- [x] 2.3 Define confirm/cancel behavior before run creation.
- [x] 2.4 Define the MVP option surface with only the work request and background-agent toggle.

## 3. Runtime State and Artifacts

- [x] 3.1 Define `.flowbot/runs/<run-id>/` directory layout.
- [x] 3.2 Define Router state schema for startup, PM modeling, route acceptance, worker dispatch, review, repair, pause, and done.
- [x] 3.3 Define Controller delivery and return receipt records.
- [x] 3.4 Define PM route package artifacts: user contract, route hypothesis, FlowGuard model, model findings, topology, linear route, node acceptance contracts, and Mermaid.

## 4. PM FlowGuard Route Synthesis

- [x] 4.1 Define PM's first route-modeling letter.
- [x] 4.2 Define how PM writes/refines the FlowGuard model from a vague user request.
- [x] 4.3 Define how PM extracts a one-direction linear route spine from model topology.
- [x] 4.4 Define Router's acceptance checks for PM route packages.

## 5. Letter Execution Loop

- [x] 5.1 Define work letter, worker checkin, PM review, and repair letter schemas.
- [x] 5.2 Define just-in-time work letter instantiation from the active route node.
- [x] 5.3 Define PM evidence review rules and allowed outcomes.
- [x] 5.4 Define retry, pause, needs-user, and final completion behavior.

## 6. Verification Plan

- [x] 6.1 Add FlowGuard checks for FlowBot's own Router/Controller protocol.
- [x] 6.2 Add a sample PM route-synthesis FlowGuard model for a small demo task.
- [x] 6.3 Add focused checks for cancel-before-run, Controller relay-only, missing PM model artifacts, reject-current-node-only, retry pause, and completion evidence.
- [x] 6.4 Validate OpenSpec artifacts before implementation begins.
