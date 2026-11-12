# KG Gap Log

> GENERATED from `kg_gaps.yaml` by `gaps.py render`. Do not edit here; edit the YAML.

**Status:** 12 open, 0 in-progress, 0 fixed, 2 noted

| Id | Status | Layer | Type | Title |
|---|---|---|---|---|
| G-001 | open | A | missing-node | Lot-stock SPs called by Purchase Bill authorization are not in the graph |
| G-002 | open | A | missing-edge | Lot tables have almost no writer SPs; lot rate column lineage is incomplete |
| G-003 | open | B | missing-node | No Freight Invoice form, concept, or process step |
| G-004 | open | B | missing-node | No concepts for stock lot / landed rate / valuation rate |
| G-005 | open | B | missing-doc | Lot-rate rule text is thin and IMPLEMENTED_BY is incomplete |
| G-006 | open | B | missing-doc | Freight-driven rate change has no rule |
| G-007 | open | B | missing-edge | Most Purchase Bill rules do not GOVERN any process |
| G-008 | open | B | missing-edge | fPurchaseBill is not a step of procure-to-pay |
| G-009 | open | C | missing-edge | Rules with no implementation link |
| G-010 | open | C | wrong-edge | Over-broad IMPLEMENTED_BY on generic rules |
| G-011 | noted | D | answer-quality | Wrong statement in the first answer (self-correction) |
| G-012 | open | A | missing-node | GRN grid columns are not nodes; "Received Qty." editability cannot be found by search |
| G-013 | open | B | missing-doc | GRN source-dependent-fields rule omits Received Qty. and the dispatch-challan and inspection exceptions |
| G-014 | noted | D | answer-quality | First answers wrongly said the GRN grid has no Received Qty. column (self-correction) |

Layers: **A** extraction; **B** functional (YAML); **C** cross-layer links; **D** doc quality

## Gaps

### G-001  Lot-stock SPs called by Purchase Bill authorization are not in the graph
- Status: **open** | Layer: A | Type: missing-node | Found: 2026-11-06 by Claude (Sonnet 5.5) + user
- Question asked: How does lot rate change in purchase bill?
- Nodes: `sp:finance.pbpbauthorize`, `sp:finance.fifiauthorize`, `sp:inventory.igrnauthorize`, `sp:inventory.invlotmaterialtransaction`, `sp:inventory.invlotbilltaxtransaction`, `sp:inventory.invlotbillmapcalculation`
- Evidence: sp:finance.pbpbauthorize code EXECs Inventory.InvLotMaterialTransaction, Inventory.InvLotBillTaxTransaction, Inventory.InvLotBillMapCalculation (and masterdata.TDSTCSThreholdStatus). None exists as a node, and pbpbauthorize has no outgoing CALLS_SP. The three SPs appear only inside the code text of pbpbauthorize, fifiauthorize and igrnauthorize. Impact: the lot rate math (ItemRate/DiffRate/VRate/LRate/DiffInLRate on InvLotSummary/InvLotBillDetail) for GRN-based bills cannot be answered from the KG.
- Fix: The extractor loads only SPs bundled per form (source_files phase-1/.../fPurchaseBill/StoredProcedures). Add a transitive SP closure step: parse each SP's EXEC targets and pull any missing SP into the graph from the DB scripts folder with a bundle tag such as shared-inventory-lot. Re-run `kg build` and check pbpbauthorize -CALLS_SP-> returns the 4 SPs.

### G-002  Lot tables have almost no writer SPs; lot rate column lineage is incomplete
- Status: **open** | Layer: A | Type: missing-edge | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `table:inventory.invlotsummary`, `table:inventory.invlotdetail`, `table:inventory.invlotbilldetail`, `table:inventory.invlottaxdetail`, `column:inventory.invlotdetail.lrate`, `column:inventory.invlotbilldetail.vrate`, `column:inventory.invlotbilldetail.diffinlrate`
- Evidence: Writers found: InvLotSummary <- igrnauthorize, fifiauthorize, pbpbauthorize; InvLotBillDetail <- vouchersavefortransaction, fifiauthorize (not pbpbauthorize); InvLotTaxDetail <- fifiauthorize only. For PBPB the writes happen inside the missing SPs (G-001). column:inventory.invlotdetail.lrate is written only by fifiauthorize, so it looks as if only the freight invoice changes the landed rate. Impact analysis and field lineage on lot columns are misleading.
- Fix: Resolved by G-001. Then verify WRITES on the 4 lot tables include the three lot SPs and USES_COLUMN shows ops=[write] for lrate, vrate, diffinlrate, itemrate.

