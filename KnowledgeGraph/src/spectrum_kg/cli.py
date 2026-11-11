"""kg - build / validate / scaffold the SpectrumERP knowledge graph."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml

from .build import build_graph
from .config import load_settings

app = typer.Typer(add_completion=False, help="SpectrumERP knowledge graph builder")


def _report(report, show_warnings: bool = True) -> None:
    typer.echo(f"bundles: {', '.join(report.bundles)}")
    if show_warnings:
        for w in report.warnings:
            typer.secho(f"  warning: {w}", fg="yellow")
    for e in report.errors:
        typer.secho(f"  error: {e}", fg="red")


@app.command()
def build(
    dry_run: Optional[Path] = typer.Option(None, "--dry-run", help="Write the graph to this JSON file instead of Neo4j."),
    no_embed: bool = typer.Option(False, "--no-embed", help="Load without (re)computing embeddings."),
    no_prune: bool = typer.Option(False, "--no-prune", help="Keep nodes/edges in Neo4j that are no longer extracted."),
    strict: bool = typer.Option(True, help="Abort when domain YAML has unresolved references."),
    embed_budget: Optional[int] = typer.Option(None, "--embed-budget", help="Max (estimated) tokens to embed this run, "
                                               "highest-priority nodes first; the rest load without vectors "
                                               "(finish them with `kg embed-step`). 0 = embed nothing new."),
):
    """Extract code + SQL, apply curated domain docs, embed with Voyage AI and load into Neo4j."""
    settings = load_settings()
    g, report = build_graph(settings, docs="apply" if dry_run else "sync")
    _report(report)
    typer.echo(json.dumps(g.stats(), indent=1))
    if report.docs:
        typer.echo(f"embedding docs ({settings.docs_dir.name}/): {report.docs.summary()}")
    if report.errors and strict:
        typer.secho("aborting: fix the errors above (or pass --no-strict)", fg="red")
        raise typer.Exit(1)
    if dry_run:
        dry_run.parent.mkdir(parents=True, exist_ok=True)
        dry_run.write_text(json.dumps(g.to_json(), indent=1, default=str), encoding="utf-8")
        typer.echo(f"wrote {dry_run}")
        return

    embeddings = hashes = None
    if not no_embed:
        from .embed import embed_order, make_embedder, text_hash
        emb = make_embedder(settings)
        ids = embed_order(g)
        texts = [g.nodes[i].props["text"] for i in ids]
        typer.echo(f"embedding {len(texts)} nodes with {settings.embedding_model} ({settings.embedding_dims}d), "
                   f"{emb.pending(texts)} not cached yet...")
        vecs = emb.embed_documents(texts, progress=lambda d, t: typer.echo(f"  embedded {d}/{t} new texts"),
                                   max_tokens=embed_budget)
        embeddings = {i: v for i, v in zip(ids, vecs) if v is not None}
        typer.echo(f"{len(embeddings)}/{len(ids)} nodes have vectors")
        hashes = {i: text_hash(t, settings.embedding_model, settings.embedding_dims) for i, t in zip(ids, texts)}

    from .load import connect, load_graph
    driver = connect(settings)
    try:
        typer.echo(f"loading into {settings.neo4j_uri} ...")
        load_graph(driver, settings, g, embeddings, hashes, log=typer.echo, prune=not no_prune)
    finally:
        driver.close()
    typer.secho("done", fg="green")


@app.command("embed-step")
def embed_step(
    budget: Optional[int] = typer.Option(None, "--budget", help="Max (estimated) tokens to embed in this run. Default: "
                                         "everything for the local model, 450K for Voyage (free tier ~540K/hour)."),
):
    """One resumable slice of the embedding backlog, for scheduled runs on the Voyage free tier.

    Rebuilds the graph in memory (Roslyn facts are cached), embeds the highest-priority nodes that have no vector yet
    (up to --budget) and writes the vectors of every node whose stored vector is missing or stale into Neo4j.
    Prints `REMAINING <n>`. Needs a graph already loaded (`kg build --embed-budget 0`)."""
    from .embed import embed_order, make_embedder, text_hash
    from .load import connect
    settings = load_settings()
    if budget is None:
        budget = 10**12 if settings.embedding_provider == "local" else 450_000
    g, report = build_graph(settings, docs="sync")
    for e in report.errors:
        typer.secho(f"  error: {e}", fg="red")
    if report.errors:
        raise typer.Exit(1)
    ids = embed_order(g)
    texts = [g.nodes[i].props["text"] for i in ids]
    emb = make_embedder(settings)
    typer.echo(f"{emb.pending(texts)} of {len(ids)} nodes still need a vector; budget {budget} tokens")
    hashes = [text_hash(t, settings.embedding_model, settings.embedding_dims) for t in texts]
    driver = connect(settings)
    try:
        db = settings.neo4j_database
        rows = driver.execute_query("MATCH (n:Searchable) RETURN n.id AS id, n.embedding_hash AS h", database_=db).records
        if not rows:
            typer.secho("Neo4j holds no graph yet: run `kg build --embed-budget 0` first", fg="red")
            raise typer.Exit(1)
        stored = {r["id"]: r["h"] for r in rows}

        def flush() -> int:
            """Write every cached vector that Neo4j does not hold yet (or holds stale)."""
            todo = [{"id": i, "v": emb.cache[h], "h": h} for i, h in zip(ids, hashes)
                    if i in stored and h in emb.cache and stored[i] != h]
            for k in range(0, len(todo), 100):
                part = todo[k:k + 100]
                driver.execute_query("UNWIND $rows AS r MATCH (n:Searchable {id: r.id}) SET n.embedding = r.v, n.embedding_hash = r.h",
                                     rows=part, database_=db)
                stored.update({r["id"]: r["h"] for r in part})
            return len(todo)

        driver.execute_query("MERGE (m:KGMeta {id: 'meta'}) SET m.embedding_model = $model, m.embedding_dims = $dims",
                             model=settings.embedding_model, dims=settings.embedding_dims, database_=db)
        typer.echo(f"wrote {flush()} cached vectors to Neo4j")
        chunk, spent = getattr(emb, 'flush_tokens', 45_000), 0          # ~5 free-tier requests, then write to Neo4j so search improves as we go
        while spent < budget and emb.pending(texts):
            before = emb.pending(texts)
            emb.embed_documents(texts, progress=lambda d, t: typer.echo(f"  embedded {d}/{t}"), max_tokens=chunk)
            spent += chunk
            typer.echo(f"wrote {flush()} vectors to Neo4j ({emb.pending(texts)} still pending)")
            if emb.pending(texts) == before:
                break                      # no progress (persistent error handled by the embedder) - stop this slice
    finally:
        driver.close()
    left = emb.pending(texts)
    typer.echo(f"REMAINING {left}")
    if left == 0:
        typer.secho("COMPLETE: every node has a vector", fg="green")


docs_app = typer.Typer(add_completion=False, help="Local, editable copy of every node's embedding text")
app.add_typer(docs_app, name="docs")


def _show(ids: list[str], title: str, limit: int = 15) -> None:
    if ids:
        typer.echo(f"{title} ({len(ids)}):")
        for i in ids[:limit]:
            typer.echo(f"  {i}")
        if len(ids) > limit:
            typer.echo(f"  ... +{len(ids) - limit} more")


@docs_app.command("sync")
def docs_sync(prune: bool = typer.Option(False, "--prune", help="Delete files of nodes that left the graph (never edited ones).")):
    """Write/refresh embedding_docs/ from the current graph (all phases).

    Backfills nodes ingested earlier, adds nodes of new phases, refreshes files you did not edit, and never overwrites
    a file you edited."""
    settings = load_settings()
    g, report = build_graph(settings, docs="sync", prune_docs=prune)
    for e in report.errors:
        typer.secho(f"  error: {e}", fg="red")
    r = report.docs
    typer.echo(f"{len(g.nodes)} nodes, phases: {', '.join(dict.fromkeys(settings.phases.values()))}")
    typer.echo(f"{settings.docs_dir}: {r.summary()}")
    _show(r.drifted, "edited files whose generated text has since changed (review: kg docs diff <id>)")
    _show(r.orphaned, "files of nodes no longer in the graph (kg docs sync --prune)")
    typer.echo("Re-embed after editing: kg build  (or kg embed-step)")


@docs_app.command("status")
def docs_status():
    """Compare embedding_docs/ with the current graph without writing anything."""
    settings = load_settings()
    g, report = build_graph(settings, docs="apply")
    r = report.docs
    typer.echo(f"{len(g.nodes)} nodes. Would write: new {len(r.new)}, refreshed {len(r.refreshed)}; "
               f"unchanged {r.unchanged}; edited {len(r.edited)} (drifted {len(r.drifted)}); orphaned {len(r.orphaned)}")
    _show(r.new, "new (no file yet)", 5)
    _show(r.edited, "hand-edited")
    _show(r.drifted, "drifted")


def _resolve(g, query: str) -> str:
    if query in g.nodes:
        return query
    hits = [i for i in g.nodes if i.lower() == query.lower()] or [i for i in g.nodes if i.lower().endswith(":" + query.lower())]
    if len(hits) != 1:
        typer.secho(f"{query!r}: {'no match' if not hits else 'ambiguous: ' + ', '.join(hits[:8])}", fg="red")
        raise typer.Exit(1)
    return hits[0]


@docs_app.command("diff")
def docs_diff(node: str = typer.Argument(..., help="Node id (form:fUnitMaster) or bare name")):
    """Show the file on disk versus what the graph would generate now."""
    import difflib
    from .embedding_docs import EmbeddingDocs, normalize
    settings = load_settings()
    g, report = build_graph(settings, docs="off")
    nid = _resolve(g, node)
    store = EmbeddingDocs(settings.docs_dir)
    entry = store.manifest.get(nid)
    cur = store.read(entry["file"]) if entry else None
    if cur is None:
        typer.echo(f"{nid}: no file yet (run kg docs sync)")
        return
    d = list(difflib.unified_diff(normalize(cur).splitlines(), normalize(report.generated[nid]).splitlines(),
                                  "file (embedded)", "generated now", lineterm=""))
    typer.echo("\n".join(d) or f"{nid}: file equals the generated text")


@docs_app.command("reset")
def docs_reset(nodes: Optional[list[str]] = typer.Argument(None, help="Node ids / names"),
               all_edited: bool = typer.Option(False, "--all", help="Reset every hand-edited file")):
    """Discard hand edits: overwrite the file(s) with the text the graph generates."""
    from .embedding_docs import EmbeddingDocs
    settings = load_settings()
    g, report = build_graph(settings, docs="apply")
    store = EmbeddingDocs(settings.docs_dir)
    targets = report.docs.edited if all_edited else [_resolve(g, n) for n in nodes or []]
    if not targets:
        typer.echo("nothing to reset (give node ids or --all)")
        return
    for nid in targets:
        store.reset(nid, report.generated[nid])
    typer.echo(f"reset {len(targets)} file(s); run kg build to re-embed")


@app.command()
def phases():
    """List the discovered phases and the form bundles in each."""
    from .extract.bundle import discover_bundles
    settings = load_settings()
    by: dict[str, list[str]] = {}
    for b in discover_bundles(settings):
        by.setdefault(settings.phase_of(b.root), []).append(b.name)
    for name, bundles in by.items():
        typer.echo(f"{name}: {len(bundles)} bundles")


@app.command()
def validate():
    """Build in memory and report unresolved references, undocumented forms and dangling edges."""
    settings = load_settings()
    g, report = build_graph(settings)
    _report(report)
    typer.echo(json.dumps(g.stats(), indent=1))
    if report.errors:
        raise typer.Exit(1)
    typer.secho("valid" if not report.warnings else f"valid with {len(report.warnings)} warnings",
                fg="green" if not report.warnings else "yellow")


@app.command()
def stats():
    """Node / edge counts of the extracted graph (no Neo4j needed)."""
    g, report = build_graph(load_settings())
    typer.echo(json.dumps(g.stats(), indent=1))


@app.command("export-html")
def export_html_cmd(
    out: Path = typer.Option(Path("kg-graph.html"), "--out", "-o", help="Output HTML file."),
):
    """Write the current graph as a standalone interactive network view (open in a browser)."""
    from .viz import export_html
    g, report = build_graph(load_settings())
    _report(report, show_warnings=False)
    path = export_html(g, out.resolve())
    typer.secho(f"wrote {path} ({len(g.nodes)} nodes, {len(g.edges)} edges)", fg="green")


@app.command("scaffold-doc")
def scaffold_doc(
    name: str = typer.Argument(..., help="Form or user-control name, e.g. fPurchaseOrder"),
    force: bool = typer.Option(False, help="Overwrite an existing doc."),
):
    """Create domain/forms/<name>.yaml pre-filled from the extracted code, to be completed by a human / Claude Code."""
    settings = load_settings()
    g, _ = build_graph(settings, with_domain=False)
    node = g.nodes.get(f"form:{name}") or g.nodes.get(f"usercontrol:{name}")
    if node is None:
        typer.secho(f"no extracted form or user control named {name}", fg="red")
        raise typer.Exit(1)
    target = settings.domain_dir / "forms" / f"{name}.yaml"
    if target.exists() and not force:
        typer.secho(f"{target} exists (use --force)", fg="red")
        raise typer.Exit(1)

    controls = [g.nodes[e.dst].props for e in g.out(node.id, "HAS_CONTROL")]
    fields = [f"{c.get('label') or c['control']} ({c['type']}{', mandatory' if c.get('mandatory') else ''}"
              f"{', tab ' + c['tab'] if c.get('tab') else ''})" for c in controls if c.get("label") or "Grid" in c["type"]]
    methods = sorted(g.nodes[e.dst].props["method"] for e in g.out(node.id, "HAS_METHOD"))
    sps = sorted(g.nodes[e.dst].props["name"] for e in g.out(node.id, "CALLS_SP"))
    tables = sorted(g.nodes[e.dst].props["name"] for e in g.out(node.id, "USES_TABLE"))
    msgs = sorted({lit for e in g.out(node.id, "HAS_METHOD") if g.nodes[e.dst].props["method"] == "ValidateForm"
                   for lit in __import__("re").findall(r'"([^"]{8,})"', g.nodes[e.dst].props.get("code", "")) if " " in lit})
    doc = {
        ("form" if node.label == "Form" else "usercontrol"): name,
        "title": node.props.get("title") or name,
        "module": "MM",
        "kind": "master | transaction | report | component",
        "users": ["TODO"],
        "summary": "TODO one sentence: what the form is for.",
        "purpose": "TODO business purpose.\n",
        "functional_description": "Fields:\n" + "\n".join(f"- {f}" for f in fields) + "\n",
        "actions": {"Save": "TODO", "Open": "TODO", "Delete": "TODO"},
        "validations": msgs or ["TODO"],
        "manages": ["TODO concept key from concepts.yaml"],
        "uses_concepts": [],
        "method_notes": {m: "TODO" for m in methods if m in ("SaveMain", "Save", "LoadData", "FillValues", "ValidateForm")},
    }
    header = (f"# Scaffolded from code. Fill the TODOs, add the form to a process in domain/processes/, then run `kg validate`.\n"
              f"# Stored procedures: {', '.join(sps)}\n# Tables: {', '.join(tables)}\n")
    target.write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=110), encoding="utf-8")
    typer.secho(f"wrote {target}", fg="green")


if __name__ == "__main__":
    sys.exit(app())
