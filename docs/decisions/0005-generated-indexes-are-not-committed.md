# 0005: Generated indexes are not committed

**Status:** accepted (see review log, uncertainty U7)

## Context
The agent benefits from a precomputed coverage index. Committing it makes it
instantly available but creates merge conflicts on every rule PR and lets it go
stale if a PR forgets to regenerate it.

## Decision
`build/coverage-index.json` is rebuilt by `dac-validate index` and published as a
CI artifact; it is gitignored.

## Consequences
- No conflicts, no stale index.
- The agent must run one command (fast, offline) before reasoning.
- If cold-start latency ever matters, a CI job on `main` can publish it to a
  release or bucket without committing it.
