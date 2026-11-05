# Material Sub Group Master (`fMaterialSubGroupMaster`)
> Maintains material sub groups (the level between Group and Item) together with their tax, warehouse, make, unit, vendor, bin and QC defaults.

**Form code:** `MSGM` (form Tag; also the Excel sheet name expected by Import)  
**Who can use / edit:** Delete is head office only. Opening a record from a non-head-office company locks the screen controls (read-only view). No other role checks appear in the code.

## What it is for
This screen creates and edits Sub Groups. A Sub Group belongs to one Group, and the Group belongs to one Category. Items (`masterdata.mItemMaster`) sit below the Sub Group, so the full item code is Category code + Group code + Sub Group code + Item code. It also stores which warehouses, makes, units, vendors and bin cards apply to the sub group, plus GST and QC defaults.

## Screen guide
| Field | Tab | Required? | Rules and limits | Notes |
|---|---|---|---|---|
| Category Name | Main (top) | Yes | Pick from list; only categories active for the logged-in company. | Picking one fills Category Code and reloads the Group list. |
| Category Code | Main | n/a | Read-only. | Filled from the category. |
| Group Name | Main | Yes | Pick from list, limited to the chosen category. | Picking one fills Group Code, suggests the Code and loads QC defaults. |
| Group Code | Main | n/a | Read-only. | |
| Code | Main | Yes | Max 2 characters. | Auto-suggested as highest numeric code in the group + 1, shown as 2 digits (e.g. 01). Can be overtyped. |
| Sub Group Code | Main | n/a | Read-only; = Category code + Group code + Code. | Also a link that switches to Fast Entry. |
| Sub Group Name | Main | Yes | Max 100 characters. | |
| Inactive | Main | n/a | Always disabled. | Shows state on opening a record; cannot be changed here. |
| BIN Applicable | Main | No | Tick box. | Shows or hides the Bin Detail tab. |
| Dispatch -ve Tolerance (%) | Main | No | Max 6 characters, decimal. | Visible only if the company setting `Sales.Setting.DisplayDisLotTole` is on. Saved empty if 0. |
| Receipt Tolerance, Shipment Tolerance | Main | n/a | Max 5 characters. | Hidden on the screen; saved as 0 on each save. |
| GST Category | GST Detail | No | Pick from active GST categories. | |
| HSN /SAC Code | GST Detail | No | Pick from list (code + description). | |
| CGST / SGST / IGST / UTGST Rate | GST Detail | n/a | Read-only. | Come from the chosen HSN/SAC code; cleared if none. |
| Warehouse grid: Select, Warehouse, Division, Company | Warehouse Detail | No | Only Select is editable. Rows cannot be deleted. | Ticked rows are saved. Division name shows only if the head-office company uses divisions. Inactive warehouses are not listed. |
| Make grid: Make Name, Code | Make Detail | No | Duplicate make not allowed. Code is read-only. | Typing in the last row adds a new row. Only makes active for the company (or already linked) appear. |
| UOM grid: Unit Type, Unit Name | UOM | No | One fixed row per unit type; Unit Type not editable; rows cannot be deleted. | Row is saved only if both Unit Type and Unit Name are filled. |
| Vendor grid: Vendor Name, Location | Vendor Detail | Location required once a vendor is chosen | Duplicate Vendor + Location not allowed. | Location list is filtered to the vendor; auto-filled if the vendor has only one. Only vendors of type 3 or 6 are listed. |
| Bin grid: Select, Bin Card No., Location, Warehouse | Bin Detail | No | Only Select is editable. | Tab appears only when BIN Applicable is ticked. Lists all bin cards (no company filter). |
| QC grid (embedded QC Group control): QC Parameter Name, Unit, Standard Value1, Standard Value2, Tolerance Value, Tolerance Type, Tolerance Unit, Deduction On, Formula Type, Deduction Rate, Deduction Type, Double Deduction From | QC Detail | Per row, see messages | Numeric cells max 10 characters, 3 decimals. Unit, Tolerance Type/Unit, Deduction On, Formula Type are read-only and copied from the QC parameter. Double Deduction From is editable only when Deduction Type is Double. | The whole QC Detail tab is hidden in the form. Actual Value columns are hidden. If the company setting `IsHideQCDeduction` is on, the deduction columns are hidden. The QC Group name combo is part of the control. |
| Fast Entry grid: Category Name, Group Name, Code (max 2), Sub Group Name (max 100), Remarks | Fast Entry panel | Category, Group, Code, Name per row | Remarks is read-only. | Group list follows the row's category. Changing the category clears the group. |

