# Material Sub Group Master Screen: Functional Documentation

## 1. Summary
*This section provides an executive overview of the Material Sub Group Master screen and its role in Materials Management.*

The Material Sub Group Master screen maintains material sub groups, the third level of the material classification hierarchy (Category, then Group, then Sub Group). Each sub group has a two-character code that, combined with its category and group codes, forms the full Sub Group Code used as the prefix of item codes (BR-08, BR-28). The screen gives each material family one place for its operational defaults: tax classification, permitted warehouses, approved makes, units per unit type, approved vendor locations, quality control parameters, bin cards and an optional dispatch negative tolerance. Users can create single records, bulk-create through Fast Entry or spreadsheet import, maintain the six detail collections and delete records. New sub groups are approved automatically and made available to every company (BR-11, BR-22). Deletion is reserved to Head Office, and branch users see loaded records in view-only form (BR-01, BR-02). Master data, purchasing, stores and quality teams benefit from consistent classification and family-level defaults across all operating companies.

## 2. Purpose and Scope
*This section outlines the business rationale for the Material Sub Group Master screen and establishes its operational boundaries within the enterprise.*

### Business Purpose of Material Sub Groups
**What it is:** A coded, fine-grained material family under a Category and Group, together with the defaults that items of that family rely on.
**When it applies:** When a new material family is introduced, or when its code, name, tax classification, warehouses, makes, units, vendors, quality parameters, bins or dispatch tolerance change.
**Business outcome:** Prevents inconsistent classification and item coding (BR-08, BR-09, BR-28), and gives downstream processes one source for family-level defaults (Inferred).

### In-Scope Functional Capabilities
**What it is:** The functional scope covered directly by the Material Sub Group Master screen.
**When it applies:**
- Single-record creation
- Fast Entry bulk creation and spreadsheet import
- Searching and retrieval
- Modification and deletion
- Maintenance of the Warehouse Detail, Make Detail, UOM, Vendor Detail, Bin Detail and QC Detail collections

**Business outcome:** Users maintain:
- Category and Group assignment, Code and Sub Group Name
- GST Category and HSN/SAC Code
- BIN Applicable and Dispatch -ve Tolerance
- The six detail collections

Company availability is set up automatically (BR-11).

### Out-of-Scope Capabilities
**What it is:** Business activities related to material sub groups that are excluded from the Material Sub Group Master screen.
**When it applies:** Covers the following needs:
- Maintaining categories, groups, units, unit types, makes, vendors and locations, warehouses, divisions, bin cards, QC parameters, QC groups, GST categories, HSN/SAC codes or tax charges
- Changing a sub group's company-level active status
- Printing, previewing, exporting or e-mailing sub groups

**Business outcome:** The supporting masters are maintained on their own screens (Inferred). This screen only selects from them. Company-level inactivation and output functions are not available here (BR-23, Section 5).

## 3. Business Glossary
*This section defines standard business terminology used on and around the Material Sub Group Master screen.*

### Material Sub Group
**What it is:** A material family that sits under one Group, which in turn sits under one Category.
**When it applies:** The record created and maintained on this screen. Its Category and Group are mandatory (BR-03).
**Business outcome:** Provides the lowest classification level above individual items.

### Category and Group
**What it is:** The first and second levels of the material classification. Each has its own code.
**When it applies:** Chosen in sequence. The Group list depends on the chosen Category (BR-06).
**Business outcome:** Supply the parent classification and the first two parts of the full Sub Group Code (BR-08).

### Code
**What it is:** The sub group's own code within its Group, up to 2 characters.
**When it applies:** Suggested automatically when a Group is chosen. The user can overwrite it (BR-05, BR-07).
**Business outcome:** Forms the last part of the full Sub Group Code.

### Sub Group Code
**What it is:** The read-only full code made up of the Category code, the Group code and the sub group's Code.
**When it applies:** Shown at the top of the card and recalculated whenever one of its parts changes (BR-08).
**Business outcome:** It must be unique within the company (BR-09) and becomes the prefix of item full codes (BR-28).

### GST Category and HSN/SAC Code
**What it is:** The statutory tax classification of the family. Choosing an HSN/SAC Code displays its CGST, SGST, IGST and UTGST rates.
**When it applies:** Optional selections on the GST Detail tab (BR-04).
**Business outcome:** Gives the family a default tax classification for its items and transactions (Inferred).

### Dispatch -ve Tolerance
**What it is:** A percentage by which dispatch quantity may fall short (Inferred from the label).
**When it applies:** Visible only when the company's sales settings allow it (BR-25).
**Business outcome:** Allows controlled short dispatch for materials in the family (Inferred).

### Receipt Tolerance and Shipment Tolerance
**What it is:** Percentage tolerances stored on the sub group.
**When it applies:** The fields are hidden on the current screen (BR-27).
**Business outcome:** Stored values are kept, but users cannot maintain them on this screen.

### Warehouse Detail
**What it is:** The warehouses, together with their company and, where used, division, in which the family is permitted.
**When it applies:** Ticked on the Warehouse Detail tab (BR-14).
**Business outcome:** Records where the family's materials may be held (Inferred).

### Make Detail
**What it is:** The manufacturers or brands approved for the family.
**When it applies:** Listed on the Make Detail tab (BR-15).
**Business outcome:** Sets the approved makes for the family's items (Inferred).

### UOM and Unit Type
**What it is:** A Unit Type is the role a unit plays, taken from the enterprise's fixed unit-type list (for example base, purchase or sales unit (Inferred)). The UOM tab assigns one unit to each unit type.
**When it applies:** Maintained on the UOM tab (BR-16).
**Business outcome:** Provides default units for the family's items (Inferred).

### Vendor Detail
**What it is:** The vendors, each with one of its registered locations, approved to supply the family.
**When it applies:** Listed on the Vendor Detail tab (BR-17).
**Business outcome:** Records the preferred supply sources (Inferred).

### Bin Detail and BIN Applicable
**What it is:** BIN Applicable states that the family is stored against bin cards, which are storage positions in warehouses. Bin Detail lists the bin cards assigned to the family.
**When it applies:** The Bin Detail tab follows the BIN Applicable checkbox (BR-18).
**Business outcome:** Directs storage of the family's materials to specific bins (Inferred).

### QC Detail, QC Parameter and QC Group
**What it is:** A QC Parameter is a measurable quality attribute with a standard value, a tolerance and deduction terms. A QC Group is a predefined set of parameters. QC Detail holds the family's parameters.
**When it applies:** The parameters are copied from the chosen Group (BR-26) and held in the embedded quality control component (Section 7).
**Business outcome:** Supplies inspection standards and the rules for price deductions on incoming material (Inferred).

### Deduction Terms
**What it is:** The QC settings that control price deductions:
- Deduction On: "Lower value before Tolerance Limit" or "Higher value after Tolerance Limit"
- Formula Type: "Rate" or "Quantity"
- Deduction Rate: "Basic", "Prorata" or "Landed"
- Deduction Type: "Single" or "Double"
- Double Deduction From: the value from which a Double deduction applies

