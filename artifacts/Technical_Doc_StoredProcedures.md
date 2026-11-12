# Technical Documentation: Stored Procedures

This document provides database-level technical documentation for all stored procedures across the SpectrumERP system (Material Group, Material SubGroup Master, Unit Master, and Shared Quality Control). It details the operational characteristics, parameter contracts, database CRUD footprint, internal SQL algorithms, return formats, and error handling mechanisms for each procedure without coupling to user interface components or application data layers.

---

## [masterdata].[MMIGDelete]

**Purpose & Database Operations:** Permanently purges a material group master record, its multi-company mapping records, and all associated child quality control parameter specifications within an autonomous database transaction.  
**Parameters:** `@GroupNo` (`smallint`, primary key identifier of the material group to delete).  
**Tables Affected / Queried:** `DELETE` on `masterdata.mGroupQCParameterDetail`, `masterdata.mGroupMasterCompanyDetail`, and `masterdata.mGroupMaster`.  
**Internal SQL Logic:** Manages an autonomous database transaction using `BEGIN TRANSACTION ... COMMIT TRANSACTION`. It enforces strict foreign-key dependency deletion order: first purges child quality parameters from `masterdata.mGroupQCParameterDetail` where `GroupNo = @GroupNo`, then deletes multi-company distribution records from `masterdata.mGroupMasterCompanyDetail` where `GroupNo = @GroupNo`, and finally deletes the primary header record from `masterdata.mGroupMaster` where `GroupNo = @GroupNo`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on successful commit. If any deletion operation fails (e.g., due to foreign key references in downstream item masters), the `CATCH` block triggers an immediate `ROLLBACK TRANSACTION` and returns `SELECT 0, ERROR_MESSAGE()`.

---

## [masterdata].[MMIGFillValues]

**Purpose & Database Operations:** Returns active material category selection catalogs and provides an empty relational schema definition for bulk fast-entry operations.  
**Parameters:** `@CompanyNo` (`int`, active operating company filter), `@GroupNo` (`smallint`, current group identifier used for preservation during update operations).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mCategoryMaster`, `masterdata.mCategoryMasterCompanyDetail`, and `masterdata.mGroupMaster`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Produces two distinct tabular result sets: Result Set 0 (Category Catalog) queries active, authorized categories mapped to `@CompanyNo` (`cmcd.Inactive = 0`) joined with `masterdata.mCategoryMasterCompanyDetail`, unioned with the specific parent category of `@GroupNo` from `masterdata.mGroupMaster` (Columns: `CategoryNo`, `Category Name`, `Code`, `Id`); Result Set 1 (Fast Entry Schema) emits an empty column structure (`WHERE 1 = 2`) defining `[Category Name]`, `[Code]`, `[Group Name]`, and `[Remarks]`.  
**Return Contract & Error Handling:** Returns two DataTables. Runtime errors are intercepted by a `CATCH` block that logs the incident directly into `masterdata.mErrorLog` (recording system timestamp, error number, severity, state, procedure name, line number, error description, system user, and `FormCode = 'MMIG'`).

---

## [masterdata].[MMIGFillValuesDependent]

**Purpose & Database Operations:** Calculates the next sequential two-digit numeric group code available under a selected parent material category.  
**Parameters:** `@CategoryNo` (`smallint`, target parent material category identifier).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mGroupMaster`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Evaluates all existing numeric codes within the specified category (`IsNumeric(Code) = 1`) in `masterdata.mGroupMaster`, computes `ISNULL(MAX(Code), 0) + 1`, and formats the integer into a zero-padded 2-character string using `RIGHT(REPLICATE('0', 2) + CONVERT(varchar, ...), 2)`.  
**Return Contract & Error Handling:** Returns a single-column, single-row scalar result set containing the formatted code string. Runtime errors are caught and logged directly into `masterdata.mErrorLog` under `FormCode = 'MMIG'`.

---

## [masterdata].[MMIGLoadData]

**Purpose & Database Operations:** Retrieves complete header information and associated child quality control parameter specifications for a single material group record.  
**Parameters:** `@GroupNo` (`smallint`, target material group identifier), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `masterdata.mGroupQCParameterDetail`, and `masterdata.mQCParameters`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Emits two relational result sets: Result Set 0 (Header Attributes) retrieves `GroupCode`, `CategoryNo`, `GroupName`, and company-level `InActive` status by joining `masterdata.mGroupMaster` with `masterdata.mGroupMasterCompanyDetail` on `@GroupNo`; Result Set 1 (Quality Specifications) joins child table `masterdata.mGroupQCParameterDetail` with definition table `masterdata.mQCParameters` on `QCParameterNo` to return `[QC Parameter Name]`, `[Unit]`, `[Standard Value]`, empty decimal placeholders for `[Standard Value2]`, `[Actual Value1]`, and `[Actual Value2]`, `[Tolerance Value]`, `[Tolerance Type]`, `[Tolerance Unit]`, `[Deduction On]`, `[Formula Type]`, `[Deduction Rate]`, `[Deduction Type]`, and `[Double Deduction From]`.  
**Return Contract & Error Handling:** Returns two DataTables. Unhandled exceptions in the `TRY` block are captured by `CATCH` and persisted to `masterdata.mErrorLog` under `FormCode = 'MMIG'`.

---

## [masterdata].[MMIGSave]

