# 0002: Rule metadata lives in a separate `metadata.yaml`

**Status:** accepted

## Context
Sentinel's alert rule resource has a closed property schema with no free-form
metadata or tags. Lifecycle, ownership, dependencies and agent controls have
nowhere to live inside the deployable definition. Existing practice in this
problem space is a sidecar file next to the rule.

## Decision
Deployable properties in `rule.yaml`; everything else in `metadata.yaml`. The
validator cross-checks them.

## Consequences
- The deployable definition stays a faithful mirror of what Sentinel accepts.
- Two files per rule must agree on the ID; the validator enforces it.
- Fields appear only once: MITRE tactics and techniques stay in `rule.yaml` and
  the index reads them from there.
