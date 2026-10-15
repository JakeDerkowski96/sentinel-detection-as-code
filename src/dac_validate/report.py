"""Render validation issues as text, JSON or Markdown (for the Actions run summary).

Required permissions: none.
"""

from __future__ import annotations

import json
from collections import Counter

from .models import Issue, Severity


def summarize(issues: list[Issue]) -> tuple[int, int]:
    """Return (errors, warnings)."""
    counts = Counter(i.severity for i in issues)
    return counts[Severity.ERROR], counts[Severity.WARNING]


def render_text(issues: list[Issue], rules: int, content: int) -> str:
    errors, warnings = summarize(issues)
    lines = [f"{i.severity.value.upper():7} [{i.code}] {i.path}: {i.message}" for i in issues]
    lines.append(
        f"checked {rules} rules and {content} content items: {errors} errors, {warnings} warnings"
    )
    return "\n".join(lines)


def render_json(issues: list[Issue], rules: int, content: int) -> str:
    errors, warnings = summarize(issues)
    return json.dumps(
        {
            "rules": rules,
            "content": content,
            "errors": errors,
            "warnings": warnings,
            "issues": [
                {"severity": i.severity.value, "code": i.code, "path": i.path, "message": i.message}
                for i in issues
            ],
        },
        indent=2,
    )


def render_markdown(issues: list[Issue], rules: int, content: int) -> str:
    errors, warnings = summarize(issues)
    status = "passed" if errors == 0 else "failed"
    out = [
        "## Content validation",
        "",
        f"**{status}**: {rules} rules and {content} content items checked, "
        f"{errors} errors, {warnings} warnings.",
        "",
    ]
    if issues:
        out += ["| Severity | Code | Path | Message |", "|---|---|---|---|"]
        out += [f"| {i.severity.value} | `{i.code}` | `{i.path}` | {i.message} |" for i in issues]
    return "\n".join(out) + "\n"
