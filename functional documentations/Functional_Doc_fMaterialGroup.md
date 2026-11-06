# Material Group Screen: Functional Documentation

## 1. Summary
*This section provides an executive overview of the Material Group screen and its role in Materials Management.*

The Material Group screen maintains material groups, the second level of the Category > Group > Sub-Group > Item classification used for materials across the enterprise. It gives each family of materials a controlled place in the hierarchy: one parent Material Category, a two-character Code that is unique within that category, and a composite Group Code that becomes part of every item's full code. Head Office master data staff can create, search, modify, navigate and delete groups, either one at a time on a detail card or in bulk through a Fast Entry grid that can be filled from an Excel sheet. New groups are made available automatically to every operating company, and changing a group realigns the full codes of all items beneath it. Branch company users can only view groups, while purchasing, inventory, quality and reporting teams rely on the consistent classification and item numbering the screen produces (Inferred).

## 2. Purpose and Scope
*This section outlines the business rationale for the Material Group screen and establishes its operational boundaries within the enterprise.*

### Business Purpose of Material Groups
**What it is:** The screen defines the group tier of the material classification hierarchy, beneath Material Categories and above Material Sub-Groups.
**When it applies:** Whenever the enterprise introduces a new family of materials within an existing category, or renames, recodes or moves an existing family.
**Business outcome:** Provides a coded classification that drives structured item numbering (BR-07, BR-18) and prevents duplicate or ambiguous group definitions (BR-08, BR-09).

### In-Scope Functional Capabilities
**What it is:** The functional scope covered directly by the Material Group screen.
**When it applies:** Single-group creation, bulk Fast Entry, Excel import into Fast Entry, searching, navigation, modification and deletion.
**Business outcome:**
- Users maintain the parent category, the two-character Code with automatic next-code suggestion, and the Group Name.
- Company availability is created automatically for every operating company.
- Quality parameter links that already exist on a group are carried through on save. The QC control is hidden on this screen (see Section 7).

### Out-of-Scope Capabilities
**What it is:** Business activities related to material groups that are excluded from the Material Group screen.
**When it applies:** When users need any of the following:
- define Material Categories, Material Sub-Groups, items, QC parameters or QC Group templates;
- maintain a group's quality parameters through a visible grid;
- retire a group for one specific company.
**Business outcome:** These needs are handled in their own master screens or utilities (Inferred). On this screen, the QC control is hidden and the Inactive indicator is view-only (BR-16).

## 3. Business Glossary
*This section defines standard business terminology used on and around the Material Group screen.*

### Material Group
**What it is:** A named family of materials within a single Material Category.
**When it applies:** Created and maintained on this screen at Head Office (BR-01).
**Business outcome:** Acts as the parent of Material Sub-Groups and, through them, of items (shown by the item code realignment in BR-18).

### Material Category
**What it is:** The top-level classification to which every material group belongs. Each category has its own short Category Code.
**When it applies:** Selected as the mandatory parent of each group (BR-02).
**Business outcome:** Places the group in the hierarchy and supplies the first part of the composite Group Code (BR-07).

### Code
**What it is:** The two-character code that identifies a group within its category.
**When it applies:** Suggested automatically when a category is chosen (BR-06). It must be exactly two characters (BR-04) and unique within the category (BR-09).
**Business outcome:** Gives a compact identifier that feeds the composite Group Code and item full codes.

### Group Code
**What it is:** The read-only composite code, made up of the Category Code followed by the Code.
**When it applies:** Refreshed whenever the category or the Code changes (BR-07).
**Business outcome:** Shows users the code under which the group appears in item numbering.

### Item Full Code
**What it is:** The complete item code: Category Code + group Code + Sub-Group code + item code.
**When it applies:** Recalculated for all affected items whenever an existing group is saved (BR-18).
**Business outcome:** Keeps item numbering in line with the classification after a group is recoded or moved to another category.

### Company Availability
**What it is:** The link that makes a group usable in each operating company, with a separate active or inactive status per company.
**When it applies:** Created for every registered company when a new group is saved (BR-10).
**Business outcome:** One definition is maintained centrally and shared by all companies.

### QC Parameter
**What it is:** A quality characteristic, such as moisture or purity (Inferred examples). Each parameter has a unit, a standard value, a tolerance and deduction settings.
**When it applies:** Can be linked to a group through the embedded Quality Control Parameters control (Section 7).
**Business outcome:** Records the group's quality standards and the deductions that apply when material falls outside tolerance (Inferred).

### QC Group Template
**What it is:** A predefined, authorised set of QC parameters that can fill the group's parameter list in one step.
**When it applies:** Available within the Quality Control Parameters control (BR-15).
**Business outcome:** Allows a standard parameter set to be applied consistently.

### Fast Entry Mode
**What it is:** A grid workspace for creating many groups in one session, by keying rows in or importing them from Excel.
**When it applies:** Opened by clicking the Group Code hyperlink on the detail card.
**Business outcome:** Speeds up bulk set-up. Each row is checked and saved separately, and its outcome is recorded in Remarks (BR-19).

