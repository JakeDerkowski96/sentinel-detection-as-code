"""dac-validate: schema and cross-reference validation for a Sentinel detection-as-code repo.

Why this exists: the repository is the contract between human authors, CI and
the AI detection agent. Anything the agent relies on (IDs, dependencies, data
sources, lifecycle) must be machine-verified, or the agent will reason over
metadata that quietly drifted away from the KQL.

Required permissions: none. Reads local files only.
"""

__version__ = "0.1.0"
