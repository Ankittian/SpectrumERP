# spectrum-kg-all-phases: MANIFEST

One combined build of Phases 0-13 (built 11 Nov 2026): every phase's form bundles, one merged `NestedSPs`, `SingleFieldConfigs` and `Reports-13*` are source roots of a single `build_graph` run. `graph/graph.json` is `json.dumps(Graph.to_json(), indent=1, default=str)`, the same call `kg build --dry-run` makes, and it is not post-processed: every property, including the full `code`, is kept.

## 1. Builder and inputs

- Builder: the Appendix A `spectrum_kg` package from the phase-0/1 repositories, unchanged except `kg.yaml` `roslyn_extractor` pointing at the Linux build (`tools/bin/RoslynExtractor/RoslynExtractor`, no `.exe`). Roslyn extractor built with .NET SDK 8.0.134, Microsoft.CodeAnalysis 4.12.0. No git repository; file hashes (SHA-256, first 16 hex):

  - `src/spectrum_kg/__init__.py` 799bfe082649c572
  - `src/spectrum_kg/build.py` a8a451337fddaecf
  - `src/spectrum_kg/cli.py` d686c9617c951ad8
  - `src/spectrum_kg/config.py` ef9f86e85e4a3151
  - `src/spectrum_kg/domain.py` 6068873f81fdf069
  - `src/spectrum_kg/embed.py` fb55b81a548f942d
  - `src/spectrum_kg/extract/__init__.py` e3b0c44298fc1c14
  - `src/spectrum_kg/extract/bundle.py` 9a99b1c6cd96373d
  - `src/spectrum_kg/extract/code.py` 957df63938eb576f
  - `src/spectrum_kg/extract/roslyn.py` 7becb90f2d0ec069
  - `src/spectrum_kg/extract/tsql.py` 2da01dddc6fc9e91
  - `src/spectrum_kg/link.py` f222414d87e65915
  - `src/spectrum_kg/load.py` 3e005c8bc9867173
  - `src/spectrum_kg/model.py` 5d13c48c6431b747
  - `src/spectrum_kg/schema.py` eff7ee2488d03876
  - `src/spectrum_kg/viz.py` 5117e4a1d361360e
  - `tools/RoslynExtractor/CSharpExtractor.cs` fdaf83679f5eb02d
  - `tools/RoslynExtractor/Model.cs` 7e6a9ec46dd06f72
  - `tools/RoslynExtractor/Program.cs` daf416b06ac01d65
  - `tools/RoslynExtractor/RoslynExtractor.csproj` 657a8cf218beb3dd
  - `tools/RoslynExtractor/VbExtractor.cs` 72506a63b4186033

- Source: `D:\Coding\_upload\source.zip` (staged from its split parts `source.zip.001`-`.005`, 53,695,195 bytes, parts dated 2026-10-20 19:59 UTC).
- Database: `D:\Coding\DbExport-20261111.zip` (16,390,265 bytes, dated 2026-11-11 09:52 UTC). Every SP file in the build comes from this export.
- Domain: `domain/` is the merge of `domain-by-phase/phase-0` ... `phase-13` in phase order (`merge_domain.py`): later phase wins on scalar text, lists are unioned (steps by form, related_to by concept); for shared rules the "Per form:" lines of every phase are kept. 54 process steps that were `status: planned` because their form was in another phase are real now (their form is bundled in this build).

- Fix made for this build: 9 generated rules (fCustomerEnquiry 2, fGatePassOut 7) had an empty summary because their BR text is on indented sub-bullets that `fdoc.py` did not read. `fix_empty_brs.py` filled them from the functional docs, in `domain/` and in `domain-by-phase/phase-2` and `phase-3`.

## 2. kg validate

- Errors: **0**. Warnings: **241**.

| Warning kind | Count |
|---|---|
| dropped dangling SP-to-SP call (system or not in export) | 105 |
| two forms write the same table, no integrity rule covers both | 76 |
| data-layer SP with no .sql (runtime-built name or missing from export) | 32 |
| parameter passed that the SP does not declare | 26 |
| validation message not quoted in any rule | 2 |

The dropped SP-to-SP calls are to SQL Server system procedures (`sp_executesql`, `sp_xml_*`, `sp_OA*`, `xp_servicecontrol`, `msdb`), plus 2 calls to `Information.SOStockDetail(Output/Input)` and `Information.SOItemSummaryForItem(output/Input)`, whose names contain `/`, so the export file is named with `_` and the call cannot match it.

## 3. Counts

Nodes: 90,733. Edges: 508,940. By type in `graph/stats.json`.

| Label | Nodes |
|---|---|
| BusinessConcept | 408 |
| BusinessProcess | 77 |
| BusinessRule | 4,927 |
| Column | 26,109 |
| Control | 15,936 |
| DAClass | 389 |
| DAMethod | 3,645 |
| DTClass | 389 |
| DTMethod | 3,649 |
| DTProperty | 10,371 |
| Form | 402 |
| FormMethod | 16,375 |
| Module | 10 |
| StoredProcedure | 4,619 |
| Table | 3,404 |
| UserControl | 23 |

