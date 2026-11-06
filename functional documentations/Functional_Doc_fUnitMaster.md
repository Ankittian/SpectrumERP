# Unit Master Screen: Functional Documentation

## 1. Summary
*This section provides an executive overview of the Unit Master screen and its role in Materials Management.*

The Unit Master screen maintains the standard units of measurement used for materials, and the conversion relationships between them. It gives the business one authoritative list of units, so that quantities bought in bulk, stocked internally and sold in smaller packs are described consistently (Inferred). Users can create units one at a time on a detail card or in bulk through a Fast Entry grid, which can also be filled from an Excel sheet. Each unit has a name, a short alias, a category and an optional GST quantity code. Users can also record standard conversion factors to other units (the system adds the reverse conversion automatically) and map the unit to material subgroups with a unit-type role. Each new unit is made available in every registered company; the screen applies no Head Office restriction. Purchasing, stores, production and billing teams benefit from consistent units and conversion ratios (Inferred).

## 2. Purpose and Scope
*This section outlines the business rationale for the Unit Master screen and establishes its operational boundaries within the enterprise.*

### Business Purpose of Units
**What it is:** The screen defines the standard units of measurement and the conversion relationships between them.
**When it applies:** Whenever the business introduces a new unit, changes how an existing unit is described, or sets up conversion ratios between units.
**Business outcome:** Downstream screens use the same unit definitions and conversion ratios, which reduces quantity discrepancies (Inferred).

### In-Scope Functional Capabilities
**What it is:** The functional scope covered directly by the Unit Master screen.
**When it applies:** Single-unit creation and modification, bulk creation in Fast Entry, bulk loading from an Excel sheet, searching, browsing, conversion factor maintenance, material subgroup mapping and deletion.
**Business outcome:** Users maintain:
- a unique Unit Name (BR-08) and a unique Alias (BR-09)
- a mandatory Category (BR-04)
- an optional GST UQC (BR-05)
- the conversion factor rows, including the automatic reverse conversions (BR-12, BR-21)
- the subgroup mappings, each with a Unit Type (BR-14)

When a unit is first saved, the system makes it available in every company (BR-10).

### Out-of-Scope Capabilities
**What it is:** Business activities related to units that are excluded from the Unit Master screen.
**When it applies:** The following needs are not served here:
- maintaining the lists of unit categories, GST quantity codes and unit types, which this screen only reads
- marking a unit inactive or active, because the Inactive box is view-only (BR-19)
- printing, previewing, exporting or emailing unit records
- shop-floor weighing, or recalculating quantities on transactions (Inferred)

**Business outcome:** These needs are handled in other screens or administrative utilities (Inferred). The Unit Master screen is limited to defining units and their relationships.

## 3. Business Glossary
*This section defines standard business terminology used on and around the Unit Master screen.*

### Unit of Measure
**What it is:** A standard quantity of mass, volume, length or count, such as a kilogram, metre or litre (Inferred examples).
**When it applies:** Used wherever quantities are recorded for materials (Inferred).
**Business outcome:** Quantities are tracked and valued consistently across the business.

### Unit Code
**What it is:** A read-only reference assigned when a unit is first saved. It is the letters "UM" followed by a four-digit running number, for example UM0001 (BR-07).
**When it applies:** Shown on the detail card, in the search list and in the conversion target list.
**Business outcome:** Gives each unit a short, permanent reference that users cannot edit.

### Unit Name
**What it is:** The full descriptive name of the unit, up to 25 characters (BR-02, BR-06).
**When it applies:** Entered on the detail card or in Fast Entry. It must be unique (BR-08).
**Business outcome:** Identifies the unit clearly in lists and searches.

### Unit Alias
**What it is:** A mandatory short form of the unit name, up to 6 characters (BR-03, BR-06).
**When it applies:** Entered on the detail card or in Fast Entry. It must be unique (BR-09). It also appears as the "Base Unit" in the conversion grid (BR-20) and as the display text in the conversion target list.
**Business outcome:** Gives a compact symbol, such as KG or LTR, for grids, lists and documents (Inferred for documents).

### Unit Category
**What it is:** The dimensional family a unit belongs to, chosen from a central category list (for example Weight, Length or Volume, Inferred).
**When it applies:** Must be selected for every unit (BR-04).
**Business outcome:** Classifies each unit within a dimensional family.

### GST Unique Quantity Code (UQC)
**What it is:** A government-defined quantity code used in GST reporting, chosen from a central list that shows each code and its name.
**When it applies:** Can be set on the detail card. It is optional (BR-05) and is not captured in Fast Entry (BR-22).
**Business outcome:** Links the unit to the statutory quantity code needed for tax reporting (Inferred).

### Company Availability
**What it is:** The record of which companies can use a unit, and whether the unit is inactive in each of them.
**When it applies:** Created automatically for every registered company when a unit is first saved (BR-10).
**Business outcome:** Search, duplicate checks and the conversion target list all work on the units available to the company the user is logged into.

### Standard Conversion Factor
**What it is:** A rule stating that a "Unit Value" of this unit (the "Base Unit") corresponds to a "Conversion Value" of another unit (the target "Unit").
**When it applies:** Set up in the Standard Conversion Factor grid (BR-12, BR-13, BR-15). When the rule is saved, the system creates the reverse rule on the target unit (BR-21).
**Business outcome:** Allows quantities to be translated between units.

### Conversion Type
**What it is:** The kind of conversion rule, chosen as either "Fixed" or "Variable".
**When it applies:** Selected on each conversion row. Only rows that have a Conversion Type are checked and saved (BR-12).
**Business outcome:** Distinguishes between kinds of conversion. A likely reading is that Fixed means a constant ratio and Variable means a ratio that can change per transaction (Inferred).