## 4. Prerequisites and Dependencies
*This section identifies upstream operational requirements and downstream dependencies associated with the Material Group screen.*

### Operating Company Structure
**What it is:** The organisational hierarchy in the ERP that defines the Head Office company and the operating companies.
**When it applies:** Required before the screen is opened. It drives the authority rule (BR-01) and the availability rule (BR-10).
**Business outcome:** Only Head Office users can edit groups, and new groups become available to every registered company.

### Material Category Master
**What it is:** Material Categories, each with a name and a Category Code.
**When it applies:** At least one category active for the current company must exist before a group can be created (BR-02).
**Business outcome:** Supplies the mandatory parent and the first segment of the composite Group Code.

### Quality Control Masters
**What it is:** The QC masters used by the embedded control:
- QC parameters registered for the company;
- QC Group templates that are authorised and active;
- units that are authorised and active;
- active tolerance types;
- the enterprise setting that hides QC deduction details.
**When it applies:** Loaded into the embedded Quality Control Parameters control each time the screen opens (BR-15).
**Business outcome:** Supplies the parameter catalogue, the defaults and the deduction options.

### Downstream Material Sub-Group and Item Reliance
**What it is:** The Material Sub-Groups classified under the group, and the items classified under those sub-groups.
**When it applies:** When a group is modified (BR-18) or deleted (BR-11).
**Business outcome:** Modifying a group realigns item full codes. Deleting a group that is still in use is expected to be refused by the database (Inferred).

### Downstream Quality Inspection Reliance
**What it is:** Quality checks on received or produced material that draw on group-level QC standards (Inferred).
**When it applies:** When material of the group is inspected (Inferred).
**Business outcome:** The same tolerances and deductions are applied to all material in the group (Inferred).

## 5. Form (Screen)
*This section details the interactive user interface areas, data entry fields, and action buttons of the Material Group screen.*

### Standard Detail Card
**What it is:** The default single-record workspace containing the Group Code display, the Category Name selection list, the Category Code and Code fields, Group Name and the Inactive checkbox.
**When it applies:** Displayed when the screen opens, or on returning from Fast Entry mode.
**Business outcome:** Provides an organised layout for creating and reviewing individual material groups. Category Name, Code and Group Name are marked as mandatory.

### Group Code Field
**What it is:** A hyperlink labelled Group Code, with the tooltip "Switch to fast entry mode.", next to a read-only display (BR-07).
**When it applies:** Always shown at the top of the card. The display can never be edited.
**Business outcome:**
- Shows the Category Code followed by the Code, and refreshes as soon as either one changes.
- Clicking the hyperlink starts a new record and opens Fast Entry mode.

### Category Name Field
**What it is:** A mandatory selection list of Material Categories, showing each category's name and code (BR-02).
**When it applies:** Shown on the card and as a column in Fast Entry. It receives the cursor when the screen opens or is reset. It is locked for branch users (BR-01).
**Business outcome:**
- Choosing a category fills Category Code, suggests the next Code (BR-06) and refreshes the Group Code.
- The category can be changed on an existing group, which triggers BR-18.
- If no valid category is selected, saving is blocked with MSG-01.

### Category Code Field
**What it is:** A read-only display of the selected category's code.
**When it applies:** Filled automatically when a category is chosen and cleared when the category is cleared. It is never editable.
**Business outcome:** Shows the first segment of the composite Group Code.

### Code Field
**What it is:** A mandatory text entry of exactly two characters. The field does not accept more than two (BR-04).
**When it applies:** Shown on the card and as a column in Fast Entry. It is filled automatically when a category is chosen (BR-06), and the user may overwrite it. It is locked for branch users (BR-01).
**Business outcome:**
- Captures the group's code within its category and can be changed after the first save, which triggers BR-18.
- Saving is blocked if the length is not exactly two characters (MSG-02) or if the code already exists in the category (MSG-04, BR-09).

### Group Name Field
**What it is:** A mandatory free-text entry of up to 100 characters. Leading and trailing spaces are removed (BR-03, BR-05).
**When it applies:** Shown on the card and as a column in Fast Entry. It is locked for branch users (BR-01).
**Business outcome:**
- Captures the group's business name and can be changed after the first save.
- Saving is blocked if the name is blank (MSG-05) or already used in the same category for the current company (MSG-03, BR-08).

### Inactive Field
**What it is:** A checkbox labelled Inactive (BR-16).
**When it applies:** Always shown and always disabled.
**Business outcome:**
- Shows the stored inactive status when a group is loaded.
- Users cannot change it here.
- New groups are always created as active (BR-10).

### Quality Control Parameters Grid
**What it is:** The embedded Quality Control Parameters control, which holds a QC Group Name selection list and a parameter grid.
**When it applies:** Part of the form but hidden: it is set to not visible and placed outside the visible area of the screen.
**Business outcome:** Users never see it, but it still loads, checks and re-saves the group's existing QC parameter links. Its columns and rules are described in Section 7 (BR-12 to BR-15).