### G-003  No Freight Invoice form, concept, or process step
- Status: **open** | Layer: B | Type: missing-node | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `sp:finance.fifiauthorize`, `table:finance.freightinvoicemain`, `rule:shared-write-finance-freightinvoicemain`
- Evidence: Name search over Form/BusinessConcept/BusinessProcess for freight, lot, landed, invoice, stock valu returns nothing. sp:finance.fifiauthorize (tag FIFI, tables Finance.FreightInvoiceMain/Detail) changes lot rates and is called from igrnauthorize and ilpusave. The rule shared-write-finance-freightinvoicemain exists but no form owns the concept.
- Fix: Add the freight invoice form YAML (domain/forms/<form>.yaml; find the form from Finance.FreightInvoiceMain writers via USES_TABLE), add concept:freight-invoice, and attach it to the P2P / payment-flow process.

### G-004  No concepts for stock lot / landed rate / valuation rate
- Status: **open** | Layer: B | Type: missing-node | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `form:fPurchaseBill`, `concept:purchase-bill`
- Evidence: 62 concepts exist, none for Stock Lot, Landed Rate (LRate), Valuation Rate (VRate), Rate difference (DiffRate) or PO rate validation. fPurchaseBill MANAGES only concept:purchase-bill and USES_CONCEPT lists 28 concepts, none about lots or rates. Functional-layer search for "lot rate" hits only rules and columns; PERSISTED_IN cannot map the lot tables.
- Fix: Add concepts stock-lot, landed-rate, valuation-rate (synonyms LRate, VRate, MAP rate, lot rate) to domain/concepts.yaml, RELATED_TO goods-receipt-note, purchase-bill, purchase-order, and PERSISTED_IN the Inventory.InvLot* tables. Link the rules in G-005 to them via applies_to.

### G-005  Lot-rate rule text is thin and IMPLEMENTED_BY is incomplete
- Status: **open** | Layer: B | Type: missing-doc | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `rule:purchase-bill-stock-on-authorization`, `rule:purchase-bill-voucher-vs-lot-and-po-rate`, `rule:purchase-bill-authorization-limit`, `sp:finance.pbpbauthorize`, `sp:customize.iskconporatevalidation`
- Evidence: (1) stock-on-authorization says rate = basic amount / billed quantity. Code (PBPBAuthorize) also divides by ChallanQty when QtybasedOn=1 else Qty, rounds to 2 decimals (decimal(12,2)), and only does this for PBSourceDocumentNo=1 AND IsUpdateStock=1. (2) It is IMPLEMENTED_BY only pbpbauthorize; the lot SPs (G-001) are not linked. (3) The GRN/SIN path (percentage split by ReceivedQty x (MAPRate or VRate), then InvLotBillTaxTransaction and InvLotBillMapCalculation) is one sentence. (4) voucher-vs-lot-and-po-rate mentions "client rule 118"; the code gates on POMain.IsPORateValidationRequired = 1 and FreightTypeNo = 1 (To Pay) in schema Customize, and rule number 118 is not traceable in the code that was read. (5) The PO-rate cap formula (ItemRate + sum DiffRate other doc + sum DiffRate this doc > POItemDetail.Rate) is not in any rule text. (6) Verify purchase-bill-authorization-limit describes the PO LRate comparison (form 202, POAmendmentItemLRate.LRate, LimitFrom/LimitTo).
- Fix: Rewrite these rule descriptions in domain/rules.yaml with the formulas and conditions; add implemented_by for the lot SPs after G-001; confirm what "rule 118" means with a domain owner.

