## ADDED Requirements

### Requirement: FlowBot is installed as a local Codex skill

The system SHALL install a `flowbot` skill in the local Codex skills directory.

#### Scenario: Skill directory is discoverable

- **WHEN** the local Codex skills directory is inspected
- **THEN** it contains `flowbot/SKILL.md` with `name: flowbot`

### Requirement: FlowBot skill remains opt-in

The installed skill SHALL activate only when the user explicitly asks to use FlowBot or the FlowBot skill.

#### Scenario: Skill description prevents implicit activation

- **WHEN** the installed `SKILL.md` frontmatter is read
- **THEN** the description states the skill is opt-in only and should not activate implicitly for generic large tasks

### Requirement: Initial local version is recorded

The project SHALL record initial version `0.1.0` and tag the local git repository as `v0.1.0`.

#### Scenario: Version baseline exists

- **WHEN** version files and git tags are inspected
- **THEN** the project reports version `0.1.0` and git contains tag `v0.1.0`

### Requirement: Generated runtime outputs are not committed

The repository SHALL ignore generated run outputs, temporary files, Python caches, and local editor/system noise.

#### Scenario: Git status after initial commit

- **WHEN** the initial commit is created
- **THEN** generated `.flowbot/runs`, `tmp`, and `__pycache__` outputs are not tracked
