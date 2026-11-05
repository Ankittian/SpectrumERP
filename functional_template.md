<!--
=====================================================================
FUNCTIONAL DOCUMENTATION TEMPLATE — GENERIC (applies to every form)
=====================================================================

HOW TO USE THIS TEMPLATE (instructions for the AI author — delete all
HTML comments from the final document)

0. Target Traversal and Output File Naming
   - Systematically traverse the contents of the target WinForm folder
     before drafting documentation. Inspect all bundled components:
     * Form/ (UI code, designer files .Designer.cs/.vb, event handlers,
       validations, toolbar bindings, dialogs).
     * DataLayer/ (DT/DA/DAO classes, parameter mappings, SP calls).
     * StoredProcedures/ (SQL scripts, tables read/written, checks).
     * Embedded user controls, helper classes, child grids.
     * CONTENTS.md or manifest files if present.
   - Generate functional documentation separately for each WinForm.
   - Save the completed document inside a dedicated directory named
     "functional documentations" (e.g. SpectrumERP/functional documentations/)
     using the exact file naming convention:
     Functional_Doc_<winform name>.md
     (Example: functional documentations/Functional_Doc_fMaterialGroup.md).

1. Source of truth
   - Read the form bundle before writing: designer file (controls, labels,
     grids, mandatory-field lists), form code (event handlers, validations,
     messages, IMDIFunctions implementations such as Save/LoadData/
     FillValues/Delete), DT/DA/DAO classes (which SP each action calls),
     the stored procedures (what they read, write, check and return), and
     any embedded user controls.
   - Document ONLY behaviour that exists in the source. Never copy content
     from another form's document or from the examples in this template.
   - If something is deduced rather than directly visible in code, append
     "(Inferred)". If a message's wording is not in this form's source
     (e.g. a shared framework message), write "standard application
     message, wording not in this screen's source".
   - Where the code contradicts its own labels/messages, or something looks
     like a defect, state it plainly in Section 13.

2. Placeholders
   - {{WinFormName}}  technical name of the WinForm / folder (e.g. fMaterialGroup).
                      Output file: functional documentations/Functional_Doc_{{WinFormName}}.md
   - {{ScreenName}}   business name of the screen (e.g. from the window
                      caption), WITHOUT the word "Screen".
   - {{Entity}}       the business object the screen maintains (singular).
   - {{Entities}}     plural of {{Entity}}.
   - {{...}}          any other placeholder: replace with form-specific text.
   - Repeatable blocks are marked [REPEAT]. Emit one block per item found.
   - Optional blocks are marked [IF ...]. Omit the whole block (heading
     included) when the condition is not met in the source. Do not write
     "Not applicable" headings.

3. Fixed structure
   - Keep all 13 numbered "##" sections, in this order, with these exact
     titles. Keep the italic one-line intro under each "##" heading.
   - "###" headings inside a section are form-specific; name them after
     what the form actually has.
   - Every "###" item in Sections 2–9 and 13 uses the same three labels:
       **What it is:** / **When it applies:** / **Business outcome:**
     Section 10 uses **Actor:** / **Flow:** / **Result:**.
   - A label's value may be a single sentence or a short bullet list when
     it covers several distinct points.

4. IDs and cross-references
   - Business rules: BR-01, BR-02, … numbered in Section 11 in the order
     the rules are first meaningful to a user (authority, mandatory
     fields, formats, uniqueness, automatic values, distribution,
     deletion, child rows, special modes).
   - Messages: MSG-01, MSG-02, … numbered in Section 12.
   - Every BR / MSG referenced anywhere must exist in Sections 11 / 12,
     and every BR / MSG defined there should be referenced at least once
     elsewhere. Every message entry names the BR it enforces, if any.

5. Writing style
   - Business language for a functional reader: describe what the user
     sees and what the business gets, not class or variable names.
     SP / table names are not used in Sections 1–8 headings or text;
     describe the operation in business terms instead.
   - Present tense, active voice, short sentences. No marketing tone.
   - Use the exact on-screen label text for fields, buttons and links.
   - Quote message text exactly as in the source, in italics and quotes,
     including original spelling.
=====================================================================
-->

# {{ScreenName}} Screen: Functional Documentation

## 1. Summary
*This section provides an executive overview of the {{ScreenName}} screen and its role in {{business area / module}}.*