### G-006  Freight-driven rate change has no rule
- Status: **open** | Layer: B | Type: missing-doc | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `sp:finance.fifiauthorize`, `process:payment-flow`
- Evidence: FIFIAuthorize allocates freight to lots by value, sets DiffRate, VRate, DiffInLRate and does InvLotSummary.VRate += DiffRate, LRate += DiffInLRate. @SetRateZero=0 zeroes all rate changes when the PO is "Against DO" (PORefDocumentTypeNo=9). No BusinessRule describes this.
- Fix: Add rules freight-invoice-lot-rate-allocation and against-do-po-no-rate-change; applies_to the freight form (G-003) and the concepts (G-004); implemented_by sp:finance.fifiauthorize; governs payment-flow.

### G-007  Most Purchase Bill rules do not GOVERN any process
- Status: **open** | Layer: B | Type: missing-edge | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `form:fPurchaseBill`, `process:payment-flow`, `process:gst-tax-determination`
- Evidence: Of 119 rules that APPLY_TO form:fPurchaseBill, among the purchase-bill-* rules only stock-on-authorization, update-stock-and-dropshipment and voucher-vs-lot-and-po-rate have a GOVERNS edge (to gst-tax-determination and payment-flow). The rest have none, so top-down navigation (Process -> rules) misses almost all bill rules.
- Fix: Set processes: for each purchase-bill rule in the rule YAML (usually payment-flow; GST ones also gst-tax-determination). Script it: default every rule whose only applies_to form is fPurchaseBill to payment-flow, then review GST rules by hand.

### G-008  fPurchaseBill is not a step of procure-to-pay
- Status: **open** | Layer: B | Type: missing-edge | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `form:fPurchaseBill`, `process:procure-to-pay`, `process:payment-flow`
- Evidence: process:procure-to-pay has no HAS_STEP to form:fPurchaseBill; the form is a step only of gst-tax-determination and payment-flow. The module is FI while the PO flow lives in MM.
- Fix: Decide whether the bill belongs in P2P (probably yes, the step after GRN). If yes, add the step to domain/processes/procure-to-pay.yaml; if no, document the hand-off (LEADS_TO) to payment-flow.

### G-009  Rules with no implementation link
- Status: **open** | Layer: C | Type: missing-edge | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `rule:three-way-match`, `rule:purchase-bill-client-custom-validations`, `sp:finance.pbpbvalidate`, `sp:inventory.ilpuvalidation`
- Evidence: three-way-match (bill vs PO vs receipt) and purchase-bill-client-custom-validations have IMPLEMENTED_BY = []. The three-way check is probably in Finance.PBPBValidate or Inventory.ILPUValidation; not verified.
- Fix: Read those SPs and add implemented_by, or mark the rule status not-implemented if it is a policy only.

### G-010  Over-broad IMPLEMENTED_BY on generic rules
- Status: **open** | Layer: C | Type: wrong-edge | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `rule:unique-master-names`, `rule:authorized-document-lock`, `rule:document-numbering`
- Evidence: unique-master-names links about 60 methods/SPs and authorized-document-lock about 75; document-numbering also GOVERNS 7 processes. They show up for every form (e.g. fPurchaseBill) and drown out form-specific rules.
- Fix: Keep them as global rules but do not APPLIES_TO each form, or add a scope: global property so search and expand can filter them out.

### G-011  Wrong statement in the first answer (self-correction)
- Status: **noted** | Layer: D | Type: answer-quality | Found: 2026-11-06 by Claude
- Question asked: How does lot rate change in purchase bill?
- Nodes: `sp:finance.fifiauthorize`, `rule:purchase-bill-voucher-vs-lot-and-po-rate`
- Evidence: The first answer said the rule's IMPLEMENTED_BY pointed at fifiauthorize. It did not (it points to fPurchaseBill.Save, IskconPORateValidation, VoucherVsLotValidation). fifiauthorize surfaced from a USES_COLUMN query on lrate/vrate/diffinlrate and was mislabeled as the bill flow; it is the freight invoice.
- Fix: Lesson, no KG change: USES_COLUMN hits with no form link are misleading when the real writer SPs are absent (G-001/G-002). Review flashcards about rate/lot against the SP code.

