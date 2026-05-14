"""FlowGuard model for FlowBot local skill install and initial version baseline.

Risk purpose:
- Use FlowGuard (https://github.com/liuyingxuvka/FlowGuard) to review the
  install/version/git process for the FlowBot MVP.
- Guard against claiming the local Codex skill is installed before validation,
  committing before version and ignore rules exist, tagging before a clean
  initial commit, or tracking generated runtime outputs.
- Run with `python scripts/run_flowbot_install_release_checks.py` before
  claiming the local skill and initial version are complete.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, NamedTuple

from flowguard import Explorer, FunctionResult, Invariant, InvariantResult, Workflow


REQUIRED_LABELS = (
    "skill_source_written",
    "skill_installed",
    "skill_validated",
    "version_recorded",
    "gitignore_written",
    "git_initialized",
    "initial_commit_created",
    "version_tag_created",
)

MAX_SEQUENCE_LENGTH = 9


@dataclass(frozen=True)
class Tick:
    """One install/release step."""


@dataclass(frozen=True)
class Action:
    name: str


@dataclass(frozen=True)
class State:
    skill_source: bool = False
    skill_installed: bool = False
    skill_validated: bool = False
    version_recorded: bool = False
    gitignore_written: bool = False
    generated_outputs_ignored: bool = False
    git_initialized: bool = False
    initial_commit: bool = False
    version_tag: bool = False
    completion_claimed: bool = False


class Transition(NamedTuple):
    label: str
    state: State


class InstallReleaseStep:
    """Model one local install/version/git transition.

    Input x State -> Set(Output x State)
    reads: skill source, installed skill, version file, git ignore, git state
    writes: installed skill, validation record, initial commit, version tag
    idempotency: repeating validation does not create commits or tags.
    """

    name = "InstallReleaseStep"

    def apply(self, input_obj: Tick, state: State) -> Iterable[FunctionResult]:
        del input_obj
        for transition in next_safe_states(state):
            yield FunctionResult(output=Action(transition.label), new_state=transition.state, label=transition.label)


def initial_state() -> State:
    return State()


def next_safe_states(state: State) -> tuple[Transition, ...]:
    if not state.skill_source:
        return (Transition("skill_source_written", replace(state, skill_source=True)),)
    if not state.skill_installed:
        return (Transition("skill_installed", replace(state, skill_installed=True)),)
    if not state.skill_validated:
        return (Transition("skill_validated", replace(state, skill_validated=True)),)
    if not state.version_recorded:
        return (Transition("version_recorded", replace(state, version_recorded=True)),)
    if not state.gitignore_written:
        return (
            Transition(
                "gitignore_written",
                replace(state, gitignore_written=True, generated_outputs_ignored=True),
            ),
        )
    if not state.git_initialized:
        return (Transition("git_initialized", replace(state, git_initialized=True)),)
    if not state.initial_commit:
        return (Transition("initial_commit_created", replace(state, initial_commit=True)),)
    if not state.version_tag:
        return (Transition("version_tag_created", replace(state, version_tag=True)),)
    if not state.completion_claimed:
        return (Transition("completion_claimed", replace(state, completion_claimed=True)),)
    return ()


def is_terminal(state: State) -> bool:
    return state.completion_claimed


def is_success(state: State) -> bool:
    return state.completion_claimed


def install_release_invariants(state: State, _trace) -> InvariantResult:
    if state.skill_installed and not state.skill_source:
        return InvariantResult.fail("installed skill has no repository source")
    if state.skill_validated and not state.skill_installed:
        return InvariantResult.fail("skill validated before installation")
    if state.initial_commit and not (state.version_recorded and state.gitignore_written and state.git_initialized):
        return InvariantResult.fail("initial commit created before version, gitignore, and git init")
    if state.initial_commit and not state.generated_outputs_ignored:
        return InvariantResult.fail("initial commit may track generated runtime outputs")
    if state.version_tag and not state.initial_commit:
        return InvariantResult.fail("version tag created before initial commit")
    if state.completion_claimed and not (
        state.skill_source
        and state.skill_installed
        and state.skill_validated
        and state.version_recorded
        and state.gitignore_written
        and state.generated_outputs_ignored
        and state.git_initialized
        and state.initial_commit
        and state.version_tag
    ):
        return InvariantResult.fail("completion claimed before install/version/git baseline is complete")
    return InvariantResult.pass_()


INVARIANTS = (
    Invariant(
        name="flowbot_local_skill_install_initial_version",
        description="FlowBot local skill install and initial version baseline must be ordered and validated.",
        predicate=install_release_invariants,
    ),
)

EXTERNAL_INPUTS = (Tick(),)


def build_workflow() -> Workflow:
    return Workflow((InstallReleaseStep(),), name="flowbot_install_release")


def invariant_failures(state: State) -> list[str]:
    result = install_release_invariants(state, ())
    return [] if result.ok else [result.message]


def hazard_states() -> dict[str, State]:
    return {
        "installed_without_source": State(skill_installed=True),
        "validated_before_install": State(skill_source=True, skill_validated=True),
        "commit_without_version": State(skill_source=True, skill_installed=True, skill_validated=True, git_initialized=True, initial_commit=True),
        "commit_tracks_outputs": State(
            skill_source=True,
            skill_installed=True,
            skill_validated=True,
            version_recorded=True,
            gitignore_written=True,
            git_initialized=True,
            initial_commit=True,
        ),
        "tag_before_commit": State(
            skill_source=True,
            skill_installed=True,
            skill_validated=True,
            version_recorded=True,
            gitignore_written=True,
            generated_outputs_ignored=True,
            git_initialized=True,
            version_tag=True,
        ),
        "claimed_before_tag": State(
            skill_source=True,
            skill_installed=True,
            skill_validated=True,
            version_recorded=True,
            gitignore_written=True,
            generated_outputs_ignored=True,
            git_initialized=True,
            initial_commit=True,
            completion_claimed=True,
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
