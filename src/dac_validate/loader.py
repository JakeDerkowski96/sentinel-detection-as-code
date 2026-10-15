"""Discover and parse repository content into a `Repository`.

Required permissions: none. Reads local files only.

Notes:
    YAML dates are kept as strings. PyYAML would otherwise turn ``2026-10-15``
    into a ``datetime.date``, which then fails a JSON Schema ``string`` check
    and makes the same file behave differently from its JSON equivalent.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .models import Issue, Manifest, Repository, RuleBundle, Severity

log = logging.getLogger(__name__)

MANIFEST_DIRS = (
    "functions",
    "parsers",
    "watchlists",
    "automation-rules",
    "playbooks",
    "workbooks",
    "hunting-queries",
)
POLICY_FILES = ("tuning-thresholds", "proposal-limits", "lifecycle", "taxonomy")


class _StringDateLoader(yaml.SafeLoader):
    """SafeLoader that leaves timestamps as plain strings."""


_StringDateLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path: Path) -> Any:
    """Parse a YAML file, raising ValueError with the path on any failure."""
    try:
        with path.open(encoding="utf-8") as handle:
            return yaml.load(handle, Loader=_StringDateLoader)  # noqa: S506 - SafeLoader subclass
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _try_yaml(root: Path, path: Path, issues: list[Issue]) -> dict[str, Any] | None:
    """Load an optional or required YAML mapping, recording a parse issue instead of raising."""
    if not path.exists():
        return None
    try:
        data = load_yaml(path)
    except ValueError as exc:
        issues.append(Issue(Severity.ERROR, "yaml-parse", _rel(root, path), str(exc)))
        return None
    if not isinstance(data, dict):
        issues.append(
            Issue(Severity.ERROR, "yaml-shape", _rel(root, path), "top level must be a mapping")
        )
        return None
    return data


def _load_rules(root: Path, issues: list[Issue]) -> list[RuleBundle]:
    rules: list[RuleBundle] = []
    base = root / "content" / "analytics-rules"
    if not base.is_dir():
        return rules
    for directory in sorted(p for p in base.iterdir() if p.is_dir()):
        rule = _try_yaml(root, directory / "rule.yaml", issues)
        metadata = _try_yaml(root, directory / "metadata.yaml", issues)
        for required in ("rule.yaml", "metadata.yaml", "tuning-history.yaml"):
            if not (directory / required).exists():
                issues.append(
                    Issue(
                        Severity.ERROR,
                        "missing-file",
                        _rel(root, directory),
                        f"required file {required} is missing",
                    )
                )
        if rule is None or metadata is None:
            continue
        query_file = directory / str(rule.get("queryFile", "query.kql"))
        query = ""
        if query_file.exists():
            query = _read_text(query_file)
        rules.append(
            RuleBundle(
                directory=directory,
                rule=rule,
                metadata=metadata,
                query=query,
                history=_try_yaml(root, directory / "tuning-history.yaml", issues),
                exceptions=_try_yaml(root, directory / "exceptions.yaml", issues),
                tests=_try_yaml(root, directory / "tests" / "test-cases.yaml", issues),
            )
        )
    return rules


def _load_manifests(root: Path, issues: list[Issue]) -> list[Manifest]:
    manifests: list[Manifest] = []
    for kind in MANIFEST_DIRS:
        base = root / "content" / kind
        if not base.is_dir():
            continue
        for directory in sorted(p for p in base.iterdir() if p.is_dir()):
            data = _try_yaml(root, directory / "manifest.yaml", issues)
            if data is None:
                if not (directory / "manifest.yaml").exists():
                    issues.append(
                        Issue(
                            Severity.ERROR,
                            "missing-file",
                            _rel(root, directory),
                            "manifest.yaml is missing",
                        )
                    )
                continue
            query = ""
            query_name = data.get("queryFile")
            if isinstance(query_name, str) and (directory / query_name).exists():
                query = _read_text(directory / query_name)
            manifests.append(Manifest(directory=directory, data=data, query=query))
    return manifests


def _load_flat(root: Path, pattern: str, issues: list[Issue]) -> list[tuple[Path, dict[str, Any]]]:
    found: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(root.glob(pattern)):
        data = _try_yaml(root, path, issues)
        if data is not None:
            found.append((path, data))
    return found


def load_repository(root: Path) -> Repository:
    """Load every content item, package, override and policy under ``root``."""
    root = root.resolve()
    log.debug("loading repository at %s", root)
    repo = Repository(root=root)
    repo.rules = _load_rules(root, repo.load_issues)
    repo.manifests = _load_manifests(root, repo.load_issues)
    repo.packages = _load_flat(root, "content/packages/*.yaml", repo.load_issues)
    repo.overrides = _load_flat(root, "tenants/overrides/*/*.yaml", repo.load_issues)
    for name in POLICY_FILES:
        data = _try_yaml(root, root / "policy" / f"{name}.yaml", repo.load_issues)
        if data is not None:
            repo.policies[name] = (root / "policy" / f"{name}.yaml", data)
    log.debug(
        "loaded %d rules, %d manifests, %d packages, %d overrides",
        len(repo.rules),
        len(repo.manifests),
        len(repo.packages),
        len(repo.overrides),
    )
    return repo
