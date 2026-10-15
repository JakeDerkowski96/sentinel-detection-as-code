"""Cross-reference checks that JSON Schema cannot express.

Required permissions: none. Reads local files only.

These checks exist because the AI agent reasons over metadata (dependencies,
data sources, lifecycle). Metadata that disagrees with the KQL or with other
files is worse than missing metadata, because it is trusted.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from .models import Issue, Manifest, Repository, RuleBundle, Severity

_DEP_KEYS = {
    "functions": "function",
    "parsers": "parser",
    "watchlists": "watchlist",
    "automationRules": "automation-rule",
    "playbooks": "playbook",
    "workbooks": "workbook",
}
_GATED_STATES = {"canary", "approved", "production"}


def _err(code: str, path: str, msg: str) -> Issue:
    return Issue(Severity.ERROR, code, path, msg)


def _warn(code: str, path: str, msg: str) -> Issue:
    return Issue(Severity.WARNING, code, path, msg)


def _word(name: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])")


def _strip_comments(kql: str) -> str:
    """Remove // comments so a table name in a comment is not counted as a reference."""
    return "\n".join(line.split("//", 1)[0] for line in kql.splitlines())


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def check_unique_ids(repo: Repository) -> list[Issue]:
    """Every content ID must be unique across all content types."""
    seen: dict[str, str] = {}
    issues: list[Issue] = []
    entries: list[tuple[str, str]] = [(b.rule_id, b.directory.name) for b in repo.rules]
    entries += [(m.item_id, m.directory.name) for m in repo.manifests]
    entries += [(str(d.get("id", "")), p.name) for p, d in repo.packages]
    for item_id, where in entries:
        if not item_id:
            continue
        if item_id in seen:
            issues.append(
                _err("duplicate-id", where, f"id {item_id} is already used by {seen[item_id]}")
            )
        seen[item_id] = where
    return issues


def _registry(repo: Repository) -> dict[str, Manifest]:
    return {m.item_id: m for m in repo.manifests}