**When it applies:** Set for each QC parameter row (BR-19).
**Business outcome:** Define how quality shortfalls become commercial deductions (Inferred).

### Fast Entry Mode
**What it is:** A grid for creating many sub groups at once, with spreadsheet import.
**When it applies:** Opened from the Sub Group Code hyperlink (BR-29).
**Business outcome:** Speeds up bulk onboarding and reports the result for each row in Remarks.

## 4. Prerequisites and Dependencies
*This section identifies upstream operational requirements and downstream dependencies associated with the Material Sub Group Master screen.*

### Operating Company Structure
**What it is:** The organisational hierarchy in the ERP that defines the Head Office company and the operating companies.
**When it applies:** Checked when a record is loaded, reset or deleted (BR-01, BR-02), and when a new record is saved (BR-11).
**Business outcome:**
- Only Head Office may delete.
- Branch users see loaded records in view-only form.
- New sub groups become available in every company.

### Categories and Groups
**What it is:** Existing Category and Group records with their codes. The category list shows categories active in the current company.
**When it applies:** Mandatory selections (BR-03, BR-06).
**Business outcome:** Supply the parent classification, the first two parts of the full code (BR-08), and the base for the suggested Code (BR-07).

### Group QC Parameters
**What it is:** The QC parameters defined against each Group.
**When it applies:** Copied to the sub group when a Group is chosen (BR-26).
**Business outcome:** Sub groups start with their parent group's quality standards.

### Supporting Masters for Detail Collections
**What it is:** The following masters supply the detail collections and tax fields:
- Warehouses, with their company and division set-up
- Makes
- Unit types and units
- Vendors and vendor locations
- Bin cards
- QC parameters and QC groups, with their tolerance types and units
- GST categories, HSN/SAC codes and their linked tax charges

**When it applies:** Loaded when the screen opens, on New, and before a record is loaded.
**Business outcome:** Fill the selection lists. Most lists are limited to records active in the current company, plus any already linked to the record (BR-12).

### Company and Enterprise Settings
**What it is:** Three settings affect this screen:
- The company sales setting that shows Dispatch -ve Tolerance
- The enterprise setting that hides QC deduction columns
- The company group's division applicability

**When it applies:** Read when the screen opens or is reset.
**Business outcome:** Show or hide the related field and columns (BR-25, Section 7).

### Configured Search Definition
**What it is:** A centrally configured search definition assigned to this screen.
**When it applies:** Used by the Search action.
**Business outcome:** Determines the records and columns in the search dialog. Its content is not defined in this screen's source (Open Question 15).

### Downstream Item Master Reliance
**What it is:** Items classified under the sub group.
**When it applies:** When an existing sub group is saved (BR-28) or deleted (BR-13).
**Business outcome:** Item full codes are rebuilt from the sub group's codes. Existing items may cause the database to refuse deletion (Inferred).

### Downstream Purchasing, Stores and Quality Reliance
**What it is:** Purchasing, receipt, storage, inspection and dispatch processes for the family's items (Inferred).
**When it applies:** When those processes look up the family's defaults (Inferred).
**Business outcome:** They use the sub group's approved makes, vendors, units, warehouses, bins, QC parameters, tax classification and dispatch tolerance (Inferred).

## 5. Form (Screen)
*This section details the interactive user interface areas, data entry fields, and action buttons of the Material Sub Group Master screen.*

### Standard Detail Card
**What it is:** The default single-record workspace. It contains the header fields (identification on the left, tolerances and flags on the right) above a tab strip. The tabs are GST Detail, QC Detail, Warehouse Detail, Make Detail, UOM, Vendor Detail and Bin Detail.
**When it applies:** Displayed when the screen opens or on returning from Fast Entry mode.
**Business outcome:** Provides an organised layout for creating and reviewing individual material sub groups. Category Name, Group Name, Code and Sub Group Name are highlighted as compulsory (BR-03).

### Sub Group Code Field
**What it is:** A hyperlink labelled "Sub Group Code" with the tooltip "Switch to fast entry mode.", next to a read-only display of the full code (BR-08).
**When it applies:** Always shown on the card and never editable.
**Business outcome:** Shows the Category code, Group code and Code joined together. Clicking the hyperlink opens Fast Entry mode.

### Category Name Field
**What it is:** A mandatory selection list of categories active in the current company, showing Category Name and Code (BR-03, BR-12).
**When it applies:** Shown on the card. It receives the cursor when the screen is reset.
**Business outcome:** Choosing a category fills the category code, clears Group Name and reloads the group list (BR-06). A missing value shows MSG-03.

### Receipt Tolerance Field
**What it is:** A percentage field with two decimals.
**When it applies:** Hidden in the current layout (BR-27).
**Business outcome:** Not maintainable by users. A stored value is kept on re-save, and new records store zero.

### Group Name Field
**What it is:** A mandatory selection list of the groups of the chosen category, showing Group Name and Code (BR-03, BR-06).
**When it applies:** Shown on the card and used after a Category is chosen.
**Business outcome:** Choosing a group fills the group code, suggests the next Code (BR-07) and loads the group's QC parameters (BR-26). A missing value shows MSG-04.

### Shipment Tolerance Field
**What it is:** A percentage field with two decimals.
**When it applies:** Hidden in the current layout (BR-27).
**Business outcome:** Not maintainable by users. A stored value is kept on re-save, and new records store zero.

### Group Code Field
**What it is:** Two read-only displays under the label "Group Code": the category code and the group code (BR-24).
**When it applies:** Filled automatically and never editable, including at branches.
**Business outcome:** Shows the first two parts of the full code.

### Dispatch -ve Tolerance Field
**What it is:** An optional percentage field with two decimals and up to 6 characters, followed by "%" (BR-05).
**When it applies:** Shown only when the company's sales setting allows it (BR-25).
**Business outcome:** Stores the permitted short-dispatch percentage. Zero or blank is stored as not set.

### Code Field
**What it is:** A mandatory free-text field of up to 2 characters (BR-03, BR-05).
**When it applies:** Shown on the card and pre-filled with the suggested code when a Group is chosen (BR-07).
**Business outcome:** Completes the full Sub Group Code and can be changed later. Surrounding spaces are removed. A blank value shows MSG-05. A full code already used in the company shows MSG-01 (BR-09).

### BIN Applicable Field
**What it is:** An optional checkbox, unticked by default.
**When it applies:** Shown on the card.
**Business outcome:** Ticking it shows the Bin Detail tab, and unticking it hides the tab. Bin links are saved only while it is ticked (BR-18).

### Sub Group Name Field
**What it is:** A mandatory free-text field of up to 100 characters (BR-03, BR-05).
**When it applies:** Shown on the card and in the Fast Entry grid.
**Business outcome:** Records the family's name. Surrounding spaces are removed. A blank value shows MSG-06. A name already used in the same group shows MSG-02 (BR-10).

