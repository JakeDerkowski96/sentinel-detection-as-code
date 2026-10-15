# Reporting fields

Which repository fields feed which report. The agent's CLI generates the reports
(see the agent repository); this table is the contract between the two.

| Report | Fields used | Source |
|---|---|---|
| Audit: content integrity | validator output | `dac-validate validate --format json` |
| Audit: ownership and review | `metadata.owner`, `lastReviewed` | `metadata.yaml` |
| Audit: exceptions | `exceptions[].expires`, `approvedBy` | `exceptions.yaml` |
| Audit: change history | `entries[]` | `tuning-history.yaml`, git log |
| Coverage: technique/tactic | `rule.techniques`, `rule.tactics`, `lifecycle`, `enabled` | `rule.yaml`, `metadata.yaml` |
| Coverage: data source | `dataSources.tables` | `metadata.yaml` |
| Coverage: gaps | hunting queries with `ruleConversion.candidate` | `manifest.yaml` |
| Coverage: tenant capability | `deployment.scope`, `requirements` | `metadata.yaml` |
| Performance: dev and prod | `id`, `lifecycle`, `quality.expectedAlertVolume`, `confidenceTier` joined to runtime telemetry | `metadata.yaml` + Log Analytics |
| Maturity | tests present, playbook present, history entries, canary configured | derived |

Runtime telemetry (alert counts, SentinelHealth, incident outcomes) is **not**
stored in Git; reports join it to this repository by rule ID.
