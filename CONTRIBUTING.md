# Contributing

## Portable-repo rule

This repository contains **generic, independently authored patterns only**. It
must never contain employer-specific detections, tenant or workspace
identifiers, internal architecture or proprietary process. Example tenants use
fictional names (`contoso`) and example data uses reserved domains
(`*.example`) and documentation IP ranges (`203.0.113.0/24`, `198.51.100.0/24`).

## Workflow

1. Branch from `main`: `<type>/<short-kebab-description>`
   (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `infra`).
   AI-authored branches use the `agent/` prefix instead.
2. Commit with [Conventional Commits](https://www.conventionalcommits.org/):
   imperative subject, 72 characters maximum, body explaining *why*.
3. Run `dac-validate validate --strict`, `ruff check .`, `ruff format --check .`,
   `mypy` and `pytest` locally.
4. Open a PR using the template. Squash-merge; delete the branch.

Never commit directly to `main`.

## Changing detection content

- A rule's behaviour changes only with a matching entry in its `tuning-history.yaml`.
- IDs are permanent. Renaming a rule's display name or folder slug never changes its ID.
- New dependencies are declared in `metadata.yaml` and must exist under `content/`.
- Exclusions go in `exceptions.yaml` with an owner, approver and expiry.

## Human-only paths

`policy/`, `schemas/`, `.github/` and `src/` define the rules the AI agent must
follow. The agent cannot modify them (see `policy/proposal-limits.yaml`).