### Material Subgroup Mapping
**What it is:** A link between the unit and a material subgroup, with a Unit Type role.
**When it applies:** Set up in the Material Subgroup grid (BR-14, BR-15).
**Business outcome:** Records which units apply to which material subgroups, and in what role.

### Unit Type
**What it is:** The role a unit plays for a subgroup, chosen from a central unit-type list. The values in that list are not defined on this screen; roles such as base, purchase or sales unit are likely (Inferred).
**When it applies:** Required on every subgroup row (BR-14).
**Business outcome:** Shows how the unit is meant to be used within each subgroup.

### Fast Entry Mode
**What it is:** A grid for creating many units at once, with Unit Name, Alias, Category and Remarks columns and an Import button.
**When it applies:** Opened by clicking the "Code" hyperlink on the detail card, whose tooltip reads "Switch to fast entry mode."
**Business outcome:** Speeds up bulk onboarding. Each row is validated and saved on its own, and its result is written in Remarks (BR-22).

## 4. Prerequisites and Dependencies
*This section identifies upstream operational requirements and downstream dependencies associated with the Unit Master screen.*

### Operating Company Structure
**What it is:** The organisational hierarchy in the ERP that defines the Head Office company and the operating companies.
**When it applies:** The list of registered companies is read when a new unit is saved (BR-10). The screen does not use the Head Office designation for any authority check (BR-01).
**Business outcome:** A new unit becomes available, and active, in every company registered at that moment, whichever company created it. A company registered later is not given existing units by this screen (Inferred).

### Unit Category List
**What it is:** The central list of unit categories.
**When it applies:** Must contain at least one entry before any unit can be saved (BR-04). The screen shows every category, with no status filter.
**Business outcome:** Supplies the mandatory dimensional classification.

### GST Unique Quantity Code List
**What it is:** The central list of statutory quantity codes, each shown with its code and name.
**When it applies:** Needed only when a GST UQC is assigned (BR-05).
**Business outcome:** Allows a statutory code to be linked to the unit.

### Unit Type List
**What it is:** The central list of unit-type roles.
**When it applies:** Needed when subgroup rows are entered (BR-14).
**Business outcome:** Supplies the roles that can be assigned in the Material Subgroup grid.

### Material Group and Subgroup Masters
**What it is:** The upstream screens where material groups and subgroups are defined and made available to companies.
**When it applies:** The Subgroup Name list shows the subgroups that are active in the current company, together with each subgroup's group name and code. It also shows any subgroups already mapped to the unit being edited.
**Business outcome:** Units can only be mapped to subgroups that exist.

### Excel Import Workbook
**What it is:** An Excel workbook with a sheet named after the screen's short code, MMUM, containing columns headed "Unit Name", "Alias" and "Category".
**When it applies:** Needed only when the Import button in Fast Entry is used (MSG-16).
**Business outcome:** Allows unit lists prepared offline to be loaded into Fast Entry.

### Downstream Item Master Reliance
**What it is:** Item definitions that refer to units and subgroups (Inferred).
**When it applies:** Whenever items are created or maintained. This screen contains no logic for them.
**Business outcome:** Items are expected to use the units, subgroup mappings and unit types maintained here (Inferred).

### Downstream Procurement, Inventory and Billing Reliance
**What it is:** Purchasing, stock and billing documents that record quantities (Inferred).
**When it applies:** Whenever these documents record or convert quantities.
**Business outcome:** They are expected to use the unit aliases and conversion factors maintained here (Inferred).

## 5. Form (Screen)
*This section details the interactive user interface areas, data entry fields, and action buttons of the Unit Master screen.*

### Standard Detail Card
**What it is:** The default single-record workspace of the "Unit Master" window, laid out as follows:
- a top panel holding Code, Alias, Unit Name, Category and Inactive
- the Standard Conversion Factor grid on the lower left and the Material Subgroup grid on the lower right
- a small panel below the grids holding GST UQC

**When it applies:** Displayed when the screen opens and on returning from Fast Entry mode.
**Business outcome:** Provides an organised layout for creating and reviewing individual units. Unit Name, Alias and Category are marked as mandatory.

### Code Field
**What it is:** A read-only display box next to a blue hyperlink labelled "Code" (BR-07).
**When it applies:** Always shown on the card. The hyperlink shows the tooltip "Switch to fast entry mode."
**Business outcome:**
- The box shows the system-assigned code of the loaded unit. It is blank for a new unit and never changes after the first save.
- Clicking the hyperlink starts a new blank record and opens Fast Entry across the whole window.

### Alias Field
**What it is:** Mandatory free text, up to 6 characters (BR-03, BR-06, BR-09).
**When it applies:** Shown on the card and as a column in Fast Entry. It is always editable.
**Business outcome:**
- Captures the short unit symbol, with spaces trimmed. It can be changed after the first save.
- Every change is copied immediately into the "Base Unit" column of the conversion grid (BR-20).
- A duplicate alias shows MSG-03 and a missing alias shows MSG-04. In both cases the cursor returns to this field.

### Unit Name Field
**What it is:** Mandatory free text, up to 25 characters (BR-02, BR-06, BR-08).
**When it applies:** Shown on the card and as a column in Fast Entry. The cursor is placed here on New and after each reset.
**Business outcome:** Captures the full unit name, with leading and trailing spaces removed. It can be changed after the first save. A missing name shows MSG-01 and a duplicate name shows MSG-02. In both cases the cursor returns to this field.

