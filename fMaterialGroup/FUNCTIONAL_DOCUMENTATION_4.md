# Material Group Screen: Functional Documentation

## Overview
Module: Material Group screen
Section: Overview

The Material Group screen organizes enterprise inventory by managing intermediate classifications that connect broad Material Categories with granular Material Sub-Groups. In large supply chain environments, materials share commercial behaviors, accounting classifications, and testing requirements that cannot be managed efficiently at the individual item level. The Material Group screen resolves this challenge by providing central governance over material families, assigning standardized inspection defaults, and maintaining uniform identification coding across all operating companies.

The scope of this screen covers authoring individual material groups, assigning descriptive titles, calculating standardized codes, configuring default quality inspection standards, performing bulk spreadsheet importing, and distributing active availability across all registered company entities. The screen does not cover the initial creation of parent Material Categories, the creation of specific item stock keeping units, or the recording of physical quality inspection results during warehouse receiving.

Key business terms include Material Group, which represents an intermediate family of related items under a parent Material Category. A QC Group is a quality template bundling standardized testing specifications. A QC Parameter is a measurable physical or chemical property evaluated during material receipt verification. Fast Entry Mode is an alternative screen arrangement designed for high-volume tabular input or spreadsheet ingestion. Composite Group Code is a structured identifier combining the category code with the group code.

This screen depends upstream upon active Material Categories, operating enterprise companies, and central quality parameter definitions. Downstream, the Material Sub-Group Master and Item Master depend on an active Material Group for hierarchy assignment, item code generation, and quality default inheritance.

## Form
Module: Material Group screen
Section: Form

**Standard detail card:** The primary card provides single-record maintenance. Category Name is a mandatory dropdown selection displaying active material categories, where choosing a category filters options and automatically populates Category Code while triggering sequential code calculation under BR-04; leaving it blank causes MSG-01 upon saving. Category Code is a read-only field displaying the system code of the selected category. Code is a mandatory two-character alphanumeric entry field that defaults to the next calculated sequential number, allows manual modification conforming to BR-03 and BR-07, and triggers MSG-02 or MSG-05 if violated. Group Code displays the combined composite code under BR-05 and acts as a clickable link that opens Fast Entry Mode. Group Name is a mandatory text entry accepting up to 100 characters under BR-06 and BR-08, triggering MSG-03 or MSG-04 if violated. Inactive is a locked checkbox that defaults to active status for all newly saved groups under BR-09.

**Fast Entry grid area:** Clicking the Group Code link opens a high-capacity data entry grid for bulk operations. The grid contains Category Name as a dropdown list, Code accepting two alphanumeric characters, Group Name accepting text descriptions, and Remarks as a read-only operational field displaying confirmation or specific validation feedback for each processed line. The Switch back to detail mode link closes the grid and restores the standard card.

**Action options:** The top toolbar provides New to clear the card and focus Category Name, Save to execute validation and commit data displaying MSG-08, Search to launch a catalog lookup window, Delete to remove unreferenced groups under BR-11, and Navigation to cycle through existing records. Within the fast entry area, the Import button prompts with MSG-06 and reads external spreadsheets conforming to BR-13, reporting results under MSG-07.

## Data Layer
Module: Material Group screen
Section: Data Layer

**Captured business information:** The Material Group screen captures master classification records containing parent category associations, two-character group codes, descriptive names, creation audit dates, authorizing user credentials, and active document state. Connected directly to each group record are enterprise company availability profiles and default quality inspection profiles. The parent category establishes classification boundaries, company profiles establish local subsidiary availability, and quality profiles bind baseline inspection specifications to the material family.

**Information lifecycle:** The business lifecycle comprises creation, viewing, modification, and deletion. Creation introduces a new Material Group under Head Office governance per BR-01, validating entries and immediately generating active company availability mappings across all registered enterprise subsidiaries under BR-09. Viewing and searching allow authorized users across all enterprise locations to locate and inspect groups, but screen fields are locked in read-only mode for branch users under BR-01.

