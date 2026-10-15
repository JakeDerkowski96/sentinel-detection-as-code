"""Build the derived coverage and dependency index the AI agent reads.

Required permissions: none. Reads local files; writes only when asked to.

Why derived, not hand-maintained: a coverage table maintained by hand is wrong
within a week. The index is rebuilt from the rule folders on demand, so it is
always consistent with the content it describes.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from .models import Repository

log = logging.getLogger(__name__)

INDEX_VERSION = 1


def build_index(repo: Repository) -> dict[str, Any]:
    """Return technique/tactic/table coverage, rule summaries and the dependency graph."""
    rules: dict[str, Any] = {}
    techniques: dict[str, list[str]] = defaultdict(list)
    tactics: dict[str, list[str]] = defaultdict(list)
    tables: dict[str, list[str]] = defaultdict(list)
    used_by: dict[str, list[str]] = defaultdict(list)

    for bundle in repo.rules:
        rid, meta, rule = bundle.rule_id, bundle.metadata, bundle.rule
        deps = [d for group in meta.get("dependencies", {}).values() for d in group]
        rules[rid] = {
            "path": bundle.directory.relative_to(repo.root).as_posix(),
            "displayName": rule.get("displayName"),
            "severity": rule.get("severity"),
            "enabled": rule.get("enabled"),
            "lifecycle": meta.get("lifecycle"),
            "confidenceTier": meta.get("confidenceTier"),
            "package": meta.get("package"),
            "scope": meta.get("deployment", {}).get("scope"),
            "agentTuning": meta.get("agent", {}).get("tuning"),
            "tactics": rule.get("tactics", []),
            "techniques": rule.get("techniques", []),
            "tables": meta.get("dataSources", {}).get("tables", []),
            "dependencies": deps,
            "hasTests": bundle.tests is not None,
            "hasExceptions": bool((bundle.exceptions or {}).get("exceptions")),
            "historyEntries": len((bundle.history or {}).get("entries", [])),
        }
        for tech in rule.get("techniques", []):
            techniques[tech].append(rid)
        for tactic in rule.get("tactics", []):
            tactics[tactic].append(rid)
        for table in meta.get("dataSources", {}).get("tables", []):
            tables[table].append(rid)
        for dep in deps:
            used_by[dep].append(rid)

    content: dict[str, Any] = {}
    for item in repo.manifests:
        content[item.item_id] = {
            "type": item.data.get("type"),
            "path": item.directory.relative_to(repo.root).as_posix(),
            "lifecycle": item.data.get("lifecycle"),
            "usedBy": sorted(used_by.get(item.item_id, [])),
        }
    # Rule-less dependencies are candidates for retirement.
    unused = sorted(
        i
        for i, v in content.items()
        if not v["usedBy"] and v["type"] not in {"hunting-query", "workbook"}
    )

    return {
        "indexVersion": INDEX_VERSION,
        "counts": {"rules": len(rules), "content": len(content), "packages": len(repo.packages)},
        "rules": rules,
        "content": content,
        "coverage": {
            "techniques": {k: sorted(v) for k, v in sorted(techniques.items())},
            "tactics": {k: sorted(v) for k, v in sorted(tactics.items())},
            "tables": {k: sorted(v) for k, v in sorted(tables.items())},
        },
        "unusedContent": unused,
        "huntingConversionCandidates": sorted(
            m.item_id
            for m in repo.manifests
            if m.data.get("type") == "hunting-query"
            and m.data.get("ruleConversion", {}).get("candidate")
        ),
    }


def write_index(index: dict[str, Any], out_dir: Path, *, dry_run: bool) -> Path:
    """Write ``coverage-index.json`` into ``out_dir``; when dry-running only report the target."""
    target = out_dir / "coverage-index.json"
    if dry_run:
        log.info("dry-run: would write %s", target)
        return target
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(index, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot write index to {target}: {exc}") from exc
    log.info("wrote %s", target)
    return target