### Category Field
**What it is:** A mandatory selection list of category names (BR-04).
**When it applies:** Shown on the card and as a column in Fast Entry.
**Business outcome:** Links the unit to a dimensional family. It can be changed after the first save. If no valid category is selected, saving stops with MSG-05.

### Inactive Field
**What it is:** A checkbox labelled "Inactive" that is always disabled (BR-19).
**When it applies:** Shown on the card only.
**Business outcome:** Shows whether the loaded unit is inactive in the current company. It cannot be changed on this screen, and saving never changes it. New units are always active in every company (BR-10).

### GST UQC Field
**What it is:** An optional selection list labelled "GST UQC", showing each code and its name (BR-05).
**When it applies:** Shown on the card only, in the panel below the grids. It is not available in Fast Entry.
**Business outcome:** Saves the chosen statutory code with the unit. It can be changed or cleared later. If left blank, the unit is saved without a code and no warning appears.

### Standard Conversion Factor Grid
**What it is:** An editable grid of the unit's conversion rules.
**When it applies:** Always shown on the card. A new blank row is added automatically when the last row is edited.
**Business outcome:** The columns, in order, are:
- "Conversion Type": "Fixed" or "Variable"
- "Unit Value": a number with up to 3 decimals
- "Base Unit": read-only, showing the unit's alias (BR-20)
- "Conversion Value": a number with up to 3 decimals
- "Unit": the target unit, chosen from the units allowed under BR-13

The rules in BR-12, BR-15, BR-16 and BR-21 apply, and the grid's messages are MSG-06 to MSG-08 and MSG-10.

### Material Subgroup Grid
**What it is:** An editable grid of the unit's subgroup mappings.
**When it applies:** Always shown on the card. A new blank row is added automatically when the last row is edited.
**Business outcome:** The columns, in order, are:
- "Subgroup Name": chosen from a list showing subgroup name, group name and code
- "Subgroup Code": read-only, filled in automatically when a subgroup is chosen
- "Unit Type": chosen from the central list

The rules in BR-14, BR-15 and BR-16 apply, and the grid's messages are MSG-09 and MSG-11.

### Fast Entry Grid Container
**What it is:** A full-window workspace with the columns "Unit Name" (up to 25 characters), "Alias" (up to 6 characters), "Category" (a selection list of category names) and "Remarks" (read-only).
**When it applies:** Opened by clicking the "Code" hyperlink. A new blank record is started first.
**Business outcome:**
- A new row is added automatically while the user edits the last row.
- On Save, each row that has a Unit Name is validated and saved as a new unit, and its result goes in Remarks: MSG-17, or the validation message (BR-22).
- MSG-18 is shown at the end.

### Import Action
**What it is:** A button labelled "Import" at the top left of the Fast Entry workspace.
**When it applies:** Visible while Fast Entry mode is open.
**Business outcome:**
1. The user confirms MSG-16 and chooses a workbook.
2. The "Unit Name", "Alias" and "Category" columns are read from the sheet named MMUM.
3. These rows replace the current grid contents.

Nothing is saved until Save is clicked. A Category value that does not match a category name leaves the row without a category, so that row fails with MSG-05.

### Switch Back To Detail Action
**What it is:** A link labelled "Switch back to detail mode." at the top right of the Fast Entry workspace.
**When it applies:** Visible whenever Fast Entry mode is active.
**Business outcome:** Hides Fast Entry and shows the detail card again. Rows in the grid are not saved by this action, and the screen does not clear them.

### New Action
**What it is:** A standard toolbar option that starts a blank record.
**When it applies:** Clicked when the user wants to create a new unit.
**Business outcome:** Clears the card fields and both grids through the standard form reset, and places the cursor in Unit Name. Inactive stays unticked and the Code box stays blank until the first save.

### Save Action
**What it is:** The main toolbar option that checks and saves the record.
**When it applies:** Clicked after entering data in detail mode or Fast Entry mode.
**Business outcome:**
- **Detail mode:** The checks run in this order: BR-02, BR-08, BR-09, BR-03, BR-04, BR-12, BR-14. They stop at the first failure, show its message (MSG-01 to MSG-09) and place the cursor on the field or cell at fault. If all checks pass, the user confirms MSG-12. The header and all grid rows are then saved together (BR-16, BR-17, BR-18, BR-21), MSG-13 is shown and the card is cleared for a new record. A technical failure rolls everything back and shows MSG-20.
- **Fast Entry mode:** The user confirms MSG-12 first. Each row is then validated and saved as described under Fast Entry Grid Container (BR-22).

### Search Action
**What it is:** A toolbar option that opens the search dialog.
**When it applies:** Clicked when the user needs to find and open an existing unit.
**Business outcome:** Lists every unit available to the current company, including inactive ones, sorted by Unit Name. The columns are Code, Unit Name, Alias, Category Name, Inactive, Created By and Created Date. Choosing a unit loads its details and both grids. No fields are locked for any company or role (BR-01).

### Delete Action
**What it is:** A toolbar option that removes a record.
**When it applies:** Clicked when a saved unit is loaded. It does nothing for an unsaved record.
**Business outcome:** After the user confirms MSG-14, the unit and everything attached to it is removed (BR-11), MSG-15 is shown and the card is cleared. The screen runs no authority check and no usage check. If the database refuses the deletion, its reason is shown (MSG-19).

### Navigation Actions
**What it is:** Toolbar options for moving between records.
**When it applies:** Enabled on this screen's toolbar.
**Business outcome:** Moves to the first, previous, next or last unit. The order and exact behaviour come from the main application frame (Inferred).

### Other Toolbar Actions (Print, Preview, Export, Email)
**What it is:** The standard print, preview, export and email functions.
**When it applies:** Not offered. They are not among the toolbar options this screen enables.
**Business outcome:** Not supported here. They have no behaviour on this screen.

