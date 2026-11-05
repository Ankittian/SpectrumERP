# Material Group (`fMaterialGroup`)
> Maintains the Material Group master: a 2-character group code and name under a Material Category, with optional default QC parameters.

**Form code:** `MMIG` (form Tag; also the Excel sheet name for import, and the error-log code)  
**Who can use / edit:** Head office only can edit. If the logged-in company is not the head office, the form locks all controls (`LockEachControl`, behaviour inferred). The code shows no other role checks.

## What it is for
Holds the second level of the item hierarchy: Category > Group > Sub Group > Item. A group belongs to one Category and has a 2-character code. The full group code is the category code plus the group code, for example `AB` + `01`. A group can also carry default QC (quality check) parameters. A new group is made available to every company.

## Screen guide
| Field | Required? | Rules and limits | Notes |
|---|---|---|---|
| Category Name (dropdown) | Yes | Must be picked from the list | Lists categories that are active for the current company, plus the record's own category when it is opened. Changing it clears Code and fills the next free code. |
| Category Code | Auto | Read-only, max 4 | Shown from the selected category. |
| Code | Yes | Exactly 2 characters (max 2) | Auto-suggested as highest numeric code in the category + 1, 2 digits. It can be overwritten. |
| Group Code | Auto | Read-only, max 4 | Category Code + Code. The "Group Code" heading is also the link to Fast Entry mode. |
| Group Name | Yes | Max 100 characters | |
| Inactive | No | Always disabled | Shows state only. Save never writes it. |
| Fast Entry grid | Per row | Columns: Category Name, Code (max 2), Group Name, Remarks | Remarks is read-only. A new blank row is added when you edit the last row. Rows with a blank Category Name are skipped. |
| QC grid (embedded QC Group control) | No | See below | **The control is hidden on this form** (see quirks). |
| QC Group Name (in QC control) | No | Template picker | Picking one replaces the grid with that QC group's parameters. |
| QC Parameter Name | Yes, per used row | No duplicates | Filling it copies unit, standard, tolerance and deduction defaults. |
| Unit, Tolerance Type, Tolerance Unit, Deduction On, Formula Type | Auto | Not editable | Come from the QC parameter. |
| Standard Value1 / Standard Value2 | Value1 yes | Value1 cannot be zero. Up to 3 decimals, 10 characters | Value2 is optional. |
| Actual Value1 / Actual Value2 | No | Hidden by default | Never saved by this form. |
| Tolerance Value | Yes | Up to 3 decimals | |
| Deduction Rate | Yes | Basic, Prorata or Landed | |
| Deduction Type | Yes | Single or Double | |
| Double Deduction From | Only if Double | Editable only when type is not Single (1). Cleared when type is set to Single | |

## Actions
| Action | What happens | Confirmations or restrictions |
|---|---|---|
| New | Clears the form. | Head office only can type. |
| Save | Validates, then saves group, then QC rows, in one transaction. Shows a saved message and starts a new record. | Save confirmation from base library (inferred). Rolls back on any error. |
| Open / Search | Opens a search list (`masterdata.MMIGSearchData`), then loads the chosen group. | The list comes from a procedure configured in `GlobalData.FormSearchDataDetail` for form 26. Its content is not in this code. |
| Delete | Deletes the open group (`masterdata.MMIGDelete`). Starts a new record on success. | Delete confirmation from base library (inferred). Nothing happens if no record is open. |
| Fast Entry (click "Group Code" heading) | Starts a new record and shows the bulk grid. | Unsaved data on the form is lost (inferred). |
| Switch back to detail mode | Hides the Fast Entry grid. | |
| Import (Fast Entry) | Asks for an Excel file, replaces the grid with its rows. | Prompt: "Your excel should consists of sheet with name MMIG. Do you want to continue?" Sheet needs columns Category Name, Code, Group Name. |
| Save in Fast Entry | Saves each row one by one and writes the result in Remarks. | Final popup: "Refer Remarks for data saved status." |
| Print, Preview, Export, Email | Do nothing. | Not on the toolbar. |

