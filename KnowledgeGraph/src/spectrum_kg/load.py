"""Load the in-memory graph into Neo4j (Aura): constraints, vector + fulltext indexes, batched MERGE, prune."""
from __future__ import annotations

import datetime as dt
import json
import re
from collections import defaultdict
from typing import Callable

import neo4j
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index

from .config import Settings
from .embed import sanitize
from .model import Graph
from .schema import LABELS, RELATIONSHIPS

VECTOR_INDEX = "kg_embedding"
FULLTEXT_INDEX = "kg_fulltext"
BASE_LABEL = "Searchable"
SAFE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def connect(settings: Settings) -> neo4j.Driver:
    driver = neo4j.GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password),
                                        notifications_min_severity="OFF")
    driver.verify_connectivity()
    return driver


def ensure_schema(driver: neo4j.Driver, settings: Settings) -> None:
    db = settings.neo4j_database
    driver.execute_query(f"CREATE CONSTRAINT kg_id IF NOT EXISTS FOR (n:{BASE_LABEL}) REQUIRE n.id IS UNIQUE", database_=db)
    driver.execute_query(f"CREATE INDEX kg_kind IF NOT EXISTS FOR (n:{BASE_LABEL}) ON (n.kind)", database_=db)
    create_vector_index(driver, VECTOR_INDEX, label=BASE_LABEL, embedding_property="embedding",
                        dimensions=settings.embedding_dims, similarity_fn="cosine", neo4j_database=db)
    create_fulltext_index(driver, FULLTEXT_INDEX, label=BASE_LABEL,
                          node_properties=["name", "title", "summary", "text"], neo4j_database=db)


def load_graph(driver: neo4j.Driver, settings: Settings, g: Graph, embeddings: dict[str, list[float]] | None,
               embedding_hashes: dict[str, str] | None, log: Callable[[str], None] = print, prune: bool = True) -> None:
    db = settings.neo4j_database
    ensure_schema(driver, settings)
    all_labels = sorted(set(LABELS) | {n.label for n in g.nodes.values()})
    remove_labels = ":".join(all_labels)

    by_label: dict[str, list[dict]] = defaultdict(list)
    for n in g.nodes.values():
        row = {"id": n.id, "props": {**sanitize(n.props), "id": n.id}}
        if embeddings and n.id in embeddings:
            row["embedding"] = embeddings[n.id]
            row["embedding_hash"] = embedding_hashes.get(n.id) if embedding_hashes else None
        else:
            row["embedding"] = None
            row["embedding_hash"] = None
        by_label[n.label].append(row)

    for label, rows in by_label.items():
        assert SAFE_NAME.match(label), label
        q = f"""
        UNWIND $rows AS row
        MERGE (n:{BASE_LABEL} {{id: row.id}})
        WITH n, row, n.embedding AS oldEmb, n.embedding_hash AS oldHash
        SET n = row.props
        SET n.embedding = CASE WHEN row.embedding IS NULL THEN oldEmb ELSE row.embedding END,
            n.embedding_hash = CASE WHEN row.embedding IS NULL THEN oldHash ELSE row.embedding_hash END
        REMOVE n:{remove_labels}
        SET n:{label}
        """
        for chunk in _chunks(rows, 200):
            driver.execute_query(q, rows=chunk, database_=db)
        log(f"  nodes {label}: {len(rows)}")

    by_type: dict[str, list[dict]] = defaultdict(list)
    for e in g.edges.values():
        by_type[e.type].append({"src": e.src, "dst": e.dst, "props": sanitize(e.props)})
    for rtype, rows in by_type.items():
        assert SAFE_NAME.match(rtype), rtype
        q = f"""
        UNWIND $rows AS row
        MATCH (a:{BASE_LABEL} {{id: row.src}})
        MATCH (b:{BASE_LABEL} {{id: row.dst}})
        MERGE (a)-[r:{rtype}]->(b)
        SET r = row.props
        """
        for chunk in _chunks(rows, 500):
            driver.execute_query(q, rows=chunk, database_=db)
        log(f"  edges {rtype}: {len(rows)}")

    if prune:
        ids = list(g.nodes)
        res = driver.execute_query(f"MATCH (n:{BASE_LABEL}) WHERE NOT n.id IN $ids DETACH DELETE n RETURN count(*) AS c",
                                   ids=ids, database_=db)
        stale_nodes = res.records[0]["c"]
        removed = 0
        for rtype, rows in by_type.items():
            pairs = [[r["src"], r["dst"]] for r in rows]
            res = driver.execute_query(
                f"MATCH (a:{BASE_LABEL})-[r:{rtype}]->(b:{BASE_LABEL}) WHERE NOT [a.id, b.id] IN $pairs DELETE r RETURN count(*) AS c",
                pairs=pairs, database_=db)
            removed += res.records[0]["c"]
        res = driver.execute_query(
            f"MATCH (:{BASE_LABEL})-[r]->(:{BASE_LABEL}) WHERE NOT type(r) IN $types DELETE r RETURN count(*) AS c",
            types=list(by_type), database_=db)
        removed += res.records[0]["c"]
        log(f"  pruned {stale_nodes} stale nodes, {removed} stale relationships")

    stats = g.stats()
    driver.execute_query(
        "MERGE (m:KGMeta {id: 'meta'}) SET m.built_at = $at, m.stats = $stats, m.embedding_model = $model, "
        "m.embedding_dims = $dims",
        at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), stats=json.dumps(stats),
        model=settings.embedding_model, dims=settings.embedding_dims, database_=db)


def _chunks(rows: list, n: int):
    for i in range(0, len(rows), n):
        yield rows[i:i + n]


def documented_types_check(g: Graph) -> list[str]:
    """Every label / relationship type in the graph must be described in schema.py (for describe_graph)."""
    problems = [f"label {l} missing from schema.LABELS" for l in {n.label for n in g.nodes.values()} - set(LABELS)]
    problems += [f"relationship {t} missing from schema.RELATIONSHIPS" for t in {e.type for e in g.edges.values()} - set(RELATIONSHIPS)]
    return problems
