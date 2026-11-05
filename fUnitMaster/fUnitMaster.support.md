# Unit Master (`fUnitMaster`)
> Maintains the list of measurement units (Kg, Mtr, Pcs...), their conversions to other units, and which material subgroups use them.

**Form code:** `MMUM` (form Tag; also the Excel import sheet name and the error-log form code)  
**Who can use / edit:** The code shows no role check. The toolbar offers New, Save, Open, Delete and Navigation (no Print, Preview, Email or Export). Access is controlled outside this form (inferred).

## What it is for
Unit Master holds the units of measure used across material and item masters. Each unit has a category, an optional GST UQC code, optional conversion factors to other units, and a list of material subgroups with the unit type for each. It is base master data: subgroups and items depend on it, and it depends on the global lists (unit category, unit type, GST UQC).

## Screen guide
| Field | Required? | Rules and limits | Notes |
|---|---|---|---|
| Code | Auto | Read-only, max 6, not in tab order | Generated on first save as `UM0001`, `UM0002`... (next number after the highest existing). |
| Unit Name | Yes | Max 25 characters. Trimmed. Must be unique within the current company. | Highlighted as a compulsory field. |
| Alias | Yes | Max 6 characters. Trimmed. Must be unique within the current company. | Short name shown in lists and as "Base Unit" in the conversion grid. |
| Category | Yes | Pick from the category list (`GlobalData.UnitCategory`). | Typed text that is not in the list is rejected. |
| GST UQC | No | Pick from the GST unit list (`GlobalData.GSTUnitMaster`). | If blank, the UQC is saved empty. |
| Inactive | No | Checkbox, disabled (greyed out). | Shows the saved status on opening a record; users cannot change it here (see quirks). |
| Standard Conversion Factor grid: Conversion Type | Per row | Fixed or Variable. | A row is only treated as filled if a type is chosen. |
| Grid: Unit Value | Yes if type chosen | Number, up to 11 characters, 3 decimals. Cannot be 0. | |
| Grid: Base Unit | Auto | Read-only. Shows this unit's Alias. | Updates as the Alias is typed. |
| Grid: Conversion Value | Yes if type chosen | Number, up to 11 characters, 3 decimals. Cannot be 0. | |
| Grid: Unit | Yes if type chosen | Pick the other unit. No duplicates. | List shows active units of the current company, except this unit itself. Already-linked units stay in the list. |
| Material Subgroup grid: Subgroup Name | Per row | Pick a subgroup. No duplicates. | List shows active subgroups of the current company, plus ones already linked to this unit. |
| Grid: Subgroup Code | Auto | Read-only, filled when a subgroup is chosen. | |
| Grid: Unit Type | Yes if subgroup chosen | Pick from `GlobalData.UnitType`. | |
| Fast Entry panel (link "Code") | - | Replaces the form with a bulk-entry grid: Unit Name (max 25), Alias (max 6), Category, Remarks (read-only). | Link tooltip: "Switch to fast entry mode." Back link: "Switch back to detail mode." |
| Import button (Fast Entry) | - | Reads Unit Name, Alias, Category columns from an Excel sheet named `MMUM`. | Adds a Remarks column to show the result per row. |

## Actions
| Action | What happens | Confirmations or restrictions |
|---|---|---|
| New | Clears the form and focuses Unit Name. | None shown by this form. |
| Save (normal mode) | Validates, then saves the unit, conversion rows and subgroup rows in one transaction. Shows a saved message and clears the form. | A save confirmation (text comes from the base library, inferred). Nothing is saved if you decline. |
| Save (Fast Entry mode) | Saves each grid row that has a Unit Name as a separate unit. Each row's result goes in Remarks. | One confirmation for the batch. Final message: "Refer remarks for saved status." |
| Open | Opens a search list of all units of the current company: Code, Unit Name, Alias, Category Name, Inactive, Created By, Created Date. Picking one loads it. | Only the current company's units are listed. |
| Delete | Removes the open unit permanently. On success the form clears. | Delete confirmation (base library, inferred). Does nothing if no record is open. |
| Import (Fast Entry only) | Loads units from Excel into the Fast Entry grid; review, then Save. | Confirmation text: "Your excel should consists of sheet with name MMUM. Do you want to continue?" |
| Print, Preview, Email, Export | Nothing happens (empty in code). | - |

