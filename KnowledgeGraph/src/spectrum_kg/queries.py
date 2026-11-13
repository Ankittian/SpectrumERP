"""Read-only graph primitives used by the MCP server (agentic RAG: the client chooses the hops)."""
from __future__ import annotations

import json
import re
from typing import Any

import neo4j
from neo4j_graphrag.embeddings.base import Embedder
from neo4j_graphrag.retrievers import HybridRetriever, VectorRetriever

from .comments import guess_language, strip_comments
from .config import Settings
from .load import BASE_LABEL, FULLTEXT_INDEX, VECTOR_INDEX
from .schema import LABELS, RELATIONSHIPS, RESPONSE_RULES, STRATEGIES, TIPS

HIDDEN_PROPS = {"embedding", "embedding_hash", "text", "comments"}
SUMMARY_PROPS = ["id", "kind", "name", "title", "summary", "status", "modules"]
CODE_META_PROPS = ["id", "kind", "name", "title", "owner", "method", "method_kind", "file", "start_line", "status"]
LUCENE_SPECIAL = re.compile(r'([+\-&|!(){}\[\]^"~*?:\\/])')
WRITE_RE = re.compile(r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH)\b|\bCALL\s+(apoc\.(create|merge|refactor|periodic)|db\.create|dbms)", re.I)
MAX_FILTER_POOL = 500
RETURN_PROPS = ["id", "kind", "name", "title", "summary", "modules", "status"]

# Response-size profiles. "compact" is the default: it keeps the same fields and hints but uses smaller fan-out,
# so a client that needs more asks for "standard" or "detailed" explicitly. Pagination (expand cursor, code cursor)
# keeps smaller defaults from hiding results.
PROFILES: dict[str, dict[str, int]] = {
    # compact_hints=1: hop hints use the short [count, labels] shape; labels are trimmed to hint_labels.
    "compact":  {"search_top_k": 5, "similar_top_k": 3, "expand_limit": 10, "cypher_limit": 50,
                 "summary_chars": 160, "compact_hints": 1, "hint_labels": 4,
                 "cypher_str_chars": 500, "cypher_max_chars": 12000, "code_chars": 6000},
    "standard": {"search_top_k": 8, "similar_top_k": 5, "expand_limit": 25, "cypher_limit": 200,
                 "summary_chars": 220, "compact_hints": 0, "hint_labels": 99,
                 "cypher_str_chars": 2000, "cypher_max_chars": 40000, "code_chars": 12000},
    "detailed": {"search_top_k": 15, "similar_top_k": 10, "expand_limit": 50, "cypher_limit": 500,
                 "summary_chars": 400, "compact_hints": 0, "hint_labels": 99,
                 "cypher_str_chars": 4000, "cypher_max_chars": 120000, "code_chars": 30000},
}
DEFAULT_PROFILE = "compact"


def profile(name: str | None) -> dict[str, int]:
    return PROFILES.get(name or DEFAULT_PROFILE, PROFILES[DEFAULT_PROFILE])


def shape_hints(hints: dict[str, Any] | None, p: dict[str, int]) -> dict[str, Any] | None:
    """Standard shape {REL: {count, labels}} or, for compact profiles, {REL: [count, labels]}."""
    if not p["compact_hints"] or not hints:
        return hints
    return {d: {rel: [v["count"], v["labels"][: p["hint_labels"]]] for rel, v in hints[d].items()}
            for d in ("out", "in") if hints.get(d)}


def _short(s: Any, n: int = 220) -> Any:
    if isinstance(s, str) and len(s) > n:
        return s[: n - 1] + "…"
    return s


def bound_code(code: str, cursor: str | None, max_chars: int) -> dict[str, Any]:
    """Return one bounded slice of code plus paging metadata (character offsets)."""
    start = int(cursor) if cursor and cursor.isdigit() else 0
    chunk = code[start:start + max_chars]
    end = start + len(chunk)
    more = end < len(code)
    return {"code": chunk, "code_chars": len(code), "returned_chars": len(chunk),
            "truncated": more, "next_cursor": str(end) if more else None}