## Actions
| Action | What happens | Confirmations or restrictions |
|---|---|---|
| New | Clears the form and asks for a new record. | None seen. |
| Open / Search | Opens a search list for the company (list is defined in `GlobalData.FormSearchDataDetail`, FormNo 28), then loads the chosen sub group. | Non-head-office users see the record locked. |
| Save (detail mode) | Validates, asks a save confirmation, then saves in one transaction and starts a new record. | Confirmation text comes from the base library (inferred). Any failure rolls back everything. |
| Save (Fast Entry mode) | Asks to confirm, then validates and saves each grid row as a separate sub group, writing the result in Remarks. | Final message "Refer remarks for saved status." |
| Delete | Hard-deletes the sub group and its child rows, then starts a new record. | Head office only; delete confirmation. A blocked delete shows the database message. |
| Sub Group Code link | Opens Fast Entry mode (and starts a new record). | |
| "Switch back to detail mode." link | Hides the Fast Entry panel. | |
| Import (Fast Entry) | Reads an Excel sheet into the Fast Entry grid. Expected columns: Category Name, Group Name, Code, Sub Group Name. | Asks "Your excel should consists of sheet with name MSGM. Do you want to continue?" |
| Print, Preview, Export, Email | Do nothing. | |

## Validation and error messages
| Message | When it appears | What the user should do |
|---|---|---|
| Duplicate Sub Group Code is not allowed. | Same Category+Group+Sub Group code already exists for this company on another sub group. | Change the Code. |
| Duplicate Sub Group Name is not allowed. | Same Sub Group Name already exists in the same Group. | Use a different name or another Group. |
| Select valid Category Name. | Category empty or not in the list. | Pick from the list. |
| Select valid Group Name. | Group empty or not in the list. | Pick a group of the chosen category. |
| Enter Code. | Code blank. | Type a 2-character code. |
| Enter Sub Group Name. | Name blank. | Type the name. |
| Select valid Location | A vendor row has no location. | Choose the vendor location. |
| Standard Value can't be empty or zero | QC row has a parameter but Standard Value is blank or 0. | Enter a value. |
| Enter Tolerance Value | QC row with blank Tolerance Value. | Enter a value. |
| Select valid Deduction Rate | QC row with blank Deduction Rate. | Choose a rate. |
| Select valid Deduction Type | QC row with blank Deduction Type. | Choose a type. |
| Enter Double Deduction From | Deduction Type is Double and the field is blank. | Enter a value. |
| Duplicate Make Name not allowed. | Same make twice in the grid. | Remove the repeat. |
| Duplicate Vendor Name and Location not allowed. | Same vendor and location twice. | Remove the repeat. |
| Duplicate QC Parameter not allowed. | Same QC parameter twice. | Remove the repeat. |
| Permission denied to delete Material Sub Group. | Delete attempted from a non-head-office company. | Ask head office. |
| Successfully Created. | Fast Entry row Remarks after a save. | See Quirks: not proof of success. |
| Refer remarks for saved status. | After Fast Entry save. | Check each row's Remarks. |
| (database error text) | Any save or delete step fails; the SQL error message is shown. | Quote it in the ticket. |

Also in the QC control code but not reachable here: "Select atleast one QC Parameter." and "Actual Value1 can't be empty or zero" (the form leaves both checks off or hidden).