## Validation and error messages
| Message | When it appears | What the user should do |
|---|---|---|
| Enter Unit Name. | Unit Name empty. | Type a name. |
| Duplicate Unit Name is not allowed. | Another unit of this company has the same name. | Use a different name, or open the existing unit. |
| Duplicate Alias is not allowed. | Another unit of this company has the same alias. | Use a different alias. |
| Enter Alias. | Alias empty. | Type an alias. |
| Select valid Category Name. | No valid category selected. | Pick one from the list. |
| Enter Unit Value in row N. | Conversion row has a type but Unit Value is 0 or empty. | Enter the value. |
| Enter Conversion Value in row N. | Conversion row has a type but Conversion Value is 0 or empty. | Enter the value. |
| Enter Unit in row N. | Conversion row has a type but no Unit. | Pick the unit, or clear the type. |
| Select valid Unit Type in row N. | Subgroup row has a subgroup but no Unit Type. | Pick the unit type. |
| Duplicate Unit is not allowed. | Same unit chosen twice in the conversion grid. | Remove the repeated row. |
| Duplicate Subgroup Name is not allowed. | Same subgroup chosen twice in the subgroup grid. | Remove the repeated row. |
| Successfully Created. | Fast Entry Remarks, row saved (see quirks). | None. |
| Refer remarks for saved status. | After a Fast Entry save. | Read each row's Remarks. |

Other errors (database error text on save or delete, for example a failed delete) are shown as returned by the database or base library; wording varies. Fast Entry rows show the same messages above in Remarks (the "row N" grid checks use pop-ups, not Remarks).

## Business rules
- Duplicate Unit Name and Duplicate Alias are checked per company (`masterdata.MMUMValidate`), against `masterdata.mUnitMaster` and `masterdata.mUnitMasterCompanyDetail`. Name is checked first, then alias. Case sensitivity depends on the database (inferred).
- Code is generated by `masterdata.MMUMSave`: `UM` plus a 4-digit number.
- New unit: a row goes into `masterdata.mUnitMaster`, plus one row per company in `masterdata.mUnitMasterCompanyDetail` (Inactive = 0 for all companies). The unit is saved as authorized (DocumentStatusNo defaults to 30; the form does not send another value).
- Editing changes the unit's name, alias, category and GST UQC for all companies (shared row), and records modified by/date.
- On every edit save, all existing conversion rows (both directions) and subgroup links for this unit are deleted and re-created from the grids (`masterdata.mUnitConversionDetail`, `masterdata.mSubGroupUnitDetail`).
- Each conversion row is saved twice (`masterdata.MMUMSaveUnitConversionDetail`): A to B with values (Unit Value, Conversion Value) and B to A with the values swapped.
- Subgroup rows are saved by `masterdata.MMUMSaveSubGroupUnitDetail`.
- Delete (`masterdata.MMUMDelete`) is a hard delete in one transaction: removes conversion rows where this unit is either side, its subgroup links, its company rows and the unit itself. The procedure has no "unit is in use" check. If the database blocks it, the error text is shown (inferred).
- Lookup lists for the screen come from `masterdata.MMUMFillValues`; load from `masterdata.MMUMLoadData`; search from `masterdata.MMUMSearchData`.
- Save and delete errors roll the whole transaction back.