### G-012  GRN grid columns are not nodes; "Received Qty." editability cannot be found by search
- Status: **open** | Layer: A | Type: missing-node | Found: 2026-11-06 by Claude (Sonnet 5.5) + user
- Question asked: Where is the Received Qty. column of the GRN form editable (especially when GRN is created against gate entry)?
- Nodes: `form:fGRN`, `control:fGRN.ugdItemDetails`, `method:fGRN.GRNAgainst`, `method:fGRN.ugdItemDetails_InitializeLayout`, `method:fGRN.ugdItemDetails_BeforeCellActivate`
- Evidence: Searching "GRN form received quantity editable gate entry" returned no node for the Received Qty. column. Grid columns exist only as string keys inside fGRN.vb (e.g. Band.Columns("Received Qty.")); Control nodes stop at the grid (ugdItemDetails, ugdGateEntryDetails). The search surfaced only the BR-46 rule text, which names Challan Qty., so Claude concluded no "Received Qty." column existed (see G-014). The real behaviour: nothing in GRNAgainst or ugdItemDetails_InitializeLayout sets Received Qty. to NoEdit, so it is editable for every source including Gate Entry; only BeforeCellActivate locks it (bIsInspectionDone). The lot grid ugdLotDetail locks it the same way. Editing it drives Accepted Qty. = Received - Rejected - FOC, Amount, Excess Qty., and ValidateItemDetail balance/tolerance checks.
- Fix: Extractor: emit a GridColumn node (id like gridcol:fGRN.ugdItemDetails.Received Qty.) for each Band.Columns("<key>") reference, with edges HAS_COLUMN from the grid Control and SETS_ACTIVATION / READS / WRITES from the FormMethods, carrying the activation value (AllowEdit/NoEdit/ActivateOnly/Hidden) and the guarding condition (source document, inspection state). Interim: add a domain rule for column editability (see G-013). Verify with search("Received Qty. editable") returning it.

### G-013  GRN source-dependent-fields rule omits Received Qty. and the dispatch-challan and inspection exceptions
- Status: **open** | Layer: B | Type: missing-doc | Found: 2026-11-06 by Claude (Sonnet 5.5) + user
- Question asked: Where is the Received Qty. column of the GRN form editable (especially when GRN is created against gate entry)?
- Nodes: `rule:material-receipt-note-source-dependent-fields`, `form:fGRN`
- Evidence: Rule text (Functional_Doc_fGRN.md BR-46) says "Challan Qty. is not editable for Gate Entry". Code (GRNAgainst, gate-entry branch) sets Challan Qty. NoEdit but flips it to AllowEdit when a selected gate entry has GateEntrySourceNo=5 (dispatch challan). The rule never mentions Received Qty., which is the editable quantity for gate-entry GRNs, nor Accepted Qty. (editable only when btGRNQtyValidateOn=2 or the item has IsMultiRateInGRN), nor the post-inspection lock in ugdItemDetails_BeforeCellActivate. IMPLEMENTED_BY lists only GRNAgainst and ugdItemDetails_AfterCellUpdate; InitializeLayout, InitializeRow and BeforeCellActivate (where the activation is actually decided) are not linked.
- Fix: Rewrite the rule in domain/rules.yaml with a per-source table of Challan/Received/Accepted Qty. activation, the GateEntrySourceNo=5 exception, btGRNQtyValidateOn and IsMultiRateInGRN conditions and the inspection lock. Add implemented_by for method:fGRN.ugdItemDetails_InitializeLayout, ugdItemDetails_InitializeRow, ugdItemDetails_BeforeCellActivate. Consider a separate rule grn-received-qty-editability so it ranks for this question.

### G-014  First answers wrongly said the GRN grid has no Received Qty. column (self-correction)
- Status: **noted** | Layer: D | Type: answer-quality | Found: 2026-11-06 by Claude (Sonnet 5.5)
- Question asked: Where is the Received Qty. column of the GRN form editable (especially when GRN is created against gate entry)?
- Nodes: `form:fGRN`, `method:fGRN.GRNAgainst`
- Evidence: The first answer treated the KG as complete: it said the grid had no column literally keyed "Received Qty." and answered for Challan/Accepted Qty. instead. The user pointed out the column exists; direct reading of fGRN.vb confirmed it (lines 269, 1276, 2234, 4537, 6700). Partly a KG gap (G-012) and partly a method error: a graph search that returns nothing for a column name is not proof the column is absent, and the search/get_node reads were never checked against the source. The KG server also dropped mid-session, so the confirming read was done on the source file.
- Fix: Lesson, no KG change: for "is column X editable" questions, grep the form source for the column key (Band.Columns("X")) and check every handler that sets CellActivation (GRNAgainst, InitializeLayout, BeforeCellActivate) before answering; tell the user when a graph miss may be an extraction gap.