### Inactive Field
**What it is:** A checkbox labelled "Inactive".
**When it applies:** Always disabled (BR-23).
**Business outcome:** Displays the stored active status when a record is loaded but cannot be changed here.

### GST Category Field
**What it is:** An optional selection list of active GST categories (BR-04).
**When it applies:** Shown on the GST Detail tab, which is open by default.
**Business outcome:** Records the family's GST category.

### HSN /SAC Code Field
**What it is:** An optional selection list of HSN/SAC codes with their descriptions (BR-04).
**When it applies:** Shown on the GST Detail tab.
**Business outcome:** Records the family's HSN/SAC classification and fills the four rate displays below it.

### CGST Rate Field
**What it is:** A read-only display (BR-24).
**When it applies:** Shown on the GST Detail tab. Filled when an HSN/SAC Code is chosen and cleared when it is removed.
**Business outcome:** Shows the central GST charge linked to the chosen HSN/SAC code. It is for information only and is not saved with the sub group.

### SGST Rate Field
**What it is:** A read-only display (BR-24).
**When it applies:** Shown on the GST Detail tab. Filled when an HSN/SAC Code is chosen and cleared when it is removed.
**Business outcome:** Shows the state GST charge linked to the chosen HSN/SAC code. It is for information only and is not saved.

### IGST Rate Field
**What it is:** A read-only display (BR-24).
**When it applies:** Shown on the GST Detail tab. Filled when an HSN/SAC Code is chosen and cleared when it is removed.
**Business outcome:** Shows the integrated GST charge linked to the chosen HSN/SAC code. It is for information only and is not saved.

### UTGST Rate Field
**What it is:** A read-only display (BR-24).
**When it applies:** Shown on the GST Detail tab. Filled when an HSN/SAC Code is chosen and cleared when it is removed.
**Business outcome:** Shows the union territory GST charge linked to the chosen HSN/SAC code. It is for information only and is not saved.

### QC Detail Grid
**What it is:** The embedded quality control component, with a QC Group Name selection list and a parameter grid (Section 7).
**When it applies:** On the QC Detail tab, which is hidden in the current layout. Nothing on the screen makes it visible.
**Business outcome:** The grid has these columns:
- QC Parameter Name
- Unit
- Standard Value1
- Standard Value2
- Tolerance Value
- Tolerance Type
- Tolerance Unit
- Deduction On
- Formula Type
- Deduction Rate
- Deduction Type
- Double Deduction From

It is still filled from the Group and still checked and saved (BR-19, BR-26).

### Warehouse Detail Grid
**What it is:** A list of every active warehouse with each company and division it is set up for. The columns are Select, Warehouse, Division and Company.
**When it applies:** On the Warehouse Detail tab, always shown.
**Business outcome:** Only Select can be changed, and rows cannot be deleted. Rows already linked are ticked and listed first. Division is filled only where divisions apply and the division is active (BR-14).

### Make Detail Grid
**What it is:** A list of approved makes with the columns Make Name, a selection list, and Code, which is filled automatically and read-only.
**When it applies:** On the Make Detail tab, always shown.
**Business outcome:** A new blank row appears when Make Name is entered on the last row. A make may appear only once (BR-15, MSG-13).

### UOM Grid
**What it is:** One fixed row per unit type, with the columns Unit Type (read-only) and Unit Name, a selection list of unit abbreviations.
**When it applies:** On the UOM tab, always shown. Rows cannot be added or deleted.
**Business outcome:** Assigns at most one unit to each unit type (BR-16).

### Vendor Detail Grid
**What it is:** A list of approved vendors with the columns Vendor Name and Location.
**When it applies:** On the Vendor Detail tab, always shown.
**Business outcome:**
- A new blank row appears when Vendor Name is entered on the last row.
- Choosing a vendor clears Location, and fills it if the vendor has only one location.
- The Location list shows only that vendor's locations.
- Location is required (MSG-12), and each vendor and location pair may appear only once (MSG-14) (BR-17).

### Bin Detail Grid
**What it is:** A list of all bin cards. The columns are an untitled Select tick column, with a tick box in its header, then Bin Card No., Location and Warehouse.
**When it applies:** On the Bin Detail tab, which follows the BIN Applicable checkbox (BR-18).
**Business outcome:** Only Select can be changed, and rows already linked are ticked. This grid stays editable for branch users after a record is loaded (BR-02).

### Fast Entry Grid Container
**What it is:** A grid with the following columns, an Import button and a return link:
- Category Name and Group Name, selection lists
- Code, up to 2 characters
- Sub Group Name, up to 100 characters
- Remarks, read-only

**When it applies:** Opened by clicking the Sub Group Code hyperlink. The card is reset first.
**Business outcome:**
- A new row appears when the last row is edited.
- Changing Category Name clears Group Name, and the Group Name list shows only groups of that row's category.
- On Save, each row's result is written to Remarks (BR-29, MSG-22, MSG-23).

### Import Action
**What it is:** The Import button inside the Fast Entry container.
**When it applies:** Available in Fast Entry mode.
**Business outcome:**
- Asks for confirmation first (MSG-24).
- Reads the spreadsheet sheet named in the prompt, with the columns Category Name, Group Name, Code and Sub Group Name.
- Replaces the grid contents with the imported rows and adds an empty Remarks column.

### Switch Back To Detail Action
**What it is:** The link "Switch back to detail mode." at the top right of the Fast Entry container.
**When it applies:** Visible whenever Fast Entry mode is active.
**Business outcome:** Hides the container and returns to the card. Unsaved grid rows are not cleared explicitly.

### New Action
**What it is:** A standard toolbar option that starts a blank record.
**When it applies:** Clicked when the user wants to create a new material sub group. It also runs automatically after a successful detail-mode save or delete.
**Business outcome:**
- Clears all fields and grids and reloads the selection lists.
- Inactive stays disabled.
- At a branch, the card is unlocked again, but the code displays stay read-only.
- The cursor goes to Category Name.

### Save Action
**What it is:** The main toolbar option that checks and saves the record.
**When it applies:** Clicked after entering data in detail mode or Fast Entry mode.
**Business outcome:** In detail mode, the save works as follows:
1. Runs the header checks (BR-03, BR-09, BR-10), the QC checks (BR-19) and the vendor checks (BR-17).
2. Asks for confirmation (MSG-16).
3. Saves the header and all details together (BR-21).
4. Shows MSG-17 and resets the card.

In Fast Entry mode, it asks for confirmation first, then validates and saves each row on its own, writes the result to Remarks and shows MSG-23 (BR-29). Save is not restricted by company (Open Question 2).

### Search Action
**What it is:** A toolbar option that opens the search dialog.
**When it applies:** Clicked when the user needs to find and open an existing material sub group.
**Business outcome:** Lists sub groups for the current company using the configured search definition. Sort order and columns are not defined in this screen's source. The chosen record opens, and at a branch it is locked for viewing (BR-02).

