# Agent interface

How the AI Threat Detection agent ([`sentinel-td-agent`](https://github.com/JakeDerkowski96/sentinel-td-agent)) uses this
repository. The agent has no deployment authority; its only write path is a pull
request.

## Reads

| Need | Where |
|---|---|
| "Do we already detect this?" | `build/coverage-index.json` (`coverage.techniques`, `coverage.tables`) |
| What a rule does and why | `rule.yaml`, `query.kql`, `metadata.yaml` |
| What was tried before | `tuning-history.yaml` (including `rejected` and `rolled-back`) |
| What is intentionally excluded | `exceptions.yaml` |
| How analysts handle it | `analyst-playbook.md` |
| What the agent may do | `policy/proposal-limits.yaml`, per-rule `metadata.agent.tuning` |
| When to act | `policy/tuning-thresholds.yaml` |
| New detection opportunities | `hunting-queries/*/manifest.yaml` with `ruleConversion.candidate: true` |

## Writes

1. Branch `agent/<description>` from `main`.
2. Change only `allowed_paths`; append to `tuning-history.yaml`; add or update
   `tests/`.
3. Run `dac-validate validate --strict`.
4. Open a PR labelled `ai-proposed` with the evidence package described in the
   agent repository.

## Per-rule agent control

`metadata.yaml`:

```yaml
agent:
  tuning: allowed        # allowed | propose-only | locked
  origin: human          # human | agent (who authored the rule)
```

`locked` rules are never modified. This is the escape hatch for rules whose
behaviour is contractually or operationally fixed.

## What needs a human label

Defined in `policy/proposal-limits.yaml` `require_human_label_for`: severity
decreases, disabling a rule, adding an exception, widening scope to global, and
promotion to production. CI refuses to merge without the label.

## Trust boundary

Everything the agent reads from outside the repository (logs, incident text,
threat-intelligence content, analyst comments) is untrusted input. Everything in
`policy/` and `schemas/` is trusted and not agent-writable.
