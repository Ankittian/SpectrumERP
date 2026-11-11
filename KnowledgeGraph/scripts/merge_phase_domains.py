"""Merge the curated functional layers of every phase-N (phase-0, phase-1, phase-2, ...) into ./domain (union by key).

The later phase wins for scalar text (it was written with more forms in view); list fields are unioned;
process steps are interleaved in a hand-set logical order and renumbered.
Usage: python scripts/merge_phase_domains.py
"""
from __future__ import annotations

import shutil
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
P = HERE.parent / "graphs-by-phase"
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
    """a = earlier phases, b = later phase (wins)."""
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


def phase_domains() -> list[Path]:
    """graphs-by-phase/phase-N/phase-N/KnowledgeGraph/domain for every phase found, ordered by N (later phases win)."""
    def n(p: Path) -> int:
        digits = "".join(c for c in p.name if c.isdigit())
        return int(digits) if digits else -1
    found = [d for d in sorted(P.glob("phase-*"), key=n) if (d / d.name / "KnowledgeGraph" / "domain").is_dir()]
    return [d / d.name / "KnowledgeGraph" / "domain" for d in found]


def main() -> None:
    domains = phase_domains()
    if not domains:
        raise SystemExit(f"no phase domains found under {P}")
    for sub in ("forms", "processes"):
        shutil.rmtree(OUT / sub, ignore_errors=True)
    (OUT / "forms").mkdir(parents=True, exist_ok=True)

    def fold(read, key: str | None = None):
        acc = None
        for d in domains:
            cur = read(d)
            if cur is None:
                continue
            acc = cur if acc is None else merge_keyed(acc, cur, key)
        return acc

    dump(OUT / "modules.yaml", {"modules": fold(lambda d: load(d / "modules.yaml")["modules"], "code")})
    for name in ("concepts", "rules"):
        dump(OUT / f"{name}.yaml", {name: fold(lambda d, name=name: load(d / f"{name}.yaml")[name], "key")})
    names = sorted({p.name for d in domains for p in (d / "processes").glob("*.yaml")})
    for n in names:
        acc = None
        for d in domains:
            if (d / "processes" / n).exists():
                cur = load(d / "processes" / n)
                acc = cur if acc is None else merge_process(acc, cur)
        dump(OUT / "processes" / n, acc)
    for name in sorted({p.name for d in domains for p in (d / "forms").glob("*.yaml")}):
        src = [d / "forms" / name for d in domains if (d / "forms" / name).exists()][-1]   # latest phase wins
        shutil.copy(src, OUT / "forms" / name)
    print(f"merged {len(domains)} phase domains ->", OUT)


if __name__ == "__main__":
    main()