**Purpose & Database Operations:** Performs an atomic insert or update of the primary Material Group master record, synchronizes multi-company access across the enterprise, purges outdated quality profiles, and cascades composite code updates to downstream inventory items.  
**Parameters:** `@GroupNo` (`smallint`, nullable/`0` to indicate an insert operation, or a valid ID to indicate an update), `@CategoryNo` (`smallint`, mandatory foreign key referencing `mCategoryMaster`), `@GroupCode` (`varchar(2)`, mandatory 2-character group identifier), `@GroupName` (`varchar(100)`, mandatory descriptive name), `@LoginNo` (`int`, mandatory audit user identifier), `@DocumentStatusNo` (`tinyint`, optional status code with default `30` indicating Authorized).  
**Tables Affected / Queried:** `INSERT`/`UPDATE` on `masterdata.mGroupMaster`, `INSERT` on `masterdata.mGroupMasterCompanyDetail`, `DELETE` on `masterdata.mGroupQCParameterDetail`, `UPDATE` on downstream `masterdata.mItemMaster`, and read access on `masterdata.mCompanyMaster`, `masterdata.mSubGroupMaster`, and `masterdata.mCategoryMaster`.  
**Internal SQL Logic:** Evaluates whether `ISNULL(@GroupNo, 0) = 0`. In insert mode, it writes the record into `masterdata.mGroupMaster`, populates audit columns (`CreatedBy`, `CreatedDate`, and sets `AuthorizedBy` and `AuthorizedDate` when `@DocumentStatusNo = 30`), retrieves the generated identity using `IDENT_CURRENT('[masterdata].[mGroupMaster]')`, and inserts active distribution records (`Inactive = 0`) into `masterdata.mGroupMasterCompanyDetail` for all registered entities in `masterdata.mCompanyMaster`. In update mode, it deletes prior quality profiles from `masterdata.mGroupQCParameterDetail` for the specified `@GroupNo`, updates header fields and modification audit stamps in `masterdata.mGroupMaster`, and recalculates the 4-tier composite item code in `masterdata.mItemMaster` (`FullCode = CM.Code + gm.Code + sg.Code + IM.Code`) across all child subgroups linked to this group.  
**Return Contract & Error Handling:** Returns `SELECT 1, @GroupNo` upon successful completion. If an unhandled exception occurs, the `CATCH` block traps the runtime failure and returns `SELECT 0, ERROR_MESSAGE()`. Participates in caller-managed external transaction boundaries.

---

## [masterdata].[MMIGSaveQCParameter]

**Purpose & Database Operations:** Commits an individual quality inspection parameter specification row into the child quality details table for a parent material group.  
**Parameters:** `@GroupNo` (`smallint`, foreign key referencing parent material group), `@QCParameterNo` (`smallint`, foreign key referencing quality inspection parameter), `@StandardValue` (`decimal(9,3)`, target baseline specification), `@ToleranceValue` (`decimal(9,3)`, permissible variation window), `@DeductionRate` (`tinyint`, deduction rate calculation option), `@DeductionType` (`tinyint`, single or double penalty designation), `@DoubleDeductionFrom` (`decimal(9,3)`, secondary penalty escalation threshold).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mGroupQCParameterDetail`.  
**Internal SQL Logic:** Directly inserts a parameter configuration row into `masterdata.mGroupQCParameterDetail` matching the supplied arguments.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success. On failure, returns `SELECT 0, ERROR_MESSAGE()`. Participates in an external caller-level transaction sequence where all previous parameters for `@GroupNo` were purged prior to batch insertion.

---

## [masterdata].[MMIGSearchData]

**Purpose & Database Operations:** Executes dynamic search lookup queries configured in central system metadata tables for the Material Group module.  
**Parameters:** `@CompanyNo` (`tinyint`, operating company filter passed to the dynamic search routine).  
**Tables Affected / Queried:** `SELECT` on `GlobalData.FormSearchDataDetail`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Queries metadata table `GlobalData.FormSearchDataDetail` where `FormNo = 26` and `InActive = 0` to retrieve the registered search procedure name, concatenates the procedure name with the `@CompanyNo` parameter string (`@Procedure = ProcedureName + ' ' + Convert(varchar(3), @CompanyNo)`), and executes the dynamically resolved search query using `EXEC (@Procedure)`.  
**Return Contract & Error Handling:** Returns the search result set produced by the resolved dynamic procedure. Runtime failures are intercepted by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MMIG'`.

---

## [masterdata].[MMIGValidate]