## Common ticket scenarios
| Symptom | Most likely cause | What to check or do |
|---|---|---|
| "Duplicate Unit Name is not allowed." on a new unit | A unit with that name already exists in this company (possibly Inactive). | Open search, look for it. Reuse or rename. |
| "Duplicate Alias is not allowed." | Same alias used by another unit. | Pick a different alias (max 6 characters). |
| Cannot type a full unit name or alias | Limits are 25 and 6 characters. | Shorten the text. |
| Inactive tick box cannot be changed | The checkbox is disabled on this form. | Possible: the unit is inactivated from another screen. Not controlled here. |
| Ticking Inactive and saving has no effect | The save does not send the Inactive value to the database. | Escalate as a defect. |
| A unit is missing from the Unit dropdown in the conversion grid | List only has active units of the current company, and excludes the unit itself. | Check the unit exists and is not inactive for this company. |
| A subgroup is missing from the Subgroup Name dropdown | List only has active subgroups of the current company. | Check the subgroup exists and is active. |
| Delete fails or the unit was deleted with its conversions | Delete removes conversions and subgroup links, with no usage check. If other data uses the unit, the database may refuse. | Read the message shown. Possible: other masters reference the unit. |
| Excel import loads nothing | Sheet must be named `MMUM` with columns Unit Name, Alias, Category. | Check the sheet name and headers. |
| Fast Entry row says "Select valid Category Name." | Category text in Excel does not match a category in the list. | Match the exact category name. |
| Fast Entry shows "Successfully Created." but the unit is not there | Possible: a save error was caught and shown as a pop-up, while the row remark still says success. | Search for the unit; check any error pop-up. |

## Limits and known quirks
- The Inactive checkbox is disabled, and the save procedure has no Inactive input. Inactive only changes elsewhere; this form shows it when loading.
- Edit saves rebuild all conversion and subgroup rows. Conversions from other units to this one are removed and re-created only from this unit's grid.
- Conversion values are saved with 3 decimals (database column decimal(8,3)); grid allows decimals(7,3).
- Fast Entry saves one row at a time. In code a failed row can still show "Successfully Created." because the save routine handles its own errors.
- Print, Preview, Email and Export do nothing.
- Fast Entry panel is entered by clicking the "Code" link, which also clears any open record. Import works only while that panel is visible (it sits inside it).
- Grids add a blank row automatically after editing the last row. Blank rows (no type / no subgroup) are ignored on save.
- Delete is permanent; no undo.
- Duplicate checks use the current company only; a name used by a unit not linked to the current company is not caught.

## Glossary
| Term | Meaning |
|---|---|
| `MMUM` | Unit Master form code (M-master, M-material, UM-unit master); prefix of its stored procedures. |
| `UM0001` | Unit code format. |
| UQC | GST Unit Quantity Code, picked from `GlobalData.GSTUnitMaster`. |
| Conversion Type | Fixed or Variable (stored as 1 / 2). |
| Base Unit | The unit being edited (shown by its Alias). |
| Unit Type | Role of the unit for a subgroup, from `GlobalData.UnitType`. |
| Fast Entry | Bulk-entry grid mode for creating many units, with Excel import. |

<!-- BEGIN GRAPH-MAP -->
## Technical map (generated from the knowledge graph)

_Generated 2026-11-04 from graph project `fUnitMaster__b630ded3`. Do not edit between the markers; re-run the refresh instead._

### What each screen action runs

