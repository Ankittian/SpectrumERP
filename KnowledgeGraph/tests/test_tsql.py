from spectrum_kg.extract.tsql import parse_sp_file

from conftest import REPO

BUNDLES = REPO / "graphs-by-phase" / "phase-0" / "phase-0"   # canonical form bundles (see kg.yaml source_roots)
SP = BUNDLES / "fUnitMaster" / "StoredProcedures"
SG = BUNDLES / "fMaterialSubGroupMaster" / "StoredProcedures"
MG = BUNDLES / "fMaterialGroup" / "StoredProcedures"


def writes(sp, in_catch=False):
    return {t.lower() for s in sp.statements if s.in_catch == in_catch for t in s.writes}


def test_mmumsave_header_params_and_writes():
    sp = parse_sp_file(SP / "masterdata.MMUMSave.sql", "masterdata")
    assert sp.qualified == "masterdata.MMUMSave"
    assert sp.author == "Namrata" and sp.description == "Save Material Unit Master"
    params = {p.name: p for p in sp.parameters}
    assert list(params) == ["@UnitNo", "@UnitName", "@Alias", "@UnitCategoryNo", "@LoginNo", "@DocumentStatusNo", "@GSTUQC"]
    assert params["@UnitName"].type == "varchar(25)" and params["@DocumentStatusNo"].default == "30"
    assert writes(sp) == {"masterdata.munitmaster", "masterdata.munitmastercompanydetail",
                          "masterdata.munitconversiondetail", "masterdata.msubgroupunitdetail"}
    assert any(c.table.lower() == "masterdata.munitmaster" and c.column == "UnitName" and c.op == "write"
               for s in sp.statements for c in s.columns if c.table)


def test_catch_block_error_log_is_flagged():
    sp = parse_sp_file(SG / "masterdata.MSGMFillValues.sql", "masterdata")
    assert writes(sp) == set()
    assert writes(sp, in_catch=True) == {"masterdata.merrorlog"}


def test_fillvalues_reads_every_lookup_table():
    sp = parse_sp_file(SG / "masterdata.MSGMFillValues.sql", "masterdata")
    reads = {t.lower() for s in sp.statements for t in s.reads}
    assert {"sales.setting", "globaldata.hsnsaccode", "masterdata.mbincard", "payroll.tbldivisionmaster"} <= reads


def test_double_from_delete_and_alias_update():
    d = parse_sp_file(MG / "masterdata.MMIGDelete.sql", "masterdata")
    assert writes(d) == {"masterdata.mgroupmaster", "masterdata.mgroupmastercompanydetail",
                         "masterdata.mgroupqcparameterdetail"}
    assert not any(s.parse_fallback for s in d.statements)
    s = parse_sp_file(MG / "masterdata.MMIGSave.sql", "masterdata")
    assert "masterdata.mitemmaster" in writes(s)            # update IM set ... from mItemMaster IM


def test_dynamic_exec_detected():
    sp = parse_sp_file(MG / "masterdata.MMIGSearchData.sql", "masterdata")
    assert sp.dynamic_sql
    dyn = [s for s in sp.statements if s.dynamic_var]
    assert dyn and dyn[0].dynamic_var == "@Procedure"


def test_qualified_columns_resolve_to_tables():
    sp = parse_sp_file(SP / "masterdata.MMUMLoadData.sql", "masterdata")
    cols = {(c.table.lower(), c.column.lower()) for s in sp.statements for c in s.columns if c.table}
    assert ("masterdata.munitconversiondetail", "firstcf") in cols


def test_every_sp_parses_without_fallback():
    files = [p for d in (SP, SG, MG) for p in sorted(d.glob("*.sql"))]
    assert files
    for p in files:
        sp = parse_sp_file(p, "masterdata")
        assert sp.statements, p
        assert not any(s.parse_fallback for s in sp.statements), p