## Validation and error messages
| Message | When it appears | What the user should do |
|---|---|---|
| Select valid Category Name. | No category selected, or the Excel category name is not in the list. | Pick an active category. In Fast Entry it appears in Remarks. |
| Code must be 2 digit. | Code is not exactly 2 characters. Only length is checked, not digits. | Enter 2 characters. |
| Duplicate Group Name is not allowed. | Same name already exists in the same category (this company). Own record excluded. | Change the name. |
| Duplicate Group Code is not allowed. | Same 2-character code already used in the same category. | Change the code or use the suggested one. |
| Enter Group Name. | Group Name is blank. Checked after the duplicate checks. | Enter a name. |
| Standard Value can't be empty or zero | A QC row has Standard Value1 blank or 0. | Fill it or remove the QC row. |
| Enter Tolerance Value | A QC row has no tolerance. | Fill it. |
| Select valid Deduction Rate | QC row has no deduction rate. | Pick one. |
| Select valid Deduction Type | QC row has no deduction type. | Pick one. |
| Enter Double Deduction From | Deduction Type is Double and the field is blank. | Fill it. |
| Duplicate QC Parameter not allowed. | Same QC parameter on two rows. Text is set by this control, the check is in the base library (inferred). | Remove one row. |
| Successfully Created. | Fast Entry Remarks for a row. | See quirks: it can be wrong. |
| Refer Remarks for data saved status. | After a Fast Entry save. | Read each row's Remarks. |
| Database error text | If saving a group, QC row or delete fails, the SQL error text is shown (`masterdata.MMIGSave`, `masterdata.MMIGSaveQCParameter`, `masterdata.MMIGDelete`). | Send the text to support. |

Not shown in practice: "Actual Value1 can't be empty or zero" (its columns are hidden) and "Select atleast one QC Parameter." (the form does not turn that check on).

## Business rules
- Group Name must be unique within a Category. Group Code must be unique within a Category. The code check ignores company.
- Full code = Category Code + Group Code. When a group's code or category changes, `masterdata.mItemMaster` FullCode is rebuilt for items under its sub groups (`masterdata.mSubGroupMaster`), using `masterdata.mCategoryMaster`.
- New group: row in `masterdata.mGroupMaster`, plus a `masterdata.mGroupMasterCompanyDetail` row (not inactive) for every company in `masterdata.mCompanyMaster`.
- New and edited groups are saved as authorized (status 30), with the saving user and date.
- Edit: all `masterdata.mGroupQCParameterDetail` rows for the group are deleted, then re-inserted from the grid.
- Delete is permanent. It removes `masterdata.mGroupQCParameterDetail`, `masterdata.mGroupMasterCompanyDetail` and `masterdata.mGroupMaster` rows. The procedure does no usage check. A database error (for example from linked sub groups) would appear as the error text (possible).
- Category list for the dropdown: `masterdata.mCategoryMaster` rows active for the company in `masterdata.mCategoryMasterCompanyDetail`.
- QC dropdowns show only authorized, active parameters, units and QC groups for the company (`masterdata.QCFillValues`, `masterdata.QCFillValuesDependent`).

## Common ticket scenarios
| Symptom | Most likely cause | What to check or do |
|---|---|---|
| Cannot type or save on the form | Logged in to a company that is not head office | Log in at head office. |
| "Duplicate Group Code is not allowed." for a code that looks unused | Code is unique per category across all companies, and the group may exist under that category | Open the category's groups and use another code. |
| Category missing from the dropdown | Category is inactive for this company, or not shared with it | Check `masterdata.mCategoryMasterCompanyDetail` for the company. |
| Suggested code is "00" | Possible: 99 was the highest code, so the next number is cut to 2 digits | Enter a free code by hand. |
| Fast Entry row says "Successfully Created." but the group is missing | The row error was swallowed (see quirks) | Check for a database error popup, then search for the group. |
| Cannot delete a group | Database refused (possible: sub groups or items still use it) | Read the error text. Move or remove dependants first. |
| "Standard Value can't be empty or zero" when only editing a group | An old QC row with zero standard value is saved on the group | Fix or remove the QC row. The QC grid is hidden, so this needs a developer (possible). |
| Inactive box cannot be ticked | The checkbox is always disabled here | Inactive status is not set on this form. Find the maintenance screen that does it (not shown in this code). |
| Excel import loads nothing | Wrong sheet name or file cancelled | Sheet must be named MMIG with columns Category Name, Code, Group Name. |
| Item full codes changed after a group code was edited | Save rebuilds item full codes under the group | Expected. Tell the client to check dependent documents. |