def _check_rule(bundle: RuleBundle, repo: Repository, registry: dict[str, Manifest]) -> list[Issue]:
    issues: list[Issue] = []
    where = bundle.directory.relative_to(repo.root).as_posix()
    rid = bundle.rule_id
    meta = bundle.metadata

    if not bundle.directory.name.startswith(f"{rid}-"):
        issues.append(_err("folder-name", where, f"folder name must start with '{rid}-'"))
    for label, doc in (
        ("metadata.yaml", meta),
        ("tuning-history.yaml", bundle.history),
        ("exceptions.yaml", bundle.exceptions),
        ("tests/test-cases.yaml", bundle.tests),
    ):
        if doc is not None and doc.get("id") != rid:
            issues.append(
                _err(
                    "id-mismatch",
                    f"{where}/{label}",
                    f"id {doc.get('id')} does not match rule id {rid}",
                )
            )

    query_name = str(bundle.rule.get("queryFile", ""))
    if not (bundle.directory / query_name).exists():
        issues.append(_err("missing-file", where, f"queryFile {query_name} does not exist"))
        return issues
    code = _strip_comments(bundle.query)

    # Domain segment must be in the shared taxonomy.
    taxonomy = repo.policies.get("taxonomy")
    parts = rid.split("-")
    if taxonomy and len(parts) == 3 and parts[1] not in taxonomy[1].get("domains", []):
        issues.append(
            _err(
                "unknown-domain",
                where,
                f"domain '{parts[1]}' is not listed in policy/taxonomy.yaml",
            )
        )

    # Lifecycle must be a known state; retired rules must not stay enabled.
    lifecycle = str(meta.get("lifecycle", ""))
    if bundle.rule.get("enabled") and lifecycle == "retired":
        issues.append(_err("retired-enabled", where, "a retired rule must have enabled: false"))

    # Dependencies: declared must exist with the right type; used must be declared.
    declared: set[str] = set()
    for key, expected_type in _DEP_KEYS.items():
        for dep in meta.get("dependencies", {}).get(key, []):
            declared.add(dep)
            item = registry.get(dep)
            if item is None:
                issues.append(
                    _err(
                        "dependency-missing",
                        where,
                        f"dependency {dep} does not exist under content/",
                    )
                )
            elif item.data.get("type") != expected_type:
                issues.append(
                    _err(
                        "dependency-type",
                        where,
                        f"{dep} is a {item.data.get('type')}, listed under {key}",
                    )
                )
    used: set[str] = set()
    for item in registry.values():
        alias = item.data.get("alias")
        if not alias:
            continue
        if item.data.get("type") == "watchlist":
            pattern = re.compile(r"_GetWatchlist\(\s*['\"]" + re.escape(str(alias)) + r"['\"]\s*\)")
        else:
            pattern = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(str(alias)) + r"\s*\(")
        if pattern.search(code):
            used.add(item.item_id)
    for item_id in sorted(used - declared):
        issues.append(
            _err(
                "dependency-undeclared",
                where,
                f"query uses {item_id} but metadata does not declare it",
            )
        )
    for item_id in sorted((declared & set(registry)) - used):
        issues.append(
            _warn(
                "dependency-unused", where, f"{item_id} is declared but not referenced in the query"
            )
        )

    # Data sources: a declared table must be reachable from the query, directly or via a dependency.
    reachable_tables = {
        t for t in meta.get("dataSources", {}).get("tables", []) if _word(t).search(code)
    }
    for dep in declared:
        item = registry.get(dep)
        if item is not None:
            reachable_tables |= set(item.data.get("tables", []))
    for table in meta.get("dataSources", {}).get("tables", []):
        if table not in reachable_tables:
            issues.append(
                _warn(
                    "table-unreferenced",
                    where,
                    f"table {table} is declared but not used by the query",
                )
            )

    # Canary needs a severity and duration to be actionable.
    canary = meta.get("deployment", {}).get("productionCanary", {})
    if canary.get("enabled") and not (canary.get("severity") and canary.get("duration")):
        issues.append(
            _err(
                "canary-incomplete",
                where,
                "productionCanary.enabled requires severity and duration",
            )
        )

    # Tests: required to reach canary or later; fixtures must exist.
    if lifecycle in _GATED_STATES and not bundle.tests:
        issues.append(
            _err("tests-required", where, f"lifecycle '{lifecycle}' requires tests/test-cases.yaml")
        )
    elif bundle.tests is None and lifecycle not in {"draft", "retired"}:
        issues.append(_warn("tests-missing", where, "no tests/test-cases.yaml"))
    for case in (bundle.tests or {}).get("cases", []):
        fixture = case.get("fixture")
        if fixture and not (bundle.directory / "tests" / fixture).exists():
            issues.append(
                _err("fixture-missing", f"{where}/tests", f"fixture {fixture} does not exist")
            )

    playbook = meta.get("documentation", {}).get("analystPlaybook")
    if playbook and not (bundle.directory / playbook).exists():
        issues.append(_err("missing-file", where, f"analystPlaybook {playbook} does not exist"))

    # Tuning history: unique versions, at least one create entry.
    entries = (bundle.history or {}).get("entries", [])
    versions = [e.get("version") for e in entries]
    if len(versions) != len(set(versions)):
        issues.append(
            _err("history-versions", f"{where}/tuning-history.yaml", "versions must be unique")
        )
    if entries and not any(e.get("type") == "create" for e in entries):
        issues.append(
            _err("history-create", f"{where}/tuning-history.yaml", "history needs a 'create' entry")
        )

    # Exceptions: expiry sanity.
    today = date.today()
    for exc in (bundle.exceptions or {}).get("exceptions", []):
        approved, expires = _parse_date(exc.get("approvedOn")), _parse_date(exc.get("expires"))
        if approved and expires and expires <= approved:
            issues.append(
                _err(
                    "exception-dates",
                    f"{where}/exceptions.yaml",
                    f"{exc.get('id')} expires before approval",
                )
            )
        elif expires and expires < today:
            issues.append(
                _warn(
                    "exception-expired", f"{where}/exceptions.yaml", f"{exc.get('id')} has expired"
                )
            )
    return issues


