# Content model

## Analytics rule folder

`content/analytics-rules/<ID>-<slug>/`

| File | Required | Schema | Purpose |
|---|---|---|---|
| `rule.yaml` | yes | `analytics-rule` | Deployable Sentinel properties (severity, frequency, entity mappings, ...) |
| `query.kql` | yes | n/a | The detection query, referenced by `rule.yaml` `queryFile` |
| `metadata.yaml` | yes | `rule-metadata` | Lifecycle, owner, data sources, dependencies, targeting, agent controls |
| `tuning-history.yaml` | yes | `tuning-history` | Append-only record of every behavioural change, including rejected ones |
| `exceptions.yaml` | no | `exceptions` | Approved exclusions with owner, approver and expiry |
| `analyst-playbook.md` | no | n/a | What fired, first checks, likely benign, when to escalate |
| `tests/test-cases.yaml` | from `canary` | `test-cases` | Synthetic, replay, Atomic Red Team and sandbox cases |
| `tests/fixtures/` | no | n/a | Data the test cases reference |

`rule.yaml` and `metadata.yaml` are separate on purpose: `rule.yaml` maps to what
Sentinel accepts, `metadata.yaml` holds everything Sentinel has no field for
(ADR 0002).

## Other content

`content/<type>/<ID>/manifest.yaml` (schema `content-manifest`) for functions,
parsers, watchlists, automation rules, playbooks, workbooks and hunting queries.
The `type` field selects which extra fields are required.

| Type | Extra required fields | Notes |
|---|---|---|
| function, parser | `alias`, `queryFile`, `tables` | `alias` is the KQL-callable name |
| watchlist | `alias`, `itemsSearchKey`, `dataFile`, `dataClassification` | Committed CSVs are synthetic |
| automation-rule, playbook, workbook | `definitionFile` | Response actions: human-authored only |
| hunting-query | `queryFile`, `tables`, `tactics`, `techniques`, `ruleConversion` | Conversion candidates are an agent CREATE trigger |

## Packages

`content/packages/<PKG-ID>.yaml` groups related content as a unit of deployment
while each item keeps its own identity. A rule's `metadata.package` must point at
a package that lists it.

## Derived data

`dac-validate index` builds `build/coverage-index.json` (not committed; ADR 0005):
rule summaries, technique/tactic/table coverage, a dependency "used by" map,
unused content and hunting-conversion candidates.
