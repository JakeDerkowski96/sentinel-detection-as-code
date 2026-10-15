# 0004: Lifecycle state lives in metadata, not in the folder path

**Status:** accepted (see review log, uncertainty U6)

## Context
Some layouts encode environment or maturity in folders (`dev/`, `prod/`,
`archived/`). Promoting a rule is then a file move, which splits its history,
makes the diff of a promotion look like a delete plus an add, and tempts people to
edit the file during the move.

## Decision
Lifecycle is `metadata.lifecycle`, governed by `policy/lifecycle.yaml`. Promotion
is a one-line change.

## Consequences
- Promotion diffs are tiny and reviewable; history follows the rule.
- Reports that previously grouped by folder group by field.
- "Dev" versus "prod" for reporting is derived from lifecycle and from which
  workspace the rule is deployed to, not from a path.