### Delete Action
**What it is:** A toolbar option that removes a record.
**When it applies:** Clicked when an authorised user wants to remove an existing material sub group. It does nothing if no record is open.
**Business outcome:**
- At a branch, deletion is blocked with MSG-18 (BR-01).
- At Head Office, a confirmation appears (MSG-19). The sub group and all its links are then removed (BR-13).
- On success MSG-21 appears and the card resets. If the database refuses, MSG-20 appears.

### Navigation Actions
**What it is:** Toolbar options for moving between records.
**When it applies:** When browsing existing records (Inferred from the shared toolbar).
**Business outcome:** Move to the first, previous, next or last record and open it the same way as Search (Inferred). The screen does not define this behaviour itself.

### Other Toolbar Actions (Print, Preview, Export, Email)
**What it is:** The remaining standard toolbar functions. They have no behaviour on this screen.
**When it applies:** Whenever the screen is open.
**Business outcome:** Nothing happens when they are used. Printing, previewing, exporting and e-mailing sub groups are not supported.

## 6. Data Layer (Business Information)
*This section describes the business information lifecycle and cross-entity relationships managed through the Material Sub Group Master screen.*

### Material Sub Group Header Record
**What it is:** The main master record. It holds:
- Parent Group, Code and Sub Group Name
- Receipt Tolerance and Shipment Tolerance
- GST Category, HSN/SAC Code and BIN Applicable
- Dispatch -ve Tolerance
- Approval status
- Created, modified and authorised user and date

**When it applies:** Created and maintained on this screen.
**Business outcome:** It is the authoritative definition of the material family.

### Company Availability Profile
**What it is:** One link per company, each with its own Inactive flag.
**When it applies:** Created for every company, as active, when a new sub group is saved (BR-11). It is not changed when the sub group is modified.
**Business outcome:** The definition is shared enterprise-wide, while active status is tracked per company. That status is display-only here (BR-23, Open Question 5).

### Child Detail Profiles
**What it is:** The detail collections attached to the header:
- Warehouse/division/company links
- Approved makes
- Unit per unit type
- Approved vendor locations
- QC parameter settings
- Bin card links

**When it applies:** Maintained in the child grids or tabs of the screen.
**Business outcome:** Together they set where the family is stocked, who supplies it, which makes and units apply, how it is inspected and which bins hold it (Inferred).

### Record Creation Lifecycle
**What it is:** The stage where a new material sub group is added.
**When it applies:** When the mandatory fields are completed and Save is clicked, in detail mode or for each Fast Entry row.
**Business outcome:** On creation:
- The validations run (BR-03, BR-09, BR-10, BR-17, BR-19).
- The record is saved as approved, with the saving user and time as authoriser (BR-22).
- It is linked to all companies as active (BR-11).
- The child rows are saved in the same unit (BR-21).

No company restriction applies to creation (BR-02).

### Record Retrieval and Search Lifecycle
**What it is:** The stage where users search for and view existing material sub groups.
**When it applies:** Started from Search or the navigation options.
**Business outcome:**
- The card is reset, then the header, GST, make, UOM, vendor and QC data are loaded.
- The warehouse and bin grids show all available rows, with this record's links ticked.
- At a branch, every control is then locked and Inactive disabled, except the Bin Detail grid (BR-02).

### Record Modification Lifecycle
**What it is:** The stage where an existing material sub group is updated.
**When it applies:** When fields are edited and Save is clicked.
**Business outcome:**
- The header is updated with modifier and authoriser stamps and stays approved (BR-22).
- All child rows are removed and saved again from the screen (BR-20).
- The full codes of all items in the sub group are rebuilt (BR-28).

### Record Retirement and Deletion Lifecycle
**What it is:** The stage where a material sub group is deactivated or removed.
**When it applies:** When Delete is clicked. Deactivation through Inactive is not possible on this screen (BR-23).
**Business outcome:**
- Head Office only (BR-01).
- Removes together: bin links, technical grade links, warehouse/division links, makes, QC settings, units, vendors, company links and the header (BR-13).
- Makes no explicit usage check. If the database refuses, nothing is removed and MSG-20 appears.

### Transactional Safety
**What it is:** Grouping the related changes of one action into a single all-or-nothing unit.
**When it applies:** During save and delete.
**Business outcome:** The header, company links and all six detail collections are saved or removed together. A failure in any part reverses the whole action (BR-21).

## 7. Child Entities and Associated Controls
*This section details secondary collections, embedded controls, or specialised configuration grids associated with the Material Sub Group Master screen.*

### Warehouse Detail Structure
**What it is:** The warehouses in which the family is permitted. Each row holds a company, a warehouse and, where divisions apply, a division.
**When it applies:** Configured on the Warehouse Detail tab by ticking rows. The list covers every active warehouse with each company and division it is set up for.
**Business outcome:** Only ticked rows are saved. Selecting a warehouse is not compulsory (BR-14).

### Make Detail Structure
**What it is:** The approved makes. Each row holds a make, and its code is shown for reference.
**When it applies:** Configured on the Make Detail tab. The list shows makes active in the current company plus any already linked (BR-12).
**Business outcome:** Each row with a make is saved, and duplicates are blocked (BR-15, MSG-13).

### UOM Structure
**What it is:** The default unit for each unit type. Each row holds a unit type and a unit.
**When it applies:** Configured on the UOM tab, with one fixed row per unit type. The unit list shows units active in the current company plus any already linked (BR-12).
**Business outcome:** A row is saved only when both Unit Type and Unit Name are present (BR-16).

### Vendor Detail Structure
**What it is:** The approved supply sources. Each row holds a vendor and one of its locations.
**When it applies:** Configured on the Vendor Detail tab. Only two specific vendor types are offered, active in the current company or already linked (BR-12, Open Question 8).
**Business outcome:** Location is required, and each vendor and location pair may appear only once (BR-17, MSG-12, MSG-14).

### Bin Detail Structure
**What it is:** The bin cards assigned to the family. Each row holds a bin card and shows its location and warehouse.
**When it applies:** Configured on the Bin Detail tab when BIN Applicable is ticked. The list includes bin cards of all warehouses, with no company filter (Open Question 10).
**Business outcome:** Ticked bins are saved only while BIN Applicable is ticked. Saving with it unticked removes existing bin links (BR-18).

### QC Detail Structure
**What it is:** The family's quality parameters. Each saved row holds a QC parameter, Standard Value, Tolerance Value, Deduction Rate, Deduction Type and Double Deduction From.
**When it applies:** Filled from the chosen Group (BR-26) or from the stored record when loaded.
**Business outcome:** Each row with a parameter is saved. Standard Value2 is shown but not saved by this screen (Open Question 14).