### Fast Entry Grid Container
**What it is:** A full-screen grid workspace with the following columns:
- Category Name (a selection list of categories);
- Code (at most two characters);
- Group Name;
- Remarks (read-only).
**When it applies:** Opened by clicking the Group Code hyperlink, which first clears the detail card.
**Business outcome:**
- A new blank row is added automatically when the user edits the last row.
- On Save, the result of each row is written to its Remarks (BR-19, MSG-19).

### Import Action
**What it is:** A button labelled Import at the top left of the Fast Entry container.
**When it applies:** Available whenever Fast Entry mode is active.
**Business outcome:**
- Asks for confirmation (MSG-18), then lets the user choose an Excel workbook.
- Loads the required sheet's Category Name, Code and Group Name columns into the grid, with an empty Remarks column (BR-20).
- Nothing is saved until the user clicks Save.

### Switch Back To Detail Action
**What it is:** A link labelled "Switch back to detail mode." at the top right of the Fast Entry container.
**When it applies:** Visible whenever Fast Entry mode is active.
**Business outcome:** Hides the Fast Entry container and shows the detail card again. The action does not save the grid's unsaved rows.

### New Action
**What it is:** A standard toolbar option that starts a blank record.
**When it applies:** Clicked when the user wants to create a new material group. It also runs automatically after a successful save or delete, and when Fast Entry is opened.
**Business outcome:**
- All card fields are cleared and the Inactive checkbox is disabled.
- For branch users, every field is locked (BR-01).
- The cursor is placed in Category Name.

### Save Action
**What it is:** The main toolbar option that checks and saves the record.
**When it applies:** Clicked after entering data in detail mode or Fast Entry mode.
**Business outcome:**
- **Detail mode:** The checks in BR-02 to BR-05, BR-08, BR-09, BR-12 and BR-13 run first. The system then asks for confirmation (MSG-14), saves the group and its QC parameter links in one transaction, shows MSG-15 and starts a new record. On failure, everything is rolled back and MSG-22 is shown.
- **Fast Entry mode:** The system asks for confirmation once (MSG-14), then checks and saves each row separately (BR-19). It writes "Successfully Created." (MSG-19) or the failure reason to Remarks, shows MSG-20 at the end and clears the detail card.

### Search Action
**What it is:** A toolbar option that opens the search dialog.
**When it applies:** Clicked when the user needs to find and open an existing material group.
**Business outcome:**
- Lists the material groups of the current company, using a search listing that is configured centrally for this screen. Sort order, columns and whether inactive groups appear are set by that configuration, not by the screen (Inferred).
- The chosen group is loaded with its category, codes, name, Inactive status and QC parameter links.
- Every field is locked for branch users (BR-01).

### Delete Action
**What it is:** A toolbar option that removes a record.
**When it applies:** Clicked when an authorised user wants to remove an existing material group. If no group is loaded, nothing happens.
**Business outcome:**
- Asks for confirmation (MSG-16), then removes the group's QC parameter links, its company availability and the group itself (BR-11).
- On success, shows MSG-17 and starts a new record.
- If the database refuses the removal, nothing is removed and its reason is shown (MSG-21).
- The screen performs no Head Office check or usage check of its own.

### Navigation Actions
**What it is:** Toolbar options for moving between records.
**When it applies:** Enabled on this screen.
**Business outcome:** Moves to the first, previous, next or last material group (Inferred: provided by the shared application framework).

### Other Toolbar Actions (Print, Preview, Export, Email)
**What it is:** The remaining standard toolbar functions. This screen neither enables nor implements them.
**When it applies:** Never available on this screen.
**Business outcome:** Printing, previewing, exporting and emailing material groups are not supported here. Excel import is available only inside Fast Entry (see Import Action).

## 6. Data Layer (Business Information)
*This section describes the business information lifecycle and cross-entity relationships managed through the Material Group screen.*

### Material Group Header Record
**What it is:** The main master record. It holds the parent category, the two-character Code, the Group Name, the creator and creation time, the last modifier and modification time, the authoriser and authorisation time, and the document status.
**When it applies:** Created and maintained on this screen by Head Office users (BR-01).
**Business outcome:** Serves as the authoritative definition of the group for the whole enterprise.

### Company Availability Profile
**What it is:** One availability link per registered operating company, each carrying its own inactive status.
**When it applies:** Created for every company, as active, when a new group is first saved (BR-10). This screen does not change it afterwards (BR-16).
**Business outcome:** The group definition is shared across all companies, and active status is tracked per company.

### Child Detail Profiles
**What it is:** The detail collection attached to the header: Quality Control Parameters. For each parameter it holds the standard value, tolerance value, deduction rate, deduction type and double-deduction threshold.
**When it applies:** Maintained through the embedded Quality Control Parameters control, which is hidden on this screen (Section 7).
**Business outcome:** Records the group's quality standards and deduction terms.

### Record Creation Lifecycle
**What it is:** The stage where a new material group is added.
**When it applies:** When the mandatory fields are completed and Save is clicked.
**Business outcome:**
- Fields are locked for branch users (BR-01).
- The checks in BR-02 to BR-09 run, using the suggested or entered Code (BR-06).
- The group is marked as authorised with the saving user as authoriser (BR-17).
- Active company links are created for all companies (BR-10).
- Any QC parameter rows are saved in the same transaction.

