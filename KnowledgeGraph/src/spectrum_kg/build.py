"""Build the full in-memory graph: code + SQL extraction, linking, derived edges, curated domain layer."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import domain, link
from .config import Settings
from .embed import enrich
from .load import documented_types_check
from .extract.bundle import discover_bundles
from .extract.code import build_code_graph, collect_types
from .extract.roslyn import extract_code_facts
from .extract.tsql import parse_sp_file
from .model import Graph


@dataclass
class BuildReport:
    bundles: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_graph(settings: Settings, with_domain: bool = True) -> tuple[Graph, BuildReport]:
    g = Graph()
    report = BuildReport()
    bundles = discover_bundles(settings)
    report.bundles = [b.name for b in bundles]

    code_files = [f for b in bundles for f in b.code_files]
    file_bundle = {f: b.name for b in bundles for f in b.code_files}
    facts = extract_code_facts(settings, code_files)
    types = collect_types(facts, file_bundle, settings.source_root)
    cm = build_code_graph(g, types, settings.ui, settings.datalayer, settings.sql.get("default_schema", "dbo"))

    sps = []
    for b in bundles:
        for f in b.sql_files:
            try:
                sps.append((parse_sp_file(f, settings.sql.get("default_schema", "dbo")), b.name,
                            f.relative_to(settings.source_root).as_posix()))
            except Exception as ex:  # keep building; report the file
                report.errors.append(f"{f}: {ex}")
    link.build_sql_graph(g, sps, settings.sql.get("error_log_tables", []))
    report.warnings += link.resolve_code_to_sql(g, cm)
    g.finalize_names()
    _canonical_schema_names(g)
    link.derive_shortcuts(g)

    if with_domain:
        w, e = domain.apply_domain(g, settings.domain_dir)
        report.warnings += w
        report.errors += e

    for e in g.dangling_edges():
        report.warnings.append(f"dropped dangling edge {e.src} -{e.type}-> {e.dst}")
        del g.edges[e.key]
    enrich(g)
    report.warnings += documented_types_check(g)
    return g, report


def _canonical_schema_names(g: Graph) -> None:
    """Use one spelling per schema (most frequent) in Table/Column/SP display names."""
    from collections import Counter
    votes: dict[str, Counter] = {}
    for n in g.nodes.values():
        if n.label in ("Table", "StoredProcedure") and "." in n.props.get("name", ""):
            schema = n.props["name"].split(".", 1)[0]
            votes.setdefault(schema.lower(), Counter())[schema] += 1
    best = {k: sorted(v.items(), key=lambda kv: (-kv[1], kv[0] == kv[0].lower(), kv[0]))[0][0] for k, v in votes.items()}
    for n in g.nodes.values():
        if n.label in ("Table", "Column", "StoredProcedure") and "." in n.props.get("name", ""):
            schema, rest = n.props["name"].split(".", 1)
            n.props["name"] = f"{best.get(schema.lower(), schema)}.{rest}"
            if n.label == "Column":
                n.props["table"] = f"{best.get(schema.lower(), schema)}.{n.props['table'].split('.', 1)[1]}"
        if n.label == "Table":
            n.props["schema"] = best.get(n.props["schema"], n.props["schema"])