**Purpose & Database Operations:** Enforces enterprise uniqueness constraints for material group names and codes prior to database persistence.  
**Parameters:** `@GroupName` (`varchar(100)`, group description to validate), `@GroupNo` (`smallint`, nullable/`0` for new records or existing record ID for modification exclusion), `@CompanyNo` (`smallint`, operating company identifier), `@CategoryNo` (`smallint`, parent category identifier), `@GroupCode` (`varchar(2)`, 2-character group code to validate).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mGroupMaster` and `masterdata.mGroupMasterCompanyDetail`.  
**Internal SQL Logic:** Executes two sequential existence checks excluding the current `@GroupNo`: (1) *Name Uniqueness:* Verifies whether `@GroupName` already exists under the same `@CategoryNo` for the specified `@CompanyNo` in `masterdata.mGroupMasterCompanyDetail`. If found, it terminates immediately and returns `SELECT 0, 'Duplicate Group Name is not allowed.', 1` (status `0`, message text, and focus code `1`); (2) *Code Uniqueness:* Verifies whether `@GroupCode` already exists under the same `@CategoryNo` enterprise-wide in `masterdata.mGroupMaster`. If found, it terminates immediately and returns `SELECT 0, 'Duplicate Group Code is not allowed.', 2` (status `0`, message text, and focus code `2`).  
**Return Contract & Error Handling:** Returns `SELECT 1` if all validation assertions pass. Exceptions in the `TRY` block are captured by `CATCH` and returned as `SELECT 0, ERROR_MESSAGE()`.

---

## [masterdata].[MSGMDelete]

**Purpose & Database Operations:** Permanently purges a material subgroup master record, its multi-company mappings, and all associated child collections (bin cards, technical grades, division mappings, makes, QC parameters, units, and vendors) within an autonomous database transaction.  
**Parameters:** `@SubGroupNo` (`smallint`, primary key identifier of the material subgroup to purge).  
**Tables Affected / Queried:** `DELETE` on `masterdata.mBinCardSubgroupDetail`, `masterdata.mSubGroupTechnicalGrade`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail`, `masterdata.mSubGroupMasterCompanyDetail`, and `masterdata.mSubGroupMaster`.  
**Internal SQL Logic:** Enforces an autonomous database transaction (`BEGIN TRANSACTION ... COMMIT TRANSACTION`). Purges child records in strict foreign-key dependency order: deletes bin card mappings from `mBinCardSubgroupDetail`, technical grades from `mSubGroupTechnicalGrade`, division mappings from `mSubGroupDivisionDetail`, make mappings from `mSubGroupMakeDetail`, QC parameters from `mSubGroupQCParameterDetail`, unit mappings from `mSubGroupUnitDetail`, vendor mappings from `mSubGroupVendorDetail`, multi-company distributions from `mSubGroupMasterCompanyDetail`, and finally the parent record from `mSubGroupMaster`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on successful commit. If any deletion operation fails (e.g., due to foreign key references in downstream item masters), the `CATCH` block triggers an immediate `ROLLBACK TRANSACTION` and returns `SELECT 0, ERROR_MESSAGE()`.

---

## [masterdata].[MSGMFillValues]

**Purpose & Database Operations:** Initializes all dropdown selection catalogs, multi-warehouse division mappings, units, makes, vendors, tax classifications, bin card mappings, sales discount settings, and fast-entry relational grid schemas for the Material SubGroup module.  
**Parameters:** `@CompanyNo` (`tinyint`, active operating company filter), `@SubGroupNo` (`smallint`, current subgroup identifier used for preservation during update operations).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mWarehouse`, `masterdata.mWarehouseDivisionDetail`, `masterdata.mCompanyMaster`, `payroll.tblDivisionMaster`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mMakeMaster`, `masterdata.mMakeMasterCompanyDetail`, `masterdata.mSubGroupMakeDetail`, `GlobalData.Unittype`, `masterdata.munitMaster`, `masterdata.mUnitMasterCompanyDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mvendorcard`, `masterdata.mVendorCardCompanyDetail`, `masterdata.mSubGroupVendorDetail`, `masterdata.mvendorLocationDetail`, `masterdata.mVendorLocationDetailCompanyDetail`, `masterdata.mCategoryMaster`, `masterdata.mCategoryMasterCompanyDetail`, `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `GlobalData.GSTCategory`, `GlobalData.HSNSACCode`, `masterdata.mMiscCharges`, `masterdata.mBinCard`, `masterdata.mBinCardSubgroupDetail`, and `Sales.Setting`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Emits 16 distinct tabular result sets (Tables 0 through 15): Table 0 (Warehouse & Division Mappings evaluating `IsDivisionApplicable`), Table 1 (Empty Make grid schema), Table 2 (Active Makes catalog), Table 3 & Table 4 (Unit Types), Table 5 (Active Units catalog), Table 6 (Empty Vendor grid schema), Table 7 (Approved Vendors catalog filtered for types 3 and 6), Table 8 (Vendor Locations), Table 9 (Categories catalog), Table 10 (Authorized Groups catalog), Table 11 (Empty Fast Entry Grid Schema with columns `[Category Name]`, `[Group Name]`, `[Code]`, `[Sub Group Name]`, `[Remarks]`), Table 12 (GST Categories), Table 13 (HSN/SAC Codes joined with CGST, SGST, IGST, and UTGST charges), Table 14 (Bin Cards linked to warehouse), and Table 15 (Sales discount display setting `DisplayDisLotTole`).  
**Return Contract & Error Handling:** Returns 16 DataTables. Runtime errors are intercepted by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MSGM'`.

---

## [masterdata].[MSGMFillValuesDependent]

