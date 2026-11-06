"""Text for search/embedding per node (role + graph context + doc/code) and the Voyage AI embedder."""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from .model import Graph, Node

CODE_CHARS = int(os.getenv("EMBED_CODE_CHARS", "3000"))   # code in embedded text (full code stays in `code`)
DOC_CHARS = 4000


class _Index:
    def __init__(self, g: Graph):
        self.g = g
        self.out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        self.inc: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for e in g.edges.values():
            self.out[e.src][e.type].append(e)
            self.inc[e.dst][e.type].append(e)

    def names(self, edges: list, end: str = "dst", limit: int = 12) -> str:
        vals = []
        for e in edges:
            n = self.g.nodes.get(getattr(e, end))
            if n:
                vals.append(n.props.get("title") or n.props.get("name", n.id))
        vals = sorted(set(vals))
        more = f" (+{len(vals) - limit} more)" if len(vals) > limit else ""
        return ", ".join(vals[:limit]) + more

    def owner_title(self, owner: str) -> str:
        for pid in (f"form:{owner}", f"usercontrol:{owner}"):
            n = self.g.nodes.get(pid)
            if n:
                t = n.props.get("title")
                return f"{owner} ({t})" if t and t != owner else owner
        return owner


def assign_modules(g: Graph, ix: "_Index") -> None:
    """Stamp `modules` on every node (from its form / the forms that reach it) so search can filter by module."""
    mods: dict[str, set[str]] = defaultdict(set)
    for n in g.nodes.values():
        if n.props.get("module"):
            mods[n.id].add(n.props["module"])
        if n.label == "Module":
            mods[n.id].add(n.props["code"])
    for n in g.nodes.values():
        if n.label in ("FormMethod", "Control"):
            for pid in (f"form:{n.props['owner']}", f"usercontrol:{n.props['owner']}"):
                mods[n.id] |= mods.get(pid, set())
    for e in g.edges.values():
        if e.type in ("CALLS_SP", "USES_TABLE"):
            mods[e.dst] |= mods.get(e.src, set())
    # SP -> params/result sets; table -> columns; DA/DT methods -> via EXECUTES / DELEGATES_TO
    for _ in range(2):
        for e in g.edges.values():
            if e.type in ("HAS_PARAM", "RETURNS", "HAS_COLUMN"):
                mods[e.dst] |= mods[e.src]
            elif e.type in ("EXECUTES", "DELEGATES_TO"):
                mods[e.src] |= mods[e.dst]
            elif e.type in ("HAS_METHOD", "HAS_PROPERTY") and g.nodes[e.src].label in ("DTClass", "DAClass"):
                mods[e.src] |= mods[e.dst]
                mods[e.dst] |= mods[e.src]
    for nid, m in mods.items():
        if m and nid in g.nodes:
            g.nodes[nid].props["modules"] = sorted(m)


def enrich(g: Graph) -> None:
    """Set `summary` (if missing), `modules`, `kind` and `text` (search/embedding text) on every node."""
    ix = _Index(g)
    assign_modules(g, ix)
    for n in g.nodes.values():
        summary, context = _describe(n, ix)
        if summary and not n.props.get("summary"):
            n.props["summary"] = summary
        body = n.props.get("doc") or ""
        code = n.props.get("code") or ""
        parts = [f"[{n.label}] {n.props.get('title') or n.props.get('name', n.id)}"]
        if n.props.get("synonyms"):
            parts.append("Also known as: " + ", ".join(n.props["synonyms"]))
        if n.props.get("summary"):
            parts.append(n.props["summary"])
        parts += [c for c in context if c and not re.fullmatch(r"[^:]*:\s*(;[^:]*:\s*)?", c)]
        if body:
            parts.append(body[:DOC_CHARS])
        if code:
            parts.append("Code:\n" + code[:CODE_CHARS])
        n.props["text"] = "\n".join(parts)
        n.props["kind"] = n.label