### Quality Control Parameters
**What it is:** A shared quality control component embedded in the QC Detail tab. It has a "QC Group Name" selection list and the parameter grid listed in Section 5.
**When it applies:** Entries are inherited from the parent Group whenever a Group is chosen (BR-26). Choosing a QC Group Name replaces the grid with that group's authorised parameters that are active in the current company.
**Business outcome:**
- Choosing a parameter fills its defaults from the parameter master.
- Unit, Tolerance Type, Tolerance Unit, Deduction On and Formula Type are read-only.
- Double Deduction From is cleared and locked when Deduction Type is Single.
- Duplicate parameters are blocked (MSG-15).
- The completeness rules are checked on every save (BR-19, MSG-07 to MSG-11).
- When the enterprise setting to hide QC deductions is on, the Deduction On, Formula Type, Deduction Rate, Deduction Type and Double Deduction From columns are hidden.
- The Actual Value1 and Actual Value2 columns and the component's OK and Cancel buttons are hidden here.
- The component's "Select atleast one QC Parameter." and "Actual Value1 can't be empty or zero" checks are not active on this screen.

These parameters are used for incoming inspection and price deductions (Inferred).

### Operational Limits on Child Rows
**What it is:** The value rules for child rows:
- Non-zero QC Standard Value; Tolerance Value, Deduction Rate and Deduction Type required; Double Deduction From required for Double deductions
- Location required for each vendor
- No duplicate makes, vendor and location pairs or QC parameters
- At most one unit per unit type

**When it applies:** Duplicates are blocked as rows are entered. The completeness checks run on Save, QC first and then vendors.
**Business outcome:** BR-15, BR-16, BR-17 and BR-19 apply, with MSG-07 to MSG-15. The first failure stops the save and moves focus to the cell and tab concerned.

### Interface Visibility and Layout Status
**What it is:** The display state of each child grid, tab or embedded control on the screen.
**When it applies:** During normal use of the screen.
**Business outcome:**
- GST Detail, Warehouse Detail, Make Detail, UOM and Vendor Detail are always visible.
- Bin Detail is conditional: it shows when BIN Applicable is ticked and hides when it is unticked (BR-18). It is visible in the layout before the checkbox is first used (Open Question 10).
- QC Detail is hidden in the layout, but it is still filled from the Group, checked on Save and saved (BR-19, BR-26, Open Question 3).
- The Fast Entry container is hidden until Fast Entry mode is opened.

## 8. Business Operations (Stored Procedures)
*This section details the discrete business operations performed by the Material Sub Group Master screen.*

### Load Selection Lists Operation
**What it is:** Loads the screen's selection lists, grid lists and settings:
- The warehouse/division list and bin card list, with the current record's links ticked
- Makes, unit types and units
- Vendors and their locations
- Categories, and the Fast Entry group list
- GST categories, and HSN/SAC codes with their tax charges
- The Dispatch -ve Tolerance setting
- The QC groups and QC parameters, with their units, tolerance types and the fixed deduction lists, and the setting that hides QC deductions

**When it applies:** When the screen opens, after New, and before a record is loaded.
**Business outcome:** Fills the lists for the current company (BR-12) and sets which fields and columns are shown (BR-25, Section 7). The Fast Entry group list shows only authorised groups active in the company. The detail-mode group list is loaded separately (Open Question 12).

### Dependent Values and Code Assignment Operation
**What it is:** Choosing a Category loads its groups. Choosing a Group returns the next suggested Code and the group's QC parameters. Choosing a QC Group Name returns that QC group's parameters.
**When it applies:** When Category Name, Group Name or QC Group Name changes.
**Business outcome:**
- The suggested Code is the highest numeric code in the group plus one, shown as two digits (BR-07).
- The full code is rebuilt (BR-08).
- The QC defaults are filled in (BR-26).

### Search Records Operation
**What it is:** Finds material sub groups that match the search criteria.
**When it applies:** When the user searches in the search dialog.
**Business outcome:** Uses the centrally configured search definition for the current company. Scope beyond the company, sort order and columns are not defined in this screen's source (Open Question 15).

### Load Record Details Operation
**What it is:** Opens the full record and its child rows.
**When it applies:** When a record is chosen from the search results or by navigation.
**Business outcome:**
- Fills the header, GST, make, QC, UOM and vendor data.
- Ticks the linked warehouse and bin rows.
- Applies branch locking (BR-02).
- Shows the Inactive status from the company links (Open Question 5).

### Validate Record Operation
**What it is:** Checks the record for completeness, format and uniqueness before saving.
**When it applies:** When Save is clicked, in detail or Fast Entry mode.
**Business outcome:** The checks run in this order:
1. Full code unique in the company (MSG-01)
2. Name unique in the group (MSG-02)
3. Category Name (MSG-03, cursor to Category Name)
4. Group Name (MSG-04, cursor to Group Name)
5. Code (MSG-05, cursor to Code)
6. Sub Group Name (MSG-06, cursor to Sub Group Name)
7. QC rows (MSG-07 to MSG-11, focus to the QC cell)
8. Vendor locations (MSG-12, focus to the Vendor Detail cell)

In Fast Entry mode, MSG-01 to MSG-04 and MSG-06 are written to the row's Remarks instead, while MSG-05 still appears as a pop-up (BR-29).

### Save Main Record Operation
**What it is:** Saves the header record and sets up company links.
**When it applies:** After validation passes during Save.
**Business outcome:**
- Saves the record as approved (BR-22).
- For a new record, creates the company links (BR-11).
- For an existing record, clears its child rows (BR-20) and rebuilds the item full codes (BR-28).
- On failure, the whole save is reversed and MSG-25 appears. On success, MSG-17 appears once the child rows are saved.

### Save Child Details Operation
**What it is:** Saves the child rows as part of the same save.
**When it applies:** During Save when child data is present.
**Business outcome:** Rows are saved in this order:
1. Ticked warehouse rows
2. Make rows
3. QC rows
4. Unit rows
5. Vendor rows
6. Ticked bin rows, only if BIN Applicable is ticked

For existing records the rows replace the previous set in full (BR-20). Any failure reverses the whole save (BR-21, MSG-25).

### Delete Record Operation
**What it is:** Removes the material sub group and its child details.
**When it applies:** After the delete prompt is confirmed.
**Business outcome:** Runs no usage check. It removes the header, company links and every detail link together (BR-13), then returns success (MSG-21) or the database's reason for refusal (MSG-20).

## 9. Modular Architecture Notes
*This section highlights business-relevant architectural principles governing the Material Sub Group Master screen.*

### Modular Business Architecture
**What it is:** The separation between the screen, the business logic and the stored data.
**When it applies:** For every action taken on the Material Sub Group Master screen.
**Business outcome:** Detail-card entries, Fast Entry rows and imported rows all go through the same validation and save path, so the same rules apply to all of them (BR-29).

### Enterprise Standardisation and Component Reuse
**What it is:** The screen reuses:
- The shared quality control component for QC Detail
- The shared search dialog with a configured search definition
- Masters maintained elsewhere: categories, groups, units, makes, vendors, warehouses, bin cards, QC parameters and tax codes

