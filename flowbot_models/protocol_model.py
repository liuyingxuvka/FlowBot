"""FlowGuard model for FlowBot Router/Controller protocol.

Risk purpose:
- Use FlowGuard (https://github.com/liuyingxuvka/FlowGuard) to review the
  FlowBot MVP control protocol before and after implementation.
- Guard against cancel creating a run, Controller planning or executing work,
  Worker dispatch before PM model-backed route acceptance, advancing after
  rejection, and done without evidence-backed PM review.
- Run with `python scripts/run_flowbot_protocol_checks.py` before claiming the
  runtime protocol is safe.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, NamedTuple

from flowguard import Explorer, FunctionResult, Invariant, InvariantResult, Workflow


REQUIRED_LABELS = (
    "intake_confirmed",
    "roles_ready",
    "pm_model_route_package_submitted",
    "route_package_accepted",
    "work_letter_dispatched",
    "worker_checkin_returned",
    "pm_review_passed",
    "node_advanced_or_done",
)

MAX_SEQUENCE_LENGTH = 9


@dataclass(frozen=True)
class Tick:
    """One Router/Controller protocol tick."""


@dataclass(frozen=True)
class Action:
    name: str


@dataclass(frozen=True)
class State:
    intake: str = "none"  # none | confirmed | cancelled
    run_created: bool = False
    controller_ready: bool = False
    pm_ready: bool = False
    worker_ready: bool = False
    controller_planned: bool = False
    controller_executed: bool = False
    controller_reviewed: bool = False
    pm_route_package: bool = False
    pm_route_has_model: bool = False
    route_accepted: bool = False
    node_dispatched: bool = False
    worker_checkin: bool = False
    evidence_present: bool = False
    pm_review: str = "none"  # none | pass | reject
    retry_count: int = 0
    node_passed: bool = False
    done: bool = False
    paused: bool = False


class Transition(NamedTuple):
    label: str
    state: State


class ProtocolStep:
    """Model one Router/Controller protocol transition.

    Input x State -> Set(Output x State)
    reads: intake result, route package, worker checkin, PM review
    writes: run state, controller ledger, current letter, retry/pause/done
    idempotency: no route progress occurs without Router accepting the prior state.
    """

    name = "ProtocolStep"

    def apply(self, input_obj: Tick, state: State) -> Iterable[FunctionResult]:
        del input_obj
        for transition in next_safe_states(state):
            yield FunctionResult(output=Action(transition.label), new_state=transition.state, label=transition.label)


def initial_state() -> State:
    return State()


def next_safe_states(state: State) -> tuple[Transition, ...]:
    if state.intake == "none":
        return (
            Transition("intake_confirmed", replace(state, intake="confirmed", run_created=True)),
            Transition("intake_cancelled", replace(state, intake="cancelled")),
        )
    if state.intake == "cancelled":
        return ()
    if not state.controller_ready:
        return (
            Transition(
                "roles_ready",
                replace(state, controller_ready=True, pm_ready=True, worker_ready=True),
            ),
        )
    if not state.pm_route_package:
        return (
            Transition(
                "pm_model_route_package_submitted",
                replace(state, pm_route_package=True, pm_route_has_model=True),
            ),
        )
    if state.pm_route_package and not state.route_accepted:
        return (Transition("route_package_accepted", replace(state, route_accepted=True)),)
    if state.route_accepted and not state.node_dispatched:
        return (Transition("work_letter_dispatched", replace(state, node_dispatched=True)),)
    if state.node_dispatched and not state.worker_checkin:
        return (
            Transition(
                "worker_checkin_returned",
                replace(state, worker_checkin=True, evidence_present=True),
            ),
        )
    if state.worker_checkin and state.pm_review == "none":
        return (
            Transition("pm_review_passed", replace(state, pm_review="pass")),
            Transition("pm_review_rejected", replace(state, pm_review="reject")),
        )
    if state.pm_review == "pass" and not state.done:
        return (Transition("node_advanced_or_done", replace(state, node_passed=True, done=True)),)
    if state.pm_review == "reject" and not state.paused:
        if state.retry_count >= 2:
            return (Transition("retry_limit_paused", replace(state, paused=True)),)
        return (
            Transition(
                "current_node_repair_dispatched",
                replace(
                    state,
                    node_dispatched=True,
                    worker_checkin=False,
                    evidence_present=False,
                    pm_review="none",
                    retry_count=state.retry_count + 1,
                ),
            ),
        )
    return ()


def is_terminal(state: State) -> bool:
    return state.done or state.paused or state.intake == "cancelled"


def is_success(state: State) -> bool:
    return state.done


def protocol_invariants(state: State, _trace) -> InvariantResult:
    if state.intake == "cancelled" and (state.run_created or state.controller_ready or state.pm_ready or state.worker_ready):
        return InvariantResult.fail("cancelled intake created run or roles")
    if state.controller_planned or state.controller_executed or state.controller_reviewed:
        return InvariantResult.fail("Controller performed cognitive work instead of relay-only work")
    if state.route_accepted and not (state.pm_route_package and state.pm_route_has_model):
        return InvariantResult.fail("Router accepted route without PM FlowGuard-backed route package")
    if state.node_dispatched and not (state.route_accepted and state.worker_ready):
        return InvariantResult.fail("Worker dispatch happened before accepted route and ready Worker")
    if state.pm_review == "pass" and not (state.worker_checkin and state.evidence_present):
        return InvariantResult.fail("PM passed a node without Worker evidence")
    if state.done and not (state.node_passed and state.pm_review == "pass"):
        return InvariantResult.fail("Run completed without PM pass and node completion")
    if state.pm_review == "reject" and state.done:
        return InvariantResult.fail("Rejected node advanced to done")
    return InvariantResult.pass_()


INVARIANTS = (
    Invariant(
        name="flowbot_controller_router_protocol",
        description="Router controls all progress and Controller remains relay-only.",
        predicate=protocol_invariants,
    ),
)

EXTERNAL_INPUTS = (Tick(),)


def build_workflow() -> Workflow:
    return Workflow((ProtocolStep(),), name="flowbot_protocol")


def invariant_failures(state: State) -> list[str]:
    result = protocol_invariants(state, ())
    return [] if result.ok else [result.message]


def hazard_states() -> dict[str, State]:
    return {
        "cancel_creates_run": State(intake="cancelled", run_created=True),
        "controller_plans": State(intake="confirmed", run_created=True, controller_planned=True),
        "dispatch_before_route": State(intake="confirmed", run_created=True, worker_ready=True, node_dispatched=True),
        "accept_route_without_model": State(intake="confirmed", run_created=True, pm_route_package=True, route_accepted=True),
        "pass_without_evidence": State(
            intake="confirmed",
            run_created=True,
            controller_ready=True,
            pm_ready=True,
            worker_ready=True,
            pm_route_package=True,
            pm_route_has_model=True,
            route_accepted=True,
            node_dispatched=True,
            pm_review="pass",
        ),
        "done_after_reject": State(
            intake="confirmed",
            run_created=True,
            controller_ready=True,
            pm_ready=True,
            worker_ready=True,
            pm_route_package=True,
            pm_route_has_model=True,
            route_accepted=True,
            node_dispatched=True,
            worker_checkin=True,
            evidence_present=True,
            pm_review="reject",
            done=True,
        ),
    }


def run_checks() -> dict[str, object]:
    report = Explorer(
        workflow=build_workflow(),
        initial_states=(initial_state(),),
        external_inputs=EXTERNAL_INPUTS,
        invariants=INVARIANTS,
        max_sequence_length=MAX_SEQUENCE_LENGTH,
        terminal_predicate=lambda _input, state, _trace: is_terminal(state),
        success_predicate=lambda state, _trace: is_success(state),
        required_labels=REQUIRED_LABELS,
        progress_steps=0,
    ).explore()
    hazards = {
        name: {"detected": bool(invariant_failures(state)), "failures": invariant_failures(state)}
        for name, state in hazard_states().items()
    }
    return {
        "ok": report.ok and all(item["detected"] for item in hazards.values()),
        "flowguard": {
            "ok": report.ok,
            "summary": report.summary,
            "violation_count": len(report.violations),
            "reachability_failure_count": len(report.reachability_failures),
        },
        "hazards": hazards,
    }
