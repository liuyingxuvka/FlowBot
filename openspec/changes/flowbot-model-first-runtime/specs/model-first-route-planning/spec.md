## ADDED Requirements

### Requirement: PM owns model-first route synthesis
The system SHALL require PM to use FlowGuard as the planning medium for each FlowBot run before Worker execution begins.

#### Scenario: PM receives a new user request
- **WHEN** Router requests route preparation for a confirmed FlowBot run
- **THEN** Controller delivers the route request to PM, and PM creates a user contract, route hypothesis, FlowGuard route model, model findings, route topology, linear route spine, and node acceptance contracts

### Requirement: FlowGuard model is an intermediate route artifact
The system SHALL treat the FlowGuard route model as the intermediate artifact from which the executable route is derived, not as a separate post-plan approval stamp.

#### Scenario: PM refines an incomplete route idea
- **WHEN** PM discovers through model findings that the current topology misses a user requirement, has a stuck state, or reaches completion without required evidence
- **THEN** PM revises the model/topology before submitting a linear route to Router

### Requirement: Linear route is derived from model topology
The system SHALL require PM to extract a one-direction linear route spine from the FlowGuard-backed topology.

#### Scenario: PM submits a route package
- **WHEN** PM submits the route package to Router
- **THEN** the package includes a linear route where each main node points to the next node or Done, with repair, retry, pause, and user-question paths represented only as local exits

### Requirement: Router accepts only model-backed route packages
The system SHALL prevent Worker execution until Router has a PM route package with the required FlowGuard-derived artifacts.

#### Scenario: PM submits a route without model artifacts
- **WHEN** PM submits a route package missing the FlowGuard route model, topology, findings, linear spine, or node acceptance contracts
- **THEN** Router rejects the package and asks PM to repair the route package before any Worker dispatch