### Record Retrieval and Search Lifecycle
**What it is:** The stage where users search for and view existing material groups.
**When it applies:** Started from Search or the navigation options.
**Business outcome:** The header, the Inactive status and the QC parameter links are shown. Every field is locked when the logged-in company is not the Head Office (BR-01).

### Record Modification Lifecycle
**What it is:** The stage where an existing material group is updated.
**When it applies:** When fields are edited and Save is clicked.
**Business outcome:**
- The category, Code and name are updated, and the modifier and authoriser are recorded (BR-17).
- All QC parameter links are replaced by the control's current rows (BR-14).
- The full codes of all items under the group's sub-groups are recalculated (BR-18).
- Choosing a different category re-suggests the Code (BR-06).

### Record Retirement and Deletion Lifecycle
**What it is:** The stage where a material group is deactivated or removed.
**When it applies:** When Delete is clicked and confirmed. Deactivation is not possible on this screen, because the Inactive checkbox is view-only (BR-16).
**Business outcome:**
- Deletion removes the QC parameter links, the company availability and the group together (BR-11).
- There is no usage check on the screen.
- If the database refuses the removal, nothing is removed and its reason is shown (MSG-21).

### Transactional Safety
**What it is:** Grouping the related changes of one action into a single all-or-nothing unit.
**When it applies:** During save and delete.
**Business outcome:**
- **Detail-mode save:** the header and its QC parameter links are committed together or rolled back together.
- **Delete:** the links, availability and header are removed together.
- **Fast Entry:** each row is a separate unit, so a failed row does not undo rows saved earlier.

## 7. Child Entities and Associated Controls
*This section details secondary collections, embedded controls, or specialised configuration grids associated with the Material Group screen.*

### Quality Control Parameters Structure
**What it is:** The group's list of linked QC parameters. For each parameter, the system stores the standard value, tolerance value, deduction rate, deduction type and double-deduction threshold.
**When it applies:** Rewritten from the embedded control on every save (BR-14) and removed when the group is deleted (BR-11). Rows without a parameter are ignored.
**Business outcome:**
- Records group-level quality standards (Inferred: used during quality inspection).
- Standard Value2 and the Actual Values are not stored for the group.
- Unit, Tolerance Type, Tolerance Unit, Deduction On and Formula Type are always read from the parameter master.

### Quality Control Parameters
**What it is:** A reusable embedded control with a QC Group Name selection list and a parameter grid. The grid columns are:
- QC Parameter Name;
- Unit (read-only);
- Standard Value1 and Standard Value2 (up to three decimal places);
- Actual Value1 and Actual Value2 (hidden on this screen);
- Tolerance Value (up to three decimal places);
- Tolerance Type and Tolerance Unit (read-only);
- Deduction On ("Lower value before Tolerance Limit" or "Higher value after Tolerance Limit"; read-only);
- Formula Type (Rate or Quantity; read-only);
- Deduction Rate (Basic, Prorata or Landed);
- Deduction Type (Single or Double);
- Double Deduction From (up to three decimal places).
**When it applies:** Parameters can be linked in two ways:
- **One at a time:** choosing a QC Parameter Name fills all of that parameter's default values; clearing it clears the row.
- **From a template:** choosing a QC Group Name replaces the grid with that template's parameters and values (BR-15).
The control loads the group's existing links when a group is opened.
**Business outcome:** Defines the quality standard and commercial deduction terms for material in the group. The rules are BR-12 to BR-15. On this screen the control is hidden, so users cannot use it (see Interface Visibility and Layout Status).

### Operational Limits on Child Rows
**What it is:** The value rules for QC rows:
- no duplicate parameter;
- a non-zero Standard Value;
- a Tolerance Value, a Deduction Rate and a Deduction Type are required;
- Double Deduction From is required when the Deduction Type is Double, and cleared and locked when it is Single;
- only parameters that are authorised and active are offered.
**When it applies:** When rows are edited, and on every save.
**Business outcome:** BR-12 to BR-15 apply, with MSG-06 to MSG-12. The control can also enforce MSG-08 (actual value) and MSG-13 (at least one parameter), but neither is active on this screen: the Actual Value columns are hidden and the at-least-one check is not switched on.

### Interface Visibility and Layout Status
**What it is:** The display state of each child grid, tab or embedded control on the screen.
**When it applies:** During normal use of the screen.
**Business outcome:**
- **Quality Control Parameters control:** hidden. It is set to not visible, the screen never makes it visible, and it sits outside the visible area. Even so, it is still filled when a group is loaded, still checked on every save (BR-12, BR-13) and still saved as the group's QC links (BR-14). In practice, existing links are carried through unchanged and new groups are saved with no QC parameters (Inferred).
- **QC deduction columns:** when the enterprise setting to hide QC deductions is on, the Deduction On, Deduction Rate, Formula Type, Deduction Type and Double Deduction From columns are hidden (BR-15).

## 8. Business Operations (Stored Procedures)
*This section details the discrete business operations performed by the Material Group screen.*

