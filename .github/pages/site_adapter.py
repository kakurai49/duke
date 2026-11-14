"""Preserve DUKE's existing public release and enforce its original policy."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import re
import stat


CORE_FILES = {".nojekyll", "README.md", "index.html", "assets/app.js", "assets/style.css", "data/dashboard.json"}
MANAGEMENT_FILES = {
    ".github/workflows/pages.yml", ".github/pages/README.md",
    ".github/pages/site_adapter.py", ".github/pages/site.json",
    ".github/pages/test_site_adapter.py", ".github/pages/duke_validator.py",
    ".github/pages/duke_history.py", ".github/pages/source-manifest.json",
    ".github/pages-core/pages_core.py",
    ".github/pages-core/security.py",
    ".github/pages-core/requirements.lock",
    ".github/pages-core/schema/bom-1.6.schema.json",
    ".github/pages-core/schema/jsf-0.82.schema.json",
    ".github/pages-core/schema/spdx.schema.json",
    ".github/pages-core/schema/LICENSE",
    ".github/pages-core/schema/source.json",
    ".github/pages-core/vendor-manifest.json",
}
MANAGEMENT_DIRS = {".github", ".github/workflows", ".github/pages",
                   ".github/pages-core", ".github/pages-core/schema"}
PUBLIC_DIRS = {"assets", "data", "records"}
RECORD = re.compile(r"records/[a-z0-9][a-z0-9._-]{0,159}\.html\Z")
SECRET_SIGNATURES = (
    re.compile(rb"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"),
    re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{80,255}\b"),
    re.compile(rb"\bAKIA[A-Z0-9]{16}\b"),
)


def require(condition, code):
    if not condition:
        raise ValueError(code)


def collect(root):
    files, total = {}, 0
    for directory, directories, names in os.walk(root, followlinks=False):
        for name in sorted(directories + names):
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            before = path.lstat()
            require(not stat.S_ISLNK(before.st_mode), "SYMLINK_FORBIDDEN:" + relative)
            if relative == ".git":
                require(stat.S_ISDIR(before.st_mode), "GIT_DIRECTORY_REQUIRED")
                directories.remove(name)
                continue
            if stat.S_ISDIR(before.st_mode):
                require(relative in PUBLIC_DIRS | MANAGEMENT_DIRS, "UNMANAGED_DIRECTORY:" + relative)
                continue
            require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "REGULAR_SINGLE_LINK_REQUIRED:" + relative)
            if relative in MANAGEMENT_FILES:
                continue
            require(relative in CORE_FILES or RECORD.fullmatch(relative), "UNMANAGED_FILE:" + relative)
            require(before.st_size <= 1_000_000, "FILE_BYTE_BUDGET")
            raw = path.read_bytes()
            after = path.stat(follow_symlinks=False)
            require((before.st_ino, before.st_size, before.st_mtime_ns) ==
                    (after.st_ino, after.st_size, after.st_mtime_ns) and len(raw) == before.st_size,
                    "FILE_CHANGED_DURING_READ")
            total += len(raw)
            require(total <= 5_000_000 and len(files) < 128, "SITE_BUDGET")
            require(not any(pattern.search(raw) for pattern in SECRET_SIGNATURES), "SECRET_SIGNATURE")
            raw.decode("utf-8")
            files[relative] = raw
    require(CORE_FILES <= files.keys(), "CORE_FILE_MISSING")
    return files


def prepare(root: Path, stage: Path) -> None:
    root, stage = Path(root), Path(stage)
    require(stage.is_dir() and not stage.is_symlink() and not any(stage.iterdir()), "EMPTY_STAGE_REQUIRED")
    require(root.resolve() != stage.resolve() and root.resolve() not in stage.resolve().parents,
            "SOURCE_STAGE_OVERLAP")
    files = collect(root)
    spec = importlib.util.spec_from_file_location("duke_site_validator", root / ".github/pages/duke_validator.py")
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    validator.validate_site(files, validator.load_json(files["data/dashboard.json"]))
    for relative, raw in sorted(files.items()):
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
