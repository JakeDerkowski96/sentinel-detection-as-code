"""Tests for dac-validate. Each failure-path test mutates a throwaway copy of the repo.

Required permissions: none.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from dac_validate.checks import run_checks
from dac_validate.cli import main
from dac_validate.index import build_index
from dac_validate.loader import load_repository
from dac_validate.models import Issue, Severity
from dac_validate.schema_check import validate_schemas

REPO_ROOT = Path(__file__).resolve().parents[1]
RULE1 = "content/analytics-rules/DET-ENTRA-0001-failed-signins-then-success"
RULE2 = "content/analytics-rules/DET-MDE-0001-encoded-powershell"


def _copy_tree(src: Path, dst: Path) -> None:
    """Copy files only. shutil.copytree also copies directory attributes, and OneDrive-synced
    checkouts carry read-only directory attributes that later make rmtree fail on Windows."""
    for path in src.rglob("*"):
        target = dst / path.relative_to(src)
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)


@pytest.fixture()
def work(tmp_path: Path) -> Path:
    """A disposable copy of the parts of the repo the validator reads."""
    for name in ("content", "schemas", "policy", "tenants"):
        _copy_tree(REPO_ROOT / name, tmp_path / name)
    return tmp_path


def _issues(root: Path) -> list[Issue]:
    repo = load_repository(root)
    return [*repo.load_issues, *validate_schemas(repo), *run_checks(repo)]


def _codes(root: Path, severity: Severity = Severity.ERROR) -> set[str]:
    return {i.code for i in _issues(root) if i.severity == severity}


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {path}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def test_shipped_repository_is_valid(work: Path) -> None:
    assert [i for i in _issues(work) if i.severity == Severity.ERROR] == []


def test_undeclared_dependency_is_an_error(work: Path) -> None:
    _replace(
        work / RULE2 / "metadata.yaml",
        "dependencies:\n  functions:\n    - FUNC-NORMALIZE-PROCESS-001\n",
        "",
    )
    assert "dependency-undeclared" in _codes(work)


def test_missing_dependency_is_an_error(work: Path) -> None:
    _replace(
        work / RULE2 / "metadata.yaml", "FUNC-NORMALIZE-PROCESS-001", "FUNC-DOES-NOT-EXIST-001"
    )
    assert "dependency-missing" in _codes(work)


def test_id_mismatch_between_files(work: Path) -> None:
    _replace(work / RULE1 / "tuning-history.yaml", "DET-ENTRA-0001", "DET-ENTRA-0002")
    assert "id-mismatch" in _codes(work)


def _add_unknown_field(work: Path) -> None:
    """Append a top-level key the schema does not allow (additionalProperties: false)."""
    with (work / RULE1 / "rule.yaml").open("a", encoding="utf-8") as handle:
        handle.write("unexpectedField: 1\n")


def test_unknown_field_rejected_by_schema(work: Path) -> None:
    _add_unknown_field(work)
    assert "schema" in _codes(work)


def test_unknown_domain_rejected(work: Path) -> None:
    _replace(work / "policy/taxonomy.yaml", "ENTRA, ", "")
    assert "unknown-domain" in _codes(work)


def test_production_requires_tests(work: Path) -> None:
    shutil.rmtree(work / RULE1 / "tests")
    _replace(work / RULE1 / "metadata.yaml", "lifecycle: validated", "lifecycle: production")
    assert "tests-required" in _codes(work)


def test_missing_fixture_detected(work: Path) -> None:
    (work / RULE1 / "tests/fixtures/below-threshold.csv").unlink()
    assert "fixture-missing" in _codes(work)


def test_retired_rule_must_be_disabled(work: Path) -> None:
    _replace(work / RULE1 / "metadata.yaml", "lifecycle: validated", "lifecycle: retired")
    assert "retired-enabled" in _codes(work)


def test_override_parameter_must_exist_in_query(work: Path) -> None:
    _replace(
        work / "tenants/overrides/contoso/DET-MDE-0001.yaml", "MinEncodedLength", "NotAParameter"
    )
    assert "override-parameter" in _codes(work)


def test_canary_needs_severity_and_duration(work: Path) -> None:
    _replace(work / RULE1 / "metadata.yaml", "    severity: Informational\n    duration: P7D\n", "")
    assert "canary-incomplete" in _codes(work)


def test_package_membership_enforced(work: Path) -> None:
    _replace(
        work / RULE1 / "metadata.yaml", "package: PKG-IDENTITY-SIGNIN", "package: PKG-LINUX-SSH"
    )
    assert "package-membership" in _codes(work)


def test_duplicate_id_detected(work: Path) -> None:
    _replace(
        work / "content/parsers/PARSER-SYSLOG-SSHD-001/manifest.yaml",
        "PARSER-SYSLOG-SSHD-001",
        "FUNC-NORMALIZE-PROCESS-001",
    )
    assert "duplicate-id" in _codes(work)


def test_index_contents(work: Path) -> None:
    index = build_index(load_repository(work))
    assert index["counts"]["rules"] == 3
    assert index["coverage"]["techniques"]["T1110"] == ["DET-ENTRA-0001"]
    assert index["huntingConversionCandidates"] == ["HUNT-IDENTITY-0001"]


def test_cli_exit_codes(work: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--root", str(work), "validate"]) == 0
    _add_unknown_field(work)
    assert main(["--root", str(work), "validate"]) == 1
    # index refuses to build from an invalid repository
    assert main(["--root", str(work), "index"]) == 1
    capsys.readouterr()


def test_cli_rejects_non_repository_root(tmp_path: Path) -> None:
    assert main(["--root", str(tmp_path), "validate"]) == 2


def test_index_dry_run_writes_nothing(work: Path) -> None:
    assert main(["--root", str(work), "index", "--dry-run"]) == 0
    assert not (work / "build").exists()


def test_index_writes_valid_json(work: Path) -> None:
    assert main(["--root", str(work), "index"]) == 0
    data = json.loads((work / "build/coverage-index.json").read_text(encoding="utf-8"))
    assert data["indexVersion"] == 1
