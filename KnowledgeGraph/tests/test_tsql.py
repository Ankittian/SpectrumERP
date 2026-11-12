"""T-SQL parser tests. The SQL is the full SP code kept in the graph (`code` property), so no form bundles are needed."""
from pathlib import Path

from spectrum_kg.extract.tsql import parse_sp_text


def parse(graph, name):
    """Parse the SP whose source is stored on graph node sp:<name> (lower-case qualified name)."""
    nid = f"sp:{name.lower()}"
    return parse_sp_text(graph.nodes[nid].props["code"], Path(nid), "masterdata")


def writes(sp, in_catch=False):
    return {t.lower() for s in sp.statements if s.in_catch == in_catch for t in s.writes}


def test_mmumsave_header_params_and_writes(graph):
    sp = parse(graph, "masterdata.MMUMSave")
    assert sp.qualified == "masterdata.MMUMSave"
    assert sp.author == "Namrata" and sp.description == "Save Material Unit Master"
    params = {p.name: p for p in sp.parameters}
    assert list(params) == ["@UnitNo", "@UnitName", "@Alias", "@UnitCategoryNo", "@LoginNo", "@DocumentStatusNo", "@GSTUQC"]
    assert params["@UnitName"].type == "varchar(25)" and params["@DocumentStatusNo"].default == "30"
    assert writes(sp) == {"masterdata.munitmaster", "masterdata.munitmastercompanydetail",
                          "masterdata.munitconversiondetail", "masterdata.msubgroupunitdetail"}
    assert any(c.table.lower() == "masterdata.munitmaster" and c.column == "UnitName" and c.op == "write"
               for s in sp.statements for c in s.columns if c.table)


def test_catch_block_error_log_is_flagged(graph):
    sp = parse(graph, "masterdata.MSGMFillValues")
    assert writes(sp) == set()
    assert writes(sp, in_catch=True) == {"masterdata.merrorlog"}


def test_fillvalues_reads_every_lookup_table(graph):
    sp = parse(graph, "masterdata.MSGMFillValues")
    reads = {t.lower() for s in sp.statements for t in s.reads}
    assert {"sales.setting", "globaldata.hsnsaccode", "masterdata.mbincard", "payroll.tbldivisionmaster"} <= reads


def test_double_from_delete_and_alias_update(graph):
    d = parse(graph, "masterdata.MMIGDelete")
    assert writes(d) == {"masterdata.mgroupmaster", "masterdata.mgroupmastercompanydetail",
                         "masterdata.mgroupqcparameterdetail"}
    assert not any(s.parse_fallback for s in d.statements)
    s = parse(graph, "masterdata.MMIGSave")
    assert "masterdata.mitemmaster" in writes(s)            # update IM set ... from mItemMaster IM


def test_dynamic_exec_detected(graph):
    sp = parse(graph, "masterdata.MMIGSearchData")
    assert sp.dynamic_sql
    dyn = [s for s in sp.statements if s.dynamic_var]
    assert dyn and dyn[0].dynamic_var == "@Procedure"


def test_qualified_columns_resolve_to_tables(graph):
    sp = parse(graph, "masterdata.MMUMLoadData")
    cols = {(c.table.lower(), c.column.lower()) for s in sp.statements for c in s.columns if c.table}
    assert ("masterdata.munitconversiondetail", "firstcf") in cols


def test_every_sp_parses_without_fallback(graph):
    """Every SP of the three phase-0 master-data bundles parses with sqlglot (no regex fallback)."""
    bundles = {"fUnitMaster", "fMaterialSubGroupMaster", "fMaterialGroup"}
    ids = sorted(n.id for n in graph.by_label("StoredProcedure")
                 if bundles & set(n.props.get("bundles") or []) and n.props.get("code"))
    assert ids
    for nid in ids:
        sp = parse(graph, nid.split(":", 1)[1])
        assert sp.statements, nid
        assert not any(s.parse_fallback for s in sp.statements), nid
