from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]  # .../KnowledgeGraph


@dataclass
class Settings:
    project_dir: Path
    graph_json: Path | None          # prebuilt graph to load instead of extracting (kg.yaml `graph_json`)
    source_root: Path
    source_roots: list[Path]
    docs_dir: Path
    domain_dir: Path
    cache_dir: Path
    roslyn_extractor: Path
    roslyn_project: Path
    bundles: str | list[str]
    exclude: list[str]
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def sql(self) -> dict[str, Any]: return self.raw.get("sql", {})
    @property
    def datalayer(self) -> dict[str, Any]: return self.raw.get("datalayer", {})
    @property
    def ui(self) -> dict[str, Any]: return self.raw.get("ui", {})

    # --- environment (.env) ---
    @property
    def neo4j_uri(self) -> str: return _env("NEO4J_URI")
    @property
    def neo4j_user(self) -> str: return os.getenv("NEO4J_USERNAME", "neo4j")
    @property
    def neo4j_password(self) -> str: return _env("NEO4J_PASSWORD")
    @property
    def neo4j_database(self) -> str | None: return os.getenv("NEO4J_DATABASE") or None
    @property
    def voyage_api_key(self) -> str: return _env("VOYAGE_API_KEY")
    @property
    def voyage_model(self) -> str: return os.getenv("VOYAGE_MODEL", "voyage-code-3")
    @property
    def embedding_provider(self) -> str: return os.getenv("EMBEDDING_PROVIDER", "local").lower()   # local | voyage
    @property
    def local_embedding_model(self) -> str: return os.getenv("LOCAL_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    @property
    def embedding_model(self) -> str:
        """Name of the model that produces the stored vectors (part of every cache key and vector hash)."""
        return self.local_embedding_model if self.embedding_provider == "local" else self.voyage_model
    @property
    def embedding_dims(self) -> int: return int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env in {PROJECT_DIR} and fill it in.")
    return v


def load_settings(config_path: Path | None = None) -> Settings:
    config_path = config_path or PROJECT_DIR / "kg.yaml"
    load_dotenv(config_path.parent / ".env")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    base = config_path.parent
    roots = [(base / r).resolve() for r in (raw.get("source_roots") or [])] or [(base / raw.get("source_root", "..")).resolve()]
    return Settings(
        project_dir=base,
        graph_json=(base / raw["graph_json"]).resolve() if raw.get("graph_json") else None,
        source_root=Path(os.path.commonpath([str(r) for r in roots])),
        source_roots=roots,
        docs_dir=(base / raw.get("embedding_docs_dir", "embedding_docs")).resolve(),
        domain_dir=(base / raw.get("domain_dir", "domain")).resolve(),
        cache_dir=(base / raw.get("cache_dir", ".cache")).resolve(),
        roslyn_extractor=(base / raw["roslyn_extractor"]).resolve(),
        roslyn_project=(base / raw["roslyn_project"]).resolve(),
        bundles=raw.get("bundles", "auto"),
        exclude=raw.get("exclude", []),
        raw=raw,
    )