## Business rules
- Sub Group Code is unique per company (Category code + Group code + Code, max 6 characters). Name is unique within a Group.
- New sub group: row in `masterdata.mSubGroupMaster` (status 30, authorized by the saving user at once) plus one `masterdata.mSubGroupMasterCompanyDetail` row per company, Inactive = 0.
- Edit: all child rows are deleted and re-inserted from the screen in `masterdata.mBinCardSubgroupDetail`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail`. Edit also rewrites `FullCode` on every item in `masterdata.mItemMaster` of that sub group.
- Delete removes those tables plus `masterdata.mSubGroupTechnicalGrade`, `masterdata.mSubGroupMasterCompanyDetail` and `masterdata.mSubGroupMaster`, for all companies.
- Code suggestion = highest numeric code in the group + 1.
- Bin rows save only when BIN Applicable is ticked and the row is selected.
- QC defaults are copied from the Group's QC parameters (`masterdata.mGroupQCParameterDetail`) when a group is chosen.
- Unit tab picks units from the Unit master by unit type; the Group form above supplies Category/Group codes.

## Common ticket scenarios
| Symptom | Most likely cause | What to check or do |
|---|---|---|
| "Duplicate Sub Group Code is not allowed." on a new code | Same code already used under this group, or code entered with different case/format. | Check existing sub groups of the group. |
| Cannot find Category or Group in the list | Category/group inactive for this company, or (Fast Entry list) group not authorized. | Check Category and Group masters. |
| Group list empty after picking a Category | The category has no groups. | Create a group first. |
| Delete says permission denied | Logged into a non-head-office company. | Log into head office. |
| Delete fails with a database message | Another record still refers to the sub group (Possible). | Quote the message. |
| Cannot edit anything | Non-head-office company opened the record (controls locked). | Edit from head office. |
| Cannot untick Inactive | Checkbox is always disabled. | Not changeable in this form. |
| Bin Detail tab missing | BIN Applicable not ticked. | Tick it. |
| QC tab or Receipt/Shipment tolerance not visible | Hidden in the form design. | Not available to users. |
| Dispatch -ve Tolerance missing | Company setting `DisplayDisLotTole` is off or empty. | Check Sales settings. |
| Fast Entry says "Successfully Created." but nothing exists | Save errors in a row are shown as a pop-up but the Remark may still read success. | Search for the code; check the pop-up. |
| A make, vendor or unit is not offered | Inactive for this company (shown only if already linked). | Check that master's company status. |
| Vendor location not shown | Only locations of the chosen vendor, active for the company, appear. | Check vendor card. |

## Limits and known quirks
- Inactive flag cannot be changed here and is not part of the save.
- Hidden: QC Detail tab, Receipt and Shipment Tolerance, QC Actual Value columns. Hidden QC values are still validated and saved, so QC errors can appear on a tab the user cannot see.
- Receipt/Shipment tolerance are overwritten with 0 on every save.
- Warehouse selection is not mandatory (the check is commented out).
- Bin cards are listed without a company filter.
- No form field exists for Technical Grade; it is only cleaned up on delete.
- Fast Entry: a row whose save fails inside the transaction still gets the Remark "Successfully Created." (the error is swallowed after a pop-up).
- Deletes are permanent, with no audit row.
- Print, Preview, Export, Email buttons do nothing.
- Non-head-office users who use New get an unlocked screen; the code does not block saving.

## Glossary
- MSGM: form code and prefix of the `masterdata.MSGM...` stored procedures.
- Fast Entry: grid mode to add many sub groups at once or from Excel.
- HSN/SAC: tax classification code that drives the read-only GST rates.
- BIN Applicable: tells the system the sub group's items are kept in bin cards.
- QC parameter: quality test with standard value, tolerance and deduction rules.
- Head office: company where `gHeadOfficeNo` equals the company; the only one allowed to delete.
- Division: optional split of a warehouse.

<!-- BEGIN GRAPH-MAP -->
## Technical map (generated from the knowledge graph)

_Generated 2026-11-04 from graph project `fMaterialSubGroupMaster__81cf52cf`. Do not edit between the markers; re-run the refresh instead._

### What each screen action runs

| Form method (VB, line) | Called from | Data-layer method | Stored procedure | Reads | Writes |
| --- | --- | --- | --- | --- | --- |
| `ValidateForm` (67) | `Save` | `Validate` | `masterdata.MSGMValidate` | `masterdata.mCategoryMaster`, `masterdata.mGroupMaster`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail` | - |
| `LoadData` (177) | `Open` | `LoadData` | `masterdata.MSGMLoadData` | `globaldata.Unittype`, `masterdata.mGroupMaster`, `masterdata.mMakeMaster`, `masterdata.mQCParameters`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail` | - |
| `Delete` (227) | - | `Delete` | `masterdata.MSGMDelete` | - | `masterdata.mBinCardSubgroupDetail`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupTechnicalGrade`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail` |
| `Open` (267) | - | `SearchData` | `masterdata.MSGMSearchData` | `globaldata.FormSearchDataDetail` | - |
| `SaveMain` (403) | `Save` | `SaveMain` | `masterdata.MSGMSaveMain` | `masterdata.mCategoryMaster`, `masterdata.mCompanyMaster`, `masterdata.mGroupMaster`, `masterdata.mSubGroupMaster` | `masterdata.mBinCardSubgroupDetail`, `masterdata.mItemMaster`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail` |
| `FillValues` (496) | `LoadData` | `FillValues` | `masterdata.MSGMFillValues` | `globaldata.GSTCategory`, `globaldata.HSNSACCode`, `globaldata.Unittype`, `masterdata.mBinCard`, `masterdata.mBinCardSubgroupDetail`, `masterdata.mCategoryMaster`, `masterdata.mCategoryMasterCompanyDetail`, `masterdata.mCompanyMaster`, `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `masterdata.mMakeMaster`, `masterdata.mMakeMasterCompanyDetail`, `masterdata.mMiscCharges`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`, `masterdata.mvendorcard`, `masterdata.mVendorCardCompanyDetail`, `masterdata.mvendorLocationDetail`, `masterdata.mVendorLocationDetailCompanyDetail`, `masterdata.mWarehouse`, `masterdata.mWarehouseDivisionDetail`, `payroll.tblDivisionMaster`, `sales.Setting` | - |
| `SaveDivision` (579) | `SaveMain` | `SaveDivision` | `masterdata.MSGMSaveDivision` | - | `masterdata.mSubGroupDivisionDetail` |
| `SaveMake` (609) | `SaveMain` | `SaveMake` | `masterdata.MSGMSaveMake` | - | `masterdata.mSubGroupMakeDetail` |
| `SaveQC` (628) | `SaveMain` | `SaveQC` | `masterdata.MSGMSaveQC` | - | `masterdata.mSubGroupQCParameterDetail` |
| `SaveUnit` (664) | `SaveMain` | `SaveUnit` | `masterdata.MSGMSaveUnit` | - | `masterdata.mSubGroupUnitDetail` |
| `SaveVendor` (684) | `SaveMain` | `SaveVendor` | `masterdata.MSGMSaveVendor` | - | `masterdata.mSubGroupVendorDetail` |
| `FillValuesDependent` (703) | `ucmbCategoryName_ValueChanged`, `ucmbGroupName_ValueChanged` | `FillValuesDependent` | `masterdata.MSGMFillValuesDependent` | `masterdata.mGroupMaster`, `masterdata.mGroupQCParameterDetail`, `masterdata.mQCParameters`, `masterdata.mSubGroupMaster` | - |
| `SaveBinDetail` (1013) | `SaveMain` | `SaveBinDetail` | `masterdata.MSGMSaveBinDetail` | - | `masterdata.mBinCardSubgroupDetail` |

