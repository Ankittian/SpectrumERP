"""Enum layer: turns the GlobalData lookup tables (exported from SQL Server) into EnumType / EnumValue nodes, and links
them to the columns and stored procedures that use the raw numbers.

Input: a folder with `_tables.csv`, `_columns.csv` and one `GlobalData.<Table>.csv` per lookup table (kg.yaml `enums_dir`).

    EnumType  -HAS_VALUE->   EnumValue            e.g. AccountType -> 3 = Bank Account
    EnumType  -BACKED_BY->   Table                the GlobalData lookup table (added when the graph has none)
    Column    -HAS_ENUM->    EnumType             a column named like the lookup key (e.g. AccountTypeNo); ambiguous=true
                                                  when several lookup tables share that key name (StatusNo ...)
    StoredProcedure -USES_ENUM_VALUE-> EnumValue  `AccountTypeNo = 3` / `IN (3,4)` in the SP code; props literal, count,
                                                  confidence (high = SP joins the lookup table or key is unique;
                                                  low = ambiguous key, edge goes to every candidate with that value)
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from .model import Graph, norm

SCHEMA = "GlobalData"
MAX_ROWS = 200
INT_TYPES = {"tinyint", "smallint", "int", "bigint"}
# configuration / catalogue tables that are not enums even though they are small
SKIP_TABLES = re.compile(r"^(APIDetail|FormMaster|ModuleMaster|Report\w*|DailyPrint\w*|Dashboard\w*|WebDashboard\w*|"
                         r"Notification\w*|EmailBodyTemplate|SpectrumERPConfiguration|FormCustomValidation|"
                         r"FormSearchDataDetail|MissingNumber|Tally\w*|Make|PortCode|\w*Procedure|\w*Setting\w*|"
                         r"VoucherNarration\w*|RecurringVoucherTemplate|TechnicalGradeMapping|FormAuthorizationAttributeDetail|"
                         r"FormExchangeRateTypeDetail|SupplementaryField|Parameter|GOLF|CRMTimeZone|CRMKeywords)$", re.I)
NAME_HINT = re.compile(r"name|type|source|nature|status|description|desc", re.I)
EXTRA_FLAGS = ("Inactive", "IsDefault")
CMP_RX = re.compile(r"(?<![\w@])\[?(\w+)\]?\s*(=|<>|!=)\s*(\d+)\b"
                    r"|(?<![\w@])\[?(\w+)\]?\s+IN\s*\(\s*(\d+(?:\s*,\s*\d+)*)\s*\)", re.I)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _name_column(cols: list[dict[str, str]], table: str, pk: str) -> str | None:
    text = [c["column_name"] for c in cols if c["data_type"] in ("varchar", "nvarchar", "char", "nchar")
            and c["column_name"] != pk and c["column_name"] not in EXTRA_FLAGS and int(c["max_length"] or 0) != 1]
    if not text:
        return None
    for c in text:                                   # column called like the table (ItemType.Type, AccountType.AccountType)
        if c.lower() == table.lower() or c.lower() in ("name", "type", "sourcedocument", "description"):
            return c
    hinted = [c for c in text if NAME_HINT.search(c)]
    return (hinted or text)[0]


def load_lookups(enums_dir: Path) -> list[dict]:
    """Eligible lookup tables with their values."""
    tables = {r["table_name"]: r for r in _read(enums_dir / "_tables.csv")}
    cols: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in _read(enums_dir / "_columns.csv"):
        cols[r["table_name"]].append(r)
    out = []
    for tn, t in tables.items():
        c = cols[tn]
        pk = [x for x in c if x["is_pk"] == "1"]
        f = enums_dir / f"{SCHEMA.lower() if False else 'globaldata'}.{tn}.csv"
        if (len(pk) != 1 or pk[0]["data_type"] not in INT_TYPES or int(t["row_count"]) > MAX_ROWS
                or SKIP_TABLES.match(tn) or not f.exists()):
            continue
        key = pk[0]["column_name"]
        name_col = _name_column(c, tn, key)
        if not name_col:
            continue
        values = []
        for r in _read(f):
            try:
                v = int(r[key])
            except (KeyError, ValueError):
                continue
            label = (r.get(name_col) or "").strip()
            if label:
                values.append({"value": v, "label": label, "inactive": r.get("Inactive") in ("1", "True"),
                               "is_default": r.get("IsDefault") in ("1", "True"),
                               "extra": {k: v2.strip() for k, v2 in r.items()
                                         if k not in (key, name_col, "Inactive", "IsDefault") and v2 and len(v2) <= 60
                                         and not k.lower().endswith(("no", "id"))}})
        if values:
            out.append({"table": tn, "key": key, "name_col": name_col, "values": values})
    return out


JSON_NAME = "globaldata-fk-enums.json"


def load_lookups_json(path: Path) -> list[dict]:
    """Lookup lists from the SQL Server export (foreign keys + code evidence). Same shape as load_lookups(), plus
    `fk_columns` (exact columns that reference the list) and `conflicts` (lookup vs. code disagreements)."""
    out = []
    for e in json.loads(path.read_text(encoding="utf-8-sig")):
        schema, _, table = (e.get("source_table") or "").partition(".")
        if not table or schema.lower() != SCHEMA.lower():
            continue
        values, seen = [], set()
        for v in e.get("values", []):
            label = (v.get("name") or "").strip()
            if not label or v.get("value") in seen:               # nameless / duplicate codes carry no meaning
                continue
            seen.add(v["value"])
            ev = [x.get("snippet", "") for x in (v.get("code_evidence") or [])][:2]
            values.append({"value": int(v["value"]), "label": label, "inactive": v.get("active") is False,
                           "is_default": False, "extra": {}, "confidence": v.get("confidence", "high"),
                           "source_type": v.get("source_type", "lookup_table"), "row_count": v.get("row_count"),
                           "code_evidence": [x for x in ev if x]})
        if not values:
            continue
        basis = e.get("applies_to_basis") or {}
        out.append({"table": table, "key": e.get("key_column") or "", "name_col": e.get("name_column") or "",
                    "values": values, "conflicts": (e.get("conflicts") or "")[:1500],
                    "fk_columns": [c for c in e.get("applies_to", []) if basis.get(c) == "foreign_key"]})
    return out


def add_enums(g: Graph, enums_dir: Path) -> dict[str, int]:
    json_path = enums_dir / JSON_NAME
    use_json = json_path.exists()
    lookups = load_lookups_json(json_path) if use_json else load_lookups(enums_dir)
    by_key: dict[str, list[dict]] = defaultdict(list)       # lowercase column name -> lookup tables
    for lk in lookups:
        lk["id"] = f"enum:{norm(SCHEMA)}.{norm(lk['table'])}"
        by_key[lk["key"].lower()].append(lk)
        for c in lk.get("fk_columns", []):                  # FK child columns may be named differently (ParentAccountTypeNo)
            leaf = c.rsplit(".", 1)[-1].lower()
            if lk not in by_key[leaf]:
                by_key[leaf].append(lk)
        vals = ", ".join(f"{v['value']}={v['label']}" for v in sorted(lk["values"], key=lambda v: v["value"])[:40])
        g.add_node(lk["id"], "EnumType", name=lk["table"], key_column=lk["key"], name_column=lk["name_col"],
                   value_count=len(lk["values"]), kind="EnumType", conflicts=lk.get("conflicts") or None,
                   summary=f"Lookup list {lk['table']} ({len(lk['values'])} values): {vals}"[:400],
                   text=f"[EnumType] {lk['table']}\nCodes stored in column {lk['key']} (GlobalData.{lk['table']}) mean:\n{vals}")
        table_id = f"table:{norm(SCHEMA)}.{norm(lk['table'])}"
        if table_id not in g.nodes:
            g.add_node(table_id, "Table", name=f"{SCHEMA}.{lk['table']}", schema=SCHEMA, table=lk["table"], kind="Table",
                       summary=f"Lookup table {SCHEMA}.{lk['table']} holding the names of {lk['key']} codes.",
                       text=f"[Table] {SCHEMA}.{lk['table']}\nLookup table: {lk['key']} -> {lk['name_col']}")
        g.add_edge(lk["id"], "BACKED_BY", table_id)
        for v in lk["values"]:
            vid = f"enumvalue:{norm(SCHEMA)}.{norm(lk['table'])}.{v['value']}"
            extra = "; ".join(f"{k}={x}" for k, x in v["extra"].items())
            g.add_node(vid, "EnumValue", name=f"{lk['table']} {v['value']} = {v['label']}", enum=lk["table"], value=v["value"],
                       label=v["label"], inactive=v["inactive"], is_default=v["is_default"], kind="EnumValue",
                       confidence=v.get("confidence"), source_type=v.get("source_type"), row_count=v.get("row_count"),
                       summary=f"{lk['key']} {v['value']} means '{v['label']}' ({lk['table']})."
                               + (" Inactive." if v["inactive"] else ""),
                       text=f"[EnumValue] {lk['table']}: {v['value']} = {v['label']}\nColumn {lk['key']}. {extra}".strip())
            g.add_edge(lk["id"], "HAS_VALUE", vid)

    stats = {"enum_types": len(lookups), "enum_values": sum(len(l["values"]) for l in lookups)}

    # Column -HAS_ENUM-> EnumType (same name as the lookup key; plus the lookup table's own key column)
    col_edges = 0
    if use_json:                                              # exact: columns that really are foreign keys to the list
        for lk in lookups:
            for c in lk.get("fk_columns", []) + [f"{SCHEMA}.{lk['table']}.{lk['key']}"]:
                cid = "column:" + ".".join(norm(x) for x in c.split("."))
                if cid in g.nodes:
                    g.add_edge(cid, "HAS_ENUM", lk["id"], ambiguous=False, own_key=cid.endswith(f".{norm(lk['key'])}"),
                               basis="foreign_key")
                    col_edges += 1
    for n in ([] if use_json else list(g.nodes.values())):
        if n.label != "Column":
            continue
        cands = by_key.get(str(n.props.get("column", "")).lower())
        if not cands:
            continue
        for lk in cands:
            own = norm(n.props.get("table", "")) == f"{norm(SCHEMA)}.{norm(lk['table'])}"
            g.add_edge(n.id, "HAS_ENUM", lk["id"], ambiguous=len(cands) > 1 and not own, own_key=own)
            col_edges += 1
    stats["column_enum_edges"] = col_edges

    # StoredProcedure -USES_ENUM_VALUE-> EnumValue (numbers compared against a lookup key in the SP code)
    sp_edges = 0
    unresolved: dict[str, int] = defaultdict(int)
    for sp in g.by_label("StoredProcedure"):
        code = sp.props.get("code") or ""
        low = code.lower()
        seen: dict[tuple[str, int], dict] = {}
        for m in CMP_RX.finditer(code):
            col = (m.group(1) or m.group(4)).lower()
            cands = by_key.get(col)
            if not cands:
                if re.search(r"(status|type|nature|mode|source)", col):
                    unresolved[col] += 1
                continue
            lits = [int(m.group(3))] if m.group(3) else [int(x) for x in re.split(r"\s*,\s*", m.group(5))]
            joined = [lk for lk in cands if f"globaldata.{lk['table'].lower()}" in low or f"[{lk['table'].lower()}]" in low]
            chosen, conf = (joined, "high") if joined else (cands, "high" if len(cands) == 1 else "low")
            for lk in chosen:
                have = {v["value"] for v in lk["values"]}
                for lit in lits:
                    if lit in have:
                        rec = seen.setdefault((lk["id"], lit), {"count": 0, "conf": conf, "col": lk["key"]})
                        rec["count"] += 1
        for (eid, lit), rec in seen.items():
            vid = f"enumvalue:{eid.split(':', 1)[1]}.{lit}"
            if vid in g.nodes:
                g.add_edge(sp.id, "USES_ENUM_VALUE", vid, literal=lit, column=rec["col"], count=rec["count"], confidence=rec["conf"])
                sp_edges += 1
    stats["sp_enum_edges"] = sp_edges
    stats["unresolved_enum_like_columns"] = len(unresolved)
    g.unresolved_enum_columns = dict(sorted(unresolved.items(), key=lambda kv: -kv[1]))   # type: ignore[attr-defined]
    return stats
