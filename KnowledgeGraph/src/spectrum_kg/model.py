"""In-memory property graph built by the extractors before it is loaded into Neo4j."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable


def norm(s: str) -> str:
    """Case-insensitive key for SQL identifiers."""
    return s.strip().lower()


# ---- stable node ids -------------------------------------------------------------------------
def ui_id(kind: str, name: str) -> str: return f"{'form' if kind == 'Form' else 'usercontrol'}:{name}"
def control_id(owner: str, name: str) -> str: return f"control:{owner}.{name}"
def method_id(owner: str, name: str) -> str: return f"method:{owner}.{name}"
def dtclass_id(name: str) -> str: return f"dtclass:{name}"
def dtprop_id(cls: str, name: str) -> str: return f"dtprop:{cls}.{name}"
def dtmethod_id(cls: str, name: str) -> str: return f"dtmethod:{cls}.{name}"
def daclass_id(name: str) -> str: return f"daclass:{name}"
def damethod_id(cls: str, name: str) -> str: return f"damethod:{cls}.{name}"
def sp_id(qualified: str) -> str: return f"sp:{norm(qualified)}"
def table_id(qualified: str) -> str: return f"table:{norm(qualified)}"
def column_id(table_qualified: str, col: str) -> str: return f"column:{norm(table_qualified)}.{norm(col)}"
def module_id(code: str) -> str: return f"module:{code}"
def process_id(key: str) -> str: return f"process:{key}"
def concept_id(key: str) -> str: return f"concept:{key}"
def rule_id(key: str) -> str: return f"rule:{key}"


@dataclass
class Node:
    id: str
    label: str
    props: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.props.get("name", self.id)


@dataclass
class Edge:
    src: str
    type: str
    dst: str
    props: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.src, self.type, self.dst)


LIST_PROPS = {"source_files", "bundles", "synonyms", "methods", "lines", "columns", "grid_columns", "events", "ops"}


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[tuple[str, str, str], Edge] = {}
        self._name_votes: dict[str, Counter] = {}

    # Nodes merge: scalar props keep the first non-empty value, list props union.
    def add_node(self, id: str, label: str, /, **props: Any) -> Node:
        node = self.nodes.get(id)
        if node is None:
            node = self.nodes[id] = Node(id, label, {})
        _merge(node.props, props)
        return node

    def vote_name(self, id: str, display: str) -> None:
        """Pick the most frequent spelling of a case-insensitive SQL name for display."""
        self._name_votes.setdefault(id, Counter())[display] += 1

    def add_edge(self, src: str, type: str, dst: str, /, **props: Any) -> Edge:
        key = (src, type, dst)
        edge = self.edges.get(key)
        if edge is None:
            edge = self.edges[key] = Edge(src, type, dst, {})
        _merge(edge.props, props)
        return edge

    def finalize_names(self) -> None:
        for id, votes in self._name_votes.items():
            if id in self.nodes:
                # most common spelling; ties broken by preferring mixed case over all-lower
                best = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0] == kv[0].lower(), kv[0]))[0][0]
                self.nodes[id].props["name"] = best

    def out(self, src: str, type: str | None = None) -> Iterable[Edge]:
        return [e for e in self.edges.values() if e.src == src and (type is None or e.type == type)]

    def inc(self, dst: str, type: str | None = None) -> Iterable[Edge]:
        return [e for e in self.edges.values() if e.dst == dst and (type is None or e.type == type)]

    def by_label(self, label: str) -> list[Node]:
        return [n for n in self.nodes.values() if n.label == label]

    def dangling_edges(self) -> list[Edge]:
        return [e for e in self.edges.values() if e.src not in self.nodes or e.dst not in self.nodes]

    def to_json(self) -> dict[str, Any]:
        return {
            # node type is `kind`; `label` is reserved for a property (a control's on-screen caption)
            "nodes": [{"id": n.id, **{k: v for k, v in n.props.items() if k != "kind"}, "kind": n.label}
                      for n in sorted(self.nodes.values(), key=lambda n: n.id)],
            "edges": [{"src": e.src, "type": e.type, "dst": e.dst, **e.props}
                      for e in sorted(self.edges.values(), key=lambda e: e.key)],
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Graph":
        """Inverse of to_json(): rebuild a graph written by `kg build --dry-run` (or a build on another machine)."""
        g = cls()
        for rec in data["nodes"]:
            props = {k: v for k, v in rec.items() if k != "id"}   # `kind` stays a prop too, as enrich() sets it
            g.nodes[rec["id"]] = Node(rec["id"], rec["kind"], props)
        for rec in data["edges"]:
            e = Edge(rec["src"], rec["type"], rec["dst"], {k: v for k, v in rec.items() if k not in ("src", "type", "dst")})
            g.edges[e.key] = e
        return g

    def stats(self) -> dict[str, dict[str, int]]:
        return {
            "nodes": dict(sorted(Counter(n.label for n in self.nodes.values()).items())),
            "edges": dict(sorted(Counter(e.type for e in self.edges.values()).items())),
        }


def _merge(target: dict[str, Any], props: dict[str, Any]) -> None:
    for k, v in props.items():
        if v is None or v == "" or v == []:
            continue
        if k in LIST_PROPS or isinstance(v, list):
            cur = target.get(k) or []
            vals = v if isinstance(v, list) else [v]
            for item in vals:
                if item not in cur:
                    cur.append(item)
            target[k] = cur
        elif k not in target or target[k] in (None, "", []):
            target[k] = v


def content_hash(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(json.dumps(p, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]
