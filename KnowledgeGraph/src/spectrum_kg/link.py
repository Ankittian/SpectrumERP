"""Turn parsed SPs into graph nodes, resolve cross-layer references and compute derived shortcut edges."""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from . import model as M
from .extract.code import CodeModel
from .extract.tsql import StoredProc
from .model import Graph, content_hash, norm


def build_sql_graph(g: Graph, sps: Iterable[tuple[StoredProc, str, str]], error_log_tables: list[str]) -> dict[str, StoredProc]:
    """sps: (parsed SP, bundle name, repo-relative path). Identical SPs in several bundles merge into one node."""
    error_tables = {norm(t) for t in error_log_tables}
    by_q: dict[str, StoredProc] = {}
    hashes: dict[str, set[str]] = defaultdict(set)
    for sp, bundle, rel in sps:
        q = norm(sp.qualified)
        hashes[q].add(content_hash(sp.code))
        sid = M.sp_id(sp.qualified)
        g.add_node(sid, "StoredProcedure", name=sp.qualified, schema=sp.schema, procedure=sp.name, code=sp.code,
                   author=sp.author, created=sp.created, description=sp.description, dynamic_sql=sp.dynamic_sql or None,
                   parameters=[f"{p.name} {p.type}" + (f" = {p.default}" if p.default else "")
                               + (" OUTPUT" if p.direction == "out" else "") for p in sp.parameters],
                   bundles=[bundle], source_files=[rel])
        if q not in by_q:
            g.nodes[sid].props["_param_names"] = [p.name.lower() for p in sp.parameters]
        g.vote_name(sid, sp.qualified)
        if q in by_q:
            continue
        by_q[q] = sp

        assigned_by: dict[str, list[str]] = defaultdict(list)
        for st in sp.statements:
            for v in st.assigned_vars:
                assigned_by[v.lower()].extend(st.reads)
            for t in st.writes:
                _table(g, t, sp)
                err = st.in_catch or norm(t) in error_tables
                g.add_edge(sid, "WRITES", M.table_id(t), ops=[st.kind], error_handling=err or None,
                           lines=[st.line])
            for t in st.reads:
                _table(g, t, sp)
                g.add_edge(sid, "READS", M.table_id(t), lines=[st.line])
            for cu in st.columns:
                if cu.table:
                    _column(g, cu.table, cu.column, sp)
                    g.add_edge(sid, "USES_COLUMN", M.column_id(cu.table, cu.column), ops=[cu.op])
            if st.exec_target:
                g.add_edge(sid, "CALLS_SP", M.sp_id(st.exec_target), line=st.line)
            if st.dynamic_var:
                for t in assigned_by.get(st.dynamic_var.lower(), []):
                    g.add_edge(sid, "DYNAMIC_EXEC", M.table_id(t), variable=st.dynamic_var, line=st.line,
                               note="procedure name looked up at runtime from this table")

    # ambiguous (unqualified, multi-table) columns: attribute when exactly one candidate table has that column
    known = defaultdict(set)
    for n in g.by_label("Column"):
        known[norm(n.props["table"])].add(norm(n.props["column"]))
    for q, sp in by_q.items():
        sid = M.sp_id(sp.qualified)
        unresolved = []
        for st in sp.statements:
            for cu in st.columns:
                if cu.table is None:
                    hits = [t for t in cu.candidates if norm(cu.column) in known[norm(t)]]
                    if len(hits) == 1:
                        g.add_edge(sid, "USES_COLUMN", M.column_id(hits[0], cu.column), ops=[cu.op], inferred=True)
                    else:
                        unresolved.append(f"{cu.column} ({'|'.join(cu.candidates)})")
        if unresolved:
            g.nodes[sid].props["ambiguous_columns"] = sorted(set(unresolved))
        if len(hashes[q]) > 1:
            g.nodes[sid].props["variants"] = len(hashes[q])
    return by_q


def _table(g: Graph, qualified: str, sp: StoredProc) -> None:
    tid = M.table_id(qualified)
    schema, name = qualified.split(".", 1)
    g.add_node(tid, "Table", name=qualified, schema=schema.lower(), table=name)
    g.vote_name(tid, sp.table_display.get(qualified.lower(), qualified))


