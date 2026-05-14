## Why

FlowBot now has a working MVP, but Codex cannot invoke it as a local skill yet and the project has no local version-control baseline. The next step is to install FlowBot as a local Codex skill and mark the initial project version.

## What Changes

- Install a `flowbot` skill under the local Codex skills directory.
- Keep the skill opt-in only: use it only when the user explicitly asks to use FlowBot or the FlowBot skill.
- Add an initial version marker for FlowBot `0.1.0`.
- Initialize a local git repository and create an initial commit/tag for the first version.
- Add a focused FlowGuard process check for install/version/git ordering.

## Capabilities

### New Capabilities

- `local-skill-installation`: FlowBot can be discovered as a local Codex skill and the repository has an initial local version baseline.

### Modified Capabilities

- None.

## Impact

- Local Codex skill directory: `C:\Users\liu_y\.codex\skills\flowbot`.
- Repository files for versioning, install verification, and git hygiene.
- Local git repository metadata and an initial version tag.
