"""Merge the curated functional layers of phase-0 and phase-1 into ./domain (union by key).

Phase-1 wins for scalar text (it was written with more forms in view); list fields are unioned;
process steps are interleaved in a hand-set logical order and renumbered.
Usage: python scripts/merge_phase_domains.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
P = HERE.parent / "graphs-by-phase"
D0 = P / "phase-0/phase-0/KnowledgeGraph/domain"
D1 = P / "phase-1/phase-1/KnowledgeGraph/domain"
OUT = HERE / "domain"

# Logical step order for processes that gain forms from both phases (forms not listed keep source order after).
STEP_ORDER = {
    "material-master-setup": ["fUnitMaster", "fSingleFieldMaster", "fMakeMaster", "fChapterHeading", "fHSNCode",
                              "fMaterialGroup", "fMaterialSubGroupMaster", "fTechSpecificationHeadMaster", "fItemMaster",
                              "fItemTechGradeMapping", "fItemStandardAttributeValue", "fChangeItemUnitWeight"],
    "goods-receipt-quality-inspection": ["fQCParameter", "fQualityParameter", "fSpecification", "fMaterialGroup",
                                         "fMaterialSubGroupMaster", "fGateEntry", "fGRN", "fInspectionIntimation",
                                         "fInspectionEntry"],
    "gst-tax-determination": ["fHSNCode", "fTDCMaster", "fTDCGroup", "fTDCAccountRule", "fMaterialSubGroupMaster",
                              "fUnitMaster", "fPurchaseOrder", "fPurchaseBill"],
    "inventory-storage": ["fWarehouse", "fMaterialSubGroupMaster", "fUnitMaster", "fBINCard", "fMaterialIssue"],
    "procure-to-pay": ["fMaterialSubGroupMaster", "fPurchaseOrganization", "fIndentRequisition", "fIndent",
                       "fRequestforQuotation", "fQuotation", "fCS", "fPurchaseOrder", "fGateEntry", "fGRN"],
    "preventive-maintenance": ["fPermitMaster", "fMaterialIssue"],
}


def load(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def dump(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")


def union(a: list | None, b: list | None) -> list:
    """Order-preserving union; strings compare case-insensitively (SQL/VB names are, and graph ids are lowercased),
    so `masterdata.mTaxGroup` and `masterdata.mtaxgroup` from the two phases do not both survive."""
    out: list = []
    seen: set = set()
    for x in (a or []) + (b or []):
        k = x.strip().lower() if isinstance(x, str) else repr(x)
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


def merge_item(base: dict, other: dict) -> dict:
    """base wins for scalars, lists are unioned (dict items in lists compared whole)."""
    m = dict(other)
    m.update(base)
    for k in set(base) | set(other):
        if isinstance(base.get(k), list) or isinstance(other.get(k), list):
            m[k] = union(base.get(k), other.get(k))
    return m


def merge_keyed(a: list[dict], b: list[dict], key: str) -> list[dict]:
    """a = phase-0, b = phase-1 (wins)."""
    items = {x[key]: x for x in a}
    for x in b:
        items[x[key]] = merge_item(x, items[x[key]]) if x[key] in items else x
    return sorted(items.values(), key=lambda x: x[key])


def merge_process(p0: dict, p1: dict) -> dict:
    m = merge_item(p1, p0)
    steps = {s["form"]: s for s in p0["steps"]}
    steps.update({s["form"]: s for s in p1["steps"]})
    order = STEP_ORDER.get(p1["key"], [])
    ranked = sorted(steps.values(), key=lambda s: (order.index(s["form"]) if s["form"] in order else len(order), s["order"]))
    m["steps"] = [{**s, "order": i + 1} for i, s in enumerate(ranked)]
    return m


def main() -> None:
    for sub in ("forms", "processes"):
        shutil.rmtree(OUT / sub, ignore_errors=True)
    dump(OUT / "modules.yaml", {"modules": merge_keyed(load(D0 / "modules.yaml")["modules"], load(D1 / "modules.yaml")["modules"], "code")})
    for name in ("concepts", "rules"):
        dump(OUT / f"{name}.yaml", {name: merge_keyed(load(D0 / f"{name}.yaml")[name], load(D1 / f"{name}.yaml")[name], "key")})
    names = {p.name for p in (D0 / "processes").glob("*.yaml")} | {p.name for p in (D1 / "processes").glob("*.yaml")}
    for n in sorted(names):
        p0, p1 = D0 / "processes" / n, D1 / "processes" / n
        dump(OUT / "processes" / n, merge_process(load(p0), load(p1)) if p0.exists() and p1.exists() else load(p1 if p1.exists() else p0))
    for p in sorted(set((D0 / "forms").glob("*.yaml")) | set((D1 / "forms").glob("*.yaml")), key=lambda x: x.name):
        src = D1 / "forms" / p.name if (D1 / "forms" / p.name).exists() else D0 / "forms" / p.name   # phase-1 wins
        shutil.copy(src, OUT / "forms" / p.name) if (OUT / "forms").exists() else (OUT / "forms").mkdir() or shutil.copy(src, OUT / "forms" / p.name)
    print("merged ->", OUT)


if __name__ == "__main__":
    main()
