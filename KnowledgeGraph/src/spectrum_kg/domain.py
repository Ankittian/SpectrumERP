"""Curated functional layer: modules, business processes, concepts, rules and per-form docs (domain/*.yaml).

References between YAML and the extracted graph use node ids, e.g.
  form:fUnitMaster  usercontrol:QCGroup  sp:masterdata.MMUMSave  table:masterdata.mUnitMaster
  column:masterdata.mItemMaster.FullCode  method:fUnitMaster.SaveMain  concept:unit-of-measure
SQL ids are matched case-insensitively. Every reference is validated; unknown ids are reported as errors.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from . import model as M
from .model import Graph

SQL_PREFIXES = ("sp:", "table:", "column:")


def resolve_ref(g: Graph, ref: str) -> str | None:
    ref = ref.strip()
    if ref.startswith(SQL_PREFIXES):
        prefix, rest = ref.split(":", 1)
        cand = f"{prefix}:{rest.lower()}"
        return cand if cand in g.nodes else None
    if ref in g.nodes:
        return ref
    low = ref.lower()
    return next((k for k in g.nodes if k.lower() == low), None)


def _load_yaml(p: Path) -> Any:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_domain_files(domain_dir: Path) -> dict[str, Any]:
    d: dict[str, Any] = {"modules": [], "concepts": [], "rules": [], "processes": [], "forms": []}
    if not domain_dir.exists():
        return d
    for name in ("modules", "concepts", "rules"):
        p = domain_dir / f"{name}.yaml"
        if p.exists():
            d[name] = _load_yaml(p).get(name, [])
    for p in sorted((domain_dir / "processes").glob("*.yaml")):
        d["processes"].append({**_load_yaml(p), "_file": p.name})
    for p in sorted((domain_dir / "forms").glob("*.yaml")):
        d["forms"].append({**_load_yaml(p), "_file": p.name})
    return d


def _md_list(items: list[Any] | None) -> str:
    return "\n".join(f"- {i}" for i in items or [])


def apply_domain(g: Graph, domain_dir: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    d = load_domain_files(domain_dir)

    def link(src: str, rel: str, ref: str, ctx: str, **props: Any) -> None:
        dst = resolve_ref(g, ref)
        if dst is None:
            errors.append(f"{ctx}: unknown reference '{ref}'")
            return
        g.add_edge(src, rel, dst, **props)

    # ---- modules --------------------------------------------------------------------------
    for m in d["modules"]:
        mid = M.module_id(m["code"])
        g.add_node(mid, "Module", name=m["name"], code=m["code"], summary=m.get("summary"),
                   doc=m.get("description"), status=m.get("status", "active"))

    # ---- concepts -------------------------------------------------------------------------
    for c in d["concepts"]:
        cid = M.concept_id(c["key"])
        g.add_node(cid, "BusinessConcept", name=c["name"], key=c["key"], summary=c.get("summary"),
                   doc=c.get("description"), synonyms=c.get("synonyms"), module=c.get("module"))
        if c.get("module"):
            g.add_edge(M.module_id(c["module"]), "HAS_CONCEPT", cid)
    for c in d["concepts"]:
        cid = M.concept_id(c["key"])
        ctx = f"concepts.yaml:{c['key']}"
        for child in c.get("parent_of", []):
            link(cid, "PARENT_OF", f"concept:{child}", ctx)
        for rel in c.get("related_to", []):
            if isinstance(rel, dict):
                link(cid, "RELATED_TO", f"concept:{rel['concept']}", ctx, how=rel.get("how"))
            else:
                link(cid, "RELATED_TO", f"concept:{rel}", ctx)
        for t in c.get("tables", []):
            link(cid, "PERSISTED_IN", t if t.startswith("table:") else f"table:{t}", ctx, derived=True)

    # ---- forms (docs attach to extracted Form / UserControl nodes) ---------------------------
    documented: set[str] = set()
    for f in d["forms"]:
        ref = f"form:{f['form']}" if "form" in f else f"usercontrol:{f['usercontrol']}"
        fid = resolve_ref(g, ref)
        ctx = f"forms/{f['_file']}"
        if fid is None:
            if f.get("status") == "planned":
                fid = ref
                g.add_node(fid, "Form", name=f.get("form") or f.get("usercontrol"), status="planned")
            else:
                errors.append(f"{ctx}: no extracted {ref} (set status: planned for forms not built yet)")
                continue
        documented.add(fid)
        node = g.nodes[fid]
        doc_parts = [f.get("purpose", "").strip()]
        if f.get("functional_description"):
            doc_parts.append(f["functional_description"].strip())
        if f.get("actions"):
            doc_parts.append("Actions:\n" + "\n".join(f"- {k}: {v}" for k, v in f["actions"].items()))
        if f.get("validations"):
            doc_parts.append("Validations:\n" + _md_list(f["validations"]))
        if f.get("users"):
            doc_parts.append("Used by: " + ", ".join(f["users"]))
        node.props.update({k: v for k, v in {
            "title": f.get("title") or node.props.get("title"),
            "summary": f.get("summary"),
            "doc": "\n\n".join(p for p in doc_parts if p),
            "module": f.get("module"),
            "form_kind": f.get("kind"),
            "users": f.get("users"),
            "status": f.get("status", node.props.get("status", "active")),
        }.items() if v})
        if f.get("module"):
            link(M.module_id(f["module"]), "HAS_FORM", fid, ctx)
        for c in f.get("manages", []):
            link(fid, "MANAGES", f"concept:{c}", ctx)
        for c in f.get("uses_concepts", []):
            link(fid, "USES_CONCEPT", f"concept:{c}", ctx)
        for method, text in (f.get("method_notes") or {}).items():
            mid = resolve_ref(g, M.method_id(f.get("form") or f.get("usercontrol"), method))
            if mid:
                g.nodes[mid].props["summary"] = text
            else:
                warnings.append(f"{ctx}: method_notes refers to unknown method {method}")

    for n in g.nodes.values():
        if n.label in ("Form", "UserControl") and n.id not in documented:
            warnings.append(f"{n.id} has no curated doc in domain/forms/ (run: kg scaffold-doc {n.name})")

    # ---- processes ------------------------------------------------------------------------
    for p in d["processes"]:
        pid = M.process_id(p["key"])
        ctx = f"processes/{p['_file']}"
        steps = p.get("steps", [])
        step_text = "\n".join(
            f"{s.get('order', i + 1)}. {s['name']}" + (f" ({s['form']})" if s.get("form") else "")
            + (" [planned]" if s.get("status") == "planned" else "") + (f": {s['description']}" if s.get("description") else "")
            for i, s in enumerate(steps))
        g.add_node(pid, "BusinessProcess", name=p["name"], key=p["key"], summary=p.get("summary"),
                   doc="\n\n".join(x for x in [p.get("description", "").strip(), "Steps:\n" + step_text if steps else ""] if x),
                   module=p.get("module"), status=p.get("status", "active"))
        if p.get("module"):
            link(M.module_id(p["module"]), "HAS_PROCESS", pid, ctx)
        for i, s in enumerate(steps):
            if not s.get("form"):
                continue
            fref = s["form"] if ":" in s["form"] else f"form:{s['form']}"
            fid = resolve_ref(g, fref)
            if fid is None:
                if s.get("status") == "planned":
                    fid = fref
                    g.add_node(fid, "Form", name=fref.split(":", 1)[1], title=s.get("name"), status="planned",
                               summary=s.get("description"), module=p.get("module"))
                    if p.get("module"):
                        g.add_edge(M.module_id(p["module"]), "HAS_FORM", fid)
                else:
                    errors.append(f"{ctx}: step '{s['name']}' references unknown {fref}")
                    continue
            g.add_edge(pid, "HAS_STEP", fid, order=s.get("order", i + 1), step=s["name"],
                       status=s.get("status", "active"), description=s.get("description"))
        for c in p.get("concepts", []):
            link(pid, "INVOLVES", f"concept:{c}", ctx)
    for p in d["processes"]:
        for nxt in p.get("leads_to", []):
            link(M.process_id(p["key"]), "LEADS_TO", f"process:{nxt}", f"processes/{p['_file']}")

    # ---- rules ----------------------------------------------------------------------------
    for r in d["rules"]:
        rid = M.rule_id(r["key"])
        ctx = f"rules.yaml:{r['key']}"
        g.add_node(rid, "BusinessRule", name=r["name"], key=r["key"], summary=r.get("summary"),
                   doc=r.get("description"), rule_type=r.get("type"))
        for ref in r.get("applies_to", []):
            link(rid, "APPLIES_TO", ref, ctx)
        for ref in r.get("implemented_by", []):
            link(rid, "IMPLEMENTED_BY", ref, ctx)
        for ref in r.get("processes", []):
            link(rid, "GOVERNS", f"process:{ref}" if ":" not in ref else ref, ctx)

    warnings += coverage_warnings(g, d)
    return warnings, errors


EVIDENCE_LINES = ("Evidence: code", "Evidence: code + ERP domain (inferred)", "Evidence: ERP domain (inferred)")


def coverage_warnings(g: Graph, d: dict[str, Any]) -> list[str]:
    """Functional-layer quality checks (GRAPH_STRUCTURE.md §5.1 / §6.2 checks 9-10)."""
    out: list[str] = []
    for kind, items, keyf in (("concept", d["concepts"], "key"), ("rule", d["rules"], "key"),
                              ("process", d["processes"], "key")):
        for it in items:
            first = (it.get("description") or "").strip().splitlines()[:1]
            if not first or first[0].strip() not in EVIDENCE_LINES:
                out.append(f"{kind} {it[keyf]}: description must start with one of {list(EVIDENCE_LINES)}")
    rule_targets = {e.dst for e in g.edges.values() if e.type == "APPLIES_TO"}
    for n in g.nodes.values():
        if n.label in ("Form", "UserControl") and n.props.get("status") != "planned" and n.id not in rule_targets:
            out.append(f"{n.id}: no business rule APPLIES_TO it")
    governed = {e.dst for e in g.edges.values() if e.type == "GOVERNS"}
    for n in g.by_label("BusinessProcess"):
        if n.id not in governed:
            out.append(f"{n.id}: no business rule GOVERNS it")
    rule_text = "\n".join((r.get("description") or "") + " " + (r.get("summary") or "") for r in d["rules"]).lower()
    for f in d["forms"]:
        for msg in f.get("validations", []) or []:
            core = msg.strip().strip('"').rstrip(".").lower()
            if core and core not in rule_text:
                out.append(f"forms/{f['_file']}: validation message not quoted in any rule: \"{msg}\"")
    # grounding: functional nodes must trace back to the forms in scope
    real_ui = {n.id for n in g.nodes.values() if n.label in ("Form", "UserControl") and n.props.get("status") != "planned"}
    used_tables = {e.dst for e in g.edges.values() if e.type == "USES_TABLE" and e.src in real_ui}
    grounded_concepts = {e.dst for e in g.edges.values()
                         if (e.type in ("MANAGES", "USES_CONCEPT") and e.src in real_ui)
                         or (e.type == "PERSISTED_IN" and e.dst in used_tables)}
    grounded_concepts |= {e.src for e in g.edges.values() if e.type == "PERSISTED_IN" and e.dst in used_tables}
    for n in g.by_label("BusinessConcept"):
        if n.id not in grounded_concepts:
            out.append(f"{n.id}: not grounded - no in-scope form manages/uses it and none of its tables is used by one")
    # a process is grounded if an in-scope form is one of its steps, or - one hop only - it directly follows such a
    # process (LEADS_TO) and involves a grounded concept (e.g. Payment Flow after Procure-to-Pay)
    direct = {n.id for n in g.by_label("BusinessProcess") if any(e.dst in real_ui for e in g.out(n.id, "HAS_STEP"))}
    for n in g.by_label("BusinessProcess"):
        if n.id in direct:
            continue
        follows = any(e.src in direct for e in g.inc(n.id, "LEADS_TO"))
        involves = any(e.dst in grounded_concepts for e in g.out(n.id, "INVOLVES"))
        if not (follows and involves):
            out.append(f"{n.id}: not grounded - no in-scope form step, and it does not directly follow a grounded "
                       f"process while involving a grounded concept")
    for n in g.by_label("BusinessRule"):
        if not any(e.dst in real_ui or e.dst in grounded_concepts for e in g.out(n.id, "APPLIES_TO")):
            out.append(f"{n.id}: not grounded - applies to no in-scope form or grounded concept")
    applies = {}
    for e in g.edges.values():
        if e.type == "APPLIES_TO" and g.nodes.get(e.src, None) and g.nodes[e.src].props.get("rule_type") == "integrity":
            applies.setdefault(e.src, set()).add(e.dst)
    for e in g.edges.values():
        if e.type == "SHARES_TABLE" and e.props.get("write_conflict"):
            if not any({e.src, e.dst} <= targets for targets in applies.values()):
                out.append(f"{e.src} / {e.dst} write {e.props.get('conflict_tables')} but no integrity rule applies to both")
    return out
