# Guidance for AI agents working in this repository

You are most likely the Threat Detection agent (or a coding assistant acting for
a human). Read this before changing anything.

## Orient first

1. Run `dac-validate index` and read `build/coverage-index.json`. It tells you which
   rules cover which techniques and tables, what each piece of content is used by,
   and which hunting queries are rule-conversion candidates. Do not scan every rule
   folder to answer coverage questions.
2. Read `policy/*.yaml`. The thresholds and limits there are binding.
3. For any rule you intend to change, read in this order: `metadata.yaml`
   (is `agent.tuning` `allowed`?), `tuning-history.yaml` (what was already tried,
   including rejected changes), `exceptions.yaml`, `analyst-playbook.md`, then
   `rule.yaml` and `query.kql`.

## Before creating a rule

Answer "do we already detect this?" from the coverage index. If a rule covers the
technique on the same data source, propose a tuning change or a new test instead.

## Rules of the road

- Branch `agent/<short-description>`, label the PR `ai-proposed`.
- Touch only paths in `policy/proposal-limits.yaml` `allowed_paths`. Never touch
  `forbidden_paths`, and never change a rule whose `agent.tuning` is `locked`.
- `propose-only` means you may open a PR but must not assume it will merge.
- Every behavioural change appends an entry to `tuning-history.yaml` with the
  evidence that justified it. Only cite triage findings that are analyst-validated
  and meet the completeness threshold in `policy/tuning-thresholds.yaml`.
- Reducing alert volume is not proof of improvement. Show that known true
  positives are still detected.
- Do not invent table or column names. A table must appear in `dataSources.tables`
  or be reachable through a declared dependency, and the validator checks this.
- Run `dac-validate validate --strict` before opening a PR. A PR that fails it will
  not merge.
- Never deploy. Deployment is human-authorised and outside your remit.

## What the validator enforces for you

IDs and folder names, dependency declaration (a function, parser or watchlist
used in KQL must be declared), declared tables, lifecycle gates (canary and later
need tests), exception expiry, package membership, and tenant-override parameters
that must exist as `let` statements in the query.
