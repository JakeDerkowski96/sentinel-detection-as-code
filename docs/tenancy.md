# Tenancy

## Targeting

`metadata.deployment.scope`:

| Scope | Meaning | Extra fields |
|---|---|---|
| `global` | Every monitored tenant | none |
| `selected` | Only listed tenants | `tenants` |
| `excluded` | Every tenant except those listed | `tenants` |
| `capability` | Only where required tables, solutions or connectors exist | `requirements` |
| `tenant-specific` | One tenant's local rule, where justified | `tenants` |

Tenants are referenced by **logical short name**. The deployment engine resolves
a short name to a workspace through the Lighthouse inventory; no runtime
identifier appears in this repository. A name that resolves to zero or several
workspaces must fail safely.

## Overrides

`tenants/overrides/<tenant>/<RULE-ID>.yaml` expresses a tenant-local difference
without copying the rule. Permitted overrides: `enabled`, `severity`,
`queryFrequency`, `queryPeriod`, `triggerThreshold`, and `queryParameters`
(replacing a top-level `let` default).

Every override needs a `reason` and `approvedBy`, may carry an `expires` date, and
must be visible in deployment plans and audit output.

## Open question: agent scope

The agent's rule for how far a tenant's evidence may reach is not settled. The
working proposal: evidence from tenant A may justify a change for tenant A only
(as an override); a global change needs validated evidence from several tenants.
See the review log in the agent repository.