def _check_manifests(repo: Repository) -> list[Issue]:
    issues: list[Issue] = []
    for item in repo.manifests:
        where = item.directory.relative_to(repo.root).as_posix()
        if item.directory.name != item.item_id:
            issues.append(_err("folder-name", where, f"folder name must equal id '{item.item_id}'"))
        for key in ("queryFile", "dataFile", "definitionFile"):
            name = item.data.get(key)
            if name and not (item.directory / name).exists():
                issues.append(_err("missing-file", where, f"{key} {name} does not exist"))
        if item.data.get("type") == "watchlist" and item.data.get("dataFile"):
            csv_path = item.directory / str(item.data["dataFile"])
            if csv_path.exists():
                header = csv_path.read_text(encoding="utf-8").splitlines()[:1]
                columns = header[0].split(",") if header else []
                if item.data.get("itemsSearchKey") not in columns:
                    issues.append(
                        _err(
                            "watchlist-key",
                            where,
                            "itemsSearchKey is not a column in the data file",
                        )
                    )
    return issues


def _check_packages(repo: Repository, registry: dict[str, Manifest]) -> list[Issue]:
    issues: list[Issue] = []
    rule_ids = {b.rule_id for b in repo.rules}
    known = rule_ids | set(registry)
    package_ids = {str(d.get("id")) for _, d in repo.packages}
    for path, data in repo.packages:
        where = path.relative_to(repo.root).as_posix()
        if path.stem != data.get("id"):
            issues.append(_err("file-name", where, f"file name must equal id '{data.get('id')}'"))
        for members in data.get("contents", {}).values():
            for member in members:
                if member not in known:
                    issues.append(_err("package-member", where, f"{member} does not exist"))
    for bundle in repo.rules:
        pkg = bundle.metadata.get("package")
        if not pkg:
            continue
        where = bundle.directory.relative_to(repo.root).as_posix()
        if pkg not in package_ids:
            issues.append(_err("package-missing", where, f"package {pkg} does not exist"))
            continue
        members = (
            [d for _, d in repo.packages if d.get("id") == pkg][0]
            .get("contents", {})
            .get("detections", [])
        )
        if bundle.rule_id not in members:
            issues.append(
                _err("package-membership", where, f"{pkg} does not list {bundle.rule_id}")
            )
    return issues


def _check_overrides(repo: Repository) -> list[Issue]:
    issues: list[Issue] = []
    by_id = {b.rule_id: b for b in repo.rules}
    today = date.today()
    for path, data in repo.overrides:
        where = path.relative_to(repo.root).as_posix()
        if path.parent.name != data.get("tenant"):
            issues.append(_err("override-tenant", where, "folder name must equal the tenant field"))
        if path.stem != data.get("rule"):
            issues.append(_err("file-name", where, "file name must equal the rule id"))
        bundle = by_id.get(str(data.get("rule")))
        if bundle is None:
            issues.append(_err("override-rule", where, f"rule {data.get('rule')} does not exist"))
            continue
        for name in data.get("overrides", {}).get("queryParameters", {}):
            if not re.search(r"^\s*let\s+" + re.escape(name) + r"\s*=", bundle.query, re.MULTILINE):
                issues.append(
                    _err(
                        "override-parameter",
                        where,
                        f"query has no `let {name} =` statement to override",
                    )
                )
        expires = _parse_date(data.get("expires")) if data.get("expires") else None
        if expires and expires < today:
            issues.append(_warn("override-expired", where, "override has expired"))
    return issues


def _check_policy(repo: Repository) -> list[Issue]:
    issues: list[Issue] = []
    lifecycle = repo.policies.get("lifecycle")
    if lifecycle:
        states = set(lifecycle[1].get("states", []))
        for bundle in repo.rules:
            state = bundle.metadata.get("lifecycle")
            if state not in states:
                issues.append(
                    _err(
                        "lifecycle-state",
                        bundle.directory.name,
                        f"lifecycle '{state}' is not in policy",
                    )
                )
        for src, targets in lifecycle[1].get("transitions", {}).items():
            for target in targets:
                if src not in states or target not in states:
                    issues.append(
                        _err(
                            "lifecycle-policy",
                            "policy/lifecycle.yaml",
                            f"unknown state in {src}->{target}",
                        )
                    )
    return issues


def run_checks(repo: Repository) -> list[Issue]:
    """Run every cross-reference check and return the combined findings."""
    registry = _registry(repo)
    issues = check_unique_ids(repo)
    for bundle in repo.rules:
        issues += _check_rule(bundle, repo, registry)
    issues += _check_manifests(repo)
    issues += _check_packages(repo, registry)
    issues += _check_overrides(repo)
    issues += _check_policy(repo)
    return issues