def _describe(n: Node, ix: _Index) -> tuple[str | None, list[str]]:
    p, o, i, L = n.props, ix.out[n.id], ix.inc[n.id], n.label
    if L == "Module":
        return None, [f"Processes: {ix.names(o['HAS_PROCESS'])}", f"Forms: {ix.names(o['HAS_FORM'])}"]
    if L == "BusinessProcess":
        return None, [f"Module: {p.get('module')}", f"Concepts: {ix.names(o['INVOLVES'])}",
                      f"Leads to: {ix.names(o['LEADS_TO'])}", f"Rules: {ix.names(i['GOVERNS'], 'src')}"]
    if L == "BusinessConcept":
        return None, [f"Maintained in forms: {ix.names(i['MANAGES'], 'src')}",
                      f"Used by forms: {ix.names(i['USES_CONCEPT'], 'src')}",
                      f"Part of: {ix.names(i['PARENT_OF'], 'src')}; contains: {ix.names(o['PARENT_OF'])}",
                      f"Stored in tables: {ix.names(o['PERSISTED_IN'])}", f"Rules: {ix.names(i['APPLIES_TO'], 'src')}"]
    if L == "BusinessRule":
        return None, [f"Applies to: {ix.names(o['APPLIES_TO'])}", f"Implemented by: {ix.names(o['IMPLEMENTED_BY'])}"]
    if L in ("Form", "UserControl"):
        steps = ", ".join(sorted({f"{ix.g.nodes[e.src].props['name']} (step {e.props.get('order')})" for e in i["HAS_STEP"]}))
        s = None if p.get("status") != "planned" else f"Planned form (not built yet): {p.get('title') or p['name']}."
        return s, [f"Business processes: {steps}", f"Manages: {ix.names(o['MANAGES'])}",
                   f"Stored procedures: {ix.names(o['CALLS_SP'], limit=20)}",
                   f"Tables: {ix.names([e for e in o['USES_TABLE']], limit=20)}",
                   f"Embeds: {ix.names(o['EMBEDS'])}" if o["EMBEDS"] else "",
                   f"Embedded in: {ix.names(i['EMBEDS'], 'src')}" if i["EMBEDS"] else ""]
    if L == "FormMethod":
        owner = ix.owner_title(p["owner"])
        sps = set()
        for inv in o["INVOKES"]:
            for d in ix.out[inv.dst]["DELEGATES_TO"]:
                for ex in ix.out[d.dst]["EXECUTES"]:
                    sps.add(ix.g.nodes[ex.dst].props["name"])
        ev = f", handles {', '.join(p['events'])}" if p.get("events") else ""
        impl = f", implements {', '.join(p['implements'])}" if p.get("implements") else ""
        s = f"{p.get('method_kind', 'method').capitalize()} method {p['method']} of {owner}{ev}{impl}." + (
            f" Executes: {', '.join(sorted(sps))}." if sps else "")
        return s, [f"Calls: {ix.names(o['CALLS'])}", f"Controls used: {ix.names(o['REFERENCES'], limit=15)}"]
    if L == "Control":
        owner = ix.owner_title(p["owner"])
        bits = [f"{p['type']} '{p['control']}' on {owner}"]
        if p.get("label"): bits.append(f"label '{p['label']}'")
        if p.get("tab"): bits.append(f"tab '{p['tab']}'")
        if p.get("mandatory"): bits.append("mandatory")
        if p.get("max_length"): bits.append(f"max length {p['max_length']}")
        return ", ".join(bits) + ".", [
            f"Saved via: {ix.names(o['BINDS_TO'])}", f"Handled events: {ix.names(i['HANDLES'], 'src')}",
            f"Used in methods: {ix.names(i['REFERENCES'], 'src', limit=15)}"]
    if L in ("DTClass", "DAClass"):
        return f"{'Data-transfer' if L == 'DTClass' else 'Data-access'} class {p['name']}.", [f"Methods: {ix.names(o['HAS_METHOD'], limit=30)}"]
    if L == "DTMethod":
        return f"DT method {p['name']}; called by {ix.names(i['INVOKES'], 'src')}.", [f"Delegates to: {ix.names(o['DELEGATES_TO'])}"]
    if L == "DAMethod":
        return f"DA method {p['name']} executing {ix.names(o['EXECUTES'])}.", [f"Parameters from: {ix.names(o['PASSES'], limit=30)}"]
    if L == "DTProperty":
        return f"Property {p['property']} ({p.get('type')}) of {p['class_name']}.", [
            f"Set from controls: {ix.names(i['BINDS_TO'], 'src')}",
            "Passed as SP parameters: " + ", ".join(sorted({f"{e.props.get('param')} of {ix.names(ix.out[e.src]['EXECUTES'])}"
                                                          for e in i['PASSES']}))]
    if L == "StoredProcedure":
        forms = ix.names(i["CALLS_SP"], "src")
        w = [e for e in o["WRITES"] if not e.props.get("error_handling")]
        s = f"Stored procedure {p['name']}" + (f": {p['description']}" if p.get("description") else "") + (
            f". Called from {forms}." if forms else ".")
        return s, [f"Writes: {ix.names(w, limit=20)}", f"Reads: {ix.names(o['READS'], limit=25)}",
                   f"Parameters: {', '.join(p.get('parameters') or [])}",
                   f"Parameters never sent by the data layer (SQL default applies): {', '.join(p.get('params_not_passed') or [])}",
                   f"Calls procedures: {ix.names(o['CALLS_SP'])}",
                   f"Rules: {ix.names(i['IMPLEMENTED_BY'], 'src')}",
                   f"Author: {p.get('author')}, created {p.get('created')}" if p.get("author") else ""]
    if L == "Table":
        w = [e for e in i["WRITES"] if not e.props.get("error_handling")]
        return f"Table {p['name']}.", [
            f"Business concept: {ix.names(i['PERSISTED_IN'], 'src')}", f"Used by forms: {ix.names(i['USES_TABLE'], 'src')}",
            f"Written by: {ix.names(w, 'src', limit=20)}", f"Read by: {ix.names(i['READS'], 'src', limit=20)}",
            f"Columns: {', '.join(sorted(ix.g.nodes[e.dst].props['column'] for e in o['HAS_COLUMN']))}"]
    if L == "Column":
        return f"Column {p['column']} of table {p['table']}.", [
            f"Used by: {ix.names(i['USES_COLUMN'], 'src', limit=20)}",
            f"Rules: {ix.names(i['IMPLEMENTED_BY'], 'src')}"]
    return None, []


