"""Run the .NET Roslyn extractor (tools/RoslynExtractor) and return syntax facts for .vb/.cs files.

Results are cached per file content hash in .cache/roslyn so unchanged files are not re-parsed.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ..config import Settings
from .bundle import file_sha


def ensure_extractor(settings: Settings) -> Path:
    exe = settings.roslyn_extractor
    sources = list(settings.roslyn_project.parent.glob("*.cs")) + [settings.roslyn_project]
    stale = not exe.exists() or max(s.stat().st_mtime for s in sources) > exe.stat().st_mtime
    if stale:
        subprocess.run(
            ["dotnet", "build", str(settings.roslyn_project), "-c", "Release", "-o", str(exe.parent), "-nologo", "-v", "q"],
            check=True,
        )
    return exe


def extract_code_facts(settings: Settings, files: list[Path]) -> dict[Path, dict[str, Any]]:
    cache_dir = settings.cache_dir / "roslyn"
    cache_dir.mkdir(parents=True, exist_ok=True)
    result: dict[Path, dict[str, Any]] = {}
    todo: list[tuple[Path, Path]] = []
    for f in files:
        cached = cache_dir / f"{file_sha(f)}.{f.suffix.lstrip('.').lower()}.json"
        if cached.exists():
            facts = json.loads(cached.read_text(encoding="utf-8"))
            facts["path"] = str(f)
            result[f] = facts
        else:
            todo.append((f, cached))

    if todo:
        exe = ensure_extractor(settings)
        # Identical files are copied into many bundles: extract each distinct content once, and keep every
        # command line under the Windows limit by sending the files in chunks.
        distinct: dict[Path, tuple[Path, Path]] = {}
        for f, cached in todo:
            distinct.setdefault(cached, (f, cached))
        by_cache: dict[Path, dict[str, Any]] = {}
        pending = list(distinct.values())
        while pending:
            chunk, size = [], 0
            while pending and (not chunk or size + len(str(pending[0][0])) + 3 < 20000):
                chunk.append(pending.pop(0))
                size += len(str(chunk[-1][0])) + 3
            out = cache_dir / "_batch.json"
            subprocess.run([str(exe), "--out", str(out), *[str(f) for f, _ in chunk]], check=True, capture_output=True)
            by_path = {Path(item["path"]).resolve(): item for item in json.loads(out.read_text(encoding="utf-8"))}
            out.unlink(missing_ok=True)
            for f, cached in chunk:
                facts = by_path[f.resolve()]
                if facts.get("language") == "error":
                    raise RuntimeError(f"Roslyn failed on {f}: {facts.get('diagnostics')}")
                cached.write_text(json.dumps(facts), encoding="utf-8")
                by_cache[cached] = facts
        for f, cached in todo:
            result[f] = {**by_cache[cached], "path": str(f)}
    return result