def bound_rows(rows: list[dict[str, Any]], limit: int, max_chars: int) -> dict[str, Any]:
    """Apply the row cap and a total serialized-size cap; report what was cut so nothing is silent.
    `rows` may hold one extra row beyond `limit` (the caller's look-ahead), which marks row truncation."""
    kept: list[dict[str, Any]] = []
    size = 0
    reason = "row_limit" if len(rows) > limit else None
    for r in rows[:limit]:
        s = len(json.dumps(r, default=str, ensure_ascii=False))
        if size + s > max_chars and kept:
            reason = "size_limit"
            break
        kept.append(r)
        size += s
    truncated = reason is not None or len(rows) > len(kept)
    return {"rows": kept, "returned": len(kept), "truncated": truncated,
            "truncated_reason": reason if truncated else None}


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
            "response_rules": RESPONSE_RULES,
            "hop_hints_format": "standard/detailed: {REL: {count, labels}}; compact: {REL: [count, labels]} (labels trimmed)",
            "profiles": PROFILES,
        }

    # ---- search -----------------------------------------------------------------------------
    def search(self, query: str, mode: str = "hybrid", labels: list[str] | None = None, module: str | None = None,
               top_k: int | None = None, prof: str | None = None) -> dict[str, Any]:
        p = profile(prof)
        top_k = max(1, min(top_k or p["search_top_k"], 30))
        filtered = bool(labels or module)
        pool = top_k * (6 if filtered else 2)
        vec = self.embedder.embed_query(query) if mode != "fulltext" else None

        def fetch(n: int) -> list[dict[str, Any]]:
            if mode == "fulltext":
                return self._fulltext(query, n)
            if mode == "vector":
                r = VectorRetriever(self.driver, VECTOR_INDEX, return_properties=RETURN_PROPS,
                                    neo4j_database=self.settings.neo4j_database)
                res = r.get_search_results(query_vector=vec, top_k=n)
            else:
                r = HybridRetriever(self.driver, VECTOR_INDEX, FULLTEXT_INDEX, return_properties=RETURN_PROPS,
                                    neo4j_database=self.settings.neo4j_database)
                res = r.get_search_results(query_text=_lucene_escape(query), query_vector=vec, top_k=n)
            return [{**(dict(rec["node"]) if not isinstance(rec["node"], dict) else rec["node"]), "score": rec["score"]}
                    for rec in res.records]

        def keep(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
            out_ = []
            for r in rows:
                if labels and r.get("kind") not in labels:
                    continue
                if module and module not in (r.get("modules") or []):
                    continue
                out_.append(r)
                if len(out_) >= top_k:
                    break
            return out_

        # Label/module filters are applied after retrieval, so widen the pool until enough rows survive
        # (a fixed pool starves rare labels: 30 column hits can leave zero Forms).
        rows = fetch(pool)
        out = keep(rows)
        while filtered and len(out) < top_k and len(rows) >= pool and pool < MAX_FILTER_POOL:
            pool = min(pool * 4, MAX_FILTER_POOL)
            rows = fetch(pool)
            out = keep(rows)
        hints = self.hop_hints([r["id"] for r in out]) if out else {}
        results = []
        for r in out:
            item = {"id": r["id"], "label": r.get("kind"), "name": r.get("title") or r.get("name"),
                    "score": round(float(r.get("score") or 0), 4),
                    "summary": _short(r.get("summary"), p["summary_chars"]),
                    "hop_hints": shape_hints(hints.get(r["id"]), p)}
            if r.get("status"):
                item["status"] = r["status"]
            results.append(item)
        return {"query": query, "mode": mode, "profile": prof or DEFAULT_PROFILE, "results": results}

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

    def get_node(self, id: str, detail: str = "summary", prof: str | None = None, cursor: str | None = None,
                 max_chars: int | None = None) -> dict[str, Any]:
        nid, candidates = self.resolve_id(id)
        if nid is None:
            return {"error": f"no node '{id}'", "candidates": candidates}
        rows = self._read(f"MATCH (n:{BASE_LABEL} {{id: $id}}) RETURN properties(n) AS p", id=nid)
        p = {k: v for k, v in rows[0]["p"].items() if k not in HIDDEN_PROPS}
        # Source-code comments are never served: drop the SP header "Description:" and strip comments from code.
        if p.get("kind") == "StoredProcedure":
            p.pop("description", None)
        if p.get("code"):
            p["code"] = strip_comments(str(p["code"]), guess_language(p.get("kind"), p))
        if detail == "code":
            # Code only, one bounded page per call. No hop hints: the client already chose this node.
            limit = max(500, min(max_chars or profile(prof)["code_chars"], 60000))
            meta = {k: p[k] for k in CODE_META_PROPS if k in p}
            return {"node": meta, **bound_code(str(p.get("code") or ""), cursor, limit)}
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
                p["code_chars"] = len(str(p["code"]))
                p["code_truncated"] = p["code_chars"] > 2500
                p["code"] = _short(p["code"], 2500)
        return {"node": p, "hop_hints": self.hop_hints([nid])[nid]}

    # ---- expand -----------------------------------------------------------------------------
    def expand(self, ids: list[str], rel_types: list[str] | None = None, direction: str = "both",
               target_labels: list[str] | None = None, limit: int | None = None, cursor: str | None = None,
               prof: str | None = None) -> dict[str, Any]:
        limit = max(1, min(limit or profile(prof)["expand_limit"], 100))
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
        return {"from": resolved, "results": grouped, "returned": len(rows), "truncated": more,
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
    def similar(self, id: str, labels: list[str] | None = None, top_k: int | None = None,
                prof: str | None = None) -> dict[str, Any]:
        nid, cands = self.resolve_id(id)
        if not nid:
            return {"error": f"no node '{id}'", "candidates": cands}
        top_k = max(1, min(top_k or profile(prof)["similar_top_k"], 20))
        rows = self._read(
            f"""MATCH (n:{BASE_LABEL} {{id: $id}}) WHERE n.embedding IS NOT NULL
            CALL db.index.vector.queryNodes($index, $pool, n.embedding) YIELD node, score
            WITH node, score WHERE node.id <> $id AND ($labels IS NULL OR node.kind IN $labels)
            RETURN node.id AS id, node.kind AS label, coalesce(node.title, node.name) AS name,
                   node.summary AS summary, score LIMIT $k""",
            id=nid, index=VECTOR_INDEX, pool=top_k * (30 if labels else 2) + 1, labels=labels, k=top_k)
        for r in rows:
            r["summary"] = _short(r["summary"], 200)
            r["score"] = round(r["score"], 4)
        return {"of": nid, "results": rows}

    # ---- cypher -----------------------------------------------------------------------------
    def run_cypher(self, query: str, params: dict[str, Any] | None = None, limit: int | None = None,
                   prof: str | None = None) -> dict[str, Any]:
        if WRITE_RE.search(re.sub(r"'[^']*'|\"[^\"]*\"", "", query)):
            return {"error": "read-only: write clauses are not allowed"}
        p = profile(prof)
        limit = max(1, min(limit or p["cypher_limit"], 1000))
        with self.driver.session(database=self.settings.neo4j_database, default_access_mode=neo4j.READ_ACCESS) as s:
            @neo4j.unit_of_work(timeout=20)
            def work(tx):
                res = tx.run(query, **(params or {}))
                out = []
                for rec in res:  # look one row past the limit so bound_rows can report truncation
                    out.append({k: _plain(v, p["cypher_str_chars"]) for k, v in rec.items()})
                    if len(out) > limit:
                        break
                return out
            try:
                rows = s.execute_read(work)
            except neo4j.exceptions.Neo4jError as ex:
                return {"error": f"{ex.code}: {ex.message}"}
        return bound_rows(rows, limit, p["cypher_max_chars"])


def _plain(v: Any, str_chars: int = 2000) -> Any:
    """Convert driver values to JSON-friendly data. String limits apply at every depth."""
    if isinstance(v, neo4j.graph.Node):
        return {k: _short(x, min(300, str_chars)) for k, x in dict(v).items() if k not in HIDDEN_PROPS} | {"_labels": sorted(v.labels)}
    if isinstance(v, neo4j.graph.Relationship):
        return {"_type": v.type, "_from": v.start_node.get("id") if v.start_node else None,
                "_to": v.end_node.get("id") if v.end_node else None, **dict(v)}
    if isinstance(v, neo4j.graph.Path):
        return {"nodes": [_plain(n, str_chars) for n in v.nodes], "rels": [_plain(r, str_chars) for r in v.relationships]}
    if isinstance(v, list):
        return [_plain(x, str_chars) for x in v]
    if isinstance(v, dict):
        return {k: _plain(x, str_chars) for k, x in v.items() if k not in HIDDEN_PROPS}
    if isinstance(v, (str, int, float, bool)) or v is None:
        return _short(v, str_chars) if isinstance(v, str) else v
    return json.loads(json.dumps(v, default=str))


def _lucene_escape(q: str) -> str:
    q = LUCENE_SPECIAL.sub(r"\\\1", q)
    return re.sub(r"\b(AND|OR|NOT)\b", lambda m: m.group(0).lower(), q)