| Form method (VB, line) | Called from | Data-layer method | Stored procedure | Reads | Writes |
| --- | --- | --- | --- | --- | --- |
| `Delete` (34) | - | `Delete` | `masterdata.MMUMDelete` | - | `masterdata.mSubGroupUnitDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail` |
| `FillValues` (64) | `LoadData` | `FillValues` | `masterdata.MMUMFillValues` | `globaldata.GSTUnitMaster`, `globaldata.UnitCategory`, `globaldata.Unittype`, `masterdata.mGroupMaster`, `masterdata.mSubGroupMaster`, `masterdata.mSubGroupMasterCompanyDetail`, `masterdata.mSubGroupUnitDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail` | - |
| `LoadData` (107) | `Open` | `LoadData` | `masterdata.MMUMLoadData` | `masterdata.mSubGroupMaster`, `masterdata.mSubGroupUnitDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail` | - |
| `Open` (147) | - | `SearchData` | `masterdata.MMUMSearchData` | `globaldata.UnitCategory`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`, `security.Login` | - |
| `SaveConversionFactor` (252) | `SaveMain` | `SaveUnitConversionDetail` | `masterdata.MMUMSaveUnitConversionDetail` | - | `masterdata.mUnitConversionDetail` |
| `SaveSubGroupUnitDetail` (281) | `SaveMain` | `SaveSubGroupUnitDetail` | `masterdata.MMUMSaveSubGroupUnitDetail` | - | `masterdata.mSubGroupUnitDetail` |
| `ValidateForm` (308) | `Save` | `Validate` | `masterdata.MMUMValidate` | `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail` | - |
| `SaveMain` (595) | `Save` | `Save` | `masterdata.MMUMSave` | `masterdata.mCompanyMaster` | `masterdata.mSubGroupUnitDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail` |

_`masterdata.mErrorLog` (written by every procedure's error handler) is left out of the table lists._

### Tables this form changes

`masterdata.mSubGroupUnitDetail`, `masterdata.mUnitConversionDetail`, `masterdata.mUnitMaster`, `masterdata.mUnitMasterCompanyDetail`

### Same tables used by other forms (impact check before changing data or rules)

| Table | Written by here | Also written by | Also read by |
| --- | --- | --- | --- |
| `globaldata.Unittype` | no | - | fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMLoadData |
| `masterdata.mCompanyMaster` | no | - | fMaterialGroup:MMIGSave, fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMSaveMain |
| `masterdata.mGroupMaster` | no | fMaterialGroup:MMIGDelete, fMaterialGroup:MMIGSave | fMaterialGroup:MMIGFillValues, fMaterialGroup:MMIGFillValuesDependent, fMaterialGroup:MMIGLoadData, fMaterialGroup:MMIGSave, fMaterialGroup:MMIGValidate, fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMFillValuesDependent, fMaterialSubGroupMaster:MSGMLoadData, fMaterialSubGroupMaster:MSGMSaveMain, fMaterialSubGroupMaster:MSGMValidate |
| `masterdata.mSubGroupMaster` | no | fMaterialSubGroupMaster:MSGMDelete, fMaterialSubGroupMaster:MSGMSaveMain | fMaterialGroup:MMIGSave, fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMFillValuesDependent, fMaterialSubGroupMaster:MSGMLoadData, fMaterialSubGroupMaster:MSGMSaveMain, fMaterialSubGroupMaster:MSGMValidate |
| `masterdata.mSubGroupMasterCompanyDetail` | no | fMaterialSubGroupMaster:MSGMDelete, fMaterialSubGroupMaster:MSGMSaveMain | fMaterialSubGroupMaster:MSGMLoadData, fMaterialSubGroupMaster:MSGMValidate |
| `masterdata.mSubGroupUnitDetail` | yes | fMaterialSubGroupMaster:MSGMDelete, fMaterialSubGroupMaster:MSGMSaveMain, fMaterialSubGroupMaster:MSGMSaveUnit | fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMLoadData |
| `masterdata.mUnitMaster` | yes | - | fMaterialGroup:QCFillValues, fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:QCFillValues |
| `masterdata.mUnitMasterCompanyDetail` | yes | - | fMaterialGroup:QCFillValues, fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:QCFillValues |

### Where to look in the source

13 source files: `DataLayer/DAOUnitMaster.cs`, `DataLayer/DAUnitMaster.cs`, `DataLayer/DTUnitMaster.cs`, `Form/fUnitMaster.Designer.vb`, `Form/fUnitMaster.vb`, `StoredProcedures/masterdata.MMUMDelete.sql`, `StoredProcedures/masterdata.MMUMFillValues.sql`, `StoredProcedures/masterdata.MMUMLoadData.sql`, `StoredProcedures/masterdata.MMUMSave.sql`, `StoredProcedures/masterdata.MMUMSaveSubGroupUnitDetail.sql`, `StoredProcedures/masterdata.MMUMSaveUnitConversionDetail.sql`, `StoredProcedures/masterdata.MMUMSearchData.sql`, `StoredProcedures/masterdata.MMUMValidate.sql`

Graph lookup: project `fUnitMaster__b630ded3`, form `fUnitMaster__b630ded3.Form.fUnitMaster`.
<!-- END GRAPH-MAP -->