## 6. Data Layer (Business Information)
*This section describes the business information lifecycle and cross-entity relationships managed through the Unit Master screen.*

### Unit Header Record
**What it is:** The main master record. It holds:
- code, unit name, alias, category and GST UQC
- who created it and when
- who last modified it and when
- who authorised it and when
- its approval status

**When it applies:** Created and maintained on this screen by any user with access to it, from any company (BR-01).
**Business outcome:** Serves as the single authoritative definition of the unit.

### Company Availability Profile
**What it is:** One availability record per unit per company, holding the unit's Inactive status in that company.
**When it applies:** Created for every registered company when a new unit is first saved (BR-10). Later edits do not change these records.
**Business outcome:** The unit definition is shared, while the active or inactive status is tracked for each company. The status is shown here but not changed here (BR-19).

### Child Detail Profiles
**What it is:** The detail collections attached to the header: the standard conversion rules and the material subgroup mappings.
**When it applies:** Maintained in the child grids of the screen.
**Business outcome:** The conversion rules support quantity translation between units, in both directions (BR-21). The subgroup mappings record which units apply to each subgroup and in what role (BR-14).

### Record Creation Lifecycle
**What it is:** The stage where a new unit is added.
**When it applies:** When the mandatory fields are completed and Save is clicked, or for each Fast Entry row.
**Business outcome:** The steps are:
1. No authority check is made (BR-01).
2. The entries are validated (see Save Action).
3. The next code is assigned (BR-07).
4. The unit is marked as authorised by the saving user (BR-18).
5. Active availability records are created for every company (BR-10).
6. The conversion rules are saved together with their reverse rules (BR-21), and then the subgroup mappings.

All of this is saved as one unit of work (BR-17).

### Record Retrieval and Search Lifecycle
**What it is:** The stage where users search for and view existing units.
**When it applies:** Started from Search or the navigation options.
**Business outcome:** Shows the units available to the current company. A loaded record shows:
- the header fields
- the Inactive status for the current company
- every conversion rule held for the unit, including reverse rules created when other units were saved
- the subgroup mappings

Nothing is locked by company or role.

### Record Modification Lifecycle
**What it is:** The stage where an existing unit is updated.
**When it applies:** When fields are edited and Save is clicked.
**Business outcome:**
- Unit Name, Alias, Category and GST UQC are updated.
- The modifying user and time are recorded, and the unit is marked as authorised again (BR-18).
- All conversion rules involving the unit, in either direction, and all subgroup mappings are deleted and rebuilt from the grids (BR-16). This changes the matching reverse rules shown on other units.
- The code and the company availability records stay as they were.

### Record Retirement and Deletion Lifecycle
**What it is:** The stage where a unit is deactivated or removed.
**When it applies:** When Delete is confirmed. Deactivation is not possible on this screen (BR-19).
**Business outcome:**
- The screen runs no authority or usage check.
- The following are removed together (BR-11):
  - the unit's conversion rules in both directions, including rules shown on other units
  - its subgroup mappings
  - its company availability records
  - the header
- If the database refuses the removal, nothing is removed and the reason is shown (MSG-19).

### Transactional Safety
**What it is:** Grouping the related changes of one action into a single all-or-nothing unit.
**When it applies:** During save and delete.
**Business outcome:** The header, conversion rules (with their reverse rules) and subgroup mappings are saved together. If any row fails, the whole save is rolled back and MSG-20 is shown. A delete is likewise completed in full or not at all (BR-17).

## 7. Child Entities and Associated Controls
*This section details secondary collections, embedded controls, or specialised configuration grids associated with the Unit Master screen.*

### Standard Conversion Factor Structure
**What it is:** The unit's conversion rules. Each row holds a Conversion Type, a Unit Value, a Conversion Value and a target Unit.
**When it applies:** Configured in the lower-left grid of the detail card. It is always visible.
**Business outcome:** Each saved row also creates the reverse rule on the target unit, with the two values swapped and the same Conversion Type (BR-21). Because of this, both units show the relationship. BR-12, BR-13, BR-15 and BR-16 apply.

### Material Subgroup Structure
**What it is:** The unit's subgroup mappings. Each row holds a subgroup, its code (shown automatically) and a Unit Type.
**When it applies:** Configured in the lower-right grid of the detail card. It is always visible.
**Business outcome:** Records which units apply to each subgroup and in what role. BR-14, BR-15 and BR-16 apply.

### Embedded Controls
**What it is:** Not applicable for this screen — the screen has no embedded shared controls; its only detail collections are the two grids above.
**When it applies:** Not applicable for this screen.
**Business outcome:** Not applicable for this screen.

### Operational Limits on Child Rows
**What it is:** The value rules for child rows:
- **Conversion rows:** non-zero Unit Value, non-zero Conversion Value and a selected target Unit
- **Subgroup rows:** a selected Unit Type
- **Both grids:** no repeated target unit and no repeated subgroup

**When it applies:** The completeness checks run when Save is clicked, and only on rows that have a Conversion Type or a subgroup. Rows without one are ignored. The duplicate checks are applied by the grids themselves.
**Business outcome:**
- BR-12 applies to conversion rows (MSG-06, MSG-07, MSG-08).
- BR-14 applies to subgroup rows (MSG-09).
- BR-15 prevents duplicates (MSG-10, MSG-11).
- Values are held to three decimal places. The screen does not check that they are positive.

### Interface Visibility and Layout Status
**What it is:** The display state of each child grid, tab or embedded control on the screen.
**When it applies:** During normal use of the screen.
**Business outcome:** Both grids are always visible and editable on the detail card, and both are saved with the header. Neither is available in Fast Entry, so units created there have no conversion rules or subgroup mappings until they are edited on the card (BR-22). No component is hidden.

