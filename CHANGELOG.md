# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Repository scaffold: `content/` tree for analytics rules, functions, parsers, watchlists,
  automation rules, playbooks, workbooks, hunting queries and packages.
- JSON Schemas for rules, rule metadata, tuning history, exceptions, test cases, content
  manifests, packages, tenant overrides and policy files.
- Policy files: tuning thresholds, proposal limits, lifecycle, taxonomy.
- `dac-validate` tool: schema validation, cross-reference checks, and a derived
  coverage/dependency index.
- Synthetic example content: three analytics rules, one function, one parser, one watchlist,
  one hunting query, three packages, one tenant override.
- CI workflow: lint, type-check, unit tests, content validation, secret scan, single gate job.
- `scripts/apply_repo_settings.sh` to apply repository settings and branch protection (supports `--dry-run`).
- Architecture decision records 0001 to 0007.
- `AGENTS.md` guidance for AI agents operating in the repository.

[Unreleased]: https://github.com/JakeDerkowski96/sentinel-detection-as-code/commits/main
