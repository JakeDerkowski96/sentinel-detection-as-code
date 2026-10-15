# Policy

Files in `policy/` are human-only (the agent cannot modify them) and
machine-readable (CI and the agent read them).

| File | Governs |
|---|---|
| `tuning-thresholds.yaml` | Signals that make a rule a tuning candidate; learning-eligibility bar for triage findings; replay requirements |
| `proposal-limits.yaml` | Branch prefix, labels, size limits, allowed and forbidden paths, changes needing a human label |
| `lifecycle.yaml` | States, allowed transitions, human-only transitions |
| `taxonomy.yaml` | ID prefixes, rule domains, confidence tiers |

## Calibrating

The numbers shipped are defaults chosen to be plausible, not measured. Before
trusting `tuning-thresholds.yaml`:

1. Pull 90 days of alert counts per rule and look at the distribution.
2. Set `excessive_volume.min_alerts` near the volume analysts say is too much,
   not at a round number.
3. Replay a few past tuning decisions through the thresholds and check the
   signals would have fired when they should.
4. Record the change and the reasoning in the commit body.

## Changing policy

Policy changes are normal human PRs. They are high-impact because they change what
the agent will do, so review them like permission changes.