**Purpose & Database Operations:** Retrieves child material groups under a selected category, calculates the next sequential numeric subgroup code within a selected group, and extracts inherited default quality inspection parameters from the parent group.  
**Parameters:** `@CategoryNo` (`smallint`, parent category identifier), `@GroupNo` (`smallint`, parent material group identifier).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mGroupMaster`, `masterdata.mSubGroupMaster`, `masterdata.mGroupQCParameterDetail`, and `masterdata.mQCParameters`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Emits three distinct result sets: Result Set 0 (Group Selection) returns `GroupNo`, `GroupName [Group Name]`, and `[Code]` for all groups belonging to `@CategoryNo`; Result Set 1 (Next SubGroup Code) calculates `ISNULL(MAX(CONVERT(smallint, Code)), 0) + 1 [SubGroupCode]` for numeric codes under `@GroupNo`; Result Set 2 (Inherited Quality Specifications) queries `masterdata.mGroupQCParameterDetail` joined with `masterdata.mQCParameters` where `GroupNo = @GroupNo`, returning standard values, tolerances, formula types, and penalty deduction rules configured at the parent group level.  
**Return Contract & Error Handling:** Returns three DataTables. Runtime errors are caught and logged into `masterdata.mErrorLog` under `FormCode = 'MSGM'`.

---

## [masterdata].[MSGMLoadData]

**Purpose & Database Operations:** Retrieves complete master header attributes and all associated child collections (Makes, Quality parameters, Units, and Vendors) for a single material subgroup record.  
**Parameters:** `@SubGroupNo` (`smallint`, target material subgroup identifier), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mSubGroupMakeDetail`, `masterdata.mmakemaster`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mQCParameters`, `GlobalData.unittype`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail`, and `masterdata.mgroupmaster`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Emits 5 relational result sets: Result Set 0 (Approved Makes) returns `MakeNo [Make Name]` and `Code` from `mSubGroupMakeDetail` joined with `mmakemaster`; Result Set 1 (QC Parameter Specifications) returns inspection parameters, standard values, tolerances, and deduction rules from `mSubGroupQCParameterDetail` joined with `mQCParameters`; Result Set 2 (Unit of Measure Mappings) queries `GlobalData.unittype` left-joined with `mSubGroupUnitDetail`; Result Set 3 (Approved Vendors) returns `VendorNo` and `VendorLocationNo` from `mSubGroupVendorDetail`; Result Set 4 (Header Attributes) returns all subgroup master fields (`sgm.*`), company-level `Inactive` status, parent `CategoryNo`, `GSTCategoryNo`, and `HSNSACCodeno`.  
**Return Contract & Error Handling:** Returns 5 DataTables. Exceptions are trapped by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MSGM'`.

---

## [masterdata].[MSGMSaveBinDetail]

**Purpose & Database Operations:** Links an approved warehouse storage bin card to a material subgroup.  
**Parameters:** `@SubGroupNo` (`smallint`, foreign key referencing parent material subgroup), `@BinNo` (`smallint`, foreign key referencing warehouse bin card).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mBinCardSubgroupDetail`.  
**Internal SQL Logic:** Directly inserts a relationship row into `masterdata.mBinCardSubgroupDetail` linking `@SubGroupNo` with `@BinNo`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous bin card links for `@SubGroupNo` were purged prior to batch insertion.

---

## [masterdata].[MSGMSaveDivision]

**Purpose & Database Operations:** Links an operational warehouse and organizational division to a material subgroup.  
**Parameters:** `@DivisionNo` (`int`, organizational division identifier), `@SubGroupNo` (`smallint`, foreign key referencing material subgroup), `@WHCompanyNo` (`tinyint`, warehouse operating company identifier), `@warehouseNo` (`smallint`, warehouse identifier).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mSubGroupDivisionDetail`.  
**Internal SQL Logic:** Directly inserts a relationship row into `masterdata.mSubGroupDivisionDetail` recording the operational link between subgroup, division, warehouse, and operating company.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous division links for `@SubGroupNo` were purged prior to batch insertion.

---

## [masterdata].[MSGMSaveMain]

