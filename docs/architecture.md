# Architecture

## Role

This repository is the **content truth**: what detections should exist and how
they should behave. It is one half of a larger system:

```text
              +--------------------------------------+
              | sentinel-detection-as-code (this)    |
 humans ----> | content/ schemas/ policy/ tenants/   |
              +------------------+-------------------+
                       PR        |        ^  read
                                 v        |
 sentinel-td-agent -- proposes --+--------+
 (AWS, Claude on Bedrock)

 CI validates  -->  human approves  -->  deployment engine  -->  Sentinel
```

Azure Lighthouse remains the **infrastructure truth**: tenant short names in this
repository are resolved to workspaces by the deployment engine at run time, so
no subscription, workspace or resource ID is ever stored here.

## Design goals

1. **An agent can orient cheaply.** A derived coverage index, stable IDs and
   per-rule history mean it reads a few files, not the whole tree.
2. **Metadata cannot silently lie.** The validator cross-checks metadata against
   the KQL (declared tables, declared dependencies) and against other files.
3. **Every change is reviewable and attributable.** Behavioural change requires a
   tuning-history entry; AI changes arrive as labelled PRs.
4. **The agent's limits are data, not prompt text.** `policy/` is human-only and
   machine-readable.
5. **Tenants differ by override, never by copy.**

## What is deliberately not here

- **The deployment engine.** It resolves targets through Lighthouse, plans, deploys
  and rolls back. It is a separate concern with different permissions and is not
  yet built. The content model is designed so it can be added without schema
  changes (rules compile to ARM at deploy time; see ADR 0001).
- **The AI agent.** It lives in [`sentinel-td-agent`](https://github.com/JakeDerkowski96/sentinel-td-agent).
- **Real data.** Watchlist CSVs are synthetic samples.

## Lifecycle

`draft -> validated -> sandbox-passed -> canary -> approved -> production -> retired`

State is recorded in each rule's `metadata.yaml` and governed by
`policy/lifecycle.yaml`. Production canaries use a deployment-time severity
override; the canonical severity in `rule.yaml` is never rewritten to run a canary.

## Planned permissions for deployment (not yet in use)

| Role | Scope | Reason |
|---|---|---|
| Microsoft Sentinel Contributor | Per-tenant workspace resource group | Create, update and remove managed content |
| Log Analytics Reader | Per-tenant workspace | Validate table schemas before deployment |

Both would be granted to a federated (OIDC) identity, not a stored secret. A
narrower role may suffice for the read path; that should be tested, not assumed.
