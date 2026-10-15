# 0003: One flat, ID-prefixed folder per rule

**Status:** accepted

## Context
Rule folders could be nested by domain, environment or quality tier. Nesting
makes moves common, and a moved folder breaks `git log --follow` for the files
inside.

## Decision
All rules sit directly under `content/analytics-rules/` as `<ID>-<slug>/`. The
ID prefix sorts rules by domain naturally and the validator enforces it.

## Consequences
- Agents glob one directory; no path logic.
- Browsing by domain relies on the sort order and the index, not folders.
- The slug may be renamed without changing identity.
