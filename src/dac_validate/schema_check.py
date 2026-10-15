"""JSON Schema validation of every structured file in the repository.

Required permissions: none. Reads local files only.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .models import Issue, Repository, Severity

log = logging.getLogger(__name__)


def _load_schema(schema_dir: Path, name: str) -> Draft202012Validator:
    path = schema_dir / name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load schema {path}: {exc}") from exc
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(validator: Draft202012Validator, data: Any, rel: str) -> list[Issue]:
    issues: list[Issue] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in err.absolute_path) or "(root)"
        issues.append(Issue(Severity.ERROR, "schema", rel, f"{where}: {err.message}"))
    return issues


def validate_schemas(repo: Repository) -> list[Issue]:
    """Validate each loaded file against its schema and return all violations."""
    schema_dir = repo.root / "schemas"
    cache: dict[str, Draft202012Validator] = {}

    def validator(name: str) -> Draft202012Validator:
        if name not in cache:
            cache[name] = _load_schema(schema_dir, name)
        return cache[name]

    def rel(path: Path) -> str:
        return path.relative_to(repo.root).as_posix()

    issues: list[Issue] = []
    for bundle in repo.rules:
        d = bundle.directory
        issues += _errors(
            validator("analytics-rule.schema.json"), bundle.rule, rel(d / "rule.yaml")
        )
        issues += _errors(
            validator("rule-metadata.schema.json"), bundle.metadata, rel(d / "metadata.yaml")
        )
        if bundle.history is not None:
            issues += _errors(
                validator("tuning-history.schema.json"),
                bundle.history,
                rel(d / "tuning-history.yaml"),
            )
        if bundle.exceptions is not None:
            issues += _errors(
                validator("exceptions.schema.json"), bundle.exceptions, rel(d / "exceptions.yaml")
            )
        if bundle.tests is not None:
            issues += _errors(
                validator("test-cases.schema.json"),
                bundle.tests,
                rel(d / "tests" / "test-cases.yaml"),
            )
    for manifest in repo.manifests:
        issues += _errors(
            validator("content-manifest.schema.json"),
            manifest.data,
            rel(manifest.directory / "manifest.yaml"),
        )
    for path, data in repo.packages:
        issues += _errors(validator("package.schema.json"), data, rel(path))
    for path, data in repo.overrides:
        issues += _errors(validator("tenant-override.schema.json"), data, rel(path))
    for name, (path, data) in repo.policies.items():
        issues += _errors(validator(f"policy-{name}.schema.json"), data, rel(path))
    log.debug("schema validation produced %d issues", len(issues))
    return issues