**Modification and removal restrictions:** Modification permits Head Office users to update group titles or codes. Updating a group code automatically triggers full item code recalculation across all linked Item Master records under BR-10 to maintain identification integrity. Deletion is restricted to Head Office users under BR-01 and succeeds only when a group has never been referenced by child Material Sub-Groups, Item Masters, or inventory transactions under BR-11; attempting to delete an active group halts the transaction and presents MSG-09.

## QC Group Control
Module: Material Group screen
Section: QC Group Control

**Quality Control grouping concept:** A QC Group represents a reusable collection of standardized testing specifications. Attaching a QC Group to a Material Group establishes corporate quality baselines for an entire family of materials. Child Material Sub-Groups created beneath the group automatically inherit these parameters, ensuring consistent receiving standards and eliminating redundant manual data entry across individual item records.

**Quality parameters and tolerances:** Users select a QC Group template or individual QC Parameters representing measurable physical or chemical attributes such as moisture, purity, or strength. For each active parameter, the user enters a mandatory standard target value greater than zero and an allowable numerical tolerance limit under BR-12. Units of measurement and tolerance types are resolved automatically from central quality master catalogs. Entering a standard value of zero triggers MSG-10, omitting tolerance triggers MSG-11, and adding duplicate parameters triggers MSG-15.

**Commercial deduction dependencies:** The quality component provides automated commercial settlement logic when receipts deviate beyond tolerance. Users specify whether deductions apply below the lower tolerance limit or above the upper tolerance limit, and whether penalties adjust invoice pricing or reduce accepted physical quantity. Valuation rates include basic, prorata, or landed cost under MSG-12. Users select single deduction or double deduction under MSG-13; selecting double deduction activates the double deduction threshold field, requiring a numerical deviation point under BR-12 and triggering MSG-14 if omitted. An enterprise-level setting can suppress deduction fields where automated penalties are not practiced.

## Business Operations
Module: Material Group screen
Section: Business Operations

**Filling selection lists:** This operation runs upon opening or resetting the Material Group screen. It loads authorized active Material Categories, sets up the fast entry grid structure, and checks global deduction visibility settings, displaying active categories in dropdown selections.

**Calculating dependent sequential code:** This operation executes immediately when a user selects a Material Category. It identifies the highest existing numeric group code in that category and suggests the next sequential two-digit code under BR-04, populating the Code field.

**Searching existing records:** This operation executes when clicking the Search toolbar action. It queries registered groups matching user criteria for the current operating company and opens a lookup dialog displaying matching records.

**Loading existing records:** This operation executes when a user selects a record from search results. It populates category details, codes, names, and linked quality parameters onto the Material Group screen, locking fields in read-only mode if opened at a branch company under BR-01.

**Validating before saving:** This operation executes when the user initiates a save action. It verifies category selection, code length, descriptive name presence, and category-level uniqueness against BR-02, BR-03, BR-06, BR-07, and BR-08, proceeding silently on success or halting with MSG-01, MSG-02, MSG-03, MSG-04, or MSG-05.

**Saving records and quality parameters:** This operation executes after successful validation. It commits the group header, generates active multi-company availability mappings under BR-09, recalculates full item codes for linked items under BR-10, saves linked quality parameters under BR-12, and displays confirmation MSG-08.

**Deleting existing records:** This operation executes when the user confirms a deletion prompt. It checks referential integrity under BR-11, completely removes unreferenced group headers, company mappings, and quality profiles, or halts and displays MSG-09 if dependent records exist.

## Rules and Messages
Module: Material Group screen
Section: Rules and Messages

**Business rules:**
BR-01: Only users logged into the Head Office company can create, edit, or delete records; operational branch users have read-only access.
BR-02: Category selection is mandatory; saving without an active category is blocked.
BR-03: Group Code must consist of exactly two alphanumeric characters; invalid length is blocked.
BR-04: The system automatically suggests the next sequential numeric code by adding one to the highest existing code in the category.
BR-05: Group Code displays as a composite key prefixed by the parent Category Code.
BR-06: Group Name must be unique within the parent category for the company; duplicates are blocked.
BR-07: Group Code must be unique within the parent category across the enterprise; duplicates are blocked.
BR-08: Group Name is mandatory up to 100 characters; empty names are blocked.
BR-09: Saving at Head Office automatically creates active operational mappings across all registered operating companies.
BR-10: Modifying an existing group code automatically recalculates the full composite code of all linked Item Master records.
BR-11: A Material Group cannot be deleted if referenced by child sub-groups, items, or inventory history; deletion is blocked.
BR-12: Quality parameters require a non-zero standard target value, mandatory tolerance limit, and an escalation threshold if double deduction is chosen.
BR-13: Bulk spreadsheet imports require an Excel file with an active sheet named MMIG and designated column headers; non-conforming files are rejected.