## Map: Form -> Module / Concepts / Process / Business Rules

### form:fPurchaseBill  (Purchase Bill)
| Item | Value |
|---|---|
| Module | **FI** |
| Status / generated | active / 2026-11-06 |
| Manages | purchase-bill |
| Uses concepts (29) | company, material-item, unit-of-measure, vendor, make, warehouse, bin, gst-category, hsn-sac-code, account-determination-rule, account-group, accounting-voucher, chapter-heading, chart-of-accounts, currency, currency-exchange-rate, document-receipt, finance-book, gate-entry, goods-receipt-note, item-technical-grade, ledger-account, material-issue, payment-plan, purchase-order, tdc-account-rule, tdc-charge, tdc-group, vendor-location |
| Process steps | gst-tax-determination, payment-flow |
| Rules applying (total in KG) | 119 |
| SPs called (33) | finance.pbpbsave, finance.pbpbvalidate, finance.pbpbauthorize, finance.pbpbdelete, finance.pbpbloaddata, finance.pbpbsearchdata, finance.pbpbfillvalues, finance.pbpbfillvaluesdependent, finance.pbpbfillvaluespowise, finance.pbpbsaveitemdetail, finance.pbpbsaveitemserialdetail, finance.pbpbsaveitemtaxdetail, finance.pbpbsaveadvancedetail, finance.pbpbsavenotesdetail, finance.pbpbsavesummary, finance.pbpbsavetaxconcessionformdetail, finance.pbpbwarehousedetail, customize.iskconporatevalidation, inventory.vouchervslotvalidation, inventory.ilpuvalidation, finance.paymentschedulesave, finance.vouchersavefortransaction, finance.vouchersavestatuory, finance.accountopening, finance.ieipsave, finance.ieipsaveitemdetail, finance.ieipsaveitemtaxdetail, finance.ieipsavepostingsummary, finance.ieipvalidate, globaldata.itemtypecheck, globaldata.vendorlocationselect, masterdata.itemaccountdetail, odtdispatchchallan.procedurename |

