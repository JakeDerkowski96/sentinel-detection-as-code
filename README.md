# sentinel-detection-as-code

An agent-ready Git repository for Microsoft Sentinel detection content: analytics
rules, the functions, parsers and watchlists they depend on, and the metadata,
tests and policy that let both humans and an AI Threat Detection agent reason
about them safely.

This repository is the **content and contract** half of a pair. The agent that
proposes changes to it lives in [`sentinel-td-agent`](https://github.com/JakeDerkowski96/sentinel-td-agent).

## Purpose

Sentinel stores detections as portal state. This repository makes them software:
reviewed, versioned, validated and queryable. It is laid out so that an AI agent
can answer "do we already detect this?" and "what happened the last time this
rule was tuned?" by reading files, and so that every change it proposes arrives
as a pull request a human can review.

## What's here

| Path | Contents |
|---|---|
| `content/analytics-rules/<ID>-<slug>/` | One folder per rule: `rule.yaml`, `query.kql`, `metadata.yaml`, `tuning-history.yaml`, tests, analyst playbook |
| `content/functions`, `parsers`, `watchlists`, ... | Everything a rule depends on, one folder each with a `manifest.yaml` |
| `content/packages/` | Groups of related content that deploy together |
| `schemas/` | JSON Schemas for every structured file |
| `policy/` | Machine-readable tuning thresholds, proposal limits, lifecycle and taxonomy |
| `tenants/overrides/` | Tenant-local differences, expressed as overrides never copies |
| `scripts/` | `apply_repo_settings.sh`: applies repository settings and branch protection with `gh` |
| `src/dac_validate/` | The validator and index builder CI runs |
| `docs/` | Design, conventions and decision records |

The example content (three rules, a function, a parser, a watchlist, a hunting
query) is **synthetic**. It exists to exercise the schemas and tooling, uses
reserved example domains and documentation IP ranges, and is not validated
against a live workspace.

## Prerequisites

- Python 3.11 or later
- Git

## Required permissions

| Role | Scope | Reason |
|---|---|---|
| None | n/a | Validation and indexing read the local checkout only |
| GitHub Actions `contents: read` | This repository | CI checkout; the workflows request nothing broader |

Deployment to Sentinel is **not implemented here yet**. When it is, the
deployment identity's roles will be documented in this table
(see `docs/architecture.md`).

## Usage

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

dac-validate validate            # schemas + cross-references
dac-validate index --dry-run -v  # show what the coverage index would write
dac-validate index               # writes build/coverage-index.json
```

`validate` exits 0 when clean, 1 on errors (or warnings with `--strict`), 2 on
usage or runtime failure.

## Documentation

See [`docs/README.md`](docs/README.md). Start with
[`docs/architecture.md`](docs/architecture.md) and
[`docs/agent-interface.md`](docs/agent-interface.md).
AI agents working in this repo should read [`AGENTS.md`](AGENTS.md) first.

Open design questions and assumptions made while building this scaffold are
tracked in the agent repository's review log:
[`docs/review-log.md`](https://github.com/JakeDerkowski96/sentinel-td-agent/blob/main/docs/review-log.md).

## Contributing

Branch, commit and PR conventions are in [`CONTRIBUTING.md`](CONTRIBUTING.md).
Changes are Conventional Commits, squash-merged; `main` is protected.

## License

MIT. See [`LICENSE`](LICENSE).
