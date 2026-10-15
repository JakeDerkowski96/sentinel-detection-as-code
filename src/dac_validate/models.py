"""Plain data containers shared by the loader, checks and index builder.

Required permissions: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class Severity(StrEnum):
    """Issue severity. Errors fail validation; warnings fail only with --strict."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Issue:
    """A single validation finding, anchored to a file so it is actionable."""

    severity: Severity
    code: str
    path: str
    message: str


@dataclass
class RuleBundle:
    """Everything that makes up one analytics rule folder."""

    directory: Path
    rule: dict[str, Any]
    metadata: dict[str, Any]
    query: str
    history: dict[str, Any] | None = None
    exceptions: dict[str, Any] | None = None
    tests: dict[str, Any] | None = None

    @property
    def rule_id(self) -> str:
        return str(self.rule.get("id", ""))


@dataclass
class Manifest:
    """A non-rule content item (function, parser, watchlist, ...)."""

    directory: Path
    data: dict[str, Any]
    query: str = ""

    @property
    def item_id(self) -> str:
        return str(self.data.get("id", ""))


@dataclass
class Repository:
    """The fully loaded repository plus any problems found while loading it."""

    root: Path
    rules: list[RuleBundle] = field(default_factory=list)
    manifests: list[Manifest] = field(default_factory=list)
    packages: list[tuple[Path, dict[str, Any]]] = field(default_factory=list)
    overrides: list[tuple[Path, dict[str, Any]]] = field(default_factory=list)
    policies: dict[str, tuple[Path, dict[str, Any]]] = field(default_factory=dict)
    load_issues: list[Issue] = field(default_factory=list)
