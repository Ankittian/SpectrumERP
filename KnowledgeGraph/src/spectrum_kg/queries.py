"""Read-only graph primitives used by the MCP server (agentic RAG: the client chooses the hops)."""
from __future__ import annotations

import json
import re
from typing import Any

import neo4j
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import HybridRetriever, VectorRetriever

from .config import Settings
from .load import BASE_LABEL, FULLTEXT_INDEX, VECTOR_INDEX
from .schema import LABELS, RELATIONSHIPS, STRATEGIES, TIPS

HIDDEN_PROPS = {"embedding", "embedding_hash", "text"}
SUMMARY_PROPS = ["id", "kind", "name", "title", "summary", "status", "modules"]
LUCENE_SPECIAL = re.compile(r'([+\-&|!(){}\[\]^"~*?:\\/])')
WRITE_RE = re.compile(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH)\b|\bCALL\s+(apoc\.(create|merge|refactor|periodic)|db\.create|dbms)", re.I)
RETURN_PROPS = ["id", "kind", "name", "title", "summary", "modules", "status"]


def _short(s: Any, n: int = 220) -> Any:
    if isinstance(s, str) and len(s) > n:
        return s[: n - 1] + "…"
    return s


class LocalQueryEmbedder(Embedder):
    """Query embeddings from the same local model that embedded the nodes (loaded on first use)."""

    def __init__(self, model: str, dims: int):
        self.model_name, self.dims, self._m = model, dims, None

    def embed_query(self, text: str) -> list[float]:
        from .embed import encode_query, load_local_model
        if self._m is None:
            self._m = load_local_model(self.model_name, self.dims)
        return encode_query(self._m, text)


class VoyageQueryEmbedder(Embedder):
    def __init__(self, api_key: str, model: str, dims: int):
        super().__init__()
        import voyageai
        self.client = voyageai.Client(api_key=api_key, max_retries=3)
        self.model, self.dims = model, dims

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed([text], model=self.model, input_type="query", output_dimension=self.dims).embeddings[0]


