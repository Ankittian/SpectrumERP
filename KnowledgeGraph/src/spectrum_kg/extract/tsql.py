"""T-SQL stored-procedure extractor.

Hybrid approach (CREATE PROCEDURE bodies are not parseable as a whole by sqlglot):
  1. regex: procedure name, parameters, header comments (Author / Create date / Description)
  2. sqlglot tokenizer: split the body into top-level statements, tracking BEGIN/END, CASE/END,
     TRY/CATCH regions and UNION / INSERT..SELECT / UPDATE..SET continuations
  3. sqlglot parser (tsql dialect) per DML statement: tables, aliases, columns, read/write ops.
     Regex fallback when a statement does not parse.
The procedure stays one node: parameters are kept as a property, result sets are not modelled.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.tokens import TokenType

TSQL = sqlglot.Dialect.get_or_raise("tsql")

CREATE_RE = re.compile(
    r"CREATE\s+(?:OR\s+ALTER\s+)?PROC(?:EDURE)?\s+((?:\[[^\]]+\]|\w+)(?:\s*\.\s*(?:\[[^\]]+\]|\w+))?)",
    re.IGNORECASE,
)
HEADER_RE = {
    "author": re.compile(r"--\s*Author\s*:\s*(.+)", re.IGNORECASE),
    "created": re.compile(r"--\s*Create\s*date\s*:\s*(.+)", re.IGNORECASE),
    "description": re.compile(r"--\s*Description\s*:\s*(.+)", re.IGNORECASE),
}
PARAM_RE = re.compile(
    r"(@\w+)\s+(?:AS\s+)?([\w\.]+(?:\s*\(\s*[\w\s,]+\))?)\s*(?:=\s*((?:'[^']*'|[^,\s]+)))?\s*(OUTPUT|OUT|READONLY)?",
    re.IGNORECASE,
)
ASSIGN_SELECT_RE = re.compile(r"^\s*select\s+(?:top\s*\(?\s*\d+\s*\)?\s+)?@\w+\s*=", re.IGNORECASE)
DOUBLE_FROM_DELETE_RE = re.compile(r"^\s*delete\s+from\s+((?:\[[^\]]+\]|\w+)(?:\s*\.\s*(?:\[[^\]]+\]|\w+))?)\s+from\b", re.IGNORECASE)
SPACE_DOT_RE = re.compile(r"(\]|\w)\s+\.\s*(\[|\w)")
EXEC_DYNAMIC_RE = re.compile(r"^\s*exec(?:ute)?\s*\(\s*(@\w+)", re.IGNORECASE)
EXEC_STATIC_RE = re.compile(r"^\s*exec(?:ute)?\s+(?:@\w+\s*=\s*)?((?:\[[^\]]+\]|\w+)(?:\s*\.\s*(?:\[[^\]]+\]|\w+))?)", re.IGNORECASE)
FALLBACK_TABLE_RE = re.compile(
    r"\b(from|join|into|update|delete(?:\s+from)?)\s+((?:\[[^\]]+\]|[A-Za-z_]\w*)(?:\s*\.\s*(?:\[[^\]]+\]|[A-Za-z_]\w*))?)",
    re.IGNORECASE,
)

STATEMENT_STARTS = {
    TokenType.SELECT, TokenType.INSERT, TokenType.UPDATE, TokenType.DELETE, TokenType.DECLARE,
    TokenType.SET, TokenType.EXECUTE, TokenType.MERGE, TokenType.TRUNCATE, TokenType.COMMIT,
    TokenType.ROLLBACK, TokenType.ELSE, TokenType.BEGIN, TokenType.END,
}
WORD_STARTS = {"IF", "WHILE", "RETURN", "PRINT", "RAISERROR", "THROW", "EXEC", "EXECUTE", "GOTO", "BREAK", "CONTINUE"}
SET_OPS = {TokenType.UNION, TokenType.EXCEPT, TokenType.INTERSECT, TokenType.ALL, TokenType.DISTINCT}


@dataclass
class ColumnUse:
    table: str | None          # normalised schema.table, None if ambiguous
    column: str
    op: str                    # read | write
    candidates: list[str] = field(default_factory=list)  # for ambiguous columns


@dataclass
class Statement:
    kind: str                  # select | assign | insert | update | delete | declare | set | if | exec | other
    text: str
    line: int
    in_catch: bool = False
    writes: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    columns: list[ColumnUse] = field(default_factory=list)
    exec_target: str | None = None
    dynamic_var: str | None = None
    assigned_vars: list[str] = field(default_factory=list)
    parse_fallback: bool = False


@dataclass
class Parameter:
    name: str
    type: str
    default: str | None
    direction: str = "in"


@dataclass
class StoredProc:
    schema: str
    name: str
    path: Path
    code: str
    author: str | None = None
    created: str | None = None
    description: str | None = None
    parameters: list[Parameter] = field(default_factory=list)
    statements: list[Statement] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    dynamic_sql: bool = False
    table_display: dict[str, str] = field(default_factory=dict)  # norm -> spelling seen

    @property
    def qualified(self) -> str:
        return f"{self.schema}.{self.name}"


def _unbracket(part: str) -> str:
    part = part.strip()
    return part[1:-1] if part.startswith("[") and part.endswith("]") else part


def split_name(raw: str, default_schema: str) -> tuple[str, str]:
    parts = [_unbracket(p) for p in re.split(r"\s*\.\s*", raw.strip())]
    if len(parts) == 1:
        return default_schema, parts[0]
    return parts[-2] or default_schema, parts[-1]


def parse_sp_file(path: Path, default_schema: str = "dbo") -> StoredProc:
    return parse_sp_text(path.read_text(encoding="utf-8-sig"), path, default_schema)


CODE_MARKER_RE = re.compile(r"(?m)^Code:[ \t]*$")


def parse_sp_embedding_text(path: Path, default_schema: str = "dbo") -> StoredProc:
    """Parse an SP rendered as embedding text (summary/facts header, then a `Code:` line followed by the SQL).

    Used for nested procedures (called only from other SPs) that have no .sql file in any form bundle.
    Only the SQL after `Code:` is used; the header is regenerated from the parsed SQL like any other SP.
    """
    text = path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    m = CODE_MARKER_RE.search(text)
    if not m:
        raise ValueError(f"no 'Code:' section in {path}")
    return parse_sp_text(text[m.end():], path, default_schema)


def parse_sp_text(text: str, path: Path, default_schema: str = "dbo") -> StoredProc:
    text = text.replace("\r\n", "\n")
    m = CREATE_RE.search(text)
    if not m:
        raise ValueError(f"no CREATE PROCEDURE in {path}")
    schema, name = split_name(m.group(1), default_schema)
    sp = StoredProc(schema=schema, name=name, path=path, code=text.strip())

    header_text = text[: m.start()]
    for key, rx in HEADER_RE.items():
        hm = rx.search(header_text)
        if hm:
            setattr(sp, key, hm.group(1).strip())

    # parameters: between the name and the first top-level AS keyword
    after = text[m.end():]
    as_m = re.search(r"(?im)^\s*AS\s*$|\)\s*AS\b|\bAS\s*\n|\bAS\s+BEGIN\b", after)
    params_text = after[: as_m.start()] if as_m else ""
    params_text = re.sub(r"--[^\n]*", "", params_text)
    for pm in PARAM_RE.finditer(params_text):
        sp.parameters.append(Parameter(
            name=pm.group(1), type=re.sub(r"\s+", "", pm.group(2)), default=pm.group(3),
            direction="out" if (pm.group(4) or "").upper().startswith("OUT") else "in",
        ))
    body_offset = m.end() + (as_m.end() if as_m else 0)
    body = text[body_offset:]
    body_line0 = text[:body_offset].count("\n") + 1
    sp.statements = list(_split_statements(body, body_line0))
    for st in sp.statements:
        _analyse(st, sp, default_schema)

    for st in sp.statements:
        if st.kind == "exec":
            if st.dynamic_var:
                sp.dynamic_sql = True
            elif st.exec_target:
                sp.calls.append(st.exec_target)
    return sp


# --------------------------------------------------------------------------------------------
# statement splitting
# --------------------------------------------------------------------------------------------
def _split_statements(body: str, line0: int):
    try:
        tokens = TSQL.tokenize(body)
    except Exception:  # pragma: no cover - tokenizer is very permissive
        yield Statement("other", body, line0, parse_fallback=True)
        return

    depth = 0
    case_depth = 0
    in_catch = False
    cur: list = []
    cur_kind: str | None = None
    insert_needs_select = False
    update_seen_set = False

    def flush():
        nonlocal cur, cur_kind, insert_needs_select, update_seen_set
        if cur:
            start, end = cur[0].start, cur[-1].end + 1
            st = Statement(cur_kind or "other", body[start:end].strip(), line0 + body[:start].count("\n"), in_catch)
            cur, cur_kind, insert_needs_select, update_seen_set = [], None, False, False
            return st
        cur, cur_kind = [], None
        return None

    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        tt = tok.token_type
        word = tok.text.upper()
        nxt = tokens[i + 1].text.upper() if i + 1 < n else ""

        if tt == TokenType.L_PAREN:
            depth += 1
        elif tt == TokenType.R_PAREN:
            depth = max(0, depth - 1)

        if depth == 0 and tt == TokenType.CASE:
            case_depth += 1
        elif depth == 0 and tt == TokenType.END and case_depth > 0:
            case_depth -= 1
            cur.append(tok); i += 1
            continue

        if depth == 0 and case_depth == 0:
            if tt == TokenType.SEMICOLON:
                st = flush()
                if st: yield st
                i += 1
                continue
            # control-flow wrappers: BEGIN [TRY|CATCH|TRAN], END [TRY|CATCH], COMMIT/ROLLBACK [TRAN]
            if tt in (TokenType.BEGIN, TokenType.END) or word in ("COMMIT", "ROLLBACK"):
                st = flush()
                if st: yield st
                if tt == TokenType.BEGIN and nxt == "CATCH":
                    in_catch = True
                elif tt == TokenType.END and nxt == "CATCH":
                    in_catch = False
                skip = 2 if nxt in ("TRY", "CATCH", "TRAN", "TRANSACTION") else 1
                i += skip
                continue
            if tt == TokenType.ELSE:
                st = flush()
                if st: yield st
                i += 1
                continue

            starts = tt in STATEMENT_STARTS or (word in WORD_STARTS and tt != TokenType.STRING)
            if word == "WITH" and not cur:
                starts = True
            if starts and cur:
                prev = cur[-1]
                cont = False
                if tt == TokenType.SELECT:
                    if prev.token_type in SET_OPS:
                        cont = True
                    elif cur_kind == "insert" and insert_needs_select:
                        cont = True
                    elif cur_kind == "with":
                        cont = True
                elif tt == TokenType.SET and cur_kind == "update" and not update_seen_set:
                    cont = True
                    update_seen_set = True
                elif cur_kind == "if" and False:
                    cont = True
                if not cont:
                    st = flush()
                    if st: yield st
            if not cur:
                cur_kind = {
                    TokenType.SELECT: "select", TokenType.INSERT: "insert", TokenType.UPDATE: "update",
                    TokenType.DELETE: "delete", TokenType.DECLARE: "declare", TokenType.SET: "set",
                    TokenType.EXECUTE: "exec", TokenType.MERGE: "merge",
                }.get(tt) or {"IF": "if", "WHILE": "if", "EXEC": "exec", "EXECUTE": "exec", "WITH": "with",
                              "RETURN": "other"}.get(word, "other")
                if cur_kind == "insert":
                    insert_needs_select = True
            if cur_kind == "insert" and tt == TokenType.VALUES:
                insert_needs_select = False
            if cur_kind == "if" and cur and tt in STATEMENT_STARTS and tt != TokenType.SELECT:
                pass
        cur.append(tok)
        i += 1

    st = flush()
    if st:
        yield st


# --------------------------------------------------------------------------------------------
# statement analysis
# --------------------------------------------------------------------------------------------
def _prep(sql: str) -> str:
    sql = SPACE_DOT_RE.sub(r"\1.\2", sql)
    dm = DOUBLE_FROM_DELETE_RE.match(sql)
    if dm:
        sql = sql[: dm.start()] + f"DELETE {dm.group(1)} FROM" + sql[dm.end():]
    return sql


def _qualify(t: exp.Table, default_schema: str) -> str | None:
    name = t.name
    if not name or name.startswith("#") or name.startswith("@"):
        return None
    schema = t.db or default_schema
    return f"{schema}.{name}"


def _analyse(st: Statement, sp: StoredProc, default_schema: str) -> None:
    text = _prep(st.text)
    kind = st.kind
    if kind == "select" and ASSIGN_SELECT_RE.match(text):
        kind = st.kind = "assign"
        st.assigned_vars = re.findall(r"(@\w+)\s*=", text.split("from")[0] if "from" in text.lower() else text)

    if kind == "exec":
        dm = EXEC_DYNAMIC_RE.match(text)
        if dm:
            st.dynamic_var = dm.group(1)
        else:
            sm = EXEC_STATIC_RE.match(text)
            if sm:
                s, n = split_name(sm.group(1), default_schema)
                st.exec_target = f"{s}.{n}"
        return

    sql = text
    if kind == "declare":
        dm = re.match(r"(?is)^\s*declare\s+(@\w+)\s+[^=]*?=\s*(.+)$", text)
        if not dm:
            return
        st.assigned_vars = [dm.group(1)]
        sql = f"SELECT {dm.group(2)}"
    elif kind == "set":
        sm = re.match(r"(?is)^\s*set\s+(@\w+)\s*=\s*(.+)$", text)
        if not sm:
            return
        st.assigned_vars = [sm.group(1)]
        sql = f"SELECT {sm.group(2)}"
    elif kind == "if":
        cond = re.sub(r"(?is)^\s*(if|while)\s+", "", text)
        if "select" not in cond.lower():
            return
        sql = f"SELECT 1 WHERE {cond}"
    elif kind not in ("select", "assign", "insert", "update", "delete", "merge", "with"):
        return

    try:
        tree = sqlglot.parse_one(sql, read="tsql")
    except Exception:
        tree = None
    if tree is None or isinstance(tree, exp.Command):
        _fallback(st, sp, sql, default_schema)
        return

    # alias -> qualified table
    alias_map: dict[str, str] = {}
    real_tables: list[str] = []
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    for t in tree.find_all(exp.Table):
        if t.name.lower() in cte_names:
            continue
        if not t.db and not t.alias and t.name.lower() in alias_map:
            continue
        q = _qualify(t, default_schema)
        if not q:
            continue
        if t.alias:
            alias_map[t.alias.lower()] = q
        if not t.db and not t.alias and isinstance(t.parent, (exp.Update, exp.Delete)):
            # UPDATE alias SET ... / DELETE alias FROM ... -> resolved below
            continue
        alias_map.setdefault(t.name.lower(), q)
        if q not in real_tables:
            real_tables.append(q)
        sp.table_display.setdefault(q.lower(), f"{t.db or default_schema}.{t.name}")

    def resolve(t: exp.Table) -> str | None:
        if not t.db and t.name.lower() in alias_map:
            return alias_map[t.name.lower()]
        return _qualify(t, default_schema)

    target: str | None = None
    write_cols: list[str] = []
    if isinstance(tree, exp.Insert):
        tgt = tree.this
        if isinstance(tgt, exp.Schema):
            write_cols = [c.name for c in tgt.expressions if isinstance(c, (exp.Identifier, exp.Column))]
            tgt = tgt.this
        if isinstance(tgt, exp.Table):
            target = resolve(tgt)
    elif isinstance(tree, (exp.Update, exp.Delete)):
        if isinstance(tree.this, exp.Table):
            target = resolve(tree.this)
        if isinstance(tree, exp.Update):
            for eq in tree.expressions:
                if isinstance(eq, exp.EQ) and isinstance(eq.this, exp.Column):
                    write_cols.append(eq.this.name)
    elif isinstance(tree, exp.Merge) and isinstance(tree.this, exp.Table):
        target = resolve(tree.this)

    if target:
        st.writes.append(target)
        if target not in real_tables:
            real_tables.insert(0, target)
    st.reads = [t for t in real_tables if t != target or _target_also_read(tree, target, resolve)]
    if isinstance(tree, exp.Delete) and target:
        st.reads = [t for t in st.reads if t != target]

    # columns
    proj_aliases = set()
    for sel in tree.find_all(exp.Select):
        for e in sel.expressions:
            if isinstance(e, exp.Alias):
                proj_aliases.add(e.alias.lower())
    single = real_tables[0] if len(real_tables) == 1 else None
    seen: set[tuple] = set()
    for col_name in write_cols:
        key = (target, col_name.lower(), "write")
        if target and key not in seen:
            seen.add(key)
            st.columns.append(ColumnUse(target, col_name, "write"))
    for c in tree.find_all(exp.Column):
        name = c.name
        if not name or name.startswith("@") or name == "*":
            continue
        if isinstance(tree, exp.Update) and isinstance(c.parent, exp.EQ) and c.parent.this is c and c.parent.parent is tree:
            continue  # SET target column (already recorded as write)
        qual = c.table.lower() if c.table else ""
        if qual:
            tbl = alias_map.get(qual)
            if not tbl:
                continue
            cu = ColumnUse(tbl, name, "read")
        elif name.lower() in proj_aliases and isinstance(c.parent, exp.Ordered):
            continue
        elif single:
            cu = ColumnUse(single, name, "read")
        else:
            cu = ColumnUse(None, name, "read", candidates=list(real_tables))
        key = (cu.table, name.lower(), cu.op)
        if key not in seen:
            seen.add(key)
            st.columns.append(cu)


def _target_also_read(tree: exp.Expression, target: str, resolve) -> bool:
    if isinstance(tree, exp.Insert):
        src = tree.expression
        return bool(src) and any(resolve(t) == target for t in src.find_all(exp.Table))
    return False


def _fallback(st: Statement, sp: StoredProc, sql: str, default_schema: str) -> None:
    st.parse_fallback = True
    for m in FALLBACK_TABLE_RE.finditer(sql):
        kw = m.group(1).lower()
        raw = m.group(2)
        if raw.startswith("@") or raw.startswith("#"):
            continue
        s, n = split_name(raw, default_schema)
        q = f"{s}.{n}"
        if kw in ("into", "update") or kw.startswith("delete"):
            if q not in st.writes:
                st.writes.append(q)
        elif q not in st.reads:
            st.reads.append(q)
