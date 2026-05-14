## ADDED Requirements

### Requirement: Controller is relay-only
The system SHALL use Controller as the only component that creates/connects background roles and relays Router-authorized envelopes.

#### Scenario: Router requests background roles
- **WHEN** Router enters the role startup phase for a confirmed FlowBot run
- **THEN** Controller creates or connects PM and Worker, records readiness, and waits for Router-authorized delivery actions

#### Scenario: Controller receives task content
- **WHEN** Controller relays a PM, Worker, review, or repair envelope
- **THEN** Controller does not plan, execute, review, infer next steps, or treat chat history as evidence

### Requirement: Worker executes only current letters
The system SHALL ensure Worker receives only the current work or repair letter authorized by Router.

#### Scenario: Router dispatches a work node
- **WHEN** a route node becomes active
- **THEN** Router instantiates the current work letter and Controller delivers it to Worker with scope, inputs, forbidden actions, completion criteria, and evidence requirements

### Requirement: PM reviews Worker evidence
The system SHALL require PM to review Worker checkins using concrete evidence before Router advances the route.

#### Scenario: Worker submits a checkin
- **WHEN** Worker returns a checkin for the active node
- **THEN** Router asks Controller to deliver a review request to PM, and PM returns pass, reject with repair instructions, or needs_user

### Requirement: Router gates all route progress
The system SHALL keep Router as the deterministic owner of route state and legal transitions.

#### Scenario: PM passes a node
- **WHEN** PM returns a pass for the active node
- **THEN** Router marks the node passed, updates run state and Mermaid progress, and activates the next linear route node

#### Scenario: PM rejects a node
- **WHEN** PM rejects the active node
- **THEN** Router generates a repair letter for the same node, increments the retry count, and does not advance to the next node

#### Scenario: Retry limit is reached
- **WHEN** the active node exceeds its retry limit
- **THEN** Router pauses the run, records the pause reason, and reports the need for user input instead of continuing