def _column(g: Graph, table_q: str, col: str, sp: StoredProc) -> None:
    _table(g, table_q, sp)
    cid = M.column_id(table_q, col)
    g.add_node(cid, "Column", name=f"{table_q}.{col}", table=table_q, column=col)
    g.add_edge(M.table_id(table_q), "HAS_COLUMN", cid)


# ---------------------------------------------------------------------------------------------
def resolve_code_to_sql(g: Graph, cm: CodeModel) -> list[str]:
    warnings: list[str] = []
    # SPs referenced by DA code but missing from the bundles -> stub node so the chain is visible
    for damethod, sp_q in cm.da_sp_calls:
        sid = M.sp_id(sp_q)
        if sid not in g.nodes:
            g.add_node(sid, "StoredProcedure", name=sp_q, missing_source=True)
            warnings.append(f"{damethod} executes {sp_q} but no .sql file was found")

    # parameters the data layer sends (DAMethod -PASSES {param}-> DTProperty) vs. parameters the SP declares
    passed: dict[str, set[str]] = defaultdict(set)
    for damethod, dtprop, sp_q, param in cm.param_feeds:
        sid = M.sp_id(sp_q)
        node = g.nodes.get(sid)
        if node is None or node.props.get("missing_source"):
            continue
        if param.lower() in node.props.get("_param_names", []):
            passed[sid].add(param.lower())
        else:
            warnings.append(f"{damethod} passes {param} which {sp_q} does not declare")
    executed = {e.dst for e in g.edges.values() if e.type == "EXECUTES"}
    for n in g.by_label("StoredProcedure"):
        names = n.props.pop("_param_names", [])
        if n.id in executed and names:
            missing = [p for p in n.props.get("parameters", []) if p.split()[0].lower() not in passed[n.id]]
            if missing:
                n.props["params_not_passed"] = [p.split()[0] for p in missing]
    return warnings


# ---------------------------------------------------------------------------------------------
def derive_shortcuts(g: Graph) -> None:
    """Form/UserControl -CALLS_SP-> SP, -USES_TABLE-> Table, Form -SHARES_TABLE-> Form (all derived:true)."""
    out = defaultdict(lambda: defaultdict(list))
    for e in g.edges.values():
        out[e.src][e.type].append(e)

    ui_nodes = [n for n in g.nodes.values() if n.label in ("Form", "UserControl")]
    usage: dict[str, dict[str, set[str]]] = {}
    for ui in ui_nodes:
        sps: dict[str, set[str]] = defaultdict(set)
        for hm in out[ui.id]["HAS_METHOD"]:
            for inv in out[hm.dst]["INVOKES"]:
                for dl in out[inv.dst]["DELEGATES_TO"]:
                    for ex in out[dl.dst]["EXECUTES"]:
                        sps[ex.dst].add(g.nodes[hm.dst].props["method"])
        for sid, methods in sps.items():
            g.add_edge(ui.id, "CALLS_SP", sid, derived=True, methods=sorted(methods))
        tables: dict[str, set[str]] = defaultdict(set)
        for sid in sps:
            for e in out[sid]["READS"]:
                tables[e.dst].add("read")
            for e in out[sid]["WRITES"]:
                if not e.props.get("error_handling"):
                    tables[e.dst].add("write")
        for tid, ops in tables.items():
            g.add_edge(ui.id, "USES_TABLE", tid, derived=True, ops=sorted(ops))
        usage[ui.id] = tables

    ids = sorted(usage)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            common = set(usage[a]) & set(usage[b])
            if not common:
                continue
            conflicts = sorted(g.nodes[t].props["name"] for t in common if "write" in usage[a][t] and "write" in usage[b][t])
            g.add_edge(a, "SHARES_TABLE", b, derived=True, tables=sorted(g.nodes[t].props["name"] for t in common),
                       write_conflict=bool(conflicts), conflict_tables=conflicts or None, count=len(common))