## Limits and known quirks
- The embedded QC grid has Visible = False in the form design and the form code never shows it. Users cannot see or edit QC rows here, yet Save still validates them and re-saves the loaded ones.
- Fast Entry says "Successfully Created." even if the save failed, because the save routine catches its own errors (a popup appears instead).
- Fast Entry group name column is set to a narrow width (100) in code; long names are cut off on screen only.
- The Inactive checkbox is disabled and not saved.
- `masterdata.MMIGLoadData` joins company details without filtering by company, so the Inactive value shown may come from another company's row (possible).
- Print, Preview, Export and Email are empty.
- Group Name has no length limit in the Fast Entry grid; over 100 characters would fail at the database (possible).
- Duplicate name check applies before the "Enter Group Name." check.
- The QC procedures log errors under form code `ODDC`, not `MMIG`.

## Glossary
| Term | Meaning |
|---|---|
| `MMIG` | Code of this form and prefix of its procedures (`masterdata.MMIG...`). |
| `QCFillValues` | Procedures of the shared QC control. |
| Category Code + Code = Group Code | 2 characters from the category plus 2 from the group, up to 4 characters. |
| Fast Entry | Bulk entry grid, typed or imported from Excel. |
| QC parameter | A quality check item with a standard value, tolerance and deduction rules. |
| Deduction Rate | Basic, Prorata or Landed. |
| Deduction Type | Single or Double. Double also needs "Double Deduction From". |
| Head office | The company where editing is allowed. |

<!-- BEGIN GRAPH-MAP -->
## Technical map (generated from the knowledge graph)

_Generated 2026-11-04 from graph project `fMaterialGroup__df413c37`. Do not edit between the markers; re-run the refresh instead._

### What each screen action runs