### Load Selection Lists Operation
**What it is:** Loads the Category Name list and the empty Fast Entry grid layout. For the QC control, it also loads:
- QC Group templates, QC parameters, units and tolerance units;
- tolerance types;
- the Deduction On, Formula Type, Deduction Rate and Deduction Type options;
- the setting that hides QC deductions.
**When it applies:** When the screen opens, and when a record is loaded.
**Business outcome:**
- The category list shows the categories active for the current company, plus the loaded group's own category (BR-02).
- The QC lists are limited to authorised and active entries (BR-15).

### Dependent Values and Code Assignment Operation
**What it is:** When a category is chosen, the system:
- fills Category Code;
- takes the highest numeric Code already used in that category, adds one and pads the result to two digits;
- rebuilds the Group Code.
**When it applies:** Whenever a category is chosen, on the card or for each Fast Entry row, and whenever the Code is changed.
**Business outcome:** Suggests the next two-digit Code, which the user may override (BR-06), and keeps the Group Code display up to date (BR-07).

### Load QC Group Template Operation
**What it is:** Retrieves the parameters and values of a chosen QC Group template. Only parameters that are authorised and active for the company are included.
**When it applies:** When a QC Group Name is chosen in the QC control. This cannot happen on this screen while the control is hidden.
**Business outcome:** Fills the QC parameter grid in one step (BR-15).

### Search Records Operation
**What it is:** Finds material groups that match the search criteria.
**When it applies:** When the user searches in the search dialog.
**Business outcome:** Runs the search listing configured centrally for this screen for the current company. Its scope, sort order and columns come from that configuration (Inferred).

### Load Record Details Operation
**What it is:** Opens the full record and its child rows.
**When it applies:** When a record is chosen from the search results or by navigation.
**Business outcome:**
- Fills Category Name, Code (and therefore Category Code and Group Code), Group Name and Inactive.
- Fills the hidden QC control, including attributes taken from the parameter master.
- Locks every field for branch users (BR-01).

### Validate Record Operation
**What it is:** Checks the record for completeness, format and uniqueness before saving.
**When it applies:** When Save is clicked, in detail or Fast Entry mode.
**Business outcome:** Checks run in this order:
1. Category Name (MSG-01; focus on Category Name).
2. Code length (MSG-02; focus on Code).
3. Duplicate name within the category for the current company (MSG-03; focus on Group Name).
4. Duplicate Code within the category (MSG-04; focus on Code).
5. Blank Group Name (MSG-05; focus on Group Name).
6. The QC row rules (MSG-07 to MSG-12).
In Fast Entry, the message text is written to the row's Remarks instead of being shown.

### Save Main Record Operation
**What it is:** Saves the header record and sets up company links.
**When it applies:** After validation passes during Save.
**Business outcome:**
- **New group:** the header is inserted as authorised (BR-17) and active links are created for all companies (BR-10).
- **Existing group:** the header is updated, its existing QC links are removed so they can be rewritten (BR-14), and item full codes are realigned (BR-18).
- **Confirmation:** MSG-15 in detail mode, or MSG-19 in the row's Remarks in Fast Entry.

### Save Child Details Operation
**What it is:** Saves the child rows as part of the same save.
**When it applies:** During Save, for each QC row that has a parameter.
**Business outcome:** The QC links are replaced in full. If any row fails, the whole save, including the header, is rolled back and MSG-22 is shown.

### Delete Record Operation
**What it is:** Removes the material group and its child details.
**When it applies:** After the delete prompt is confirmed.
**Business outcome:**
- Runs no usage or authority check of its own.
- Removes the QC links, the company availability and the header together.
- Shows MSG-17 on success. If the database refuses, it rolls back and shows the database's reason (MSG-21).

## 9. Modular Architecture Notes
*This section highlights business-relevant architectural principles governing the Material Group screen.*

### Modular Business Architecture
**What it is:** The separation between the screen, the business logic and the stored data.
**When it applies:** For every action taken on the Material Group screen.
**Business outcome:** The same checks (BR-02 to BR-09, BR-12, BR-13) apply whether data comes from the detail card, from Fast Entry or from an Excel import.

### Enterprise Standardisation and Component Reuse
**What it is:** The screen reuses shared masters (Material Categories, QC parameters, QC Group templates, units, tolerance types) and the shared Quality Control Parameters control. The control is designed for use on other screens too (Inferred from its configurable options, such as its OK and Cancel row-template buttons and its optional at-least-one-parameter check).
**When it applies:** When the screen opens and on every save.
**Business outcome:** Quality parameter behaviour is the same wherever the control is used. On this screen it runs in plain grid mode, without the OK and Cancel buttons, and is hidden.

### Centralised Transactional Safety
**What it is:** The all-or-nothing handling of multi-record changes.
**When it applies:** During save and delete.
**Business outcome:**
- The group header and its QC parameter links are always committed or rolled back together.
- On delete, the links, the company availability and the header are removed together.
- Each Fast Entry row is its own unit.

## 10. Use Cases
*This section outlines standard operational scenarios executed on the Material Group screen.*

