# 0006: Policy is human-only, machine-readable data

**Status:** accepted

## Context
The agent's limits could live in its prompts or in its own repository. Either
way, whoever changes the agent also changes its limits.

## Decision
Limits and thresholds live here in `policy/`, which the agent cannot modify
(forbidden path, CODEOWNERS, and the GitHub App's permissions).

## Consequences
- Changing agent behaviour within these bounds is a reviewed diff in the content
  repository, with history.
- The agent repo must read policy at run time rather than hard-code it.
