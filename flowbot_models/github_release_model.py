"""FlowGuard model for FlowBot public GitHub release ordering.

Risk purpose:
- Use FlowGuard (https://github.com/liuyingxuvka/FlowGuard) to review the
  public GitHub publication path for FlowBot.
- Guard against pushing or releasing before privacy audit, public README
  preparation, version synchronization, runtime checks, source commit, tag push,
  and conservative default-branch protection are complete.
- Run with `python scripts/run_flowbot_github_release_checks.py` before
  publishing a source release.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, NamedTuple

from flowguard import Explorer, FunctionResult, Invariant, InvariantResult, Workflow


REQUIRED_LABELS = (
    "privacy_audited",
    "readme_prepared",
    "version_synced",
    "checks_passed",
    "release_commit_created",
    "version_tag_created",
    "remote_created",
    "branch_pushed",
    "tag_pushed",
    "github_release_created",
    "default_branch_protected",
)

MAX_SEQUENCE_LENGTH = 12


@dataclass(frozen=True)
class Tick:
    """One release pipeline step."""


@dataclass(frozen=True)
class Action:
    name: str


@dataclass(frozen=True)
class State:
    privacy_audit: bool = False
    readme_public: bool = False
    version_synced: bool = False
    checks_passed: bool = False
    release_commit: bool = False
    version_tag: bool = False
    remote_created: bool = False
    branch_pushed: bool = False
    tag_pushed: bool = False
    github_release: bool = False
    default_branch_protected: bool = False
    completion_claimed: bool = False


class Transition(NamedTuple):
    label: str
    state: State


class GitHubReleaseStep:
    """Model one public-release transition.

    Input x State -> Set(Output x State)
    reads: privacy status, README status, version state, validation results,
      commit/tag/remote/release/protection state
    writes: staged publication side effects and completion claim
    idempotency: repeated pre-publish checks do not create duplicate remote
      releases or branch-protection rules.
    """

    name = "GitHubReleaseStep"

    def apply(self, input_obj: Tick, state: State) -> Iterable[FunctionResult]:
        del input_obj
        for transition in next_safe_states(state):
            yield FunctionResult(output=Action(transition.label), new_state=transition.state, label=transition.label)


def initial_state() -> State:
    return State()


def next_safe_states(state: State) -> tuple[Transition, ...]:
    if not state.privacy_audit:
        return (Transition("privacy_audited", replace(state, privacy_audit=True)),)
    if not state.readme_public:
        return (Transition("readme_prepared", replace(state, readme_public=True)),)
    if not state.version_synced:
        return (Transition("version_synced", replace(state, version_synced=True)),)
    if not state.checks_passed:
        return (Transition("checks_passed", replace(state, checks_passed=True)),)
    if not state.release_commit:
        return (Transition("release_commit_created", replace(state, release_commit=True)),)
    if not state.version_tag:
        return (Transition("version_tag_created", replace(state, version_tag=True)),)
    if not state.remote_created:
        return (Transition("remote_created", replace(state, remote_created=True)),)
    if not state.branch_pushed:
        return (Transition("branch_pushed", replace(state, branch_pushed=True)),)
    if not state.tag_pushed:
        return (Transition("tag_pushed", replace(state, tag_pushed=True)),)
    if not state.github_release:
        return (Transition("github_release_created", replace(state, github_release=True)),)
    if not state.default_branch_protected:
        return (Transition("default_branch_protected", replace(state, default_branch_protected=True)),)
    if not state.completion_claimed:
        return (Transition("completion_claimed", replace(state, completion_claimed=True)),)
    return ()


def is_terminal(state: State) -> bool:
    return state.completion_claimed


def is_success(state: State) -> bool:
    return state.completion_claimed


def release_invariants(state: State, _trace) -> InvariantResult:
    if state.release_commit and not (state.privacy_audit and state.readme_public and state.version_synced):
        return InvariantResult.fail("release commit created before privacy, README, and version were ready")
    if state.version_tag and not (state.release_commit and state.checks_passed):
        return InvariantResult.fail("version tag created before commit and checks")
    if state.branch_pushed and not (state.remote_created and state.release_commit):
        return InvariantResult.fail("branch pushed before remote and release commit")
    if state.tag_pushed and not (state.branch_pushed and state.version_tag):
        return InvariantResult.fail("tag pushed before branch push or local tag")
    if state.github_release and not state.tag_pushed:
        return InvariantResult.fail("GitHub release created before tag push")
    if state.default_branch_protected and not state.branch_pushed:
        return InvariantResult.fail("branch protection checked before default branch exists remotely")
    if state.completion_claimed and not (
        state.privacy_audit
        and state.readme_public
        and state.version_synced
        and state.checks_passed
        and state.release_commit
        and state.version_tag
        and state.remote_created
        and state.branch_pushed
        and state.tag_pushed
        and state.github_release
        and state.default_branch_protected
    ):
        return InvariantResult.fail("completion claimed before the public release pipeline finished")
    return InvariantResult.pass_()


INVARIANTS = (
    Invariant(
        name="flowbot_public_github_release_order",
        description="FlowBot public GitHub release must pass privacy, validation, tag, release, and branch-protection gates.",
        predicate=release_invariants,
    ),
)

EXTERNAL_INPUTS = (Tick(),)


def build_workflow() -> Workflow:
    return Workflow((GitHubReleaseStep(),), name="flowbot_github_release")


def invariant_failures(state: State) -> list[str]:
    result = release_invariants(state, ())
    return [] if result.ok else [result.message]


def hazard_states() -> dict[str, State]:
    return {
        "commit_without_privacy": State(readme_public=True, version_synced=True, release_commit=True),
        "tag_without_checks": State(privacy_audit=True, readme_public=True, version_synced=True, release_commit=True, version_tag=True),
        "push_without_remote": State(privacy_audit=True, readme_public=True, version_synced=True, checks_passed=True, release_commit=True, branch_pushed=True),
        "release_without_tag_push": State(
            privacy_audit=True,
            readme_public=True,
            version_synced=True,
            checks_passed=True,
            release_commit=True,
            version_tag=True,
            remote_created=True,
            branch_pushed=True,
            github_release=True,
        ),
        "claim_without_branch_protection": State(
            privacy_audit=True,
            readme_public=True,
            version_synced=True,
            checks_passed=True,
            release_commit=True,
            version_tag=True,
            remote_created=True,
            branch_pushed=True,
            tag_pushed=True,
            github_release=True,
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