### Single Material Group Creation
**Actor:** Master Data Clerk (Head Office)
**Flow:**
1. Click New.
2. Select a Category Name (BR-02).
3. Accept or override the suggested Code (BR-04, BR-06).
4. Enter the Group Name (BR-03, BR-05).
5. Click Save and confirm (MSG-14).
**Result:** The group is saved as authorised (BR-17) and made available to all companies (BR-10). MSG-15 is shown and the card is cleared. If a check fails, the cursor moves to the field at fault and MSG-01, MSG-02, MSG-03, MSG-04 or MSG-05 is shown. A database failure shows MSG-22.

### Bulk Entry Through Fast Entry
**Actor:** Master Data Clerk (Head Office)
**Flow:**
1. Click the Group Code hyperlink.
2. Either type rows of Category Name, Code (optional) and Group Name, or click Import, confirm MSG-18 and load the required Excel sheet (BR-20).
3. Click Save and confirm (MSG-14).
**Result:**
- Rows without a Category Name are skipped.
- Every other row is checked and saved on its own. A blank Code takes the suggested next code (BR-19).
- Remarks shows "Successfully Created." (MSG-19) or the reason for failure, and MSG-20 is shown at the end.

### Maintain Quality Control Parameters
Not applicable for this screen. The Quality Control Parameters control is hidden, so users cannot add or change QC rows here. Existing links are carried through on every save (BR-14).

### Search and Modify Material Group
**Actor:** Master Data Clerk (Head Office), and Branch User for viewing
**Flow:**
1. Click Search and select a group.
2. Change its Category Name, Code or Group Name.
3. Click Save and confirm (MSG-14).
**Result:**
- **Head Office:** the update is saved with MSG-15, the QC links are rewritten (BR-14) and the full codes of affected items are realigned (BR-18).
- **Branch user:** the record opens with every field locked (BR-01).

### Material Group Deletion
**Actor:** Master Data Clerk (Head Office)
**Flow:**
1. Open the group.
2. Click Delete and confirm (MSG-16).
**Result:** The group, its company availability and its QC links are removed, and MSG-17 is shown (BR-11). If the database refuses the removal, for example because sub-groups still use the group (Inferred), nothing is removed and MSG-21 shows the database's reason.

### Duplicate Prevention Handling
**Actor:** Data Entry Operator (Head Office)
**Flow:** The user tries to save a Group Name or a Code that is already used in the same category.
**Result:**
- **Duplicate name:** MSG-03 is shown and the cursor moves to Group Name (BR-08).
- **Duplicate Code:** MSG-04 is shown and the cursor moves to Code (BR-09).
- **Fast Entry:** the same text is written to the row's Remarks.

## 11. Business Rules
*This section establishes the authoritative business rules governing the Material Group screen.*

- **BR-01 (Head Office Authority):** When the logged-in company is not the Head Office, every field is locked on New, on reset and when a record is loaded, so branch users can only view groups.
- **BR-02 (Mandatory Valid Category):** A valid Category Name must be selected (MSG-01). The list offers the categories active for the current company, plus the category of the group currently loaded.
- **BR-03 (Mandatory Group Name):** The Group Name is required (MSG-05).
- **BR-04 (Two-Character Code):** The Code is mandatory and must be exactly two characters. Entry is limited to two characters (MSG-02).
- **BR-05 (Group Name Length and Trimming):** The Group Name may be up to 100 characters. Leading and trailing spaces are removed before saving.
- **BR-06 (Automatic Next Code):** Choosing a category suggests the next Code: the highest numeric Code in that category plus one, padded to two digits. Non-numeric Codes are ignored when working out the suggestion. The user may override it.
- **BR-07 (Composite Group Code):** The Group Code is always the Category Code followed by the Code, and it is read-only.
- **BR-08 (Group Name Uniqueness):** The Group Name must be unique within the same category among groups available to the current company (MSG-03).
- **BR-09 (Group Code Uniqueness):** The Code must be unique within the same category across the enterprise (MSG-04).
- **BR-10 (Company Availability):** A new group is automatically made available, as active, to every registered operating company.
- **BR-11 (Deletion Scope):** Deletion removes the group's QC parameter links, its company availability and the group itself together. The screen performs no usage or authority check of its own. A refusal by the database stops the deletion (MSG-21).
- **BR-12 (QC Row Completeness):** Every QC row with a parameter must have a non-zero Standard Value, a Tolerance Value, a Deduction Rate and a Deduction Type. A parameter may not appear twice (MSG-06, MSG-07, MSG-09, MSG-10, MSG-11).
- **BR-13 (Double Deduction Threshold):** When the Deduction Type is Double, Double Deduction From is required (MSG-12). When it is Single, the field is cleared and cannot be edited.
- **BR-14 (QC Link Replacement on Save):** On every save of an existing group, all of its QC parameter links are removed and rewritten from the control's current rows.
- **BR-15 (QC Catalogue Scope and Deduction Visibility):**
  - QC Group templates, units and template parameters are offered only when they are authorised and active for the company.
  - Inactive QC parameters are hidden unless they are already in use in the grid.
  - The enterprise setting to hide QC deductions hides the deduction columns.