**Messages:**
MSG-01: Triggered when category is missing; exact text "Select valid Category Name."; user must select an active category.
MSG-02: Triggered when code length is not two; exact text "Code must be 2 digit."; user must enter two characters.
MSG-03: Triggered when name is blank; exact text "Enter Group Name."; user must type a group name.
MSG-04: Triggered on duplicate name; exact text "Duplicate Group Name is not allowed."; user must enter a unique name.
MSG-05: Triggered on duplicate code; exact text "Duplicate Group Code is not allowed."; user must enter an unassigned code.
MSG-06: Triggered clicking Import; exact text "Your excel should consists of sheet with name MMIG. Do you want to continue?"; user confirms sheet name.
MSG-07: Triggered after batch saving; exact text "Refer Remarks for data saved status."; user reviews grid Remarks.
MSG-08: Triggered on successful save; exact text "Record Saved Successfully."; user acknowledges confirmation.
MSG-09: Triggered when deletion is blocked; text indicates dependent records exist; user must retain the record for audit integrity.
MSG-10: Triggered when quality target is zero; exact text "Standard Value can't be empty or zero"; user enters a valid target.
MSG-11: Triggered when tolerance is blank; exact text "Enter Tolerance Value"; user enters an allowable variance.
MSG-12: Triggered when deduction rate is missing; exact text "Select valid Deduction Rate"; user selects valuation basis.
MSG-13: Triggered when deduction type is missing; exact text "Select valid Deduction Type"; user selects deduction type.
MSG-14: Triggered when double threshold is missing; exact text "Enter Double Deduction From"; user enters numerical threshold.
MSG-15: Triggered on duplicate parameter; exact text "Duplicate QC Parameter not allowed."; user removes duplicate line.

## Use Cases
Module: Material Group screen
Section: Use Cases

**Single group creation:** Performed by Central Master Data Clerk. The user logs in at Head Office under BR-01, navigates to the Material Group screen, clicks New, selects a Category Name, reviews the code suggested under BR-04, enters a Group Name, and clicks Save. The system validates entries, persists the master record, creates operational mappings across all operating companies under BR-09, displays confirmation MSG-08, and clears the card for subsequent entry.

**Search and record modification:** Performed by Central Master Data Clerk. The user accesses the Material Group screen, clicks Search, enters search criteria, selects an existing record, modifies the Group Name or Code, and clicks Save. The system updates the central record, recalculates the full composite code of all linked Item Master records under BR-10, and presents confirmation MSG-08.

**Unreferenced group deletion:** Performed by Central Master Data Clerk. The user retrieves an obsolete group on the Material Group screen, clicks Delete, and confirms the prompt. Because no child sub-groups or inventory movements reference the group under BR-11, the system purges the group header, company mappings, and quality profiles, displaying deletion confirmation.

**Quality parameter assignment:** Performed by Quality Assurance Manager. The user loads a Material Group on the Material Group screen, selects a QC Group template, confirms standard targets and tolerance limits under BR-12, and clicks Save. Quality parameters bind to the group and cascade automatically to child Material Sub-Groups.

**Validation failure remediation:** Performed by Central Master Data Clerk. The user clicks Save on the Material Group screen with an unselected category, single-character code, or empty name. The system halts the save, sets focus to the invalid field, and presents MSG-01, MSG-02, or MSG-03. The user corrects the input to complete saving.

**Duplicate entry rejection:** Performed by Central Master Data Clerk. The user enters a code or name already assigned within the selected category on the Material Group screen and clicks Save. The system blocks the save under BR-06 or BR-07, displaying MSG-04 for duplicate name or MSG-05 for duplicate code. The user enters distinct values to proceed.