_`masterdata.mErrorLog` (written by every procedure's error handler) is left out of the table lists._

Procedures in this form's folder that the graph could not link to a form method (called some other way, for example from the embedded QC control; check the source): `masterdata.QCFillValues`, `masterdata.QCFillValuesDependent`.

### Tables this form changes

`masterdata.mBinCardSubgroupDetail`, `masterdata.mItemMaster`, `masterdata.mSubGroupDivisionDetail`, `masterdata.mSubGroupMakeDetail`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mSubGroupQCParameterDetail`, `masterdata.mSubGroupTechnicalGrade`, `masterdata.mSubGroupUnitDetail`, `masterdata.mSubGroupVendorDetail`

### Same tables used by other forms (impact check before changing data or rules)

| Table | Written by here | Also written by | Also read by |
| --- | --- | --- | --- |
| `globaldata.FormSearchDataDetail` | no | - | fMaterialGroup:MMIGSearchData |
| `globaldata.Unittype` | no | - | fUnitMaster:MMUMFillValues |
| `masterdata.mCategoryMaster` | no | - | fMaterialGroup:MMIGFillValues, fMaterialGroup:MMIGSave |
| `masterdata.mCategoryMasterCompanyDetail` | no | - | fMaterialGroup:MMIGFillValues |
| `masterdata.mCompanyMaster` | no | - | fMaterialGroup:MMIGSave, fUnitMaster:MMUMSave |
| `masterdata.mGroupMaster` | no | fMaterialGroup:MMIGDelete, fMaterialGroup:MMIGSave | fMaterialGroup:MMIGFillValues, fMaterialGroup:MMIGFillValuesDependent, fMaterialGroup:MMIGLoadData, fMaterialGroup:MMIGSave, fMaterialGroup:MMIGValidate, fUnitMaster:MMUMFillValues |
| `masterdata.mGroupMasterCompanyDetail` | no | fMaterialGroup:MMIGDelete, fMaterialGroup:MMIGSave | fMaterialGroup:MMIGLoadData, fMaterialGroup:MMIGValidate |
| `masterdata.mGroupQCParameterDetail` | no | fMaterialGroup:MMIGDelete, fMaterialGroup:MMIGSave, fMaterialGroup:MMIGSaveQCParameter | fMaterialGroup:MMIGLoadData |
| `masterdata.mItemMaster` | yes | fMaterialGroup:MMIGSave | - |
| `masterdata.mQCParameters` | no | - | fMaterialGroup:MMIGLoadData, fMaterialGroup:QCFillValues, fMaterialGroup:QCFillValuesDependent |
| `masterdata.mSubGroupMaster` | yes | - | fMaterialGroup:MMIGSave, fUnitMaster:MMUMFillValues, fUnitMaster:MMUMLoadData |
| `masterdata.mSubGroupMasterCompanyDetail` | yes | - | fUnitMaster:MMUMFillValues |
| `masterdata.mSubGroupUnitDetail` | yes | fUnitMaster:MMUMDelete, fUnitMaster:MMUMSave, fUnitMaster:MMUMSaveSubGroupUnitDetail | fUnitMaster:MMUMFillValues, fUnitMaster:MMUMLoadData |
| `masterdata.mUnitMaster` | no | fUnitMaster:MMUMDelete, fUnitMaster:MMUMSave | fMaterialGroup:QCFillValues, fUnitMaster:MMUMFillValues, fUnitMaster:MMUMLoadData, fUnitMaster:MMUMSearchData, fUnitMaster:MMUMValidate |
| `masterdata.mUnitMasterCompanyDetail` | no | fUnitMaster:MMUMDelete, fUnitMaster:MMUMSave | fMaterialGroup:QCFillValues, fUnitMaster:MMUMFillValues, fUnitMaster:MMUMLoadData, fUnitMaster:MMUMSearchData, fUnitMaster:MMUMValidate |

### Where to look in the source

26 source files: `DataLayer/DAMaterialSubGroupMaster.cs`, `DataLayer/DAOMaterialSubGroupMaster.cs`, `DataLayer/DTMaterialSubGroupMaster.cs`, `Form/fMaterialSubGroupMaster.Designer.vb`, `Form/fMaterialSubGroupMaster.vb`, `QCGroupControl/DAOQCGroup.cs`, `QCGroupControl/DAQCGroup.cs`, `QCGroupControl/DTQCGroup.cs`, `QCGroupControl/QCGroup.Designer.cs`, `QCGroupControl/QCGroup.cs`, `QCGroupControl/Struct.cs`, `StoredProcedures/masterdata.MSGMDelete.sql`, `StoredProcedures/masterdata.MSGMFillValues.sql`, `StoredProcedures/masterdata.MSGMFillValuesDependent.sql`, `StoredProcedures/masterdata.MSGMLoadData.sql`, `StoredProcedures/masterdata.MSGMSaveBinDetail.sql`, `StoredProcedures/masterdata.MSGMSaveDivision.sql`, `StoredProcedures/masterdata.MSGMSaveMain.sql`, `StoredProcedures/masterdata.MSGMSaveMake.sql`, `StoredProcedures/masterdata.MSGMSaveQC.sql`, `StoredProcedures/masterdata.MSGMSaveUnit.sql`, `StoredProcedures/masterdata.MSGMSaveVendor.sql`, `StoredProcedures/masterdata.MSGMSearchData.sql`, `StoredProcedures/masterdata.MSGMValidate.sql`, `StoredProcedures/masterdata.QCFillValues.sql`, `StoredProcedures/masterdata.QCFillValuesDependent.sql`

Graph lookup: project `fMaterialSubGroupMaster__81cf52cf`, form `fMaterialSubGroupMaster__81cf52cf.Form.fMaterialSubGroupMaster`.
<!-- END GRAPH-MAP -->