| Rule | Type | Implemented by | Governs | Gaps |
|---|---|---|---|---|
| purchase-bill-stock-on-authorization | calculation | finance.pbpbauthorize | gst-tax-determination, payment-flow | G-001, G-005 |
| purchase-bill-voucher-vs-lot-and-po-rate | calculation | fPurchaseBill.Save, inventory.vouchervslotvalidation, customize.iskconporatevalidation | gst-tax-determination, payment-flow | G-005 |
| purchase-bill-update-stock-and-dropshipment | default | fPurchaseBill.ucmbSourceDocument_ValueChanged, fPurchaseBill.uchkDropShipment_CheckedChanged | gst-tax-determination, payment-flow | - |
| purchase-bill-authorization-limit | validation | finance.pbpbauthorize | - | G-005, G-007 |
| purchase-bill-double-billing-on-authorization | workflow | finance.pbpbauthorize | - | G-007 |
| purchase-bill-voucher-presence | calculation | finance.pbpbauthorize | - | G-007 |
| purchase-bill-purchase-voucher | calculation | fPurchaseBill.CreateVoucher | - | G-007 |
| purchase-bill-qty-basis | calculation | fPurchaseBill.ValidateItemDetail, fPurchaseBill.ugdItemDetail_AfterCellUpdate, fPurchaseBill.CalculateTaxes | - | G-007 |
| purchase-bill-entry-mode-by-source | calculation | fPurchaseBill.ugdItemDetail_AfterCellUpdate, fPurchaseBill.ReadOnlyColumn | - | G-007 |
| purchase-bill-unit-conversion | calculation | fPurchaseBill.uoptUnitType_ValueChanged | - | G-007 |
| purchase-bill-net-amount | calculation | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-bill-amount-warning | calculation | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-bill-tax-summary | calculation | fPurchaseBill.SaveSummary | - | G-007 |
| purchase-bill-item-lines | validation | fPurchaseBill.ValidateItemDetail, fPurchaseBill.SaveItemDetail | - | G-007 |
| purchase-bill-at-least-one-receipt-and-item-per-receipt | validation | fPurchaseBill.ValidateGRNDetails, inventory.ilpuvalidation | - | G-007 |
| purchase-bill-eligible-receipts | workflow | finance.pbpbfillvaluesdependent | - | G-007 |
| purchase-bill-billable-lines | default | finance.pbpbfillvaluesdependent | - | G-007 |
| purchase-bill-gst-applicability | control | finance.pbpbfillvaluesdependent | - | G-007 |
| purchase-bill-advance-and-recurring-agreement-pos | control | finance.pbpbvalidate | - | G-007 |
| purchase-bill-advance-list | calculation | fPurchaseBill.AdvanceAutoFill, fPurchaseBill.AdvanceBinding, fPurchaseBill.AdvanceDetailHightLightRows | - | G-007 |
| purchase-bill-advance-save | calculation | fPurchaseBill.Save, fPurchaseBill.SaveAdvanceDetail | - | G-007 |
| purchase-bill-adjusting-limits | calculation | fPurchaseBill.ValidateAdvanceDetail, fPurchaseBill.ugdAdvanceDetail_BeforeCellUpdate, fPurchaseBill.CalculateTotalAdvance | - | G-007 |
| purchase-bill-adjust-advance-default | default | fPurchaseBill.FillValues, fPurchaseBill.ValidateForm | - | G-007 |
| purchase-bill-advance-adjustment-voucher | validation | fPurchaseBill.ValidateForm, fPurchaseBill.Save, fPurchaseBill.createVoucherAdvance | - | G-007 |
| purchase-bill-imprest-balance | calculation | fPurchaseBill.GetAccountBalance, fPurchaseBill.ValidateAdvanceDetail | - | G-007 |
| purchase-bill-imprest-pairing | calculation | fPurchaseBill.ValidateAdvanceDetail | - | G-007 |
| purchase-bill-payment-mode | validation | fPurchaseBill.ValidateGeneralDetail, fPurchaseBill.LoadGRNdetail | - | G-007 |
| purchase-bill-payment-schedule-calculation | calculation | fPurchaseBill.PaymentSchedule | - | G-007 |
| purchase-bill-schedule-checks | calculation | fPurchaseBill.ValidatePaymentSchdule | - | G-007 |
| purchase-bill-schedule-save | control | fPurchaseBill.Save, fPurchaseBill.SavePaymentSchedule | - | G-007 |
| purchase-bill-cash-counter | workflow | finance.pbpbsave | - | G-007 |
| purchase-bill-document-receipt-single-use | control | finance.pbpbsave | - | G-007 |
| purchase-bill-gst-category | calculation | fPurchaseBill.ValidateItemDetail | - | G-007 |
| purchase-bill-gst-exempted | calculation | fPurchaseBill.ValidateForm, fPurchaseBill.ucmbVendorLocation_ValueChanged | - | G-007 |
| purchase-bill-hsn-on-authorization | default | fPurchaseBill.ValidateItemDetail, fPurchaseBill.ugdItemDetail_AfterCellUpdate | - | G-007 |
| purchase-bill-intra-and-inter-state-gst | calculation | fPurchaseBill.ValidateForm | - | G-007 |
| purchase-bill-tax-validation | validation | fPurchaseBill.ValidateForm | - | G-007 |
| purchase-bill-tax-rule-exclusivity | calculation | fPurchaseBill.ValidateGeneralDetail, fPurchaseBill.ValidateItemDetail, fPurchaseBill.ucmbServiceTaxAbatementRule_ValueChanged | - | G-007 |
| purchase-bill-tax-rule-save | calculation | fPurchaseBill.Save, fPurchaseBill.SaveItemDetail | - | G-007 |
| purchase-bill-foreign-vendor-taxable-value | calculation | fPurchaseBill.ValidateItemDetail, fPurchaseBill.ucmbVendorLocation_ValueChanged | - | G-007 |
| purchase-bill-unregistered-vendor-gst | workflow | fPurchaseBill.ValidateItemDetail | - | G-007 |
| purchase-bill-service-tax-rule-client-rule | calculation | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-tds-tcs | validation | fPurchaseBill.ValidateTDSTCS, masterdata.checkvalidationfortdstcs | - | G-007 |
| purchase-bill-e-way-bill-check-for-direct | calculation | fPurchaseBill.ValidateGeneralDetail, fPurchaseBill.ucmbSourceDocument_ValueChanged | - | G-007 |
| purchase-bill-e-way-bill-date | control | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-invoice-date | validation | fPurchaseBill.ValidateGeneralDetail, fPurchaseBill.ucmbVendorBillNo_TextChanged | - | G-007 |
| purchase-bill-vendor-bill-date | control | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-vendor-bill-no | validation | fPurchaseBill.FillValues, fPurchaseBill.ValidateGeneralDetail, finance.pbpbfillvaluesdependent | - | G-007 |
| purchase-bill-receipt-date | control | fPurchaseBill.ValidateGRNDetails | - | G-007 |
| purchase-bill-expiry-date | control | fPurchaseBill.ValidateItemDetail | - | G-007 |
| purchase-bill-currency | validation | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-single-currency | calculation | fPurchaseBill.ValidateGRNDetails, fPurchaseBill.ugdGRNDetails_AfterCellUpdate | - | G-007 |
| purchase-bill-capital-items | control | fPurchaseBill.ValidateItemDetail, globaldata.itemtypecheck | - | G-007 |
| purchase-bill-warehouse-for-direct | workflow | fPurchaseBill.ValidateItemDetail, fPurchaseBill.ugdItemDetail_AfterCellUpdate | - | G-007 |
| purchase-bill-legacy-excise-posting | validation | fPurchaseBill.LoadGRNdetail, fPurchaseBill.Save, fPurchaseBill.ValidateInExcisePostingDetails | - | G-007 |
| purchase-bill-location-master-completeness-on-authorization | workflow | fPurchaseBill.ValidateGeneralDetail | - | G-007 |
| purchase-bill-authorization-posting-view | validation | fPurchaseBill.ValidateForm, fPurchaseBill.FinancePostingVisibility | - | G-007 |
| purchase-bill-maintenance-rebuild | control | fPurchaseBill.fPurchaseBill_KeyUp | - | G-007 |
| purchase-bill-client-custom-validations | validation | **none** | - | G-007, G-009 |
| three-way-match | control | **none** | - | G-009 |

