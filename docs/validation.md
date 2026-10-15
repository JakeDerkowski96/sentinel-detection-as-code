# Validation

## What CI runs

| Job | Checks |
|---|---|
| Lint and type-check | `ruff check`, `ruff format --check`, `mypy --strict` on `src/` |
| Unit tests | `pytest`, including failure-path tests that mutate a copy of the repo |
| Validate content | `dac-validate validate --strict` then `dac-validate index` |
| Secret scan | `gitleaks` over full history |
| `validate-gate` | The single required check; fails if any job above did not succeed |

## What `dac-validate validate` checks

Schema (every structured file) plus these cross-references:

| Code | Meaning |
|---|---|
| `folder-name`, `file-name` | Folder or file name does not match the ID |
| `id-mismatch` | Files in one rule folder disagree about the rule ID |
| `duplicate-id` | An ID is used twice |
| `unknown-domain` | Rule domain not in `policy/taxonomy.yaml` |
| `dependency-missing`, `dependency-type` | Declared dependency does not exist or is the wrong type |
| `dependency-undeclared` | Query calls a function, parser or watchlist that metadata does not declare (error: deployment ordering depends on it) |
| `dependency-unused` | Declared but never called (warning) |
| `table-unreferenced` | Declared table not reachable from the query or its dependencies (warning) |
| `canary-incomplete` | `productionCanary.enabled` without severity and duration |
| `tests-required`, `tests-missing`, `fixture-missing` | Lifecycle test gates and fixtures |
| `retired-enabled` | A retired rule is still `enabled: true` |
| `history-versions`, `history-create` | Tuning history sanity |
| `exception-dates`, `exception-expired` | Exception expiry |
| `package-missing`, `package-member`, `package-membership` | Package consistency |
| `override-tenant`, `override-rule`, `override-parameter`, `override-expired` | Tenant override consistency |
| `lifecycle-state`, `lifecycle-policy` | Lifecycle values disagree with policy |

## Not yet validated

- KQL syntax and schema (needs a KQL parser or a live workspace).
- That `entityMappings` columns exist in the query output.
- Historical replay, sandbox and Atomic Red Team execution.
- Lifecycle *transition* legality across commits (needs git history).

These belong to later phases; see the roadmap in the agent repository.

## Running locally

```bash
dac-validate validate --strict
dac-validate validate --format json     # machine-readable
dac-validate index --dry-run -v
```