<!-- One paragraph, 4–7 sentences. Cover: what the screen maintains or
processes, the business problem it solves, the key things it captures or
controls, who governs it (e.g. central vs. branch), and who benefits
downstream. No BR/MSG references here. -->
{{Executive summary paragraph.}}

## 2. Purpose and Scope
*This section outlines the business rationale for the {{ScreenName}} screen and establishes its operational boundaries within the enterprise.*

### Business Purpose of {{Entities}}
**What it is:** {{What the screen establishes or manages, in business terms.}}
**When it applies:** {{The business event that leads a user to this screen.}}
**Business outcome:** {{The business problem prevented or value delivered.}}

### In-Scope Functional Capabilities
**What it is:** The functional scope covered directly by the {{ScreenName}} screen.
**When it applies:** {{List the user activities the screen supports, e.g. creation, bulk entry, import, search, modification, child-detail maintenance, deletion — only those present.}}
**Business outcome:** {{The data users can maintain and the controls the screen enforces.}}

### Out-of-Scope Capabilities
**What it is:** Business activities related to {{Entities}} that are not performed on the {{ScreenName}} screen.
**When it applies:** {{Related needs a user might expect here but which the screen does not handle.}}
**Business outcome:** {{Where those needs are handled (name the screen or area if known; otherwise mark (Inferred)).}}

## 3. Business Glossary
*This section defines standard business terminology used on and around the {{ScreenName}} screen.*

<!-- [REPEAT] One block per business term a functional reader needs:
the entity itself, its key attributes/codes, related master entities,
child-detail concepts, statuses, and special modes (e.g. Fast Entry,
Import) — only those present on this form. -->
### {{Term}}
**What it is:** {{Plain-language definition.}}
**When it applies:** {{Where/when the term is used on or around this screen; cite BR-xx if a rule governs it.}}
**Business outcome:** {{Why the term matters to the business.}}

## 4. Prerequisites and Dependencies
*This section identifies upstream operational requirements and downstream dependencies associated with the {{ScreenName}} screen.*

<!-- [REPEAT] Upstream: every master/list/setting the screen reads that
must exist before use (dropdown sources, lookup masters, company
structure, configuration flags).
[REPEAT] Downstream: every screen, process or document that relies on
data this screen writes (derived from tables it writes and who else
reads them). Prefix headings with "Downstream" for those. -->
### {{Upstream Dependency Name}}
**What it is:** {{What the prerequisite is.}}
**When it applies:** {{When it must be in place; cite BR-xx where relevant.}}
**Business outcome:** {{What it supplies to this screen.}}