**Purpose & Database Operations:** Performs an atomic insert or update of the primary Material SubGroup master record, manages enterprise-wide multi-company distribution, purges previous child collections on update, and cascades composite code updates to downstream inventory items.  
**Parameters:** `@SubGroupNo` (`smallint`, nullable/`0` for insert, existing ID for update), `@GroupNo` (`smallint`, foreign key referencing parent material group), `@Code` (`varchar(2)`, 2-character subgroup identifier), `@SubGroupName` (`varchar(100)`, descriptive name), `@ReceiptTolerance` (`decimal(5,2)`, allowable incoming receipt variance percentage), `@ShipmentTolerance` (`decimal(5,2)`, allowable outgoing shipment variance percentage), `@LoginNo` (`smallint`, audit user identifier), `@DocumentStatusNo` (`tinyint`, status code, default `30` indicating Authorized), `@HSNSACCodeno` (`smallint`, optional tax classification key, default `NULL`), `@GSTCategoryNo` (`tinyint`, optional GST category key, default `NULL`), `@IsBinApplicable` (`bit`, storage bin tracking flag, default `0`), `@DispatchNegTolerance` (`decimal(5,2)`, optional negative dispatch tolerance, default `NULL`).  
**Tables Affected / Queried:** `INSERT`/`UPDATE` on `masterdata.mSubGroupMaster`, `INSERT` on `masterdata.mSubGroupMasterCompanyDetail`, `DELETE` on child detail tables (`masterdata.mBinCardSubgroupDetail`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail`), `UPDATE` on downstream `masterdata.mItemMaster`, and read access on `masterdata.mCompanyMaster`.  
**Internal SQL Logic:** Evaluates `ISNULL(@SubGroupNo, 0) = 0`. In insert mode, writes header records to `masterdata.mSubGroupMaster` with audit tracking (`CreatedBy`, `CreatedDate`, and sets `AuthorizedBy` and `AuthorizedDate` when `@DocumentStatusNo = 30`), retrieves the generated identity using `IDENT_CURRENT('[masterdata].[mSubGroupMaster]')`, and creates active distribution records (`Inactive = 0`) in `masterdata.mSubGroupMasterCompanyDetail` for all registered entities in `masterdata.mCompanyMaster`. In update mode, purges all existing child records across 6 detail tables for `@SubGroupNo`, updates primary fields and modification stamps in `masterdata.mSubGroupMaster`, and recalculates downstream item composite codes in `masterdata.mItemMaster` (`FullCode = CM.Code + gm.Code + sg.Code + IM.Code`).  
**Return Contract & Error Handling:** Returns `SELECT 1, @SubGroupNo` on success. On exception, returns `SELECT 0, ERROR_MESSAGE()`. Participates in caller-managed external transaction boundaries.

---

## [masterdata].[MSGMSaveMake]

**Purpose & Database Operations:** Persists an approved manufacturer or make link for a material subgroup.  
**Parameters:** `@SubGroupNo` (`smallint`, foreign key referencing parent material subgroup), `@MakeNo` (`smallint`, foreign key referencing manufacturer master), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mSubGroupMakeDetail`.  
**Internal SQL Logic:** Directly inserts a relationship row into `masterdata.mSubGroupMakeDetail` linking `@SubGroupNo` with `@MakeNo`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous make links for `@SubGroupNo` were purged prior to batch insertion.

---

## [masterdata].[MSGMSaveQC]

**Purpose & Database Operations:** Commits an individual quality inspection parameter specification row into the child quality details table for a material subgroup.  
**Parameters:** `@SubGroupNo` (`smallint`, foreign key referencing parent material subgroup), `@QCParameterNo` (`smallint`, foreign key referencing quality inspection parameter), `@StandardValue` (`decimal(9,3)`, target baseline specification), `@ToleranceValue` (`decimal(9,3)`, permissible variation window), `@DeductionRate` (`tinyint`, deduction rate calculation option), `@DeductionType` (`tinyint`, single or double penalty designation), `@DoubleDeductionFrom` (`decimal(9,3)`, secondary penalty escalation threshold), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mSubGroupQCParameterDetail`.  
**Internal SQL Logic:** Directly inserts a parameter configuration row into `masterdata.mSubGroupQCParameterDetail` matching the supplied arguments.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous QC parameters for `@SubGroupNo` were purged prior to batch insertion.

---

## [masterdata].[MSGMSaveUnit]

**Purpose & Database Operations:** Links an approved unit of measure and unit type classification to a material subgroup.  
**Parameters:** `@SubGroupNo` (`smallint`, foreign key referencing parent material subgroup), `@UnitTypeNo` (`tinyint`, classification foreign key referencing `GlobalData.UnitType`), `@UnitNo` (`smallint`, unit foreign key referencing `masterdata.mUnitMaster`), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mSubGroupUnitDetail`.  
**Internal SQL Logic:** Directly inserts a relationship row into `masterdata.mSubGroupUnitDetail` linking `@SubGroupNo`, `@UnitTypeNo`, and `@UnitNo`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous unit links for `@SubGroupNo` were purged prior to batch insertion.

---

## [masterdata].[MSGMSaveVendor]

**Purpose & Database Operations:** Links an approved supplier vendor card and specific vendor dispatch location to a material subgroup.  
**Parameters:** `@SubGroupNo` (`smallint`, foreign key referencing parent material subgroup), `@VendorNo` (`int`, supplier vendor identifier referencing `masterdata.mVendorCard`), `@VendorLocationNo` (`int`, specific supplier address location identifier referencing `masterdata.mVendorLocationDetail`), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mSubGroupVendorDetail`.  
**Internal SQL Logic:** Directly inserts a relationship row into `masterdata.mSubGroupVendorDetail` linking `@SubGroupNo`, `@VendorNo`, and `@VendorLocationNo`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous vendor links for `@SubGroupNo` were purged prior to batch insertion.

---

## [masterdata].[MSGMSearchData]

**Purpose & Database Operations:** Executes dynamic search lookup queries configured in central system metadata tables for the Material SubGroup module.  
**Parameters:** `@CompanyNo` (`tinyint`, operating company filter passed to the dynamic search routine).  
**Tables Affected / Queried:** `SELECT` on `GlobalData.FormSearchDataDetail`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Queries metadata table `GlobalData.FormSearchDataDetail` where `FormNo = 28` and `InActive = 0` to retrieve the registered search procedure name, concatenates the procedure name with the `@CompanyNo` parameter string (`@Procedure = ProcedureName + ' ' + Convert(varchar(3), @CompanyNo)`), and executes the dynamically resolved search query using `EXEC (@Procedure)`.  
**Return Contract & Error Handling:** Returns the search result set produced by the resolved dynamic procedure. Runtime failures are intercepted by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MSGM'`.

---

## [masterdata].[MSGMValidate]

**Purpose & Database Operations:** Enforces enterprise uniqueness constraints for material subgroup composite codes and names prior to database persistence.  
**Parameters:** `@CompanyNo` (`tinyint`, operating company identifier), `@FullSubGroupCode` (`varchar(6)`, 6-character composite code string consisting of category code + group code + subgroup code), `@SubGroupNo` (`smallint`, nullable/`0` for new records or existing record ID for modification exclusion), `@SubGroupName` (`varchar(100)`, subgroup descriptive name to validate), `@GroupNo` (`smallint`, parent material group identifier).  
**Tables Affected / Queried:** `SELECT` on `masterdata.msubgroupmaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mgroupmaster`, and `masterdata.mCategorymaster`.  
**Internal SQL Logic:** Executes sequential validation checks excluding the current `@SubGroupNo`: (1) *Composite Code Uniqueness:* Joins `mSubGroupMaster` with `mSubGroupMasterCompanyDetail`, `mGroupMaster`, and `mCategoryMaster` to verify whether `cm.code + gm.code + sgm.Code = @FullSubGroupCode` already exists for `@CompanyNo`. If violated, terminates execution and returns `SELECT 0, 'Duplicate Sub Group Code is not allowed.'`; (2) *Name Uniqueness:* Verifies whether `@SubGroupName` already exists under the same parent `@GroupNo`. If violated, terminates execution and returns `SELECT 0, 'Duplicate Sub Group Name is not allowed.'`.  
**Return Contract & Error Handling:** Returns `SELECT 1, 'Success'` when all validation checks pass. Runtime exceptions in `TRY` are trapped by `CATCH` and returned as `SELECT 0, ERROR_MESSAGE()`.

---

## [masterdata].[MMUMDelete]

**Purpose & Database Operations:** Permanently purges a unit master record, its multi-company mapping records, and all associated unit conversion and subgroup relationships within an autonomous database transaction.  
**Parameters:** `@UnitNo` (`smallint`, primary key identifier of the unit master record to purge).  
**Tables Affected / Queried:** `DELETE` on `masterdata.mUnitConversionDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mUnitMasterCompanyDetail`, and `masterdata.mUnitMaster`.  
**Internal SQL Logic:** Manages an autonomous database transaction using `BEGIN TRANSACTION ... COMMIT TRANSACTION`. It enforces strict foreign-key dependency deletion order: first deletes unit conversion factor records where `@UnitNo` is the primary unit (`UnitNo = @UnitNo`) or conversion target unit (`ConversionUnitNo = @UnitNo`), deletes subgroup unit relationships from `masterdata.mSubGroupUnitDetail`, deletes multi-company distribution records from `masterdata.mUnitMasterCompanyDetail`, and finally deletes the parent header record from `masterdata.mUnitMaster`.  
**Return Contract & Error Handling:** Returns `SELECT 1, 'Success'` on successful commit. If any deletion operation fails (e.g., due to foreign key references in transactions or inventory balances), the `CATCH` block triggers an immediate `ROLLBACK TRANSACTION` and returns `SELECT 0, ERROR_MESSAGE()`.

---

## [masterdata].[MMUMFillValues]

**Purpose & Database Operations:** Populates selection catalogs for unit categories, conversion factor grids, conversion types, units of measure, material subgroups, unit types, fast-entry relational grid schemas, and GST unit quantity codes (UQC).  
**Parameters:** `@CompanyNo` (`tinyint`, active operating company filter), `@UnitNo` (`smallint`, current unit identifier used for exclusion and preservation during update operations).  
**Tables Affected / Queried:** `SELECT` on `GlobalData.UnitCategory`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mSubgroupmaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mGroupMaster`, `masterdata.mSubGroupUnitDetail`, `GlobalData.UnitType`, and `GlobalData.GSTUnitMaster`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Emits 9 distinct tabular result sets (Tables 0 through 8): Table 0 (Unit Categories from `GlobalData.UnitCategory`), Table 1 (Empty conversion factor grid schema `WHERE 1 = 2`), Table 2 (Static Conversion Types: `1 = Fixed`, `2 = Variable`), Table 3 (Active Units catalog unioned with existing conversion units linked to `@UnitNo`), Table 4 (Empty Material Subgroup grid schema), Table 5 (Active Material Subgroups catalog joined with parent group names), Table 6 (Unit Types from `GlobalData.UnitType`), Table 7 (Empty Fast Entry Grid Schema with columns `[Unit Name]`, `[Alias]`, `[Category]`, `[Remarks]`), and Table 8 (GST Unit Masters from `GlobalData.GSTUnitMaster`).  
**Return Contract & Error Handling:** Returns 9 DataTables. Runtime errors are intercepted by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MMUM'`.

---

## [masterdata].[MMUMLoadData]

**Purpose & Database Operations:** Retrieves complete header information, standard conversion factor specifications, and linked material subgroups for a single unit master record.  
**Parameters:** `@UnitNo` (`smallint`, target unit master identifier), `@CompanyNo` (`tinyint`, operating company identifier).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mSubGroupUnitDetail`, and `masterdata.mSubGroupMaster`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Emits three relational result sets: Result Set 0 (Header Attributes) retrieves `Code`, `UnitName`, `Alias`, `UnitCategoryNo`, company-level `Inactive` status, and `GSTUnitNo` by joining `masterdata.mUnitMaster` with `masterdata.mUnitMasterCompanyDetail` on `@UnitNo`; Result Set 1 (Standard Conversion Factors) selects conversion details (`ConversionType`, `FirstCF`, `SecondCF`, `ConversionUnitNo`) from `masterdata.mUnitConversionDetail` where `UnitNo = @UnitNo`; Result Set 2 (Material Subgroups) selects linked subgroups and unit types by joining `masterdata.mSubGroupUnitDetail` with `masterdata.mSubGroupMaster` where `UnitNo = @UnitNo`.  
**Return Contract & Error Handling:** Returns three DataTables. Unhandled exceptions are captured by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MMUM'`.

---

## [masterdata].[MMUMSave]

**Purpose & Database Operations:** Performs an atomic insert or update of a unit master record, auto-generates a standardized sequential unit code, manages enterprise-wide multi-company distribution, and purges previous child conversion factors and subgroup links.  
**Parameters:** `@UnitNo` (`smallint`, nullable/`0` to indicate an insert operation, or a valid ID to indicate an update), `@UnitName` (`varchar(25)`, unit descriptive name), `@Alias` (`varchar(6)`, abbreviated unit symbol/alias), `@UnitCategoryNo` (`tinyint`, category foreign key referencing `GlobalData.UnitCategory`), `@LoginNo` (`int`, audit user identifier), `@DocumentStatusNo` (`tinyint`, status code, default `30` indicating Authorized), `@GSTUQC` (`tinyint`, statutory GST Unit Quantity Code referencing `GlobalData.GSTUnitMaster`).  
**Tables Affected / Queried:** `INSERT`/`UPDATE` on `masterdata.mUnitMaster`, `INSERT` on `masterdata.mUnitMasterCompanyDetail`, `DELETE` on child detail tables (`masterdata.mUnitConversionDetail`, `masterdata.mSubGroupUnitDetail`), and read access on `masterdata.mCompanyMaster`.  
**Internal SQL Logic:** Evaluates `ISNULL(@UnitNo, 0) = 0`. In insert mode, dynamically calculates the next sequential code using `'UM' + RIGHT(REPLICATE('0', 4) + CAST(ISNULL(MAX(CONVERT(int, SUBSTRING(Code, 3, 4))), 0) + 1 AS varchar(4)), 4)` from `masterdata.mUnitMaster`, writes the header record with audit tracking (`CreatedBy`, `CreatedDate`, `AuthorizedBy`, `AuthorizedDate`), retrieves the generated identity using `IDENT_CURRENT('[masterdata].[mUnitMaster]')`, and creates active distribution records (`Inactive = 0`) in `masterdata.mUnitMasterCompanyDetail` for all registered entities in `masterdata.mCompanyMaster`. In update mode, purges previous conversion factors (where `UnitNo = @UnitNo` or `ConversionUnitNo = @UnitNo`) and subgroup links from `masterdata.mSubGroupUnitDetail`, and updates primary fields and modification stamps in `masterdata.mUnitMaster`.  
**Return Contract & Error Handling:** Returns `SELECT 1, @UnitNo` on success. On exception, the `CATCH` block returns `SELECT 0, ERROR_MESSAGE()`. Participates in caller-managed external transaction boundaries.

---

## [masterdata].[MMUMSaveSubGroupUnitDetail]

**Purpose & Database Operations:** Links an approved material subgroup and unit type classification to a unit master record.  
**Parameters:** `@UnitNo` (`smallint`, foreign key referencing parent unit master), `@SubGroupNo` (`smallint`, foreign key referencing material subgroup), `@UnitTypeNo` (`tinyint`, classification foreign key referencing `GlobalData.UnitType`).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mSubGroupUnitDetail`.  
**Internal SQL Logic:** Directly inserts a relationship row into `masterdata.mSubGroupUnitDetail` recording the operational association between `@UnitNo`, `@SubGroupNo`, and `@UnitTypeNo`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous subgroup links for `@UnitNo` were purged prior to batch insertion.

---

## [masterdata].[MMUMSaveUnitConversionDetail]

**Purpose & Database Operations:** Persists standard conversion factor specifications between two units of measure, automatically creating both forward and reciprocal conversion relationships.  
**Parameters:** `@UnitNo` (`smallint`, primary unit identifier), `@ConversionType` (`tinyint`, conversion calculation mode: 1 = Fixed, 2 = Variable), `@FirstCF` (`decimal(8,3)`, forward conversion multiplier), `@SecondCF` (`decimal(8,3)`, reciprocal conversion multiplier), `@ConversionUnitNo` (`smallint`, target conversion unit identifier).  
**Tables Affected / Queried:** `INSERT` into `masterdata.mUnitConversionDetail`.  
**Internal SQL Logic:** Inserts two reciprocal relationship rows into `masterdata.mUnitConversionDetail` to ensure mathematical symmetry across inventory calculations:
1. Direct conversion row: `(@UnitNo, @ConversionType, @FirstCF, @SecondCF, @ConversionUnitNo)`.
2. Reciprocal conversion row: `(@ConversionUnitNo, @ConversionType, @SecondCF, @FirstCF, @UnitNo)`.  
**Return Contract & Error Handling:** Returns `SELECT 1` on success; returns `SELECT 0, ERROR_MESSAGE()` on exception. Participates in an external caller-level transaction sequence where all previous conversions for `@UnitNo` were purged prior to batch insertion.

---

## [masterdata].[MMUMSearchData]

**Purpose & Database Operations:** Searches and lists active unit master records with category and creator names for a specified operating company.  
**Parameters:** `@CompanyNo` (`tinyint`, operating company identifier filter).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`, `GlobalData.UnitCategory`, and `Security.Login`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Executes a direct SQL query joining `masterdata.mUnitMaster UM` with `masterdata.mUnitMasterCompanyDetail UMcd` on `UnitNo`, `GlobalData.UnitCategory CatM` on `UnitCategoryNo`, and `Security.Login SL` on `CreatedBy`. It filters where `UMcd.CompanyNo = @CompanyNo` and orders output rows by `[Unit Name]`, returning `UnitNo`, `Code`, `Unit Name`, `Alias`, `Category Name`, `Inactive`, `Created By`, and `Created Date`.  
**Return Contract & Error Handling:** Returns a single populated DataTable. Unhandled exceptions in the `TRY` block are captured by `CATCH` and logged into `masterdata.mErrorLog` under `FormCode = 'MMUM'`.

---

## [masterdata].[MMUMValidate]

**Purpose & Database Operations:** Enforces enterprise uniqueness validation for unit names and abbreviation aliases within an operating company prior to database persistence.  
**Parameters:** `@UnitName` (`varchar(25)`, unit name to validate), `@UnitNo` (`smallint`, nullable/`0` for new records or existing record ID for modification exclusion), `@CompanyNo` (`smallint`, operating company identifier), `@Alias` (`varchar(6)`, unit abbreviation symbol to validate).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mUnitMaster` and `masterdata.mUnitMasterCompanyDetail`.  
**Internal SQL Logic:** Executes sequential validation checks excluding the current `@UnitNo`: (1) *Unit Name Uniqueness:* Verifies whether `@UnitName` already exists for `@CompanyNo` in `masterdata.mUnitMasterCompanyDetail`. If violated, terminates execution and returns `SELECT 0, 'Duplicate Unit Name is not allowed.', 1` (status `0`, validation message, focus code `1`); (2) *Alias Uniqueness:* Verifies whether `@Alias` already exists for `@CompanyNo` in `masterdata.mUnitMasterCompanyDetail`. If violated, terminates execution and returns `SELECT 0, 'Duplicate Alias is not allowed.', 2` (status `0`, validation message, focus code `2`).  
**Return Contract & Error Handling:** Returns `SELECT 1` when all validation checks pass. Runtime exceptions in `TRY` are trapped by `CATCH` and returned as `SELECT 0, ERROR_MESSAGE()`.

---

## [masterdata].[QCFillValues]

**Purpose & Database Operations:** Initializes all dropdown selection catalogs, lookup lists, unit definitions, tolerance rules, and system visibility settings required by the shared quality control subsystem across multiple forms.  
**Parameters:** `@CompanyNo` (`tinyint`, operating company filter for authorized quality masters).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mQCGroup`, `masterdata.mQCGroupCompanyDetail`, `masterdata.mQCParameters`, `masterdata.mQCParametersCompanyDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`, `GlobalData.QCToleranceType`, and `Config.DBCommonSetting`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Issues 13 distinct relational result sets (Tables 0 through 12): Table 0 (Authorized QC Groups for `@CompanyNo`), Table 1 (Empty QC parameter grid schema `WHERE 1 = 2`), Table 2 (Active QC Parameters catalog with benchmark values and deduction rules), Table 3 & Table 10 (Active Units and Tolerance Units from `mUnitMaster`), Table 4 (Tolerance Types from `GlobalData.QCToleranceType`), Tables 5, 6, 7, 8 (Static Quality Enums: Deduction On `1 = Lower, 2 = Higher`, Formula Type `1 = Rate, 2 = Quantity`, Deduction Rate `1 = Basic, 2 = Prorata, 3 = Landed`, and Deduction Type `1 = Single, 2 = Double`), Table 9 (Default QC datatable column typing definition), Table 11 (Empty Parameter Detail observation schema), and Table 12 (Global deduction visibility flag `IsHideQCDeduction` from `Config.DBCommonSetting`).  
**Return Contract & Error Handling:** Returns 13 DataTables. Any exception is intercepted and logged into `masterdata.mErrorLog` under `FormCode = 'ODDC'`.

---

## [masterdata].[QCFillValuesDependent]

**Purpose & Database Operations:** Retrieves and expands all pre-configured quality inspection parameter specifications defined under a selected Quality Control Group template.  
**Parameters:** `@QCGroupNo` (`smallint`, selected quality group template identifier), `@CompanyNo` (`tinyint`, active operating company filter).  
**Tables Affected / Queried:** `SELECT` on `masterdata.mQCGroupDetail`, `masterdata.mQCParameters`, and `masterdata.mQCParametersCompanyDetail`. Writes runtime errors to `masterdata.mErrorLog`.  
**Internal SQL Logic:** Queries `masterdata.mQCGroupDetail QCG` joined with `masterdata.mQCParameters QCP` and company detail `masterdata.mQCParametersCompanyDetail QCPCD` on `QCParameterNo`. It filters by `QCG.QCGroupNo = @QCGroupNo`, `QCPCD.CompanyNo = @CompanyNo`, `QCPCD.Inactive = 0`, and ensures the parameter is authorized (`QCP.AuthorizedBy IS NOT NULL`). It maps and extracts the template's baseline specifications: `QCParameterNo`, `UnitNo`, `StandardValue`, `StandardValue2`, `ToleranceValue`, `ToleranceTypeNo`, `ToleranceUnit`, `DeductionOn`, `FormulaType`, `DeductionRate`, `DeductionType`, and `DoubleDeductionFrom`.  
**Return Contract & Error Handling:** Returns a single DataTable containing the expanded parameter specifications. Any exception is captured and logged into `masterdata.mErrorLog` under `FormCode = 'ODDC'`.
