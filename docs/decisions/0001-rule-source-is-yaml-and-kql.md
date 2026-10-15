# 0001: Rule source is YAML plus KQL; ARM is generated

**Status:** accepted (see review log, uncertainty U5)

## Context
Sentinel rules deploy as ARM resources. An ARM JSON file embeds the query as an
escaped string, so diffs are unreadable, KQL cannot be linted as KQL, and comments
are impossible. An AI agent editing escaped JSON strings is error-prone.

## Options
1. Keep ARM JSON as the source of truth.
2. YAML for properties plus a separate `.kql` file; generate ARM at deploy time.
3. Sentinel's own YAML content-hub format.

## Decision
Option 2.

## Consequences
- Readable diffs; KQL in its own file with real comments; the agent edits a
  `.kql` file, not an escaped string.
- A deployment step must compile to ARM. Until it exists, deployment is out of
  scope.
- Importing existing ARM rules needs a one-off converter (not built).
- Option 3 stays viable: the YAML here is close to it, and a converter could be
  added if content-hub compatibility becomes a goal.

## Alternatives rejected
Option 1 loses readability and agent reliability. Option 3 has no slot for
lifecycle, agent controls or history.
