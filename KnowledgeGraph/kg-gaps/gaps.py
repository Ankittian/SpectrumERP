"""KG gap log tool.

    python kg-gaps/gaps.py check     validate kg_gaps.yaml (schema, ids, cross references); exit 1 on errors
    python kg-gaps/gaps.py render    check, then write KG_GAP_LOG.md and kg_gaps.csv next to the YAML
    python kg-gaps/gaps.py list [status]   one line per gap (optionally only one status)

Source of truth is kg_gaps.yaml. Needs only PyYAML (a project dependency).
Domain ids (form/concept/rule/process/module) are checked offline against ../domain/*.yaml;
sp/table/column/method ids are format-checked only (a live check needs Neo4j).
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DOMAIN = HERE.parent / "domain"
SRC = HERE / "kg_gaps.yaml"

STATUSES = {"open", "in-progress", "fixed", "noted"}
LAYERS = {"A": "extraction", "B": "functional (YAML)", "C": "cross-layer links", "D": "doc quality"}
TYPES = {"missing-node", "missing-edge", "wrong-edge", "missing-doc", "stale", "ambiguous", "answer-quality"}
REQUIRED = ["id", "title", "status", "layer", "type", "found", "found_by", "nodes", "evidence", "fix"]
ID_RE = re.compile(r"^G-\d{3,}$")
NODE_RE = re.compile(r"^(form|usercontrol|concept|rule|process|module|sp|table|column|method|control|"
                     r"dtclass|dtprop|dtmethod|daclass|damethod):\S+$")
SQL_KINDS = {"sp", "table", "column"}


def load(path: Path):
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def domain_ids() -> dict[str, set[str]]:
    ids: dict[str, set[str]] = {k: set() for k in ("form", "concept", "rule", "process", "module")}
    for p in (DOMAIN / "forms").glob("*.yaml"):
        d = load(p) or {}
        if d.get("form"):
            ids["form"].add(str(d["form"]))
    for p in (DOMAIN / "processes").glob("*.yaml"):
        d = load(p) or {}
        if d.get("key"):
            ids["process"].add(str(d["key"]))
    for name, key, bucket in (("concepts.yaml", "concepts", "concept"), ("rules.yaml", "rules", "rule")):
        p = DOMAIN / name
        if p.exists():
            for item in (load(p) or {}).get(key, []):
                ids[bucket].add(str(item["key"]))
    p = DOMAIN / "modules.yaml"
    if p.exists():
        for m in (load(p) or {}).get("modules", []):
            ids["module"].add(str(m["code"]))
    return ids


def check(doc) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    known = domain_ids()
    gaps = doc.get("gaps") or []
    seen: set[str] = set()

    def check_node(owner: str, node: str):
        if not isinstance(node, str) or not NODE_RE.match(node):
            errors.append(f"{owner}: bad node id {node!r}")
            return
        kind, _, key = node.partition(":")
        if kind in SQL_KINDS and key != key.lower():
            errors.append(f"{owner}: SQL ids must be lowercase: {node}")
        if kind in known:
            if kind == "rule" and key.startswith("shared-write-"):
                return  # auto-generated rules, not in domain/rules.yaml
            if key not in known[kind]:
                warnings.append(f"{owner}: {node} not found in domain/ (planned in a gap, generated, or typo)")

    for g in gaps:
        gid = g.get("id", "?")
        for field in REQUIRED:
            if g.get(field) in (None, "", []):
                errors.append(f"{gid}: missing field '{field}'")
        if not ID_RE.match(str(gid)):
            errors.append(f"{gid}: id must look like G-001")
        if gid in seen:
            errors.append(f"{gid}: duplicate id")
        seen.add(gid)
        if g.get("status") not in STATUSES:
            errors.append(f"{gid}: status must be one of {sorted(STATUSES)}")
        if g.get("layer") not in LAYERS:
            errors.append(f"{gid}: layer must be one of {sorted(LAYERS)}")
        if g.get("type") not in TYPES:
            errors.append(f"{gid}: type must be one of {sorted(TYPES)}")
        if g.get("status") == "fixed" and not (g.get("fixed") and g.get("build")):
            errors.append(f"{gid}: fixed gaps need 'fixed' (date) and 'build'")
        for n in g.get("nodes") or []:
            check_node(gid, n)

    for fm in doc.get("form_map") or []:
        owner = f"form_map[{fm.get('form')}]"
        for field in ("form", "title", "module", "manages", "uses", "processes", "rules"):
            if fm.get(field) in (None, ""):
                errors.append(f"{owner}: missing field '{field}'")
        check_node(owner, f"form:{fm.get('form')}")
        check_node(owner, f"module:{fm.get('module')}")
        for c in (fm.get("manages") or []) + (fm.get("uses") or []):
            check_node(owner, f"concept:{c}")
        for p in fm.get("processes") or []:
            check_node(owner, f"process:{p}")
        for sp in fm.get("sps_called") or []:
            check_node(owner, sp)
        rule_keys = set()
        for r in fm.get("rules") or []:
            if r["key"] in rule_keys:
                errors.append(f"{owner}: duplicate rule {r['key']}")
            rule_keys.add(r["key"])
            check_node(owner, f"rule:{r['key']}")
            for i in r.get("implemented_by") or []:
                check_node(f"{owner}/{r['key']}", i)
            for p in r.get("governs") or []:
                check_node(f"{owner}/{r['key']}", f"process:{p}")
            for gid in r.get("gaps") or []:
                if gid not in seen:
                    errors.append(f"{owner}/{r['key']}: unknown gap {gid}")
        for gid in (fm.get("global_rules_gaps") or []):
            if gid not in seen:
                errors.append(f"{owner}: unknown gap {gid}")
        for k in fm.get("global_rules_applying") or []:
            check_node(owner, f"rule:{k}")
    return errors, warnings


def one_line(text: str) -> str:
    return " ".join(str(text).split())


def render_md(doc) -> str:
    gaps = doc["gaps"]
    out = ["# KG Gap Log", "",
           "> GENERATED from `kg_gaps.yaml` by `gaps.py render`. Do not edit here; edit the YAML.", ""]
    counts = {s: sum(1 for g in gaps if g["status"] == s) for s in ("open", "in-progress", "fixed", "noted")}
    out += ["**Status:** " + ", ".join(f"{n} {s}" for s, n in counts.items()), "",
            "| Id | Status | Layer | Type | Title |", "|---|---|---|---|---|"]
    for g in gaps:
        out.append(f"| {g['id']} | {g['status']} | {g['layer']} | {g['type']} | {g['title']} |")
    out += ["", "Layers: " + "; ".join(f"**{k}** {v}" for k, v in LAYERS.items()), "", "## Gaps", ""]
    for g in gaps:
        out += [f"### {g['id']}  {g['title']}",
                f"- Status: **{g['status']}** | Layer: {g['layer']} | Type: {g['type']} | Found: {g['found']} by {g['found_by']}",
                f"- Question asked: {g.get('question', '')}",
                "- Nodes: " + ", ".join(f"`{n}`" for n in g["nodes"]),
                f"- Evidence: {one_line(g['evidence'])}",
                f"- Fix: {one_line(g['fix'])}"]
        if g.get("fixed"):
            out.append(f"- Fixed: {g['fixed']} (build {g.get('build')})")
        out.append("")
    out += ["## Map: Form -> Module / Concepts / Process / Business Rules", ""]
    for fm in doc.get("form_map") or []:
        out += [f"### form:{fm['form']}  ({fm['title']})",
                "| Item | Value |", "|---|---|",
                f"| Module | **{fm['module']}** |",
                f"| Status / generated | {fm.get('status', '')} / {fm.get('generated', '')} |",
                f"| Manages | {', '.join(fm['manages'])} |",
                f"| Uses concepts ({len(fm['uses'])}) | {', '.join(fm['uses'])} |",
                f"| Process steps | {', '.join(fm['processes'])} |",
                f"| Rules applying (total in KG) | {fm.get('total_rules_applying', '')} |",
                f"| SPs called ({len(fm.get('sps_called') or [])}) | "
                + ", ".join(s.split(':', 1)[1] for s in fm.get("sps_called") or []) + " |", "",
                "| Rule | Type | Implemented by | Governs | Gaps |", "|---|---|---|---|---|"]
        for r in fm["rules"]:
            impl = ", ".join(i.split(":", 1)[1] for i in r.get("implemented_by") or []) or "**none**"
            out.append(f"| {r['key']} | {r.get('type', '')} | {impl} | {', '.join(r.get('governs') or []) or '-'} "
                       f"| {', '.join(r.get('gaps') or []) or '-'} |")
        out += ["", "Global rules also applying: " + ", ".join(fm.get("global_rules_applying") or [])
                + f" (gaps: {', '.join(fm.get('global_rules_gaps') or []) or '-'}). " + str(fm.get("shared_write_rules_note", "")), ""]
    out += ["## Queries to refresh the map", ""]
    for name, q in (doc.get("refresh_queries") or {}).items():
        out += [f"**{name}**", "```cypher", q.strip(), "```", ""]
    return "\n".join(out)


def render_csv(doc, path: Path):
    cols = ["id", "status", "layer", "type", "title", "found", "found_by", "question", "nodes", "evidence", "fix", "fixed", "build"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel opens UTF-8
        w = csv.writer(f)
        w.writerow(cols)
        for g in doc["gaps"]:
            w.writerow([one_line("; ".join(g[c])) if c == "nodes" else one_line(g.get(c, "")) for c in cols])


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "check"
    doc = load(SRC)
    if cmd == "list":
        want = argv[2] if len(argv) > 2 else None
        for g in doc["gaps"]:
            if want is None or g["status"] == want:
                print(f"{g['id']}  {g['status']:<11} {g['layer']}  {g['title']}")
        return 0
    errors, warnings = check(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(doc['gaps'])} gaps, {len(doc.get('form_map') or [])} form map(s): {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors:
        return 1
    if cmd == "render":
        (HERE / "KG_GAP_LOG.md").write_text(render_md(doc), encoding="utf-8")
        render_csv(doc, HERE / "kg_gaps.csv")
        print("wrote KG_GAP_LOG.md, kg_gaps.csv")
    elif cmd != "check":
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
