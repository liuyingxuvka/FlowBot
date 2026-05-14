## ADDED Requirements

### Requirement: FlowBot provides a minimal startup intake
The system SHALL provide a FlowPilot-derived startup intake surface for explicit FlowBot runs.

#### Scenario: User confirms FlowBot intake
- **WHEN** the user enters a work request and confirms the startup intake
- **THEN** the system records a confirmed intake result, receipt, envelope, and body file for the new FlowBot run

#### Scenario: User cancels FlowBot intake
- **WHEN** the user cancels or closes the startup intake before confirmation
- **THEN** the system records cancellation or terminates without creating a run, starting agents, or dispatching work

### Requirement: Startup intake stays bootloader-only
The startup intake SHALL collect the user request and startup options, but MUST NOT plan routes, execute work, review evidence, or directly control Worker actions.

#### Scenario: Intake body is submitted
- **WHEN** the startup intake writes the user's work request body
- **THEN** Router and Controller receive only the contracted result/envelope references needed to start the run

### Requirement: MVP startup options stay minimal
The MVP startup intake SHALL expose only options needed for a lightweight FlowBot run.

#### Scenario: User starts a normal FlowBot MVP run
- **WHEN** the startup intake is displayed
- **THEN** it shows a work request field and a background-agent option, without FlowPilot Cockpit, scheduled continuation, heartbeat, or six-role crew controls
