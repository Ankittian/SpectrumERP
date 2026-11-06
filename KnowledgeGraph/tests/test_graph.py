"""End-to-end assertions on the extracted + curated graph (no Neo4j needed)."""
from spectrum_kg.load import documented_types_check


def reach(g, start, path):
    frontier = {start}
    for rel in path:
        frontier = {e.dst for n in frontier for e in g.out(n, rel)}
    return frontier


def test_build_is_clean(built):
    g, report = built
    assert report.errors == []
    assert report.warnings == []
    assert documented_types_check(g) == []
    assert not g.dangling_edges()


def test_save_chain_reaches_conversion_sp(graph):
    g = graph
    assert "method:fUnitMaster.SaveConversionFactor" in reach(g, "method:fUnitMaster.SaveMain", ["CALLS"])
    sps = reach(g, "method:fUnitMaster.SaveConversionFactor", ["INVOKES", "DELEGATES_TO", "EXECUTES"])
    assert sps == {"sp:masterdata.mmumsaveunitconversiondetail"}


def test_every_sp_is_reachable_from_a_form(graph):
    reached = {e.dst for e in graph.edges.values() if e.type == "CALLS_SP"}
    assert {n.id for n in graph.by_label("StoredProcedure")} <= reached


def test_shared_qc_control_is_one_node(graph):
    g = graph
    qc = g.nodes["sp:masterdata.qcfillvalues"]
    assert sorted(qc.props["bundles"]) == ["fMaterialGroup", "fMaterialSubGroupMaster"]
    assert len(g.by_label("UserControl")) == 1
    hosts = {e.src for e in g.inc("usercontrol:QCGroup", "EMBEDS")}
    assert hosts == {"form:fMaterialGroup", "form:fMaterialSubGroupMaster"}
    assert "sp:masterdata.qcfillvalues" in reach(g, "usercontrol:QCGroup", ["CALLS_SP"])


def test_shared_table_write_conflict(graph):
    e = graph.edges[("form:fMaterialSubGroupMaster", "SHARES_TABLE", "form:fUnitMaster")]
    assert e.props["write_conflict"] is True
    assert "masterdata.mSubGroupUnitDetail" in e.props["conflict_tables"]


def test_field_lineage_control_to_sp(graph):
    g = graph
    props = reach(g, "control:fUnitMaster.utxtUnitName", ["BINDS_TO"])
    assert "dtprop:DTUnitMaster.UnitName" in props
    passes = [e for e in g.inc("dtprop:DTUnitMaster.UnitName", "PASSES") if e.src == "damethod:DAUnitMaster.Save"]
    assert passes and passes[0].props["param"] == "@UnitName"
    assert "sp:masterdata.mmumsave" in reach(g, "damethod:DAUnitMaster.Save", ["EXECUTES"])
    assert "column:masterdata.munitmaster.unitname" in reach(g, "sp:masterdata.mmumsave", ["USES_COLUMN"])
    c = g.nodes["control:fUnitMaster.utxtUnitName"].props
    assert c["label"] == "Unit Name" and c["mandatory"] is True and c["max_length"] == 25


def test_sp_is_one_node_with_parameters(graph):
    assert not graph.by_label("SPParameter") and not graph.by_label("ResultSet")
    sp = graph.nodes["sp:masterdata.mmumsave"].props
    assert "@DocumentStatusNo tinyint = 30" in sp["parameters"]
    assert sp["params_not_passed"] == ["@DocumentStatusNo"]


def test_error_log_write_is_not_business_write(graph):
    e = graph.edges[("sp:masterdata.msgmfillvalues", "WRITES", "table:masterdata.merrorlog")]
    assert e.props["error_handling"] is True
    assert ("form:fMaterialSubGroupMaster", "USES_TABLE", "table:masterdata.merrorlog") not in graph.edges


def test_functional_layer(graph):
    g = graph
    steps = {e.dst: e.props["order"] for e in g.out("process:material-master-setup", "HAS_STEP")}
    assert steps["form:fUnitMaster"] == 1 and steps["form:fMaterialSubGroupMaster"] == 4
    assert g.nodes["form:fItemMaster"].props["status"] == "planned"
    assert "concept:material-sub-group" in reach(g, "concept:material-group", ["PARENT_OF"])
    assert "form:fUnitMaster" in reach(g, "module:MM", ["HAS_FORM"])
    rule_targets = reach(g, "rule:subgroup-unit-links-shared", ["IMPLEMENTED_BY"])
    assert "table:masterdata.msubgroupunitdetail" in rule_targets
    for n in g.nodes.values():
        assert n.props.get("text"), n.id
        assert n.props.get("kind") == n.label


def test_tabs_and_labels(graph):
    c = graph.nodes["control:fMaterialSubGroupMaster.ucmbHSNSACCode"].props
    assert c["tab"] == "GST Detail" and c["tab_key"] == "GST"