# --------------------------------------------------------------------------------------------
def text_hash(text: str, model: str, dims: int) -> str:
    return hashlib.sha256(f"{model}|{dims}|{text}".encode()).hexdigest()[:24]


class VoyageEmbedderCache:
    """Embeds texts with Voyage AI, caching vectors on disk by (model, dims, text) hash."""

    def __init__(self, api_key: str, model: str, dims: int, cache_dir: Path):
        import voyageai
        self.client = voyageai.Client(api_key=api_key, max_retries=0)  # retries/pacing handled in _run
        self.model, self.dims = model, dims
        # Per-request token budget and minimum seconds between requests. Defaults suit paid accounts; on the first
        # free-tier rate-limit error (3 RPM / 10K TPM) they switch to 9K tokens per request, one request per minute.
        free = os.getenv("VOYAGE_FREE_TIER", "1") != "0"   # default: assume the free tier (3 RPM / 10K TPM)
        self.batch_tokens = int(os.getenv("VOYAGE_BATCH_TOKENS", "9000" if free else "90000"))
        self.min_interval = float(os.getenv("VOYAGE_MIN_INTERVAL", "61" if free else "0"))
        self._last_call = 0.0
        self._rate_limited = 0
        self.path = cache_dir / f"embeddings-{model}-{dims}.jsonl"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, list[float]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.cache[rec["h"]] = rec["v"]

    def embed_documents(self, texts: list[str], progress=None, max_tokens: int | None = None) -> list[list[float] | None]:
        """Embed `texts` in the given order. With `max_tokens`, stop once that many (estimated) tokens were sent;
        texts not embedded come back as None and are picked up by the next run (vectors are cached on disk)."""
        hashes = [text_hash(t, self.model, self.dims) for t in texts]
        todo = [(h, t) for h, t in dict(zip(hashes, texts)).items() if h not in self.cache]
        queue = list(todo)
        done = 0
        spent = 0
        while queue:
            if max_tokens is not None and spent >= max_tokens:
                break
            batch: list[tuple[str, str]] = []
            budget = 0
            while queue and len(batch) < 64:
                est = len(queue[0][1]) // 3 + 1
                if batch and budget + est > self.batch_tokens:
                    break
                batch.append(queue.pop(0))
                budget += est
            if self._run(batch):
                done += len(batch)
                spent += budget
                if progress:
                    progress(done, len(todo))
            else:
                queue = batch + queue          # retry with the (now smaller) budget
        return [self.cache.get(h) for h in hashes]

    def pending(self, texts: list[str]) -> int:
        return len({text_hash(t, self.model, self.dims) for t in texts} - self.cache.keys())

    def _run(self, batch: list[tuple[str, str]]) -> bool:
        """Embed one request. Returns False after a rate limit (budget/pacing adjusted, caller re-queues)."""
        import voyageai
        wait = self.min_interval - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        try:
            res = self.client.embed([t for _, t in batch], model=self.model, input_type="document",
                                    output_dimension=self.dims, truncation=True)
        except voyageai.error.RateLimitError as ex:
            self._last_call = time.time()
            self._rate_limited += 1
            if self._rate_limited > 60:
                raise
            msg = str(ex)
            if "3 RPM" in msg or "10K TPM" in msg:     # free tier without payment method
                self.batch_tokens = min(self.batch_tokens, 9000)
                self.min_interval = max(self.min_interval, 61.0)
            else:
                self.batch_tokens = max(2000, self.batch_tokens // 2)
                self.min_interval = max(self.min_interval, 20.0)
            return False
        except (voyageai.error.APIConnectionError, voyageai.error.Timeout, voyageai.error.ServiceUnavailableError, voyageai.error.ServerError) as ex:
            # network blip / transient server error: back off and let the caller re-queue the batch
            self._last_call = time.time()
            self._net_errors = getattr(self, "_net_errors", 0) + 1
            if self._net_errors > 30:
                raise
            time.sleep(min(300, 15 * self._net_errors))
            return False
        self._last_call = time.time()
        with self.path.open("a", encoding="utf-8") as f:
            for (h, _), v in zip(batch, res.embeddings):
                self.cache[h] = v
                f.write(json.dumps({"h": h, "v": v}) + "\n")
        return True

    def embed_query(self, text: str) -> list[float]:
        return self.client.embed([text], model=self.model, input_type="query", output_dimension=self.dims).embeddings[0]


# Embedding order for budgeted / scheduled runs: functional + entry-point nodes first, fine-grained code last.
TIERS = [
    ["Module", "BusinessProcess", "BusinessConcept", "BusinessRule", "Form", "UserControl", "Table"],
    ["StoredProcedure", "FormMethod"],
    ["DAMethod", "Control", "Column", "DTMethod", "DTProperty", "DTClass", "DAClass"],
]
_RANK = {label: i for i, labels in enumerate(TIERS) for label in labels}


def embed_order(g: Graph) -> list[str]:
    """Node ids sorted by tier, then label, then id."""
    return sorted(g.nodes, key=lambda i: (_RANK.get(g.nodes[i].label, len(TIERS)), g.nodes[i].label, i))


QUERY_TASK = ("Given a question about the SpectrumERP ERP codebase or its business processes, retrieve the relevant "
              "forms, code, stored procedures, tables, columns and business rules")


def _pick_device() -> str:
    import torch
    return os.getenv("LOCAL_EMBEDDING_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")


def load_local_model(model: str, dims: int, max_seq: int | None = None):
    import torch
    from sentence_transformers import SentenceTransformer
    device = _pick_device()
    kwargs = {"torch_dtype": torch.float16} if device == "cuda" else {}
    m = SentenceTransformer(model, device=device, truncate_dim=dims, model_kwargs=kwargs, tokenizer_kwargs={"padding_side": "left"})
    m.max_seq_length = max_seq or int(os.getenv("LOCAL_EMBEDDING_MAX_TOKENS", "1024"))
    return m


class LocalEmbedderCache:
    """Embeds texts with a local sentence-transformers model (default Qwen3-Embedding-0.6B), cached on disk by hash.

    Same interface as VoyageEmbedderCache. No rate limits: texts are embedded in chunks and each chunk is appended to the
    cache, so an interrupted run loses at most one chunk."""

    flush_tokens = 150_000      # estimated tokens between Neo4j flushes in `kg embed-step`
    CHUNK = 128

    def __init__(self, model: str, dims: int, cache_dir: Path):
        self.model_name, self.model, self.dims = model, None, dims
        self.path = cache_dir / f"embeddings-{model.replace('/', '_')}-{dims}.jsonl"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, list[float]] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.cache[rec["h"]] = rec["v"]

    def _model(self):
        if self.model is None:
            self.model = load_local_model(self.model_name, self.dims)
        return self.model

    def pending(self, texts: list[str]) -> int:
        return len({text_hash(t, self.model_name, self.dims) for t in texts} - self.cache.keys())

    def embed_documents(self, texts: list[str], progress=None, max_tokens: int | None = None) -> list[list[float] | None]:
        hashes = [text_hash(t, self.model_name, self.dims) for t in texts]
        todo = [(h, t) for h, t in dict(zip(hashes, texts)).items() if h not in self.cache]
        done = spent = 0
        for k in range(0, len(todo), self.CHUNK):
            if max_tokens is not None and spent >= max_tokens:
                break
            part = todo[k:k + self.CHUNK]
            vecs = self._model().encode([t for _, t in part], batch_size=int(os.getenv("LOCAL_EMBEDDING_BATCH", "16")),
                                        normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
            with self.path.open("a", encoding="utf-8") as f:
                for (h, _), v in zip(part, vecs):
                    self.cache[h] = [round(float(x), 6) for x in v]
                    f.write(json.dumps({"h": h, "v": self.cache[h]}) + "\n")
            done += len(part)
            spent += sum(len(t) // 3 + 1 for _, t in part)
            if progress:
                progress(done, len(todo))
        return [self.cache.get(h) for h in hashes]

    def embed_query(self, text: str) -> list[float]:
        return encode_query(self._model(), text)


def encode_query(model, text: str) -> list[float]:
    """Queries get the model's instruction prefix; documents are embedded as-is."""
    v = model.encode([text], prompt=f"Instruct: {QUERY_TASK}\nQuery:", normalize_embeddings=True, convert_to_numpy=True)[0]
    return [float(x) for x in v]


def make_embedder(settings):
    """Document embedder (with on-disk cache) for the configured provider."""
    if settings.embedding_provider == "local":
        return LocalEmbedderCache(settings.embedding_model, settings.embedding_dims, settings.cache_dir)
    return VoyageEmbedderCache(settings.voyage_api_key, settings.voyage_model, settings.embedding_dims, settings.cache_dir)


def node_texts(g: Graph) -> dict[str, str]:
    return {n.id: n.props["text"] for n in g.nodes.values()}


def sanitize(props: dict[str, Any]) -> dict[str, Any]:
    """Neo4j properties: primitives or homogeneous lists only."""
    out: dict[str, Any] = {}
    for k, v in props.items():
        if v is None or v == [] or v == "":
            continue
        if isinstance(v, dict):
            out[k] = json.dumps(v)
        elif isinstance(v, (list, tuple)):
            vals = [x for x in v if x is not None]
            if vals and len({type(x) for x in vals}) > 1:
                vals = [str(x) for x in vals]
            if vals:
                out[k] = list(vals)
        else:
            out[k] = v
    return out
