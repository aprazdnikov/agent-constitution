import argparse
import os
import sys
from collections.abc import Sequence
from enum import IntEnum
from pathlib import Path
from typing import NoReturn

from ac_tools.findings import Finding
from ac_tools.layout import PLUGINS, load_texts, scanned_files
from ac_tools.manifests import check_manifests
from ac_tools.marketplaces import check_marketplaces
from ac_tools.provenance import (
    WINDOW,
    check_overlap,
    check_stoplist,
    corpus_shingles,
    load_stoplist,
)
from ac_tools.skills import check_placeholders, check_skills

STOPLIST_ENV = "AC_STOPLIST"
CORPUS_ENV = "AC_CORPUS"


class Exit(IntEnum):
    OK = 0
    FINDINGS = 1
    USAGE = 2


class UsageError(Exception):
    pass


def _warn(message: str) -> None:
    sys.stderr.write(f"ac-check: {message}\n")


def _corpus_dirs(raw: str, repo: Path) -> list[Path]:
    directories = [Path(part).resolve() for part in raw.split(os.pathsep) if part]
    for directory in directories:
        if not directory.is_dir():
            msg = f"{CORPUS_ENV}: {directory} is not a directory"
            raise UsageError(msg)
        if directory.is_relative_to(repo):
            msg = f"{CORPUS_ENV}: {directory} is inside the checked repository"
            raise UsageError(msg)
    return directories


def _provenance(texts: dict[Path, str], repo: Path) -> list[Finding]:
    findings: list[Finding] = []
    match os.environ.get(STOPLIST_ENV, ""):
        case "":
            _warn(f"{STOPLIST_ENV} not set: stoplist check skipped")
        case raw:
            path = Path(raw)
            if not path.is_file():
                msg = f"{STOPLIST_ENV}: {path} is not a file"
                raise UsageError(msg)
            try:
                stoplist = load_stoplist(path)
            except (OSError, UnicodeDecodeError) as error:
                msg = f"{STOPLIST_ENV}: cannot read {path}: {error}"
                raise UsageError(msg) from error
            findings += check_stoplist(texts, stoplist)
    match os.environ.get(CORPUS_ENV, ""):
        case "":
            _warn(f"{CORPUS_ENV} not set: overlap check skipped")
        case raw:
            try:
                corpus = corpus_shingles(_corpus_dirs(raw, repo), WINDOW)
            except OSError as error:
                msg = f"{CORPUS_ENV}: cannot read corpus: {error}"
                raise UsageError(msg) from error
            findings += check_overlap(texts, corpus, WINDOW)
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ac-check")
    parser.add_argument("repo", type=Path)
    repo: Path = parser.parse_args(argv).repo.resolve()
    if not (repo / PLUGINS).is_dir():
        _warn(f"{repo} has no {PLUGINS}/ directory")
        return Exit.USAGE
    texts, findings = load_texts(scanned_files(repo))
    try:
        findings += [
            *check_manifests(repo),
            *check_marketplaces(repo),
            *check_skills(repo, texts),
            *check_placeholders(texts),
            *_provenance(texts, repo),
        ]
    except UsageError as error:
        _warn(str(error))
        return Exit.USAGE
    sys.stdout.writelines(f"{finding.render(repo)}\n" for finding in findings)
    return Exit.FINDINGS if findings else Exit.OK


def run() -> NoReturn:
    sys.exit(main())
