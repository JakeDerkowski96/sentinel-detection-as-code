# Conventions

## Identifiers

IDs are permanent and independent of display names. Renaming never creates a new
logical detection.

| Type | Pattern | Example |
|---|---|---|
| Analytics rule | `DET-<DOMAIN>-<nnnn>` | `DET-ENTRA-0001` |
| Function | `FUNC-<NAME>-<nnn>` | `FUNC-NORMALIZE-PROCESS-001` |
| Parser | `PARSER-<NAME>-<nnn>` | `PARSER-SYSLOG-SSHD-001` |
| Watchlist | `WL-<NAME>` | `WL-PRIVILEGED-ACCOUNTS` |
| Automation rule | `AUTO-<NAME>-<nnn>` | |
| Playbook | `PB-<NAME>-<nnn>` | |
| Workbook | `WB-<NAME>-<nnn>` | |
| Hunting query | `HUNT-<DOMAIN>-<nnnn>` | `HUNT-IDENTITY-0001` |
| Package | `PKG-<NAME>` | `PKG-IDENTITY-SIGNIN` |

`<DOMAIN>` for rules comes from `policy/taxonomy.yaml`.

## Folders

- Rule folders are named `<ID>-<kebab-slug>`. The validator requires the ID prefix;
  the slug may change (ADR 0003).
- Other content folders are named exactly the ID.
- Rule folders are flat: no per-domain or per-environment nesting (ADR 0003, 0004).

## Parameters that tenants may override

Any value a tenant might reasonably change is a top-level `let` in `query.kql`
(for example `let FailureThreshold = 10;`). A tenant override may then replace the
default through `queryParameters` without forking the rule. The validator checks
every overridden parameter exists.

## Dates and versions

Dates are quoted ISO strings (`"2026-10-15"`) so YAML does not turn them into
objects. Rule versions in `tuning-history.yaml` are semantic: a threshold change is
a minor bump, a logic rewrite a major bump, a typo fix a patch.

## Comments

Comments in KQL and YAML explain *why*, not what. Keep them next to the decision
they justify.