- **BR-16 (View-Only Inactive):** The Inactive checkbox is always disabled. It shows the stored status and cannot be changed on this screen.
- **BR-17 (Automatic Authorisation and Audit):** Every save marks the group as authorised, with the saving user and time recorded as the authoriser. The creator is recorded on insert and the modifier on update.
- **BR-18 (Item Code Realignment):** Saving an existing group recalculates the full code (Category Code + group Code + Sub-Group code + item code) of every item under the group's sub-groups.
- **BR-19 (Fast Entry Row Processing):**
  - Fast Entry rows with a blank Category Name are skipped.
  - Every other row goes through the same checks as detail mode and is saved in its own transaction. A blank Code takes the suggested next code.
  - Each row's outcome is written to its Remarks.
- **BR-20 (Excel Import Format):** An imported workbook must contain a sheet named with this screen's code, MMIG, that has the columns Category Name, Code and Group Name.

## 12. Messages
*This section catalogues all user-facing notifications, validation prompts, and error messages generated by the Material Group screen.*

- **MSG-01:** Category missing or invalid; *"Select valid Category Name."*; select a category from the list (BR-02).
- **MSG-02:** Code not exactly two characters; *"Code must be 2 digit."*; enter a two-character code (BR-04).
- **MSG-03:** Group Name already used in the category; *"Duplicate Group Name is not allowed."*; enter a different name (BR-08).
- **MSG-04:** Code already used in the category; *"Duplicate Group Code is not allowed."*; enter an unused code (BR-09).
- **MSG-05:** Group Name blank; *"Enter Group Name."*; type the group's name (BR-03).
- **MSG-06:** QC parameter repeated in the grid; *"Duplicate QC Parameter not allowed."*; remove the repeated row (BR-12).
- **MSG-07:** QC standard value missing or zero; *"Standard Value can't be empty or zero"*; enter a non-zero standard value (BR-12).
- **MSG-08:** QC actual value missing or zero (not active on this screen because the Actual Value columns are hidden); *"Actual Value1 can't be empty or zero"*; enter a non-zero actual value.
- **MSG-09:** QC tolerance value missing; *"Enter Tolerance Value"*; enter a tolerance value (BR-12).
- **MSG-10:** QC deduction rate missing; *"Select valid Deduction Rate"*; choose Basic, Prorata or Landed (BR-12).
- **MSG-11:** QC deduction type missing; *"Select valid Deduction Type"*; choose Single or Double (BR-12).
- **MSG-12:** Double deduction threshold missing; *"Enter Double Deduction From"*; enter the threshold value (BR-13).
- **MSG-13:** No QC parameter entered (not active on this screen because the check is not switched on); *"Select atleast one QC Parameter."*; add at least one parameter.
- **MSG-14:** Save confirmation prompt; standard application message, wording not in this screen's source; confirm to save or cancel.
- **MSG-15:** Save successful in detail mode; standard application message, wording not in this screen's source; acknowledge it. The card is cleared for a new record.
- **MSG-16:** Delete confirmation prompt; standard application message, wording not in this screen's source; confirm to delete or cancel.
- **MSG-17:** Delete successful; standard application message, wording not in this screen's source; acknowledge it. The card is cleared for a new record.
- **MSG-18:** Import confirmation; *"Your excel should consists of sheet with name MMIG. Do you want to continue?"*; confirm, then choose the workbook (BR-20).
- **MSG-19:** Fast Entry row saved, written to Remarks; *"Successfully Created."*; no action needed. Rows that fail show the validation or error text instead.
- **MSG-20:** Fast Entry batch finished; *"Refer Remarks for data saved status."*; review each row's Remarks (BR-19).
- **MSG-21:** Deletion refused by the database; the database's own error description is shown as a delete validation notice; keep the group, or first remove the records that depend on it (BR-11).
- **MSG-22:** Save failed; the database's own error description is shown as an error notice and all changes are rolled back; correct the cause and save again.

## 13. Limitations and Assumptions
*This section identifies functional constraints and operational assumptions governing the Material Group screen.*

### Hidden Quality Control Parameters
**What it is:** The QC control is hidden and lies outside the visible area of the screen (Section 7).
**When it applies:** Whenever users want to add or change a group's quality parameters.
**Business outcome:**
- Existing links are only carried through on save (BR-14), and new groups are saved without QC parameters.
- If a carried-through row ever failed BR-12 or BR-13, the user would see the message but could not correct the row (Inferred).

### Code Length Checked, Not Digits
**What it is:** BR-04 checks only that the Code has two characters, although MSG-02 says "2 digit".
**When it applies:** When a user overrides the suggested Code.
**Business outcome:** Codes containing letters are accepted, and they are then ignored by the next-code suggestion (BR-06). This may be a defect.

### Ninety-Nine Numeric Codes per Category
**What it is:** The suggested Code is two digits, padded and cut to two characters (BR-06).
**When it applies:** Once a category reaches Code 99.
**Business outcome:** The next suggestion becomes "00". That code is then either rejected as a duplicate (BR-09) or accepted out of sequence.