## 8. Business Operations (Stored Procedures)
*This section details the discrete business operations performed by the Unit Master screen.*

### Load Selection Lists Operation
**What it is:** Loads the selection lists and prepares the empty grid layouts. The lists are:
- all unit categories
- the conversion types "Fixed" and "Variable"
- the conversion target units (BR-13)
- the material subgroups that are active in the current company, plus those already mapped to the unit
- all unit types
- all GST quantity codes

**When it applies:** When the screen is first used, and each time a record is loaded.
**Business outcome:** Fills the selection lists and sets up the conversion, subgroup and Fast Entry grids. The duplicate checks and the 3-decimal number format are set up at the same time. If a technical failure occurs while loading, it is recorded in the system error log under the screen's code.

### Dependent Values and Code Assignment Operation
**What it is:** Works out the values that fill in automatically, and assigns the next code.
**When it applies:**
- The code is assigned when a new unit is first saved.
- "Base Unit" is refreshed whenever the Alias changes.
- "Subgroup Code" is refreshed whenever a subgroup is chosen.

**Business outcome:** The code is "UM" followed by the next four-digit running number (BR-07). "Base Unit" mirrors the Alias (BR-20). "Subgroup Code" shows the chosen subgroup's code.

### Search Records Operation
**What it is:** Finds units that match the search criteria.
**When it applies:** When the user searches in the search dialog.
**Business outcome:** Covers the units available to the current company, including inactive ones, sorted by Unit Name. It shows Code, Unit Name, Alias, Category Name, Inactive, Created By and Created Date.

### Load Record Details Operation
**What it is:** Opens the full record and its child rows.
**When it applies:** When a record is chosen from the search results or by navigation.
**Business outcome:** Fills in the header fields, the Inactive status for the current company, the conversion rows and the subgroup rows. Nothing is locked (BR-01).

### Validate Record Operation
**What it is:** Checks the record for completeness, format and uniqueness before saving.
**When it applies:** When Save is clicked, in detail or Fast Entry mode.
**Business outcome:** The checks run in this order and stop at the first failure:

| Order | Check | Rule | Message | Focus on failure |
|---|---|---|---|---|
| 1 | Unit Name present | BR-02 | MSG-01 | Unit Name |
| 2 | Unit Name not already used by another unit available to the current company | BR-08 | MSG-02 | Unit Name |
| 3 | Alias not already used by another unit available to the current company | BR-09 | MSG-03 | Alias |
| 4 | Alias present | BR-03 | MSG-04 | Alias |
| 5 | Valid Category selected | BR-04 | MSG-05 | Category |
| 6 | Conversion rows complete | BR-12 | MSG-06, MSG-07, MSG-08 | The cell at fault |
| 7 | Subgroup rows have a Unit Type | BR-14 | MSG-09 | The cell at fault |

In Fast Entry, failures from checks 1 to 5 are written in the row's Remarks instead of being shown.

### Save Main Record Operation
**What it is:** Saves the header record and sets up company links.
**When it applies:** After validation passes during Save.
**Business outcome:**
- **New unit:** assigns the code (BR-07), records the creator, marks the unit as authorised (BR-18) and creates active availability records for every company (BR-10).
- **Existing unit:** updates the header, records the modifier, marks the unit as authorised again and clears all its conversion rules (both directions) and subgroup mappings, ready for them to be rebuilt (BR-16).

The confirmation message (MSG-13) is shown after the child rows are also saved.

### Save Child Details Operation
**What it is:** Saves the child rows as part of the same save.
**When it applies:** During Save when child data is present. Conversion rows without a Conversion Type and subgroup rows without a subgroup are skipped.
**Business outcome:**
- Each conversion row is saved together with its reverse rule on the target unit (BR-21).
- Each subgroup row is saved with its Unit Type.
- The rows replace the unit's previous rows in full (BR-16).
- A failure on any row rolls back the whole save, including the header, and shows MSG-20 (BR-17).

### Delete Record Operation
**What it is:** Removes the unit and its child details.
**When it applies:** After the delete prompt is confirmed.
**Business outcome:** No authority or usage check is run. The operation removes, in one unit of work (BR-11, BR-17):
- conversion rules in both directions
- subgroup mappings
- company availability records
- the header

On success MSG-15 is shown. If the database refuses, its reason is shown (MSG-19).

## 9. Modular Architecture Notes
*This section highlights business-relevant architectural principles governing the Unit Master screen.*

### Modular Business Architecture
**What it is:** The separation between the screen, the business logic and the stored data.
**When it applies:** For every action taken on the Unit Master screen.
**Business outcome:** Fast Entry and Excel import place each row's values on the detail card and run the same validation and save routine as a manual save. The same rules (BR-02 to BR-04 and BR-06 to BR-10) therefore apply whichever way a unit is created.

### Enterprise Standardisation and Component Reuse
**What it is:** The screen reuses shared central lists (unit categories, GST quantity codes and unit types) and the shared material group and subgroup masters. It also uses the standard search dialog, toolbar and confirmation messages.
**When it applies:** During unit creation, conversion setup, subgroup mapping, search and save.
**Business outcome:** All modules work from the same reference definitions and behave the same way (Inferred for modules beyond this screen).

### Centralised Transactional Safety
**What it is:** The all-or-nothing handling of multi-record changes.
**When it applies:** During save and delete.
**Business outcome:** The unit header, company availability records, conversion rules (including reverse rules on other units) and subgroup mappings are always committed or rolled back together (BR-17).

