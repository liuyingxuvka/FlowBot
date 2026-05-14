"""FlowGuard model for FlowBot PM route synthesis.

Risk purpose:
- Use FlowGuard (https://github.com/liuyingxuvka/FlowGuard) as PM's runtime
  planning medium for FlowBot demo route synthesis.
- Guard against a PM submitting a route before the user contract, model
  topology, linear spine, and node acceptance contracts exist.
- Guard against completion paths that lack a one-direction route or final
  evidence gate.
- Run with `python scripts/run_flowbot_route_synthesis_checks.py` before
  trusting the demo PM route package.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, NamedTuple

from flowguard import Explorer, FunctionResult, Invariant, InvariantResult, Workflow


REQUIRED_LABELS = (
    "user_contract_extracted",
    "route_hypothesis_written",
    "flowguard_model_built",
    "topology_refined_from_model",
    "linear_route_extracted_from_topology",
    "node_acceptance_contracts_written",
    "route_package_ready",
)

MAX_SEQUENCE_LENGTH = 8


DEMO_LINEAR_ROUTE = [
    {
        "id": "node-001-capture-request",
        "title": "Capture request artifact",
        "worker_action": "write_note",
        "acceptance": ["artifacts/note.md exists", "note includes original request"],
    },
    {
        "id": "node-002-summarize-request",
        "title": "Create concise summary",
        "worker_action": "write_summary",
        "acceptance": ["artifacts/summary.md exists", "summary references note"],
    },
    {
        "id": "node-003-final-report",
        "title": "Write final report",
        "worker_action": "write_final_report",
        "acceptance": ["artifacts/final_report.md exists", "final report references summary"],
    },
]


@dataclass(frozen=True)
class Tick:
    """One PM modeling step."""


@dataclass(frozen=True)
class Action:
    name: str


@dataclass(frozen=True)
class State:
    user_contract: bool = False
    route_hypothesis: bool = False
    flowguard_model: bool = False
    topology: bool = False
    topology_has_start: bool = False
    topology_has_done: bool = False
    topology_is_one_direction: bool = False
    linear_route: bool = False
    node_acceptance_contracts: bool = False
    route_package: bool = False


class Transition(NamedTuple):
    label: str
    state: State


class RouteSynthesisStep:
    """Model one PM route-synthesis transition.

    Input x State -> Set(Output x State)
    reads: user request, PM route hypothesis, model findings
    writes: user contract, FlowGuard topology, linear route, node contracts
    idempotency: repeated PM modeling ticks do not skip required route artifacts.
    """

    name = "RouteSynthesisStep"

    def apply(self, input_obj: Tick, state: State) -> Iterable[FunctionResult]:
        del input_obj
        for transition in next_safe_states(state):
            yield FunctionResult(output=Action(transition.label), new_state=transition.state, label=transition.label)


def initial_state() -> State:
    return State()


def next_safe_states(state: State) -> tuple[Transition, ...]:
    if not state.user_contract:
        return (Transition("user_contract_extracted", replace(state, user_contract=True)),)
    if not state.route_hypothesis:
        return (Transition("route_hypothesis_written", replace(state, route_hypothesis=True)),)
    if not state.flowguard_model:
        return (Transition("flowguard_model_built", replace(state, flowguard_model=True)),)
    if not state.topology:
        return (
            Transition(
                "topology_refined_from_model",
                replace(
                    state,
                    topology=True,
                    topology_has_start=True,
                    topology_has_done=True,
                    topology_is_one_direction=True,
                ),
            ),
        )
    if not state.linear_route:
        return (Transition("linear_route_extracted_from_topology", replace(state, linear_route=True)),)
    if not state.node_acceptance_contracts:
        return (Transition("node_acceptance_contracts_written", replace(state, node_acceptance_contracts=True)),)
    if not state.route_package:
        return (Transition("route_package_ready", replace(state, route_package=True)),)
    return ()


def is_terminal(state: State) -> bool:
    return state.route_package


def is_success(state: State) -> bool:
    return state.route_package


def route_synthesis_invariants(state: State, _trace) -> InvariantResult:
    if state.route_hypothesis and not state.user_contract:
        return InvariantResult.fail("route hypothesis exists before user contract")
    if state.flowguard_model and not state.route_hypothesis:
        return InvariantResult.fail("FlowGuard model exists before route hypothesis")
    if state.topology and not state.flowguard_model:
        return InvariantResult.fail("topology exists before FlowGuard model")
    if state.linear_route and not (
        state.topology and state.topology_has_start and state.topology_has_done and state.topology_is_one_direction
    ):
        return InvariantResult.fail("linear route was extracted from incomplete topology")
    if state.node_acceptance_contracts and not state.linear_route:
        return InvariantResult.fail("node acceptance contracts exist before linear route")
    if state.route_package and not (
        state.user_contract
        and state.route_hypothesis
        and state.flowguard_model
        and state.topology
        and state.linear_route
        and state.node_acceptance_contracts
    ):
        return InvariantResult.fail("route package is missing model-first artifacts")
    return InvariantResult.pass_()


INVARIANTS = (
    Invariant(
        name="pm_model_first_route_synthesis",
        description="PM route package must be synthesized through FlowGuard model topology.",
        predicate=route_synthesis_invariants,
    ),
)

EXTERNAL_INPUTS = (Tick(),)


def build_workflow() -> Workflow:
    return Workflow((RouteSynthesisStep(),), name="flowbot_pm_route_synthesis")


def invariant_failures(state: State) -> list[str]:
    result = route_synthesis_invariants(state, ())
    return [] if result.ok else [result.message]


def hazard_states() -> dict[str, State]:
    return {
        "linear_route_without_topology": State(
            user_contract=True,
            route_hypothesis=True,
            flowguard_model=True,
            linear_route=True,
        ),
        "route_package_without_model": State(user_contract=True, route_hypothesis=True, route_package=True),
        "acceptance_before_route": State(
            user_contract=True,
            route_hypothesis=True,
            flowguard_model=True,
            topology=True,
            node_acceptance_contracts=True,
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
        "linear_route": DEMO_LINEAR_ROUTE,
    }
