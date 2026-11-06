"""Discover form bundles (one folder per form: Form/, DataLayer/, StoredProcedures/, user controls...)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from ..config import Settings


@dataclass
class Bundle:
    name: str
    root: Path
    code_files: list[Path] = field(default_factory=list)   # .vb / .cs
    sql_files: list[Path] = field(default_factory=list)
    contents_md: Path | None = None

    def rel(self, p: Path, source_root: Path) -> str:
        return p.relative_to(source_root).as_posix()


def discover_bundles(settings: Settings) -> list[Bundle]:
    excluded = {e.lower() for e in settings.exclude}
    if settings.bundles == "auto":
        candidates = [
            d for root in settings.source_roots for d in sorted(root.iterdir())
            if d.is_dir() and d.name.lower() not in excluded and not d.name.startswith(".")
            and ((d / "CONTENTS.md").exists() or (d / "Form").is_dir() or (d / "StoredProcedures").is_dir())
        ]
    else:
        candidates = [root / b for root in settings.source_roots for b in settings.bundles if (root / b).is_dir()]

    bundles: list[Bundle] = []
    for d in candidates:
        b = Bundle(name=d.name, root=d, contents_md=(d / "CONTENTS.md") if (d / "CONTENTS.md").exists() else None)
        for p in sorted(d.rglob("*")):
            if any(part.lower() in {"bin", "obj"} for part in p.parts):
                continue
            suffix = p.suffix.lower()
            if suffix in {".vb", ".cs"}:
                b.code_files.append(p)
            elif suffix == ".sql":
                b.sql_files.append(p)
        if any(x.name == b.name for x in bundles):
            raise ValueError(f"duplicate bundle {b.name} in {d} (already found in {next(x for x in bundles if x.name == b.name).root})")
        bundles.append(b)
    return bundles


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()
