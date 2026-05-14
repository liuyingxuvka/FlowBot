## Context

The project already contains the FlowBot runtime, native startup intake, OpenSpec artifacts, FlowGuard models, and verification scripts. The user now explicitly wants this project installed as a local Codex skill and committed as the initial local version.

## Goals / Non-Goals

**Goals:**

- Install `flowbot` into the local Codex skills directory.
- Keep the skill concise and opt-in only.
- Preserve locked runtime/UI scope; do not add a new UI, server, API, or product surface.
- Create a local git repository with a reviewable initial commit and version tag.

**Non-Goals:**

- Publish to GitHub or any remote.
- Create a plugin or marketplace package.
- Add new FlowBot runtime behavior.
- Replace PM/Worker deterministic demo classes.

## Decisions

### Decision: Install a lean SKILL.md

The installed skill should act as a bootloader and usage guide. It should point to the project root, startup-intake command, verification commands, and strict boundaries. It should not duplicate the full protocol.

### Decision: Use version 0.1.0

The existing package already declares `flowbot.__version__ = "0.1.0"`. This becomes the initial version and local git tag `v0.1.0`.

### Decision: Keep generated run outputs out of git

The repository should commit source, OpenSpec, FlowGuard models, scripts, docs, and skill artifacts. Generated `.flowbot/runs`, `tmp`, caches, and editor/system noise should be ignored.

## Risks / Trade-offs

- [Risk] Installed skill may become stale relative to repository source. -> Mitigation: verify installed `SKILL.md` exists and contains the same version/project path after installation.
- [Risk] Skill activation may happen implicitly for large tasks. -> Mitigation: skill description says opt-in only.
- [Risk] Initial git commit may include generated run data. -> Mitigation: add `.gitignore` before commit.
