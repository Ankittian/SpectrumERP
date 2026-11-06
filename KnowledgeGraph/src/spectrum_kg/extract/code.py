"""Interpret Roslyn syntax facts (VB.NET + C#) into graph nodes/edges.

Roles are detected from code shape, not folder names, so new bundles with different layouts still work:
  DAO  - class whose fields are string constants holding SP names ("schema.Proc") / parameter names ("@X")
  DA   - class whose methods call an exec method (ExecuteProc ...) on the base helper
  DT   - class whose methods instantiate a DA class (Active-Record style transfer object)
  UI   - Form / UserControl (base type, or has InitializeComponent)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import model as M
from ..model import Graph

SP_LITERAL_RE = re.compile(r'^"?\s*(\[?[A-Za-z_]\w*\]?\s*\.\s*\[?[A-Za-z_]\w*\]?)\s*"?$')
PARAM_LITERAL_RE = re.compile(r'^"(@\w+)"$')
IDENT_RE = re.compile(r"[A-Za-z_]\w*")
GRID_COL_RE = re.compile(r'(?:Columns|Cells|GetCellValue|Item)\s*[\(\[]\s*"([^"]+)"|\w+\s*\(\s*"([^"]+)"\s*\)')
SELF_RECEIVERS = {None, "", "Me", "this", "MyBase", "MyClass", "base"}
LABEL_PREFIX_RE = re.compile(r"^([a-z]+)(?=[A-Z0-9])")


def last_segment(type_name: str) -> str:
    t = re.sub(r"\(.*$", "", type_name or "").strip()
    return t.split(".")[-1]


def strip_self(expr: str) -> str:
    for p in ("Me.", "this.", "MyBase."):
        if expr.startswith(p):
            return expr[len(p):]
    return expr


def literal(s: str | None) -> str | None:
    if s is None:
        return None
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1].replace('""', '"')
    return None


def clean_label(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)  # formatted link labels
    return re.sub(r"\s+", " ", text.replace("&", "")).strip().rstrip(":").strip()


@dataclass
class TypeInfo:
    name: str
    kind: str
    namespace: str
    bundles: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    bases: list[str] = field(default_factory=list)
    implements: list[str] = field(default_factory=list)
    fields: list[dict] = field(default_factory=list)
    properties: list[dict] = field(default_factory=list)
    methods: list[dict] = field(default_factory=list)
    language: str = ""
    role: str = "other"
    seen_files: set = field(default_factory=set)

    def method(self, name: str) -> dict | None:
        return next((m for m in self.methods if m["name"].lower() == name.lower()), None)


@dataclass
class CodeModel:
    types: dict[str, TypeInfo]
    dao_consts: dict[str, str]           # "DAOUnitMaster.Save" -> "masterdata.MMUMSave"
    da_sp_calls: list[tuple[str, str]]   # (damethod_id, sp qualified)
    param_feeds: list[tuple[str, str, str, str]]  # (damethod_id, dtprop_id, sp qualified, @param)


def collect_types(facts_by_file: dict[Path, dict[str, Any]], file_bundle: dict[Path, str], source_root: Path) -> dict[str, TypeInfo]:
    types: dict[str, TypeInfo] = {}
    for path, facts in facts_by_file.items():
        rel = path.relative_to(source_root).as_posix()
        for t in facts.get("types", []):
            ti = types.get(t["name"])
            if ti is None:
                ti = types[t["name"]] = TypeInfo(t["name"], t["kind"], t.get("namespace", ""), language=facts["language"])
            bundle = file_bundle[path]
            if bundle not in ti.bundles:
                ti.bundles.append(bundle)
            ti.files.append(rel)
            # identical copies of the same file in different bundles (e.g. QCGroup) are merged once
            sig = (Path(rel).name.lower(), len(t.get("methods", [])), len(t.get("fields", [])))
            if sig in ti.seen_files:
                continue
            ti.seen_files.add(sig)
            designer = ".designer." in rel.lower()
            for b in t.get("bases", []):
                if b not in ti.bases:
                    ti.bases.append(b)
            for b in t.get("implements", []):
                if b not in ti.implements:
                    ti.implements.append(b)
            for f in t.get("fields", []):
                ti.fields.append({**f, "file": rel, "designer": designer})
            for p in t.get("properties", []):
                ti.properties.append({**p, "file": rel})
            for m in t.get("methods", []):
                ti.methods.append({**m, "file": rel, "designer": designer})
    return types


def classify(types: dict[str, TypeInfo], settings_ui: dict, settings_dl: dict) -> None:
    exec_methods = set(settings_dl.get("exec_methods", ["ExecuteProc"]))
    form_bases = {last_segment(b) for b in settings_ui.get("form_base_types", ["Form"])}
    uc_bases = {last_segment(b) for b in settings_ui.get("usercontrol_base_types", ["UserControl"])}
    for ti in types.values():
        bases = {last_segment(b) for b in ti.bases}
        if bases & uc_bases:
            ti.role = "UserControl"
        elif bases & form_bases:
            ti.role = "Form"
        elif any(m["name"] == "InitializeComponent" for m in ti.methods):
            ti.role = "Form"
        elif ti.fields and sum(1 for f in ti.fields if literal(f.get("initializer")) and (
                SP_LITERAL_RE.match(f["initializer"]) or PARAM_LITERAL_RE.match(f["initializer"]))) >= max(1, len(ti.fields) // 2):
            ti.role = "DAO"
        elif any(inv["member"] in exec_methods for m in ti.methods for inv in m.get("invocations", [])):
            ti.role = "DA"
    da_names = {n for n, t in types.items() if t.role == "DA"}
    for ti in types.values():
        if ti.role == "other" and any(last_segment(oc) in da_names for m in ti.methods for oc in m.get("objectCreations", [])):
            ti.role = "DT"


def build_code_graph(g: Graph, types: dict[str, TypeInfo], settings_ui: dict, settings_dl: dict, default_schema: str) -> CodeModel:
    classify(types, settings_ui, settings_dl)
    dao_consts: dict[str, str] = {}
    for ti in types.values():
        if ti.role == "DAO":
            for f in ti.fields:
                val = literal(f.get("initializer"))
                if val is not None:
                    dao_consts[f"{ti.name}.{f['name']}"] = val

    cm = CodeModel(types, dao_consts, [], [])
    for ti in types.values():
        if ti.role == "DA":
            _build_da(g, ti, cm, settings_dl, types, default_schema)
    for ti in types.values():
        if ti.role == "DT":
            _build_dt(g, ti, types)
    for ti in types.values():
        if ti.role in ("Form", "UserControl"):
            _build_ui(g, ti, types, cm, settings_ui)
    return cm


# ---------------------------------------------------------------------------------------------
def _sp_name(raw: str, default_schema: str) -> str:
    parts = [p.strip().strip("[]") for p in raw.split(".")]
    return ".".join(parts) if len(parts) > 1 else f"{default_schema}.{parts[0]}"


def _build_da(g: Graph, ti: TypeInfo, cm: CodeModel, settings_dl: dict, types: dict[str, TypeInfo], default_schema: str) -> None:
    exec_methods = set(settings_dl.get("exec_methods", ["ExecuteProc"]))
    add_methods = set(settings_dl.get("param_add_methods", ["Add"]))
    g.add_node(M.daclass_id(ti.name), "DAClass", name=ti.name, namespace=ti.namespace, language=ti.language,
               bundles=ti.bundles, source_files=ti.files)
    for m in ti.methods:
        mid = M.damethod_id(ti.name, m["name"])
        dt_param_types = {p["name"]: last_segment(p["type"]) for p in m.get("parameters", [])}
        g.add_node(mid, "DAMethod", name=f"{ti.name}.{m['name']}", method=m["name"], class_name=ti.name,
                   code=m["code"], file=m["file"], start_line=m["startLine"], end_line=m["endLine"],
                   language=ti.language, bundles=ti.bundles)
        g.add_edge(M.daclass_id(ti.name), "HAS_METHOD", mid)
        sp_q = None
        for inv in m.get("invocations", []):
            if inv["member"] in exec_methods and inv.get("args"):
                arg0 = inv["args"][0].strip()
                raw = cm.dao_consts.get(arg0) or literal(arg0) or arg0
                if SP_LITERAL_RE.match(raw) or SP_LITERAL_RE.match(f'"{raw}"'):
                    sp_q = _sp_name(raw.strip('"'), default_schema)
                    cm.da_sp_calls.append((mid, sp_q))
                    g.add_edge(mid, "EXECUTES", M.sp_id(sp_q), via=arg0, line=inv["line"])
        for inv in m.get("invocations", []):
            if inv["member"] in add_methods and len(inv.get("args", [])) >= 2:
                p_raw = inv["args"][0].strip()
                param = cm.dao_consts.get(p_raw) or literal(p_raw)
                if not param or not param.startswith("@"):
                    continue
                val = inv["args"][1].strip()
                vm = re.match(r"^(\w+)\.(\w+)$", val)
                if vm and vm.group(1) in dt_param_types:
                    dt_cls, prop = dt_param_types[vm.group(1)], vm.group(2)
                    pid = M.dtprop_id(dt_cls, prop)
                    g.add_edge(mid, "PASSES", pid, param=param, line=inv["line"])
                    if sp_q:
                        cm.param_feeds.append((mid, pid, sp_q, param))


def _build_dt(g: Graph, ti: TypeInfo, types: dict[str, TypeInfo]) -> None:
    cid = M.dtclass_id(ti.name)
    g.add_node(cid, "DTClass", name=ti.name, namespace=ti.namespace, language=ti.language,
               bundles=ti.bundles, source_files=ti.files)
    for p in ti.properties:
        pid = M.dtprop_id(ti.name, p["name"])
        g.add_node(pid, "DTProperty", name=f"{ti.name}.{p['name']}", property=p["name"], class_name=ti.name,
                   type=p["type"], backing_field=p.get("backingField"), bundles=ti.bundles)
        g.add_edge(cid, "HAS_PROPERTY", pid)
    da_names = {n for n, t in types.items() if t.role == "DA"}
    for m in ti.methods:
        mid = M.dtmethod_id(ti.name, m["name"])
        g.add_node(mid, "DTMethod", name=f"{ti.name}.{m['name']}", method=m["name"], class_name=ti.name,
                   code=m["code"], file=m["file"], start_line=m["startLine"], end_line=m["endLine"],
                   language=ti.language, bundles=ti.bundles)
        g.add_edge(cid, "HAS_METHOD", mid)
        local_types = {l["name"]: last_segment(l["type"]) for l in m.get("locals", [])}
        for inv in m.get("invocations", []):
            recv = inv.get("receiver") or ""
            da_cls = None
            nm = re.match(r"^\(?\s*new\s+([\w\.]+)\s*\(", recv, re.IGNORECASE)
            if nm and last_segment(nm.group(1)) in da_names:
                da_cls = last_segment(nm.group(1))
            elif recv in local_types and local_types[recv] in da_names:
                da_cls = local_types[recv]
            if da_cls and types[da_cls].method(inv["member"]):
                g.add_edge(mid, "DELEGATES_TO", M.damethod_id(da_cls, types[da_cls].method(inv["member"])["name"]), line=inv["line"])


# ---------------------------------------------------------------------------------------------
def _build_ui(g: Graph, ti: TypeInfo, types: dict[str, TypeInfo], cm: CodeModel, settings_ui: dict) -> None:
    owner = ti.name
    uid = M.ui_id(ti.role, owner)
    init = next((m for m in ti.methods if m["name"] == "InitializeComponent"), None)
    init_assign = init.get("assignments", []) if init else []

    def self_prop(prop: str) -> str | None:
        for a in init_assign:
            if a["left"] in (f"Me.{prop}", f"this.{prop}", prop):
                return literal(a["right"])
        return None

    title = self_prop("Text")
    g.add_node(uid, ti.role, name=owner, title=clean_label(title) if title and title != owner else None,
               sp_prefix=self_prop("Tag"), language=ti.language, namespace=ti.namespace,
               implements=ti.implements, bases=ti.bases, bundles=ti.bundles, source_files=ti.files)

    # ---- controls ----------------------------------------------------------------------------
    ui_names = {n for n, t in types.items() if t.role in ("Form", "UserControl")}
    controls: dict[str, dict[str, Any]] = {}
    for f in ti.fields:
        if not f.get("designer"):
            continue
        ctype = last_segment(f["type"])
        if ctype in ("IContainer", "Container") or f["name"] == "components":
            continue
        controls[f["name"]] = {"name": f["name"], "type": ctype, "full_type": f["type"]}
    if not controls and init:
        for a in init_assign:
            m = re.match(r"^(?:Me\.|this\.)?(\w+)$", a["left"])
            nm = re.match(r"^New\s+([\w\.]+)\(|^new\s+([\w\.]+)\(", a["right"])
            if m and nm:
                controls[m.group(1)] = {"name": m.group(1), "type": last_segment(nm.group(1) or nm.group(2))}

    tabs_by_page: dict[str, dict[str, str]] = {}
    tab_props: dict[str, dict[str, str]] = {}
    for a in init_assign:
        left = strip_self(a["left"])
        parts = left.split(".")
        if len(parts) == 2 and parts[0] in controls:
            c = controls[parts[0]]
            prop, val = parts[1], a["right"]
            if prop in ("Text", "Value", "Tag", "NullText"):
                lit = literal(val)
                if lit is not None:
                    c[prop.lower()] = lit
            elif prop == "MaxLength" and val.isdigit():
                c["max_length"] = int(val)
            elif prop == "Visible":
                c["visible"] = val.lower() != "false"
            elif prop == "Location":
                pm = re.search(r"\((-?\d+)\s*,\s*(-?\d+)\)", val)
                if pm:
                    c["x"], c["y"] = int(pm.group(1)), int(pm.group(2))
            elif prop == "ReadOnly":
                c["read_only"] = val.lower() == "true"
        elif len(parts) == 2 and parts[1] in ("TabPage", "Key", "Text"):
            tp = tab_props.setdefault(parts[0], {})
            tp[parts[1]] = strip_self(a["right"]) if parts[1] == "TabPage" else (literal(a["right"]) or "")
    for tab, p in tab_props.items():
        if "TabPage" in p:
            tabs_by_page[p["TabPage"]] = {"key": p.get("Key", ""), "text": clean_label(p.get("Text", ""))}

    parent_of: dict[str, str] = {}
    for inv in (init.get("invocations", []) if init else []):
        recv = strip_self(inv.get("receiver") or "")
        if inv["member"] in ("Add", "AddRange") and recv.endswith("Controls"):
            parent = recv[: -len("Controls")].rstrip(".") or "__self__"
            parent = strip_self(parent) if parent != "__self__" else parent
            for arg in inv.get("args", []):
                for ident in IDENT_RE.findall(arg):
                    if ident in controls:
                        parent_of[ident] = parent

    def tab_of(name: str) -> dict[str, str] | None:
        seen = set()
        while name in parent_of and name not in seen:
            seen.add(name)
            name = parent_of[name]
            if name in tabs_by_page:
                return tabs_by_page[name]
        return None

    mandatory: set[str] = set()
    mand_methods = set(settings_ui.get("mandatory_methods", []))
    for m in ti.methods:
        for inv in m.get("invocations", []):
            if inv["member"] in mand_methods:
                for arg in inv.get("args", []):
                    mandatory.update(i for i in IDENT_RE.findall(arg) if i in controls)

    # label pairing: name stem, then geometry (same parent, same row, left of control)
    labels = {n: c for n, c in controls.items() if "Label" in c["type"]}
    inputs = {n: c for n, c in controls.items() if n not in labels and not any(
        k in c["type"] for k in ("GroupBox", "Panel", "TabPageControl", "TabControl", "SharedControlsPage", "Button"))}

    def stem(name: str) -> str:
        return LABEL_PREFIX_RE.sub("", name).lower()

    label_for: dict[str, str] = {}
    by_stem = {stem(n): n for n in inputs}
    for ln, lc in labels.items():
        target = by_stem.get(stem(ln))
        if target and target not in label_for:
            label_for[target] = ln
    for ln, lc in labels.items():
        if ln in label_for.values() or "y" not in lc:
            continue
        cands = [n for n, c in inputs.items() if n not in label_for and parent_of.get(n) == parent_of.get(ln)
                 and "y" in c and abs(c["y"] - lc["y"]) <= 8 and c.get("x", 0) > lc.get("x", 0)]
        if cands:
            best = min(cands, key=lambda n: inputs[n]["x"] - lc["x"])
            label_for[best] = ln

    for n, c in controls.items():
        cid = M.control_id(owner, n)
        tab = tab_of(n)
        lbl = label_for.get(n)
        label_text = None
        if lbl:
            label_text = clean_label(controls[lbl].get("text") or controls[lbl].get("value") or "")
        g.add_node(cid, "Control", name=f"{owner}.{n}", control=n, owner=owner, type=c["type"],
                   label=label_text or None, text=clean_label(c.get("text", "")) or None,
                   max_length=c.get("max_length"), visible=c.get("visible"), read_only=c.get("read_only"),
                   mandatory=n in mandatory or None, tab=tab["text"] if tab else None,
                   tab_key=tab["key"] if tab else None, parent=parent_of.get(n) if parent_of.get(n) != "__self__" else None)
        g.add_edge(uid, "HAS_CONTROL", cid)
        if lbl:
            g.add_edge(M.control_id(owner, lbl), "LABELS", cid)
        if c["type"] in ui_names and c["type"] != owner:
            g.add_edge(uid, "EMBEDS", M.ui_id(types[c["type"]].role, c["type"]), control=n)

    # ---- methods -----------------------------------------------------------------------------
    method_names = {m["name"] for m in ti.methods}
    dt_types = {n for n, t in types.items() if t.role == "DT"}
    field_types = {f["name"]: last_segment(f["type"]) for f in ti.fields}

    # event subscriptions wired in the designer (C# +=, VB AddHandler)
    subs: dict[str, list[tuple[str, str]]] = {}
    for m in ti.methods:
        for s in m.get("subscriptions", []):
            subs.setdefault(strip_self(s["handler"]), []).append((strip_self(s["target"]), s["event"]))

    for m in ti.methods:
        if m["name"] == "InitializeComponent" or (m.get("designer") and m["name"] == "Dispose"):
            continue
        mid = M.method_id(owner, m["name"])
        handles = [(h["target"], h["event"]) for h in m.get("handles", [])] + subs.get(m["name"], [])
        kind = "interface" if m.get("implementsMembers") else ("handler" if handles else
                                                                ("constructor" if m["kind"] == "constructor" else "helper"))
        g.add_node(mid, "FormMethod", name=f"{owner}.{m['name']}", method=m["name"], owner=owner, method_kind=kind,
                   implements=m.get("implementsMembers") or None, code=m["code"], file=m["file"],
                   start_line=m["startLine"], end_line=m["endLine"], language=ti.language,
                   comments=m.get("leadingComments") or None, events=[f"{t}.{e}" for t, e in handles] or None)
        g.add_edge(uid, "HAS_METHOD", mid)
        for target, event in handles:
            t = strip_self(target)
            if t in ("MyBase", "Me", "this", "base", "") or t == owner:
                g.add_edge(mid, "HANDLES", uid, event=event)
            elif t in controls:
                g.add_edge(mid, "HANDLES", M.control_id(owner, t), event=event)

        local_types = {l["name"]: last_segment(l["type"]) for l in m.get("locals", [])}
        param_types = {p["name"]: last_segment(p["type"]) for p in m.get("parameters", [])}
        var_types = {**field_types, **param_types, **local_types}
        dt_vars = {v: t for v, t in var_types.items() if t in dt_types}

        def norm_recv(r: str | None) -> str | None:
            return strip_self(r) if r else r

        calls = [(norm_recv(i.get("receiver")), i["member"], i["line"]) for i in m.get("invocations", [])]
        calls += [(norm_recv(a["receiver"]), a["member"], a["line"]) for a in m.get("memberAccesses", [])]
        referenced: set[str] = set()
        for recv, member, line in calls:
            if recv in SELF_RECEIVERS or recv is None:
                if member in method_names and member != m["name"] and member != "InitializeComponent":
                    g.add_edge(mid, "CALLS", M.method_id(owner, member), line=line)
            elif recv in dt_vars:
                dtm = types[dt_vars[recv]].method(member)
                if dtm:
                    g.add_edge(mid, "INVOKES", M.dtmethod_id(dt_vars[recv], dtm["name"]), line=line, via=recv)
            elif recv in controls:
                referenced.add(recv)
                ctype = controls[recv]["type"]
                if ctype in types and types[ctype].role == "UserControl" and types[ctype].method(member):
                    g.add_edge(mid, "CALLS", M.method_id(ctype, types[ctype].method(member)["name"]), line=line, via=recv)
            first = (recv or "").split(".")[0]
            if first in controls:
                referenced.add(first)

        # DT property assignments (control -> DT property)
        for a in m.get("assignments", []):
            left = strip_self(a["left"])
            lm = re.match(r"^(\w+)\.(\w+)$", left)
            if lm and lm.group(1) in dt_vars:
                dt_cls, prop = dt_vars[lm.group(1)], lm.group(2)
                if not any(p["name"] == prop for p in types[dt_cls].properties):
                    continue
                pid = M.dtprop_id(dt_cls, prop)
                right = a["right"]
                gc = GRID_COL_RE.search(right)
                grid_col = (gc.group(1) or gc.group(2)) if gc else None
                g.add_edge(mid, "SETS", pid, expr=right, line=a["line"], grid_column=grid_col)
                for ident in IDENT_RE.findall(right):
                    if ident in controls:
                        g.add_edge(M.control_id(owner, ident), "BINDS_TO", pid, expr=right, method=m["name"], line=a["line"])
            for ident in IDENT_RE.findall(left + " " + a["right"]):
                if ident in controls:
                    referenced.add(ident)
        for c in referenced:
            g.add_edge(mid, "REFERENCES", M.control_id(owner, c))