## 10. Use Cases
*This section outlines standard operational scenarios executed on the Unit Master screen.*

### Single Unit Creation
**Actor:** Master Data Clerk
**Flow:**
1. Click New.
2. Enter the Alias (BR-03), the Unit Name (BR-02) and the Category (BR-04).
3. Optionally choose a GST UQC (BR-05).
4. Optionally add conversion and subgroup rows.
5. Click Save and confirm MSG-12.

**Result:** The unit receives its code (BR-07), is marked as authorised (BR-18) and is made available in every company (BR-10). MSG-13 is shown and the card is cleared. If a check fails, the matching message (MSG-01 to MSG-09) is shown and the cursor is placed on the field or cell at fault.

### Bulk Entry Through Fast Entry
**Actor:** Master Data Clerk
**Flow:**
1. Click the "Code" hyperlink to open Fast Entry.
2. Either type rows with Unit Name, Alias and Category, or click Import, confirm MSG-16 and choose a workbook with a sheet named MMUM that has "Unit Name", "Alias" and "Category" columns. Imported rows replace the grid contents.
3. Click Save and confirm MSG-12.

**Result:** Each row with a Unit Name is validated and saved as a new unit. Its Remarks shows MSG-17 or the validation message (for example MSG-02 or MSG-04), and MSG-18 is shown at the end. Rows that fail stay in the grid for correction. These units have no GST UQC, conversion rules or subgroup mappings (BR-22). An imported Category value that does not match a category name leaves the row with no category, and that row fails with MSG-05.

### Maintain Standard Conversion Factor
**Actor:** Master Data Specialist
**Flow:**
1. Load a unit.
2. In the Standard Conversion Factor grid, add, change or remove rows. Each row needs a Conversion Type ("Fixed" or "Variable"), a Unit Value, a Conversion Value and a target Unit.
3. Click Save.

**Result:** The unit's conversion rules are replaced by the rows in the grid (BR-16), and their reverse rules on the target units are rebuilt (BR-21). MSG-13 is shown. An incomplete row stops the save with MSG-06, MSG-07 or MSG-08 (BR-12). A repeated target unit is flagged with MSG-10 (BR-15).

### Maintain Material Subgroup
**Actor:** Inventory Master Specialist
**Flow:**
1. Load a unit.
2. In the Material Subgroup grid, add, change or remove rows by choosing a Subgroup Name (the Subgroup Code fills in) and a Unit Type.
3. Click Save.

**Result:** The unit's subgroup mappings are replaced by the rows in the grid (BR-16), and MSG-13 is shown. A row without a Unit Type stops the save with MSG-09 (BR-14). A repeated subgroup is flagged with MSG-11 (BR-15).

### Search and Modify Unit
**Actor:** Master Data Clerk (any company; the screen does not distinguish Head Office from branch users)
**Flow:**
1. Click Search.
2. Choose a unit from the current company's list.
3. Change the name, alias, category, GST UQC, conversion rows or subgroup rows.
4. Click Save and confirm MSG-12.

**Result:** The changes are saved, the unit is marked as authorised again (BR-18) and MSG-13 is shown. The same outcome applies to every user and company, because no fields are locked (BR-01). Only the Inactive box stays read-only (BR-19).

### Unit Deletion
**Actor:** Master Data Clerk
**Flow:** Load a unit, click Delete and confirm MSG-14.
**Result:** The unit is removed together with its conversion rules in both directions, its subgroup mappings and its company availability records (BR-11), and MSG-15 is shown. If the database refuses the deletion, for example because the unit is used elsewhere (Inferred), the reason is shown (MSG-19) and nothing is removed.

### Duplicate Prevention Handling
**Actor:** Data Entry Operator
**Flow:** Try to save a Unit Name or Alias that is already used by another unit available to the current company.
**Result:**
- On the detail card: MSG-02 is shown with the cursor in Unit Name (BR-08), or MSG-03 with the cursor in Alias (BR-09).
- In Fast Entry: the same message is written in the row's Remarks.

## 11. Business Rules
*This section establishes the authoritative business rules governing the Unit Master screen.*

- **BR-01 (No Head Office or Role Restriction):** The screen applies no Head Office, branch or role check. Any user who can open it can create, change and delete units, and nothing is locked by company.
- **BR-02 (Mandatory Unit Name):** Unit Name is mandatory. If it is blank, the save stops (MSG-01).
- **BR-03 (Mandatory Alias):** Alias is mandatory. If it is blank, the save stops (MSG-04).
- **BR-04 (Mandatory Category):** A valid Category must be selected from the list. Otherwise the save stops (MSG-05).
- **BR-05 (Optional GST UQC):** GST UQC may be left blank. It can only be set on the detail card.
- **BR-06 (Length Limits and Trimming):** Unit Name allows up to 25 characters and Alias up to 6. Leading and trailing spaces are removed from both before they are checked and saved.
- **BR-07 (System-Generated Code):** The Code is assigned on first save as "UM" followed by the next four-digit running number. It is read-only and never changes.
- **BR-08 (Unit Name Uniqueness):** No other unit available to the current company may have the same Unit Name (MSG-02).
- **BR-09 (Alias Uniqueness):** No other unit available to the current company may have the same Alias (MSG-03).
- **BR-10 (Company Availability):** When a new unit is first saved, it is made available, and active, in every company registered at that moment, whichever company the user is logged into. Later edits do not change company availability.
- **BR-11 (Deletion Scope):** Deleting a unit also removes:
  - every conversion rule where the unit is the base or the target
  - its subgroup mappings
  - its company availability records

  The screen does not check whether the unit is in use. Only the database can refuse the deletion (MSG-19).