| Form method (VB, line) | Called from | Data-layer method | Stored procedure | Reads | Writes |
| --- | --- | --- | --- | --- | --- |
| `Delete` (60) | - | `Delete` | `masterdata.MMIGDelete` | - | `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `masterdata.mGroupQCParameterDetail` |
| `FillValues` (91) | `LoadData` | `FillValues` | `masterdata.MMIGFillValues` | `masterdata.mCategoryMaster`, `masterdata.mCategoryMasterCompanyDetail`, `masterdata.mGroupMaster` | - |
| `LoadData` (122) | `Open` | `LoadData` | `masterdata.MMIGLoadData` | `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `masterdata.mGroupQCParameterDetail`, `masterdata.mQCParameters` | - |
| `Open` (161) | - | `SearchData` | `masterdata.MMIGSearchData` | `globaldata.FormSearchDataDetail` | - |
| `SaveMain` (280) | `Save` | `Save` | `masterdata.MMIGSave` | `masterdata.mCategoryMaster`, `masterdata.mCompanyMaster`, `masterdata.mGroupMaster`, `masterdata.mSubGroupMaster` | `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `masterdata.mGroupQCParameterDetail`, `masterdata.mItemMaster` |
| `SaveQC` (329) | `SaveMain` | `SaveQCParameter` | `masterdata.MMIGSaveQCParameter` | - | `masterdata.mGroupQCParameterDetail` |
| `ValidateForm` (363) | `Save` | `Validate` | `masterdata.MMIGValidate` | `masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail` | - |
| `ucmbCategoryName_ValueChanged` (452) | - | `FillValuesDependent` | `masterdata.MMIGFillValuesDependent` | `masterdata.mGroupMaster` | - |

_`masterdata.mErrorLog` (written by every procedure's error handler) is left out of the table lists._

Procedures in this form's folder that the graph could not link to a form method (called some other way, for example from the embedded QC control; check the source): `masterdata.QCFillValues`, `masterdata.QCFillValuesDependent`.

### Tables this form changes

`masterdata.mGroupMaster`, `masterdata.mGroupMasterCompanyDetail`, `masterdata.mGroupQCParameterDetail`, `masterdata.mItemMaster`

### Same tables used by other forms (impact check before changing data or rules)

| Table | Written by here | Also written by | Also read by |
| --- | --- | --- | --- |
| `globaldata.FormSearchDataDetail` | no | - | fMaterialSubGroupMaster:MSGMSearchData |
| `masterdata.mCategoryMaster` | no | - | fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMSaveMain, fMaterialSubGroupMaster:MSGMValidate |
| `masterdata.mCategoryMasterCompanyDetail` | no | - | fMaterialSubGroupMaster:MSGMFillValues |
| `masterdata.mCompanyMaster` | no | - | fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMSaveMain, fUnitMaster:MMUMSave |
| `masterdata.mGroupMaster` | yes | - | fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMFillValuesDependent, fMaterialSubGroupMaster:MSGMLoadData, fMaterialSubGroupMaster:MSGMSaveMain, fMaterialSubGroupMaster:MSGMValidate, fUnitMaster:MMUMFillValues |
| `masterdata.mGroupMasterCompanyDetail` | yes | - | fMaterialSubGroupMaster:MSGMFillValues |
| `masterdata.mGroupQCParameterDetail` | yes | - | fMaterialSubGroupMaster:MSGMFillValuesDependent |
| `masterdata.mItemMaster` | yes | fMaterialSubGroupMaster:MSGMSaveMain | - |
| `masterdata.mQCParameters` | no | - | fMaterialSubGroupMaster:MSGMFillValuesDependent, fMaterialSubGroupMaster:MSGMLoadData, fMaterialSubGroupMaster:QCFillValues, fMaterialSubGroupMaster:QCFillValuesDependent |
| `masterdata.mSubGroupMaster` | no | fMaterialSubGroupMaster:MSGMDelete, fMaterialSubGroupMaster:MSGMSaveMain | fMaterialSubGroupMaster:MSGMFillValues, fMaterialSubGroupMaster:MSGMFillValuesDependent, fMaterialSubGroupMaster:MSGMLoadData, fMaterialSubGroupMaster:MSGMSaveMain, fMaterialSubGroupMaster:MSGMValidate, fUnitMaster:MMUMFillValues, fUnitMaster:MMUMLoadData |

### Where to look in the source

21 source files: `DataLayer/DAMaterialGroup.cs`, `DataLayer/DAOMaterialGroup.cs`, `DataLayer/DTMaterialGroup.cs`, `Form/fMaterialGroup.Designer.vb`, `Form/fMaterialGroup.vb`, `QCGroupControl/DAOQCGroup.cs`, `QCGroupControl/DAQCGroup.cs`, `QCGroupControl/DTQCGroup.cs`, `QCGroupControl/QCGroup.Designer.cs`, `QCGroupControl/QCGroup.cs`, `QCGroupControl/Struct.cs`, `StoredProcedures/masterdata.MMIGDelete.sql`, `StoredProcedures/masterdata.MMIGFillValues.sql`, `StoredProcedures/masterdata.MMIGFillValuesDependent.sql`, `StoredProcedures/masterdata.MMIGLoadData.sql`, `StoredProcedures/masterdata.MMIGSave.sql`, `StoredProcedures/masterdata.MMIGSaveQCParameter.sql`, `StoredProcedures/masterdata.MMIGSearchData.sql`, `StoredProcedures/masterdata.MMIGValidate.sql`, `StoredProcedures/masterdata.QCFillValues.sql`, `StoredProcedures/masterdata.QCFillValuesDependent.sql`

Graph lookup: project `fMaterialGroup__df413c37`, form `fMaterialGroup__df413c37.Form.fMaterialGroup`.
<!-- END GRAPH-MAP -->
