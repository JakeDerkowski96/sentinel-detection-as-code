"""Command-line entry point: ``dac-validate validate`` and ``dac-validate index``.

Argument parsing only; the work lives in the other modules so it can be tested
without invoking the CLI.

Required permissions: none. Reads the repository checkout; ``index`` writes
into ``build/`` (or ``--out``) unless ``--dry-run`` is given.

Usage:
    dac-validate validate
    dac-validate validate --format markdown --summary-file "$GITHUB_STEP_SUMMARY" --strict
    dac-validate index --dry-run -v
    dac-validate index --out build

Exit codes: 0 success, 1 validation errors (or warnings with --strict), 2 usage or runtime failure.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .checks import run_checks
from .index import build_index, write_index
from .loader import load_repository
from .models import Issue, Repository
from .report import render_json, render_markdown, render_text, summarize
from .schema_check import validate_schemas

log = logging.getLogger("dac_validate")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dac-validate", description=__doc__.split("\n\n")[0] if __doc__ else None
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="show debug detail on stderr")
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="repository root (default: current directory)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    val = sub.add_parser("validate", help="validate schemas and cross-references")
    val.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    val.add_argument("--strict", action="store_true", help="treat warnings as failures")
    val.add_argument(
        "--summary-file",
        type=Path,
        help="append a Markdown summary here (e.g. $GITHUB_STEP_SUMMARY)",
    )

    idx = sub.add_parser("index", help="build the derived coverage/dependency index")
    idx.add_argument(
        "--out", type=Path, default=Path("build"), help="output directory (default: build)"
    )
    idx.add_argument(
        "--dry-run", action="store_true", help="report what would be written without writing"
    )
    return parser


def _validate(repo: Repository) -> list[Issue]:
    return [*repo.load_issues, *validate_schemas(repo), *run_checks(repo)]


def _cmd_validate(args: argparse.Namespace, repo: Repository) -> int:
    issues = _validate(repo)
    rules, content = len(repo.rules), len(repo.manifests)
    renderers = {"text": render_text, "json": render_json, "markdown": render_markdown}
    print(renderers[args.format](issues, rules, content))
    if args.summary_file:
        try:
            with args.summary_file.open("a", encoding="utf-8") as handle:
                handle.write(render_markdown(issues, rules, content))
        except OSError as exc:
            log.error("cannot write summary to %s: %s", args.summary_file, exc)
            return 2
    errors, warnings = summarize(issues)
    return 1 if errors or (args.strict and warnings) else 0


def _cmd_index(args: argparse.Namespace, repo: Repository) -> int:
    # Refuse to index a repository that fails validation: a coverage report built
    # from invalid metadata would look authoritative and be wrong.
    errors, _ = summarize(_validate(repo))
    if errors:
        log.error("repository has %d validation errors; fix them before building the index", errors)
        return 1
    target = write_index(build_index(repo), args.root.resolve() / args.out, dry_run=args.dry_run)
    print(f"{'would write' if args.dry_run else 'wrote'} {target}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
    )
    if not (args.root / "schemas").is_dir():
        log.error(
            "%s does not look like a DaC repository root (no schemas/ directory)",
            args.root.resolve(),
        )
        return 2
    try:
        repo = load_repository(args.root)
        return _cmd_validate(args, repo) if args.command == "validate" else _cmd_index(args, repo)
    except ValueError as exc:
        log.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