- **BR-12 (Complete Conversion Rows):** A conversion row that has a Conversion Type must have a non-zero Unit Value (MSG-06), a non-zero Conversion Value (MSG-07) and a target Unit (MSG-08). Rows without a Conversion Type are ignored. Values are held to three decimal places.
- **BR-13 (Valid Conversion Targets):** A unit cannot be its own conversion target. The target list shows the current company's active units, plus any units already linked to the unit being edited.
- **BR-14 (Subgroup Requires Unit Type):** A subgroup row must have a Unit Type (MSG-09). Rows without a subgroup are ignored.
- **BR-15 (No Duplicate Child Rows):** A target unit may appear only once in the conversion grid (MSG-10), and a subgroup only once in the subgroup grid (MSG-11).
- **BR-16 (Full Replacement of Child Rows):** Saving an existing unit deletes all its conversion rules (in both directions) and subgroup mappings, and rebuilds them from the grids.
- **BR-17 (Atomic Save and Delete):** The header and all child rows are saved together or rolled back together. The same applies to a delete.
- **BR-18 (Automatic Authorisation):** Every save, whether of a new or an existing unit, marks the unit as authorised by the saving user at the time of saving. There is no separate approval step.
- **BR-19 (View-Only Inactive):** The Inactive checkbox is always disabled. It shows the status in the current company, and saving never changes it.
- **BR-20 (Base Unit Mirrors Alias):** The "Base Unit" column of the conversion grid always shows the current Alias and cannot be edited.
- **BR-21 (Automatic Reverse Conversion):** Each saved conversion rule from this unit to a target unit also creates the reverse rule on the target unit, with Unit Value and Conversion Value swapped and the same Conversion Type. Changing or deleting the rule from either unit changes or removes it on both.
- **BR-22 (Fast Entry Scope):** Fast Entry and Excel import only create new units, and only capture Unit Name, Alias and Category. Rows with a blank Unit Name are skipped. Each row is checked against BR-02, BR-08, BR-09, BR-03 and BR-04, and its outcome is written in Remarks.

## 12. Messages
*This section catalogues all user-facing notifications, validation prompts, and error messages generated by the Unit Master screen.*

- **MSG-01:** Unit Name is blank; *"Enter Unit Name."*; type a unit name (BR-02).
- **MSG-02:** Unit Name is already used; *"Duplicate Unit Name is not allowed."*; enter a different name (BR-08).
- **MSG-03:** Alias is already used; *"Duplicate Alias is not allowed."*; enter a different alias (BR-09).
- **MSG-04:** Alias is blank; *"Enter Alias."*; type an alias of up to 6 characters (BR-03).
- **MSG-05:** Category is missing or invalid; *"Select valid Category Name."*; choose a category from the list (BR-04).
- **MSG-06:** A conversion row has no Unit Value; *"Enter Unit Value in row \<n\>."*; enter a non-zero Unit Value in that row (BR-12).
- **MSG-07:** A conversion row has no Conversion Value; *"Enter Conversion Value in row \<n\>."*; enter a non-zero Conversion Value in that row (BR-12).
- **MSG-08:** A conversion row has no target Unit; *"Enter Unit in row \<n\>."*; choose the target Unit in that row (BR-12).
- **MSG-09:** A subgroup row has no Unit Type; *"Select valid Unit Type in row \<n\>."*; choose a Unit Type in that row (BR-14).
- **MSG-10:** The same target unit appears twice in the conversion grid; *"Duplicate Unit is not allowed."*; remove or change the repeated unit (BR-15).
- **MSG-11:** The same subgroup appears twice in the subgroup grid; *"Duplicate Subgroup Name is not allowed."*; remove or change the repeated subgroup (BR-15).
- **MSG-12:** Save confirmation prompt; standard application message, wording not in this screen's source; confirm to save, or cancel.
- **MSG-13:** Save succeeded; standard application message, wording not in this screen's source; acknowledge it. The card is then cleared.
- **MSG-14:** Delete confirmation prompt; standard application message, wording not in this screen's source; confirm to delete, or cancel.
- **MSG-15:** Delete succeeded; standard application message, wording not in this screen's source; acknowledge it. The card is then cleared.
- **MSG-16:** Import confirmation in Fast Entry; *"Your excel should consists of sheet with name MMUM. Do you want to continue?"*; continue only if the workbook has a sheet with that name.
- **MSG-17:** A Fast Entry row was saved, shown in its Remarks; *"Successfully Created."*; no action needed (BR-22).
- **MSG-18:** Fast Entry save finished; *"Refer remarks for saved status."*; check each row's Remarks and correct the rows that failed (BR-22).
- **MSG-19:** The database refused a deletion; standard application message showing the reason returned by the database, wording not in this screen's source; review the reason, then keep the unit or first remove whatever depends on it (BR-11).
- **MSG-20:** Save failed with a technical error; standard application message showing the system error text, wording not in this screen's source; correct the cause and save again. Nothing was saved (BR-17).

## 13. Limitations and Assumptions
*This section identifies functional constraints and operational assumptions governing the Unit Master screen.*

### Name and Alias Length Limits
**What it is:** Unit Name is limited to 25 characters and Alias to 6, both on the card and in Fast Entry (BR-06).
**When it applies:** Unit creation and editing.
**Business outcome:** Keeps names and aliases short. Values loaded through Excel import are not length-checked on screen, and longer values may be cut to these limits when saved (Inferred; possible defect).

### Company-Scoped Uniqueness
**What it is:** Duplicate checks, search and target lists only consider units available to the current company (BR-08, BR-09).
**When it applies:** Unit creation, editing and lookup.
**Business outcome:** In practice this works across the enterprise, because each new unit reaches every company (BR-10). A company registered after a unit was created would not see that unit, and could create a duplicate of it (Inferred).