### Downstream {{Dependent Area}} Reliance
**What it is:** {{The dependent screen, process or document.}}
**When it applies:** {{When it uses this screen's data.}}
**Business outcome:** {{How it depends on the data maintained here.}}

## 5. Form (Screen)
*This section details the interactive user interface areas, data entry fields, and action buttons of the {{ScreenName}} screen.*

<!-- Order: (a) layout areas/panels, (b) header fields in on-screen
order, (c) grids and embedded controls, (d) alternate modes and their
links, (e) toolbar actions. Include every user-visible control; group
trivial read-only labels with their field. State for each field:
mandatory or optional, editable or read-only, data type/length limits,
default or auto-filled values, list source, and which BR/MSG apply. -->

### {{Main Layout Area Name}}
**What it is:** {{Description of the default workspace.}}
**When it applies:** {{When it is shown.}}
**Business outcome:** {{What it lets the user do.}}

<!-- [REPEAT] one block per field / control -->
### {{On-Screen Label}} Field
**What it is:** {{Control type (text box, dropdown, checkbox, date, read-only display, hyperlink …), mandatory/optional, limits; cite BR-xx.}}
**When it applies:** {{When it is visible/enabled; conditions that lock or hide it.}}
**Business outcome:** {{What it captures or displays, automatic behaviour (trimming, defaulting, code generation), and messages triggered (MSG-xx).}}

<!-- [IF the form has grids / embedded user controls] [REPEAT] -->
### {{Grid or Control Name}}
**What it is:** {{Purpose of the grid/control.}}
**When it applies:** {{Where and when it is visible; note if hidden, collapsed or positioned off-screen.}}
**Business outcome:** {{Columns captured and the rules enforced on rows; cite BR-xx.}}

<!-- [IF the form has an alternate entry mode, e.g. Fast Entry / grid mode] -->
### {{Alternate Mode Name}} Grid Container
**What it is:** {{Columns provided.}}
**When it applies:** {{How the user opens it.}}
**Business outcome:** {{Entry behaviour, e.g. automatic new rows, Remarks column.}}

### {{Return Link Label}} Action
**What it is:** {{The link/button that returns to the main layout and where it sits.}}
**When it applies:** {{When it is visible.}}
**Business outcome:** {{What happens to unsaved rows.}}

<!-- [IF the form supports Import] -->
### Import Action
**What it is:** {{What can be imported and in what format.}}
**When it applies:** {{When it is available.}}
**Business outcome:** {{How imported rows are processed; cite BR-xx / MSG-xx.}}

<!-- Toolbar actions: describe each action the form actually implements.
Include only the actions present; describe their real behaviour on THIS
form (confirmation prompts, validations run, what is cleared, locks). -->
### New Action
**What it is:** {{…}}
**When it applies:** {{…}}
**Business outcome:** {{What is cleared/reset, defaults applied, where focus lands, locks applied.}}

### Save Action
**What it is:** {{…}}
**When it applies:** {{In which modes.}}
**Business outcome:** {{Validations run (BR range), confirmation/success/failure messages, behaviour per mode.}}

### Search Action
**What it is:** {{…}}
**When it applies:** {{…}}
**Business outcome:** {{Search scope (company/enterprise), what is loaded, locks applied.}}

### Delete Action
**What it is:** {{…}}
**When it applies:** {{…}}
**Business outcome:** {{Confirmation, checks performed (or not performed), what is removed, messages.}}

### Navigation Actions
**What it is:** {{First / Previous / Next / Last, if implemented.}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

### Other Toolbar Actions ({{list, e.g. Print, Preview, Export, Email}})
**What it is:** {{Standard toolbar actions that are inactive or not implemented on this form, or describe them if they are implemented.}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

## 6. Data Layer (Business Information)
*This section describes the business information lifecycle and cross-entity relationships managed through the {{ScreenName}} screen.*

<!-- Describe data in business terms (no table names). Derive from the
tables written by the save/delete SPs. -->
### {{Entity}} Header Record
**What it is:** {{The main record and the kinds of information it holds, including audit/authorisation details if stored.}}
**When it applies:** {{Where and by whom it is created/maintained.}}
**Business outcome:** {{Its role as master/transaction data.}}

<!-- [IF the save writes company-level availability / mapping rows] -->
### Company Availability Profile
**What it is:** {{…}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

<!-- [IF child tables exist] -->
### Child Detail Profiles
**What it is:** {{The child collections attached to the header.}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

### Record Creation Lifecycle
**What it is:** The stage where a new {{Entity}} is introduced.
**When it applies:** {{…}}
**Business outcome:** {{Authority check, validations, automatic values/status, distribution, child rows saved.}}

### Record Retrieval and Search Lifecycle
**What it is:** The stage where users find and view existing {{Entities}}.
**When it applies:** {{…}}
**Business outcome:** {{Scope, what is shown, locks.}}

### Record Modification Lifecycle
**What it is:** The stage where an existing {{Entity}} is updated.
**When it applies:** {{…}}
**Business outcome:** {{What can change, side effects on other data (e.g. recalculations), audit.}}

### Record Retirement and Deletion Lifecycle
**What it is:** The stage where a {{Entity}} is removed or retired.
**When it applies:** {{…}}
**Business outcome:** {{Who may delete, what checks apply, what is removed together.}}

### Transactional Safety
**What it is:** How multi-record changes are grouped.
**When it applies:** {{Save / update / delete, per mode.}}
**Business outcome:** {{What commits or rolls back together; note per-row transactions in bulk modes.}}

## 7. Child Entities and Associated Controls
*This section details secondary collections, embedded controls, or specialized configuration grids associated with the {{ScreenName}} screen.*

<!-- [IF the form has no child grids or embedded controls] replace the
blocks below with a single sentence stating that the screen maintains
only header information. -->
<!-- [REPEAT] one structure block per child grid / embedded control -->
### {{Child Collection}} Structure
**What it is:** {{What the child collection represents.}}
**When it applies:** {{Where it is maintained.}}
**Business outcome:** {{Business value.}}

<!-- [IF the child has notable fields / columns] -->
### {{Child Collection}} Fields
**What it is:** {{Columns and their meaning, list sources, defaults, hidden columns.}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

### Operational Limits on Child Rows
**What it is:** {{Row-level validations: mandatory columns, value ranges, duplicates, conditional fields.}}
**When it applies:** {{…}}
**Business outcome:** {{Cite BR-xx / MSG-xx.}}

### Interface Visibility and Layout Status
**What it is:** {{Whether each child grid/control is visible, hidden, collapsed or off-screen.}}
**When it applies:** {{…}}
**Business outcome:** {{Practical effect on users and on save.}}

## 8. Business Operations (Stored Procedures)
*This section details the discrete business operations performed by the {{ScreenName}} screen.*

<!-- [REPEAT] One block per distinct business operation backed by an SP
(or group of SPs). Typical operations — include only those present:
Load Selection Lists, Dependent Values and Code Assignment, Load
Template/Defaults, Search Records, Load Record Details, Validate Record,
Save Main Record, Save Child Details, Delete Record, Import. Name them in
business terms; do not use SP names. -->
### {{Operation Name}} Operation
**What it is:** {{What the operation does.}}
**When it applies:** {{The user action or event that triggers it.}}
**Business outcome:** {{Result, checks performed, messages; cite BR-xx / MSG-xx.}}

## 9. Modular Architecture Notes
*This section highlights business-relevant architectural principles governing the {{ScreenName}} screen.*

### Modular Business Architecture
**What it is:** {{Separation between screen, business logic and database operations, as seen in this form.}}
**When it applies:** {{…}}
**Business outcome:** {{e.g. same rules applied in every entry mode — only if true.}}

### Enterprise Standardisation and Component Reuse
**What it is:** {{Shared masters, shared user controls, shared framework services this form reuses.}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

### Centralised Transactional Safety
**What it is:** {{Transaction handling across the records this form writes.}}
**When it applies:** {{…}}
**Business outcome:** {{…}}

## 10. Use Cases
*This section outlines standard operational scenarios executed on the {{ScreenName}} screen.*

<!-- [REPEAT] One block per realistic scenario the form supports.
Typically: single creation, bulk/fast entry, import, maintaining each
child collection, search and modify, deletion (success and blocked),
duplicate/validation failure, branch/view-only access — only those
supported. Actor = business role and, where relevant, company level. -->
### {{Use Case Title}}
**Actor:** {{Business role (company level, if relevant)}}
**Flow:** {{Step-by-step user actions with on-screen labels; cite BR-xx.}}
**Result:** {{Outcome on success and on failure; cite MSG-xx.}}

## 11. Business Rules
*This section establishes the authoritative business rules governing the {{ScreenName}} screen.*

<!-- [REPEAT] One bullet per rule, numbered sequentially. Each rule must
be specific and testable (exact lengths, scopes, conditions). State the
scope of uniqueness precisely (company / category / enterprise). Use
sub-bullets for rules with several parts. Cite related MSG-xx. -->
- **BR-01 ({{Short Rule Title}}):** {{Rule statement.}}
- **BR-02 ({{Short Rule Title}}):** {{Rule statement.}}

## 12. Messages
*This section catalogues all user-facing notifications, validation prompts, and error messages generated by the {{ScreenName}} screen.*

<!-- [REPEAT] One bullet per distinct message, including confirmations,
success notices, row-level Remarks text and database-error pass-through.
Format: trigger; exact text in italics and quotes (or the "standard
application message" note); user action; (BR-xx). Mark messages present
in code but not reachable on this form as "(not active on this screen
because …)". -->
- **MSG-01:** {{Trigger}}; *"{{Exact message text}}"*; {{user action}} (BR-xx).
- **MSG-02:** {{Trigger}}; *"{{Exact message text}}"*; {{user action}} (BR-xx).

## 13. Limitations, Defects and Open Questions
*This section documents observed contradictions, defects, operational constraints, and technical ambiguities identified in the {{ScreenName}} screen.*

<!-- [REPEAT] One block per limitation, defect, contradiction between UI and
backend, or unhandled edge-case. Use the standard three labels.
If no issues are found, include a single entry stating standard operation. -->
### {{Issue or Limitation Title}}
**What it is:** {{Description of the defect, discrepancy, or operational limitation.}}
**When it applies:** {{Circumstances or data conditions under which this issue manifests.}}
**Business outcome:** {{Business impact, operational risk, or recommended resolution.}}