class KGClient:
    def __init__(self, settings: Settings, driver: neo4j.Driver | None = None, embedder: Embedder | None = None):
        self.settings = settings
        self._driver = driver
        self._embedder = embedder

    # ---- plumbing -------------------------------------------------------------------------
    @property
    def driver(self) -> neo4j.Driver:
        if self._driver is None:
            s = self.settings
            self._driver = neo4j.GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password),
                                                        notifications_min_severity="OFF")
        return self._driver

    @property
    def embedder(self) -> Embedder:
        if self._embedder is None:
            s = self.settings
            self._embedder = (LocalQueryEmbedder(s.embedding_model, s.embedding_dims) if s.embedding_provider == "local"
                              else VoyageQueryEmbedder(s.voyage_api_key, s.voyage_model, s.embedding_dims))
        return self._embedder

    def _read(self, query: str, timeout: float = 20.0, **params: Any) -> list[dict[str, Any]]:
        @neo4j.unit_of_work(timeout=timeout)
        def work(tx):
            return [r.data() for r in tx.run(query, **params)]

        with self.driver.session(database=self.settings.neo4j_database, default_access_mode=neo4j.READ_ACCESS) as s:
            return s.execute_read(work)

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    # ---- hop hints --------------------------------------------------------------------------
    def hop_hints(self, ids: list[str]) -> dict[str, dict[str, dict[str, Any]]]:
        rows = self._read(
            f"""UNWIND $ids AS id
            MATCH (n:{BASE_LABEL} {{id: id}})-[r]-(m:{BASE_LABEL})
            WITH id, type(r) AS rel, CASE WHEN startNode(r) = n THEN 'out' ELSE 'in' END AS dir, m
            RETURN id, rel, dir, count(*) AS c, collect(DISTINCT m.kind) AS labels""", ids=ids)
        hints: dict[str, dict[str, dict[str, Any]]] = {i: {"out": {}, "in": {}} for i in ids}
        for r in rows:
            hints[r["id"]][r["dir"]][r["rel"]] = {"count": r["c"], "labels": sorted(r["labels"])}
        return hints

    # ---- describe ---------------------------------------------------------------------------
    def describe_graph(self) -> dict[str, Any]:
        label_counts = {r["k"]: r["c"] for r in self._read(f"MATCH (n:{BASE_LABEL}) RETURN n.kind AS k, count(*) AS c")}
        rel_counts = {r["t"]: r["c"] for r in self._read(
            f"MATCH (:{BASE_LABEL})-[r]->(:{BASE_LABEL}) RETURN type(r) AS t, count(*) AS c")}
        meta = self._read("MATCH (m:KGMeta {id:'meta'}) RETURN m.built_at AS built_at, m.embedding_model AS model")
        return {
            "built_at": meta[0]["built_at"] if meta else None,
            "embedding_model": meta[0]["model"] if meta else None,
            "id_conventions": "form:<Form> usercontrol:<Ctl> method:<Owner>.<Method> control:<Owner>.<ctl> "
                              "dtclass:/dtprop:/dtmethod:/daclass:/damethod:<Class>[.<Member>] sp:<schema.proc> "
                              "table:<schema.table> column:<schema.table>.<col> "
                              "module:<code> process:<key> concept:<key> rule:<key> (SQL ids lowercase)",
            "labels": [{"label": k, **v, "count": label_counts.get(k, 0)} for k, v in LABELS.items()],
            "relationships": [{"type": k, **{kk: vv for kk, vv in v.items()}, "derived": bool(v.get("derived")),
                               "count": rel_counts.get(k, 0)} for k, v in RELATIONSHIPS.items()],
            "strategies": STRATEGIES,
            "tips": TIPS,
        }

    # ---- search -----------------------------------------------------------------------------
    def search(self, query: str, mode: str = "hybrid", labels: list[str] | None = None, module: str | None = None,
               top_k: int = 8) -> dict[str, Any]:
        top_k = max(1, min(top_k, 30))
        pool = top_k * (6 if (labels or module) else 2)
        rows: list[dict[str, Any]] = []
        if mode == "fulltext":
            rows = self._fulltext(query, pool)
        else:
            vec = self.embedder.embed_query(query)
            if mode == "vector":
                r = VectorRetriever(self.driver, VECTOR_INDEX, return_properties=RETURN_PROPS,
                                    neo4j_database=self.settings.neo4j_database)
                res = r.get_search_results(query_vector=vec, top_k=pool)
            else:
                r = HybridRetriever(self.driver, VECTOR_INDEX, FULLTEXT_INDEX, return_properties=RETURN_PROPS,
                                    neo4j_database=self.settings.neo4j_database)
                res = r.get_search_results(query_text=_lucene_escape(query), query_vector=vec, top_k=pool)
            for rec in res.records:
                node = dict(rec["node"]) if not isinstance(rec["node"], dict) else rec["node"]
                rows.append({**node, "score": rec["score"]})
        out = []
        for r in rows:
            if labels and r.get("kind") not in labels:
                continue
            if module and module not in (r.get("modules") or []):
                continue
            out.append(r)
            if len(out) >= top_k:
                break
        hints = self.hop_hints([r["id"] for r in out]) if out else {}
        return {"query": query, "mode": mode, "results": [
            {"id": r["id"], "label": r.get("kind"), "name": r.get("title") or r.get("name"),
             "score": round(float(r.get("score") or 0), 4), "summary": _short(r.get("summary")),
             "status": r.get("status"), "hop_hints": hints.get(r["id"])} for r in out]}

    def _fulltext(self, query: str, k: int) -> list[dict[str, Any]]:
        rows = self._read(
            f"""CALL db.index.fulltext.queryNodes($index, $q, {{limit: $k}}) YIELD node, score
            RETURN node {{ .{', .'.join(RETURN_PROPS)} }} AS n, score""",
            index=FULLTEXT_INDEX, q=_lucene_escape(query), k=k)
        return [{**r["n"], "score": r["score"]} for r in rows]

    # ---- node -------------------------------------------------------------------------------
    def resolve_id(self, id_or_name: str) -> tuple[str | None, list[dict[str, Any]]]:
        rows = self._read(f"MATCH (n:{BASE_LABEL} {{id: $id}}) RETURN n.id AS id", id=id_or_name)
        if not rows and ":" in id_or_name:
            prefix, rest = id_or_name.split(":", 1)
            rows = self._read(f"MATCH (n:{BASE_LABEL} {{id: $id}}) RETURN n.id AS id", id=f"{prefix}:{rest.lower()}")
        if rows:
            return rows[0]["id"], []
        rows = self._read(
            f"""MATCH (n:{BASE_LABEL}) WHERE toLower(n.name) = toLower($q) OR toLower(n.title) = toLower($q)
            RETURN n.id AS id, n.kind AS label, n.name AS name LIMIT 10""", q=id_or_name)
        if len(rows) == 1:
            return rows[0]["id"], []
        if not rows:
            rows = [{"id": r["id"], "label": r.get("kind"), "name": r.get("name")} for r in self._fulltext(id_or_name, 5)]
        return None, rows

    def get_node(self, id: str, detail: str = "summary") -> dict[str, Any]:
        nid, candidates = self.resolve_id(id)
        if nid is None:
            return {"error": f"no node '{id}'", "candidates": candidates}
        rows = self._read(f"MATCH (n:{BASE_LABEL} {{id: $id}}) RETURN properties(n) AS p", id=nid)
        p = {k: v for k, v in rows[0]["p"].items() if k not in HIDDEN_PROPS}
        if detail == "summary":
            raw = p
            p = {k: _short(raw[k], 400) for k in SUMMARY_PROPS if k in raw}
            for k, v in raw.items():
                if k in p or k in ("code", "doc"):
                    continue
                if isinstance(v, list) and k not in ("events", "columns", "synonyms", "ambiguous_columns", "implements"):
                    continue
                p[k] = _short(v, 200)
            if "doc" in raw:
                p["doc_preview"] = _short(raw["doc"], 600)
            if "code" in raw:
                p["has_code"] = True
        elif detail == "full":
            if "code" in p:
                p["code"] = _short(p["code"], 2500)
        return {"node": p, "hop_hints": self.hop_hints([nid])[nid]}

    # ---- expand -----------------------------------------------------------------------------
    def expand(self, ids: list[str], rel_types: list[str] | None = None, direction: str = "both",
               target_labels: list[str] | None = None, limit: int = 25, cursor: str | None = None) -> dict[str, Any]:
        limit = max(1, min(limit, 100))
        skip = int(cursor) if cursor and cursor.isdigit() else 0
        resolved = [self.resolve_id(i)[0] or i for i in ids]
        pattern = {"out": "-[r]->", "in": "<-[r]-"}.get(direction, "-[r]-")
        rows = self._read(
            f"""UNWIND $ids AS sid
            MATCH (s:{BASE_LABEL} {{id: sid}}){pattern}(t:{BASE_LABEL})
            WHERE ($types IS NULL OR type(r) IN $types) AND ($labels IS NULL OR t.kind IN $labels)
            RETURN sid, type(r) AS rel, CASE WHEN startNode(r) = s THEN 'out' ELSE 'in' END AS dir,
                   properties(r) AS rp, t.id AS id, t.kind AS label, coalesce(t.title, t.name) AS name,
                   t.summary AS summary, t.status AS status
            ORDER BY sid, rel, dir, id SKIP $skip LIMIT $lim""",
            ids=resolved, types=rel_types, labels=target_labels, skip=skip, lim=limit + 1)
        more = len(rows) > limit
        rows = rows[:limit]
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for r in rows:
            key = f"{r['rel']} ({r['dir']})"
            item = {"id": r["id"], "label": r["label"], "name": r["name"], "summary": _short(r["summary"], 160)}
            if r["status"] == "planned":
                item["status"] = "planned"
            rp = {k: _short(v, 160) for k, v in (r["rp"] or {}).items()}
            if rp:
                item["edge"] = rp
            grouped.setdefault(r["sid"], {}).setdefault(key, []).append(item)
        return {"from": resolved, "results": grouped, "returned": len(rows),
                "next_cursor": str(skip + limit) if more else None}

    # ---- paths ------------------------------------------------------------------------------
    def find_paths(self, from_id: str, to_id: str, max_hops: int = 6, rel_types: list[str] | None = None,
                   k: int = 3, exclude_derived: bool = False, avoid_ids: list[str] | None = None) -> dict[str, Any]:
        a, _ = self.resolve_id(from_id)
        b, _ = self.resolve_id(to_id)
        if not a or not b:
            return {"error": f"unknown node: {from_id if not a else to_id}"}
        max_hops = max(1, min(int(max_hops), 8))
        rows = self._read(
            f"""MATCH (a:{BASE_LABEL} {{id: $a}}), (b:{BASE_LABEL} {{id: $b}})
            MATCH p = allShortestPaths((a)-[*..{max_hops}]-(b))
            WHERE all(r IN relationships(p) WHERE ($types IS NULL OR type(r) IN $types)
                      AND NOT coalesce(r.error_handling, false)
                      AND (NOT $exclude_derived OR NOT coalesce(r.derived, false)))
              AND none(n IN nodes(p)[1..-1] WHERE n.id IN $avoid)
            RETURN [n IN nodes(p) | {{id: n.id, label: n.kind, name: coalesce(n.title, n.name)}}] AS nodes,
                   [r IN relationships(p) | {{type: type(r), from: startNode(r).id, to: endNode(r).id}}] AS rels
            LIMIT $k""",
            a=a, b=b, types=rel_types, exclude_derived=exclude_derived, avoid=avoid_ids or [], k=max(1, min(k, 10)),
            timeout=30)
        paths = []
        for r in rows:
            steps = []
            for i, n in enumerate(r["nodes"]):
                steps.append(n)
                if i < len(r["rels"]):
                    rel = r["rels"][i]
                    steps.append({"rel": rel["type"], "dir": "->" if rel["from"] == n["id"] else "<-"})
            paths.append({"length": len(r["rels"]), "steps": steps})
        return {"from": a, "to": b, "paths": paths}

    # ---- similar ----------------------------------------------------------------------------
    def similar(self, id: str, labels: list[str] | None = None, top_k: int = 5) -> dict[str, Any]:
        nid, cands = self.resolve_id(id)
        if not nid:
            return {"error": f"no node '{id}'", "candidates": cands}
        top_k = max(1, min(top_k, 20))
        rows = self._read(
            f"""MATCH (n:{BASE_LABEL} {{id: $id}}) WHERE n.embedding IS NOT NULL
            CALL db.index.vector.queryNodes($index, $pool, n.embedding) YIELD node, score
            WITH node, score WHERE node.id <> $id AND ($labels IS NULL OR node.kind IN $labels)
            RETURN node.id AS id, node.kind AS label, coalesce(node.title, node.name) AS name,
                   node.summary AS summary, score LIMIT $k""",
            id=nid, index=VECTOR_INDEX, pool=top_k * (6 if labels else 2) + 1, labels=labels, k=top_k)
        for r in rows:
            r["summary"] = _short(r["summary"], 200)
            r["score"] = round(r["score"], 4)
        return {"of": nid, "results": rows}

    # ---- cypher -----------------------------------------------------------------------------
    def run_cypher(self, query: str, params: dict[str, Any] | None = None, limit: int = 200) -> dict[str, Any]:
        if WRITE_RE.search(re.sub(r"'[^']*'|\"[^\"]*\"", "", query)):
            return {"error": "read-only: write clauses are not allowed"}
        limit = max(1, min(limit, 1000))
        with self.driver.session(database=self.settings.neo4j_database, default_access_mode=neo4j.READ_ACCESS) as s:
            @neo4j.unit_of_work(timeout=20)
            def work(tx):
                res = tx.run(query, **(params or {}))
                out = []
                for rec in res:
                    out.append({k: _plain(v) for k, v in rec.items()})
                    if len(out) > limit:
                        break
                return out
            try:
                rows = s.execute_read(work)
            except neo4j.exceptions.Neo4jError as ex:
                return {"error": f"{ex.code}: {ex.message}"}
        return {"rows": rows[:limit], "truncated": len(rows) > limit}


def _plain(v: Any) -> Any:
    if isinstance(v, neo4j.graph.Node):
        return {k: _short(x, 300) for k, x in dict(v).items() if k not in HIDDEN_PROPS} | {"_labels": sorted(v.labels)}
    if isinstance(v, neo4j.graph.Relationship):
        return {"_type": v.type, "_from": v.start_node.get("id") if v.start_node else None,
                "_to": v.end_node.get("id") if v.end_node else None, **dict(v)}
    if isinstance(v, neo4j.graph.Path):
        return {"nodes": [_plain(n) for n in v.nodes], "rels": [_plain(r) for r in v.relationships]}
    if isinstance(v, list):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items() if k not in HIDDEN_PROPS}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return _short(v, 2000) if isinstance(v, str) else v
    return json.loads(json.dumps(v, default=str))


def _lucene_escape(q: str) -> str:
    q = LUCENE_SPECIAL.sub(r"\\\1", q)
    return re.sub(r"\b(AND|OR|NOT)\b", lambda m: m.group(0).lower(), q)