### No Head Office or Role Restriction
**What it is:** The screen does not limit creating, changing or deleting units to Head Office or to particular roles (BR-01).
**When it applies:** All maintenance actions.
**Business outcome:** Any user with access can change units for the whole enterprise. Access is assumed to be controlled by the application's menu security (Inferred).

### No Inactivation on This Screen
**What it is:** The Inactive checkbox is view-only (BR-19).
**When it applies:** When a unit needs to be retired in one or all companies.
**Business outcome:** Retiring a unit must be done outside this screen.

### No Usage Check Before Deletion
**What it is:** Delete removes the unit and its links without checking whether items or transactions use it (BR-11).
**When it applies:** Unit deletion.
**Business outcome:** Protection against deleting a unit that is in use depends on the database's own integrity rules (Inferred; possible defect).

### Fast Entry Captures Header Fields Only
**What it is:** Fast Entry and import only save Unit Name, Alias and Category (BR-22).
**When it applies:** Bulk creation.
**Business outcome:** GST UQC, conversion rules and subgroup mappings must be added afterwards on the detail card.

### Fast Entry Remarks After a Database Failure
**What it is:** When a Fast Entry row passes validation but the database save fails, the error message (MSG-20) is shown, yet the row's Remarks can still read "Successfully Created." (MSG-17).
**When it applies:** Bulk creation.
**Business outcome:** After any error message during a Fast Entry save, users should use Search to confirm the units were actually created (possible defect).

### Conversion Value Range
**What it is:** The grid accepts numbers up to 11 characters long with 3 decimals, but stored values are limited to 99,999.999 (Inferred from the stored precision).
**When it applies:** Entering large conversion ratios.
**Business outcome:** Very large values may fail to save (MSG-20) (possible defect).

### Reverse Rules Shared Between Units
**What it is:** A rule saved on one unit appears on the target unit's grid (BR-21). Saving either unit rebuilds the rules in both directions (BR-16).
**When it applies:** Editing conversions from either side.
**Business outcome:** Changing or removing a rule on one unit also changes or removes it on the other.

## 14. Open Questions
*This section records unresolved business and functional items requiring formal confirmation from the business owner.*

1. **Meaning of Conversion Types:** The screen offers "Fixed" and "Variable" conversions without defining them. What is the business difference, and how do transaction screens use each one (Inferred reading: constant versus per-transaction ratio)? Suggested Business Owner: Enterprise Supply Chain Engineering Lead.
2. **Unit Type Values and Exclusivity:** Which roles are in the unit-type list (for example base, purchase or sales unit, Inferred)? Should a subgroup be limited to one unit per role? Suggested Business Owner: Corporate Inventory Master Director.
3. **Head Office Authority:** Should creating, changing and deleting units be limited to Head Office users, with branch companies given view-only access? The screen does not enforce this today (BR-01). Suggested Business Owner: Enterprise Master Data Governance Lead.
4. **Inactivation Capability:** Should authorised users be able to set the Inactive status on this screen, for each company or for all companies (BR-19)? Suggested Business Owner: Enterprise Master Data Governance Lead.
5. **Usage Check on Deletion:** Should the screen itself block deletion of a unit used by items, bills of materials or transactions, with a clear message, rather than relying on the database (BR-11)? This may be a defect. Suggested Business Owner: Enterprise Master Data Governance Lead.
6. **Mandatory GST UQC:** Should a GST UQC be required for every unit, including units created through Fast Entry or import, to meet statutory reporting (BR-05)? Suggested Business Owner: Finance and Tax Compliance Lead.
7. **Positive Values Only:** Should negative Unit Values and Conversion Values be explicitly rejected? Today only zero is rejected (BR-12). Suggested Business Owner: Enterprise Supply Chain Engineering Lead.
8. **Companies Added Later:** Should existing units be made available automatically when a new company is registered (BR-10)? Without this, the new company would not see older units and could create duplicates (Inferred). Suggested Business Owner: Enterprise Master Data Governance Lead.
9. **Fast Entry Result Accuracy:** When a Fast Entry row fails to save in the database, its Remarks can still read "Successfully Created." Should the actual failure reason be written instead? This is a possible defect. Suggested Business Owner: Master Data Operations Lead.
10. **Conversion Value Range:** The grid accepts values larger than can be stored, and such values may fail to save. Should the grid limit entries to the storable range? This is a possible defect. Suggested Business Owner: Enterprise Supply Chain Engineering Lead.
11. **Import Length Checks:** Should Excel import reject Unit Names longer than 25 characters and Aliases longer than 6, rather than risk them being cut when saved (Inferred)? This is a possible defect. Suggested Business Owner: Master Data Operations Lead.
12. **Uniqueness Scope:** Unit Name and Alias are only checked against units available to the current company. Should they be checked across all units in the enterprise (BR-08, BR-09)? Suggested Business Owner: Enterprise Master Data Governance Lead.
13. **Unsaved Fast Entry Rows:** Switching back to detail mode neither saves nor explicitly clears the Fast Entry rows. Should users be warned about unsaved rows before they leave Fast Entry? Suggested Business Owner: Master Data Operations Lead.
14. **Downstream Use of Units:** Confirm which item, purchasing, stock and billing processes use the unit alias, the conversion factors and the subgroup mappings maintained here (Inferred). Suggested Business Owner: Production and Inventory Operations Lead.
15. **Inactive Status Cascade to Linked Items:** When a unit is inactive in a company, should transactions for items that use it as their stocking unit be blocked automatically? Suggested Business Owner: Production and Inventory Operations Lead.