### Group Name Limit and Uniqueness Scope
**What it is:** The Group Name is limited to 100 characters (BR-05). It is unique only within the category for the current company (BR-08), whereas the Code is unique within the category across the enterprise (BR-09).
**When it applies:** When groups are created or renamed.
**Business outcome:** The same name can be used in different categories, and the name check and the code check have different scopes.

### Inactive Status May Not Be the Current Company's
**What it is:** When a group is loaded, the Inactive value comes from the first company availability link found for the group. It is not filtered to the logged-in company.
**When it applies:** When a group is retrieved.
**Business outcome:** The checkbox may not show the current company's real status. This may be a defect.

### Fast Entry May Report Success for a Failed Row
**What it is:** When a Fast Entry row passes the checks but then fails while being saved, the failure is shown as a separate error notice (MSG-22), but the row's Remarks still says "Successfully Created." (MSG-19).
**When it applies:** In Fast Entry saves.
**Business outcome:** Users must watch for error notices as well as reading Remarks. This may be a defect.

### Branch Restriction Enforced Only by Locking Fields
**What it is:** BR-01 locks the fields. Neither the save nor the delete operation checks Head Office authority itself.
**When it applies:** When branch users use the Save or Delete toolbar options.
**Business outcome:** It is assumed that toolbar permissions stop branch users from saving or deleting (Inferred).

### No Usage Check Before Deletion
**What it is:** Deletion relies on the database to refuse removal of a group that is in use (BR-11).
**When it applies:** When a group with sub-groups or other references is deleted.
**Business outcome:** If the database refuses, the user sees its technical reason (MSG-21) rather than a business message.

### Silent Item Renumbering
**What it is:** Changing a group's category or Code realigns the full codes of every item under it (BR-18), with no warning.
**When it applies:** When an existing group is modified.
**Business outcome:** Item codes that appear on documents or in external systems may change without notice (Inferred).

### Company Availability at Creation Only
**What it is:** Company links are created only for the companies registered at the moment the group is first saved (BR-10).
**When it applies:** When operating companies are added later.
**Business outcome:** It is assumed that another process makes existing groups available to new companies (Inferred).

### Centralised Authority and Live Connectivity
**What it is:** The assumptions that a single Head Office governs the classification and that branches work against the live central data.
**When it applies:** For screen locking (BR-01) and company availability (BR-10).
**Business outcome:** Prevents conflicting local versions of the classification (Inferred).

## 14. Open Questions
*This section records unresolved business and functional items requiring formal confirmation from the business owner.*

1. **Hidden Quality Control Parameters:** The QC control is hidden but is still checked and saved on every save. Is this intended? If it is, where are group-level QC parameters maintained, and how should a user correct a carried-through row that fails validation? If it is not, should the control be made visible? Suggested Business Owner: Quality Control Head.
2. **Branch Save and Delete Access:** Branch users have their fields locked, but the screen does not itself block Save or Delete. Should these actions be disabled or refused for companies other than the Head Office? Suggested Business Owner: Enterprise Master Data Governance Lead.
3. **Deletion Usage Check:** Deletion relies on the database to refuse a group that is in use, and then shows the database's technical message. Should the screen check explicitly for linked sub-groups, items or transactions and show a business message? Suggested Business Owner: Enterprise Master Data Governance Lead.
4. **Numeric-Only Codes:** The message says "Code must be 2 digit." but letters are accepted, and such codes are ignored by the next-code suggestion. Should the Code be restricted to digits? Suggested Business Owner: Material Classification Owner.
5. **More Than 99 Groups per Category:** What should happen when a category passes 99 numeric codes, given that the suggestion wraps to "00"? Suggested Business Owner: Material Classification Owner.
6. **Inactive Status Source:** Should the Inactive checkbox show the logged-in company's status instead of the first company link found? Suggested Business Owner: Enterprise Master Data Governance Lead.
7. **Fast Entry Failure Reporting:** Should a Fast Entry row that fails while being saved show the failure reason in Remarks instead of "Successfully Created."? Suggested Business Owner: Master Data Operations Lead.
8. **Uniqueness Scope Difference:** Group Name uniqueness is checked within the category for the current company, while Code uniqueness is checked within the category across the enterprise. Is this difference intended? Suggested Business Owner: Material Classification Owner.
9. **Recategorising or Recoding a Group in Use:** Should a change of category or Code be allowed for a group that already has sub-groups and items, given that it silently renumbers the items' full codes? Suggested Business Owner: Inventory Operations Lead.
10. **Standard Message Wording:** What exact wording do the save and delete confirmation and success messages use (MSG-14 to MSG-17)? It is not in this screen's source. Suggested Business Owner: ERP Application Owner.
11. **New Company Onboarding:** How are existing groups made available to operating companies registered after the groups were created? Suggested Business Owner: Enterprise Master Data Governance Lead.
12. **Downstream Use of Group QC Parameters:** Which inspection or receipt processes use the group-level QC standards and deductions? (This document infers quality inspection.) Suggested Business Owner: Quality Control Head.
13. **Unsaved Fast Entry Rows:** Switching back to detail mode does not save the grid's rows. Should the user be warned, or should the rows be kept for later? Suggested Business Owner: Master Data Operations Lead.