**When it applies:** When selection lists load, when QC parameters are maintained, and when searching.
**Business outcome:** Quality rules and lists behave the same wherever the shared component is used (Inferred), and classifications stay consistent across modules.

### Centralised Transactional Safety
**What it is:** The all-or-nothing handling of multi-record changes.
**When it applies:** During save and delete.
**Business outcome:** The header, company links, warehouse, make, QC, unit, vendor and bin rows, and the item full-code refresh are always committed or reversed together (BR-13, BR-21).

## 10. Use Cases
*This section outlines standard operational scenarios executed on the Material Sub Group Master screen.*

### Single Material Sub Group Creation
**Actor:** Master Data Clerk (Head Office)
**Flow:**
1. Clicks New.
2. Chooses Category Name, then Group Name (BR-06).
3. Accepts or changes the suggested Code (BR-07).
4. Enters Sub Group Name (BR-03).
5. Optionally sets GST Category, HSN/SAC Code, BIN Applicable and Dispatch -ve Tolerance.
6. Clicks Save and confirms MSG-16.

**Result:** The record is saved as approved and available in all companies (BR-11, BR-22), MSG-17 appears and the card resets. If a check fails, the save stops with MSG-01 to MSG-12 and the cursor moves to the field concerned.

### Bulk Entry Through Fast Entry
**Actor:** Master Data Clerk (Head Office)
**Flow:**
1. Clicks the Sub Group Code hyperlink.
2. Types rows, or clicks Import and confirms MSG-24.
3. Clicks Save and confirms.

**Result:** Each row with a Category Name is validated and saved as a separate new sub group (BR-29). Remarks shows "Successfully Created." (MSG-22) or the reason for failure, and MSG-23 appears at the end. Each row inherits its Group's QC parameters (BR-26).

### Maintain Warehouse Detail
**Actor:** Stores Master Data Specialist (Head Office)
**Flow:** Opens a sub group, ticks or unticks rows on the Warehouse Detail tab, and saves.
**Result:** The ticked combinations replace the previous set (BR-14, BR-20) and MSG-17 appears. No selection is compulsory.

### Maintain Make Detail
**Actor:** Purchasing Master Data Specialist (Head Office)
**Flow:** Opens a sub group, adds or removes makes on the Make Detail tab, and saves.
**Result:** The makes replace the previous set (BR-20). A duplicate make is blocked when entered (MSG-13).

### Maintain UOM
**Actor:** Master Data Clerk (Head Office)
**Flow:** Opens a sub group, picks a Unit Name for each unit type needed on the UOM tab, and saves.
**Result:** Rows with both a unit type and a unit replace the previous set (BR-16, BR-20).

### Maintain Vendor Detail
**Actor:** Purchasing Master Data Specialist (Head Office)
**Flow:** Opens a sub group, adds vendors on the Vendor Detail tab, confirms or chooses a Location for each, and saves.
**Result:** The vendor locations replace the previous set (BR-20). A missing location (MSG-12) or a duplicate pair (MSG-14) stops the save.

### Maintain Bin Detail
**Actor:** Stores Master Data Specialist (Head Office)
**Flow:** Opens a sub group, ticks BIN Applicable, ticks bin cards on the Bin Detail tab (or uses the header tick box), and saves.
**Result:** The ticked bins replace the previous links. If BIN Applicable is unticked when saving, all bin links are removed (BR-18, BR-20).

### Maintain QC Detail
**Actor:** Master Data Clerk (Head Office)
**Flow:** Opens a sub group, chooses or changes Group Name, and saves.
**Result:** The group's QC parameters replace the sub group's settings (BR-26) and are saved. If an inherited row is incomplete, MSG-07 to MSG-11 stop the save, even though the QC Detail tab is hidden (Open Question 3).

### Search and Modify Material Sub Group
**Actor:** Master Data Clerk (Head Office), and Branch User
**Flow:** Clicks Search, chooses a sub group, edits fields or details, and clicks Save.
**Result:**
- At Head Office, the changes are saved (MSG-17), the child rows are replaced (BR-20) and the item full codes are rebuilt (BR-28).
- At a branch, the loaded record is locked for viewing apart from the Bin Detail grid (BR-02).

### Material Sub Group Deletion
**Actor:** Master Data Clerk (Head Office)
**Flow:** Opens a sub group, clicks Delete and confirms MSG-19.
**Result:**
- On success, the sub group and all its links are removed (MSG-21) and the card resets (BR-13).
- If the database refuses, for example because items still use it (Inferred), MSG-20 shows the reason and nothing is removed.
- Branch users receive MSG-18 (BR-01).

### Duplicate Prevention Handling
**Actor:** Data Entry Operator (Head Office)
**Flow:** The user tries to save a sub group whose full code already exists in the company, or whose name already exists in the same group.
**Result:** The save is blocked with MSG-01 (BR-09) or MSG-02 (BR-10). These server-side checks show a message without moving the cursor. In Fast Entry, the message goes to Remarks.

## 11. Business Rules
*This section establishes the authoritative business rules governing the Material Sub Group Master screen.*