Global rules also applying: unique-master-names, authorized-document-lock, detail-replacement-on-save, document-numbering, inactive-flag-handling, mandatory-document-fields, transaction-delete-rules (gaps: G-010). ~45 auto-generated shared-write-* integrity rules (one per shared table, e.g. shared-write-inventory-invlotsummary).

## Queries to refresh the map

**form_overview**
```cypher
MATCH (m:Module)-[:HAS_FORM]->(f:Form {id:$form})
OPTIONAL MATCH (f)-[:MANAGES]->(cm:BusinessConcept)
OPTIONAL MATCH (f)-[:USES_CONCEPT]->(cu:BusinessConcept)
OPTIONAL MATCH (p:BusinessProcess)-[:HAS_STEP]->(f)
RETURN m.code, f.title, collect(DISTINCT cm.id) AS manages, collect(DISTINCT cu.id) AS uses, collect(DISTINCT p.id) AS processes
```

**form_rules**
```cypher
MATCH (r:BusinessRule)-[:APPLIES_TO]->(f:Form {id:$form})
OPTIONAL MATCH (r)-[:IMPLEMENTED_BY]->(i)
OPTIONAL MATCH (r)-[:GOVERNS]->(p:BusinessProcess)
RETURN r.id, r.rule_type, collect(DISTINCT i.id) AS impl, collect(DISTINCT p.id) AS procs
```

**missing_sp_check**
```cypher
MATCH (s:StoredProcedure) WHERE s.code CONTAINS $spName RETURN s.id
```