| Edge type | Edges |
|---|---|
| APPLIES_TO | 13,555 |
| BINDS_TO | 5,369 |
| CALLS | 10,694 |
| CALLS_SP | 5,246 |
| DELEGATES_TO | 3,644 |
| DYNAMIC_EXEC | 56 |
| EMBEDS | 654 |
| EXECUTES | 3,645 |
| GOVERNS | 6,881 |
| HANDLES | 7,262 |
| HAS_COLUMN | 26,109 |
| HAS_CONCEPT | 408 |
| HAS_CONTROL | 15,936 |
| HAS_FORM | 425 |
| HAS_METHOD | 23,669 |
| HAS_PROCESS | 77 |
| HAS_PROPERTY | 10,371 |
| HAS_STEP | 415 |
| IMPLEMENTED_BY | 6,764 |
| INVOKES | 4,422 |
| INVOLVES | 401 |
| LABELS | 4,715 |
| LEADS_TO | 14 |
| MANAGES | 399 |
| PARENT_OF | 16 |
| PASSES | 18,273 |
| PERSISTED_IN | 1,727 |
| READS | 35,958 |
| REFERENCES | 31,316 |
| RELATED_TO | 47 |
| SETS | 21,193 |
| SHARES_TABLE | 67,564 |
| USES_COLUMN | 153,854 |
| USES_CONCEPT | 2,160 |
| USES_TABLE | 17,145 |
| WRITES | 8,556 |

Form bundles per phase (each form once, in the first phase that has it; `fSingleFieldMaster` is in Phase 1 only):

| Phase | Form bundles |
|---|---|
| 0 | 4 |
| 1 | 52 |
| 2 | 21 |
| 3 | 42 |
| 4 | 27 |
| 5 | 27 |
| 6 | 12 |
| 7 | 26 |
| 8 | 11 |
| 10 | 6 |
| 11 | 75 |
| 12 | 96 |
| **All** | **399** |

Other bundles: NestedSPs (377 SPs not already in a form bundle), SingleFieldConfigs (54 SPs), Reports-13a/b/c/d/e/g. User-control folders inside form bundles are listed in `graph/phase-map.csv` as `usercontrol`.

## 4. Integrity

- Dangling edges in graph.json: **0**.
- Nodes missing id / kind / text / summary: 0 / 0 / 0 / 0.

## 5. Code property

| Label | Nodes | With code | Max length | Median length | Over 3,000 chars |
|---|---|---|---|---|---|
| DAMethod | 3,645 | 3,645 | 9,674 | 553 | 48 |
| DTMethod | 3,649 | 3,649 | 565 | 191 | 0 |
| FormMethod | 16,375 | 16,375 | 52,925 | 816 | 1,846 |
| Module | 10 | 10 | 3 | 2 | 0 |
| StoredProcedure | 4,619 | 4,587 | 276,604 | 2,343 | 1,957 |

`Module.code` is the module code (for example `MM`), not source. The code is complete: SP code is the whole export file text, method code is the whole method body as Roslyn extracted it. Only the embedding `text` cuts it to the builder's `Code:` block (CODE_CHARS = 3000).

## 6. Forms still planned

3 Form/UserControl nodes have `status: planned`: `form:fMaintenanceWorkOrder`, `form:fOtherVoucher`, `form:fQCGroupMaster`.

- `fMaintenanceWorkOrder`: not in the source. No class, file or designer of that name exists in source.zip. It is a placeholder step of the Phase 0/1 `preventive-maintenance` process. The EAM order screens that do exist are `fMaintenanceOrder` and `fMaintenanceServiceOrder` (both bundled, Phase 11).
- `fOtherVoucher`: not in the source. It is in the plan (Phase 12) and has a functional doc, but source.zip has no such file or class, and `forms\index.csv` does not list it.
- `fQCGroupMaster`: not in the source under that name. It is a placeholder step of the `goods-receipt-quality-inspection` process. The real screen is `fQCGroup` (`Code\Master Forms\fQCGroup.vb`). It is not in any phase of the plan, so it is not bundled. The QC group user control (`QCGroup`) is bundled.

## 7. Plan forms with no bundle

1 of 400 forms in the KB validation plan (Phases 0-12; Phase 13 is reports): `fOtherVoucher` (no source, see above).
Phase 13 reports: 617 of 879 have their SP in the export and are in Reports-13*; 191 (13f, payroll) read the HIRA database and 71 have no ProcName.

## 8. SHA-256

`graph/graph.json`: `c88936a85dcd1a698e47fa63c6665d863d2b099c30746fcbf5bbab1b441a0bac` (275,507,935 bytes).