- **BR-01 (Head Office Deletion Authority):** Only Head Office users may delete a material sub group. Branch users are refused with MSG-18.
- **BR-02 (Branch View-Only Retrieval):** At a branch, a loaded record is locked for viewing and Inactive is disabled. The Bin Detail grid stays editable. A new record at a branch is not locked, and Save is not restricted by company.
- **BR-03 (Mandatory Header Fields):** Category Name, Group Name, Code and Sub Group Name are required (MSG-03, MSG-04, MSG-05, MSG-06).
- **BR-04 (Optional Tax Classification):** GST Category and HSN/SAC Code are optional.
- **BR-05 (Field Length and Format Limits):** Code allows up to 2 characters and Sub Group Name up to 100. Both are trimmed of surrounding spaces. Dispatch -ve Tolerance accepts a number with two decimals, up to 6 characters.
- **BR-06 (Category-Group Dependency):** The Group list shows only groups of the chosen category. Changing the category clears the group, and changing the group clears and re-suggests the Code.
- **BR-07 (Code Suggestion):** When a Group is chosen, the suggested Code is the highest numeric code already used in that group plus one, shown as two digits. The user may overwrite it.
- **BR-08 (Full Sub Group Code Composition):** The full Sub Group Code is the Category code, the Group code and the Code joined together. It is calculated automatically and is read-only.
- **BR-09 (Full Code Uniqueness):** The full Sub Group Code must be unique among sub groups available in the current company (MSG-01).
- **BR-10 (Name Uniqueness within Group):** Sub Group Name must be unique within its group. The same name may be used under different groups (MSG-02).
- **BR-11 (Enterprise-Wide Availability):** A new sub group is linked to every company as active. The links are not changed on modification.
- **BR-12 (Company-Scoped Selection Lists):** Category, make, unit, vendor and location lists show records active in the current company. Make, unit, vendor and location lists also show records already linked to the open sub group.
- **BR-13 (Cascading Deletion):** Deletion removes the header together with its company links and all of these: warehouse, make, QC, unit, vendor, bin and technical grade links. No explicit usage check is made, and a database refusal is reported with MSG-20.
- **BR-14 (Optional Warehouse Selection):** Only ticked Warehouse Detail rows are saved, and selecting at least one is not enforced.
- **BR-15 (Unique Makes):** A make may appear only once per sub group (MSG-13), and its code is filled automatically.
- **BR-16 (One Unit per Unit Type):** The UOM tab has one fixed row per unit type. A row is saved only when both Unit Type and Unit Name are present.
- **BR-17 (Vendor Location Rules):** Each vendor row needs a Location belonging to that vendor (MSG-12). Each vendor and location pair may appear only once (MSG-14). A vendor's only location is filled automatically.
- **BR-18 (Bin Applicability):** The Bin Detail tab follows the BIN Applicable checkbox. Bin links are saved only while it is ticked, and saving with it unticked removes existing bin links.
- **BR-19 (QC Row Completeness):** Each QC row with a parameter needs all of the following, and a parameter may appear only once (MSG-15):
- **BR-20 (Replace-on-Save Details):** Saving an existing sub group removes all its warehouse, make, QC, unit, vendor and bin rows and saves them again from the screen.
  - a non-zero Standard Value (MSG-07)
  - a Tolerance Value (MSG-08)
  - a Deduction Rate (MSG-09)
  - a Deduction Type (MSG-10)
  - Double Deduction From when Deduction Type is Double (MSG-11); it is cleared and locked when Deduction Type is Single
- **BR-21 (Atomic Save):** The header, company links and all child rows are saved as one unit. Any failure reverses the whole save (MSG-25).
- **BR-22 (Automatic Approval):** Every save marks the sub group as approved and records the saving user and time as authoriser. There is no separate approval step.
- **BR-23 (View-Only Inactive):** The Inactive checkbox is always disabled on this screen and only displays the stored status.
- **BR-24 (System-Filled Read-Only Displays):** These are filled automatically and cannot be edited: the full Sub Group Code, the category and group code displays, and the CGST, SGST, IGST and UTGST rate displays.
- **BR-25 (Dispatch Negative Tolerance Display and Default):** Dispatch -ve Tolerance is shown only when the company's sales setting allows it. Zero or blank is stored as not set.
- **BR-26 (Group QC Inheritance):** Choosing a Group replaces the sub group's QC parameters with those defined for that group.
- **BR-27 (Hidden Tolerances Retained):** Receipt Tolerance and Shipment Tolerance are hidden. Stored values are kept on re-save, and new sub groups store zero.
- **BR-28 (Item Code Cascade):** Saving an existing sub group rebuilds the full code of every item in it from the current Category, Group and Sub Group codes plus the item's own code.
- **BR-29 (Fast Entry Row Processing):** In Fast Entry, only rows with a Category Name are processed. Each is validated by the same rules as detail mode and saved as a separate new sub group, with its result written to Remarks.

## 12. Messages
*This section catalogues all user-facing notifications, validation prompts, and error messages generated by the Material Sub Group Master screen.*

- **MSG-01:** Full code already used in the company; *"Duplicate Sub Group Code is not allowed."*; change Code so the full code is unique (BR-09).
- **MSG-02:** Name already used in the group; *"Duplicate Sub Group Name is not allowed."*; enter a different name (BR-10).
- **MSG-03:** Category not chosen; *"Select valid Category Name."*; choose a category (BR-03).
- **MSG-04:** Group not chosen; *"Select valid Group Name."*; choose a group (BR-03).
- **MSG-05:** Code blank; *"Enter Code."*; enter a code of up to 2 characters (BR-03). Shown as a pop-up even in Fast Entry.
- **MSG-06:** Sub Group Name blank; *"Enter Sub Group Name."*; enter the name (BR-03).
- **MSG-07:** QC standard value blank or zero; *"Standard Value can't be empty or zero"*; enter a non-zero standard value (BR-19).
- **MSG-08:** QC tolerance blank; *"Enter Tolerance Value"*; enter a tolerance value (BR-19).
- **MSG-09:** QC deduction rate not chosen; *"Select valid Deduction Rate"*; choose Basic, Prorata or Landed (BR-19).
- **MSG-10:** QC deduction type not chosen; *"Select valid Deduction Type"*; choose Single or Double (BR-19).
- **MSG-11:** Double deduction value blank; *"Enter Double Deduction From"*; enter the value from which double deduction applies (BR-19).
- **MSG-12:** Vendor without location; *"Select valid Location"*; choose a location for the vendor (BR-17).
- **MSG-13:** Make repeated; *"Duplicate Make Name not allowed."*; remove the repeated make (BR-15).
- **MSG-14:** Vendor and location repeated; *"Duplicate Vendor Name and Location not allowed."*; remove the repeated row (BR-17).
- **MSG-15:** QC parameter repeated; *"Duplicate QC Parameter not allowed."*; remove the repeated parameter (BR-19).
- **MSG-16:** Save confirmation; standard application message, wording not in this screen's source; confirm to save.
- **MSG-17:** Save successful; standard application message, wording not in this screen's source; acknowledge; the card resets.
- **MSG-18:** Delete attempted at a branch; *"Permission denied to delete Material Sub Group."*; delete from Head Office (BR-01).
- **MSG-19:** Delete confirmation; standard application message, wording not in this screen's source; confirm to delete.
- **MSG-20:** Delete refused by the database; the database's reason is shown as a delete validation notice; resolve the dependency and retry (BR-13).
- **MSG-21:** Delete successful; standard application message, wording not in this screen's source; acknowledge; the card resets.
- **MSG-22:** Fast Entry row saved; *"Successfully Created."* (written in Remarks); no action needed (BR-29).
- **MSG-23:** Fast Entry save finished; *"Refer remarks for saved status."*; review Remarks for each row (BR-29).
- **MSG-24:** Import confirmation; *"Your excel should consists of sheet with name MSGM. Do you want to continue?"*; confirm only if the workbook has a sheet with that name.
- **MSG-25:** Save failed during saving; standard application error message showing the reason returned, wording not in this screen's source; correct the cause and save again (BR-21).

## 13. Limitations and Assumptions
*This section identifies functional constraints and operational assumptions governing the Material Sub Group Master screen.*

### Two-Character Code Capacity
**What it is:** Code is limited to 2 characters, and the suggested code counts upwards from the highest numeric code (BR-05, BR-07).
**When it applies:** Groups with many sub groups.
**Business outcome:** A group can hold at most 99 numeric codes. Beyond that, the suggestion would exceed the permitted length (Open Question 7).

