# 0007: The validator lives in the content repository

**Status:** accepted

## Context
Schemas change with the content model. If the validator lived with the agent, a
schema change here would need a coordinated release elsewhere, and this
repository's CI could not run on its own.

## Decision
Schemas and the validator ship together here. The agent repo pins a version and
runs it against proposals.

## Consequences
- This repository is self-validating.
- The agent depends on a released version of `dac-validate`; a schema change here
  that breaks the agent shows up as a failing agent test, not a bad proposal.