### Scope of Uniqueness
**What it is:** Full codes are unique per company (BR-09), and names are unique per group (BR-10).
**When it applies:** Creation and modification.
**Business outcome:** The same name may exist under different groups. Because every sub group is linked to every company (BR-11), the code check works enterprise-wide in practice (Inferred).

### Hidden QC Detail Tab
**What it is:** QC parameters are inherited, checked and saved, but the QC Detail tab is hidden (BR-19, BR-26).
**When it applies:** Every save where the Group has QC parameters.
**Business outcome:** Users cannot review or correct QC values here, and a QC check failure points to a tab they cannot see. This may be a defect (Open Question 3).

### Hidden Receipt and Shipment Tolerances
**What it is:** These fields are hidden (BR-27).
**When it applies:** Always.
**Business outcome:** They cannot be maintained on this screen (Open Question 11).

### Full Replacement of Child Rows
**What it is:** Every save of an existing record rewrites all child rows (BR-20). Changing the Group also replaces the QC settings (BR-26).
**When it applies:** Every modification.
**Business outcome:** The screen must hold the complete intended detail set when Save is clicked.

### Branch Authority Gap
**What it is:** Only deletion is restricted to Head Office (BR-01, BR-02).
**When it applies:** Branch users who start a new record, or who save a loaded record.
**Business outcome:** Branch users may be able to create sub groups and change bin links. This may be a defect (Open Question 2).

### Deletion Without Usage Check
**What it is:** Deletion relies on the database to refuse when the sub group is in use (BR-13).
**When it applies:** Deleting a sub group that items or transactions still use (Inferred).
**Business outcome:** The user sees the database's wording rather than a business message (Open Question 4).

### Fast Entry Scope and Result Reporting
**What it is:** Fast Entry captures only Category, Group, Code and Sub Group Name (BR-29).
**When it applies:** Bulk creation.
**Business outcome:**
- Tax, warehouse, make, unit, vendor and bin details must be added afterwards in detail mode.
- If a row fails while saving, rather than during validation, an error appears but Remarks may still say "Successfully Created.". This may be a defect (Open Question 6).
- The Fast Entry container sits within the GST Detail tab area in the layout (Open Question 13).

### Inactive Status Not Maintainable
**What it is:** Inactive is display-only (BR-23). The status shown on loading is not explicitly taken from the current company.
**When it applies:** Retiring a sub group, or reading its status.
**Business outcome:** Retirement must be done outside this screen (Inferred). The status shown may belong to another company (Open Question 5).

### Bin Detail Visibility and Scope
**What it is:** Bin Detail follows BIN Applicable (BR-18). However, it is visible before the checkbox is first used, and it lists bin cards from all warehouses.
**When it applies:** When the screen is first opened, and during bin assignment.
**Business outcome:** Users may see the bin list for a non-bin family, and bins of other companies (Open Question 10).

### Centralised Authority and Connectivity Assumptions
**What it is:** The screen assumes one Head Office governs deletion, and that all companies share one live database.
**When it applies:** Deletion (BR-01) and company availability (BR-11).
**Business outcome:** New sub groups are immediately available in every company.

## 14. Open Questions
*This section records unresolved business and functional items requiring formal confirmation from the business owner.*

1. **Screen Title:** The form's design-time title is its internal name. Please confirm that users see "Material Sub Group Master" as the window title. Suggested Business Owner: ERP Product Owner.
2. **Branch Creation and Modification Rights:** Only deletion is restricted to Head Office. A branch user can start a new record with all fields unlocked and save it, and Save is not blocked for loaded records, whose Bin Detail grid stays editable. Should creation and modification also be Head Office only? Suggested Business Owner: Enterprise Master Data Governance Lead.
3. **Hidden QC Detail Tab:** The tab is hidden, yet the Group's QC parameters are still inherited, checked and saved. Is hiding intended, and should users be able to review or adjust the sub group's QC settings? Suggested Business Owner: Quality Assurance Head.
4. **Deletion Usage Check:** Deletion makes no explicit check for items, stock or transactions that use the sub group, and relies on the database to refuse. Should an explicit check with a business message be added? Suggested Business Owner: Inventory Master Data Lead.
5. **Displayed Inactive Status:** On loading, the active status is read from the company links without restricting it to the current company. Which company's status should the Inactive box show? Suggested Business Owner: Enterprise Master Data Governance Lead.
6. **Fast Entry Result Accuracy:** If a row fails while saving rather than during validation, an error appears but Remarks may still read "Successfully Created.". Should the failure be written to Remarks? Suggested Business Owner: ERP Product Owner.
7. **Code Capacity Beyond 99:** What should happen when a group already has code 99 and the suggested code would exceed two characters? Suggested Business Owner: Inventory Master Data Lead.
8. **Eligible Vendor Types:** The Vendor Name list is limited to two specific vendor types, for example suppliers and manufacturer-suppliers (Inferred). Which vendor classifications should be eligible? Suggested Business Owner: Procurement Head.
9. **Mandatory Warehouse Selection:** A check that once required at least one warehouse is now disabled. Should at least one warehouse be mandatory? Suggested Business Owner: Stores and Warehouse Operations Lead.
10. **Bin Detail Visibility and Scope:** The Bin Detail tab may be visible on first opening before BIN Applicable is ticked. The bin list also shows bin cards of all warehouses with no company filter. Are both intended? Suggested Business Owner: Stores and Warehouse Operations Lead.
11. **Receipt and Shipment Tolerances:** These fields are hidden but still stored. Are they retired, or should they be shown again? Suggested Business Owner: Procurement and Sales Operations Leads.
12. **Group List Consistency:** In detail mode the Group list shows all groups of the category. In Fast Entry it shows only authorised groups active in the current company. Should detail mode apply the same restriction? Suggested Business Owner: Inventory Master Data Lead.
13. **Fast Entry Container Placement:** In the layout, the Fast Entry container sits within the GST Detail tab area. Does it display correctly when another tab is selected? Suggested Business Owner: ERP Product Owner.
14. **Standard Value2 Retention:** The QC grid shows Standard Value2, but this screen does not save it. Should it be stored for sub groups? Suggested Business Owner: Quality Assurance Head.
15. **Search Definition Content:** The search list comes from a central configuration whose columns, sort order and inclusion of inactive records are not defined in this screen's source. Please confirm the intended search content. Suggested Business Owner: ERP Product Owner.
16. **Use of Sub Group Defaults Downstream (Inferred):** Several purchasing, receipt, storage, inspection and dispatch processes are assumed to use the sub group's makes, vendors, units, warehouses, bins, QC parameters, tax classification and dispatch tolerance. Please confirm which processes enforce them and which only suggest them. Suggested Business Owner: Supply Chain Process Owner.
17. **Meaning of Unit Types and Dispatch -ve Tolerance (Inferred):** Please confirm the business meaning of each unit type on the UOM tab, and of Dispatch -ve Tolerance. Suggested Business Owner: Inventory Master Data Lead.
