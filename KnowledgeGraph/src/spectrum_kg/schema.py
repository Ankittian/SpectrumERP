"""Self-description of the graph for agentic clients (served by describe_graph / kg://schema)."""
from __future__ import annotations

LABELS: dict[str, dict[str, str]] = {
    # functional layer
    "Module": {"layer": "functional", "means": "ERP module (Material Management, Plant Maintenance, Finance, Sales and Distribution, Production Planning, Master Data, Weigh Bridge, Discrete Raw Material, Settings and Utilities, Reports).",
               "key_props": "name, code, summary, doc, status"},
    "BusinessProcess": {"layer": "functional", "means": "End-to-end business flow, e.g. Procure-to-Pay (PO Flow), Payment Flow; ordered steps point to forms.",
                        "key_props": "name, key, summary, doc (includes ordered steps), status"},
    "BusinessConcept": {"layer": "functional", "means": "ERP domain entity (Material Group, Unit of Measure, QC Parameter, Vendor ...), with synonyms.",
                        "key_props": "name, key, summary, doc, synonyms"},
    "BusinessRule": {"layer": "functional", "means": "Business rule / policy and where it is enforced (SPs, methods, columns).",
                     "key_props": "name, summary, doc, rule_type"},
    "Form": {"layer": "bridge", "means": "WinForms screen. Curated doc (purpose, actions, validations) + extracted code. status=planned means a placeholder for a form not built yet.",
             "key_props": "name, title, summary, doc, module, sp_prefix, status"},
    "UserControl": {"layer": "bridge", "means": "Reusable UI component embedded in forms (e.g. QCGroup).",
                    "key_props": "name, title, summary, doc"},
    # technical layer
    "FormMethod": {"layer": "code", "means": "VB/C# method of a form or user control (event handler, IMDIFunctions action like Save/LoadData, helper).",
                   "key_props": "name, method, owner, method_kind, events, code, file, start_line"},
    "Control": {"layer": "code", "means": "UI control on a form (textbox, combo, grid, tab page ...), with its label, tab, mandatory flag.",
                "key_props": "name, control, type, label, tab, mandatory, max_length"},
    "DTClass": {"layer": "code", "means": "Data-transfer (active-record) class; forms set its properties and call its methods.", "key_props": "name"},
    "DTProperty": {"layer": "code", "means": "Property of a DT class; carries a form field value to an SP parameter.", "key_props": "name, property, type"},
    "DTMethod": {"layer": "code", "means": "DT method called by forms; delegates to a DA method.", "key_props": "name, code"},
    "DAClass": {"layer": "code", "means": "Data-access class.", "key_props": "name"},
    "DAMethod": {"layer": "code", "means": "Data-access method: builds the parameter dictionary and executes one stored procedure.", "key_props": "name, code"},
    "StoredProcedure": {"layer": "data", "means": "T-SQL stored procedure (one node, full code): header author/date/description, parameters list, params_not_passed (never sent by the data layer, SQL default applies).",
                        "key_props": "name, code, description, author, created, parameters, params_not_passed, dynamic_sql, ambiguous_columns"},
    "Table": {"layer": "data", "means": "Database table (schema.name).", "key_props": "name, schema, table"},
    "EnumType": {"layer": "data", "means": "Lookup list from the GlobalData tables: what the numeric codes of one column mean (e.g. AccountType, ItemType, Status).",
                 "key_props": "name, key_column, name_column, value_count, summary"},
    "EnumValue": {"layer": "data", "means": "One code of a lookup list, e.g. AccountType 3 = Bank Account.",
                  "key_props": "enum, value, label, inactive, is_default"},
    "Column": {"layer": "data", "means": "Table column observed in SP code (no DDL available, so only used columns exist).",
               "key_props": "name, table, column"},
}

# type -> (from, to, meaning, follow when, derived)
RELATIONSHIPS: dict[str, dict[str, object]] = {
    "HAS_PROCESS": {"from": "Module", "to": "BusinessProcess", "means": "module owns the process"},
    "HAS_FORM": {"from": "Module", "to": "Form|UserControl", "means": "module owns the form"},
    "HAS_CONCEPT": {"from": "Module", "to": "BusinessConcept", "means": "module owns the concept"},
    "HAS_STEP": {"from": "BusinessProcess", "to": "Form", "means": "process step performed in the form; props order, step, status"},
    "LEADS_TO": {"from": "BusinessProcess", "to": "BusinessProcess", "means": "downstream process"},
    "INVOLVES": {"from": "BusinessProcess", "to": "BusinessConcept", "means": "concepts used by the process"},
    "MANAGES": {"from": "Form|UserControl", "to": "BusinessConcept", "means": "form creates/maintains this concept (its master)"},
    "USES_CONCEPT": {"from": "Form|UserControl", "to": "BusinessConcept", "means": "form references / looks up this concept"},
    "PARENT_OF": {"from": "BusinessConcept", "to": "BusinessConcept", "means": "classification hierarchy (Category > Group > Sub Group > Item)"},
    "RELATED_TO": {"from": "BusinessConcept", "to": "BusinessConcept", "means": "domain relationship; prop how"},
    "PERSISTED_IN": {"from": "BusinessConcept", "to": "Table", "means": "tables storing the concept", "derived": True},
    "APPLIES_TO": {"from": "BusinessRule", "to": "Form|UserControl|BusinessConcept", "means": "scope of the rule"},
    "IMPLEMENTED_BY": {"from": "BusinessRule", "to": "StoredProcedure|FormMethod|Table|Column", "means": "where the rule is enforced"},
    "GOVERNS": {"from": "BusinessRule", "to": "BusinessProcess", "means": "process governed by the rule"},
    "HAS_CONTROL": {"from": "Form|UserControl", "to": "Control", "means": "control on the form"},
    "LABELS": {"from": "Control", "to": "Control", "means": "label control captioning an input control"},
    "EMBEDS": {"from": "Form", "to": "UserControl", "means": "form hosts the user control"},
    "HAS_METHOD": {"from": "Form|UserControl|DTClass|DAClass", "to": "FormMethod|DTMethod|DAMethod", "means": "method of the class"},
    "HANDLES": {"from": "FormMethod", "to": "Control|Form|UserControl", "means": "event handler; prop event"},
    "CALLS": {"from": "FormMethod", "to": "FormMethod", "means": "method call (incl. into an embedded user control)"},
    "REFERENCES": {"from": "FormMethod", "to": "Control", "means": "method reads/writes the control"},
    "INVOKES": {"from": "FormMethod", "to": "DTMethod", "means": "form method calls DT method (data-layer entry)"},
    "SETS": {"from": "FormMethod", "to": "DTProperty", "means": "method assigns the DT property; props expr, grid_column"},
    "BINDS_TO": {"from": "Control", "to": "DTProperty", "means": "control value is copied into the DT property; props expr, method"},
    "HAS_PROPERTY": {"from": "DTClass", "to": "DTProperty", "means": "property of the DT class"},
    "DELEGATES_TO": {"from": "DTMethod", "to": "DAMethod", "means": "DT method calls DA method"},
    "PASSES": {"from": "DAMethod", "to": "DTProperty", "means": "DA method sends the DT property as SP parameter `param` (the SP it executes is the EXECUTES target)"},
    "EXECUTES": {"from": "DAMethod", "to": "StoredProcedure", "means": "DA method executes the SP"},
    "READS": {"from": "StoredProcedure", "to": "Table", "means": "SP reads the table"},
    "WRITES": {"from": "StoredProcedure", "to": "Table", "means": "SP inserts/updates/deletes; props ops, error_handling (CATCH-block error log)"},
    "USES_COLUMN": {"from": "StoredProcedure", "to": "Column", "means": "SP reads/writes the column; props ops, inferred"},
    "HAS_COLUMN": {"from": "Table", "to": "Column", "means": "column of the table"},
    "HAS_VALUE": {"from": "EnumType", "to": "EnumValue", "means": "code that belongs to the lookup list"},
    "BACKED_BY": {"from": "EnumType", "to": "Table", "means": "GlobalData table the lookup list is stored in"},
    "HAS_ENUM": {"from": "Column", "to": "EnumType", "means": "column holds codes of this lookup list (matched by key column name); ambiguous=true when several lists share the key name"},
    "USES_ENUM_VALUE": {"from": "StoredProcedure", "to": "EnumValue", "means": "SP compares a column with this raw number; props literal, column, count, confidence (high|low)"},
    "CALLS_SP": {"from": "Form|UserControl|StoredProcedure", "to": "StoredProcedure",
                 "means": "shortcut Form->...->SP (props methods); or SP EXEC of another SP", "derived": True},
    "DYNAMIC_EXEC": {"from": "StoredProcedure", "to": "Table", "means": "SP executes dynamic SQL whose procedure name is looked up in this table"},
    "USES_TABLE": {"from": "Form|UserControl", "to": "Table", "means": "shortcut: tables touched through the form's SPs; prop ops [read, write]", "derived": True},
    "SHARES_TABLE": {"from": "Form|UserControl", "to": "Form|UserControl",
                     "means": "shortcut: forms touching common tables; props tables, write_conflict, conflict_tables (treat as undirected)", "derived": True},
}

STRATEGIES = [
    {"name": "functional top-down",
     "path": "Module -HAS_PROCESS-> BusinessProcess -HAS_STEP-> Form -MANAGES/USES_CONCEPT-> BusinessConcept <-APPLIES_TO- BusinessRule",
     "use_for": "what a process/form does, who uses it, which rules apply"},
    {"name": "technical drill-down",
     "path": "Form -HAS_METHOD-> FormMethod -CALLS-> FormMethod -INVOKES-> DTMethod -DELEGATES_TO-> DAMethod -EXECUTES-> StoredProcedure -WRITES/READS-> Table -HAS_COLUMN-> Column",
     "use_for": "what happens on Save/Load/Delete, which SQL runs"},
    {"name": "field lineage",
     "path": "Control -BINDS_TO-> DTProperty <-PASSES {param}- DAMethod -EXECUTES-> StoredProcedure -WRITES-> Table -HAS_COLUMN-> Column",
     "use_for": "where a screen field is saved"},
    {"name": "impact analysis (bottom-up)",
     "path": "Column <-USES_COLUMN- StoredProcedure <-EXECUTES- DAMethod <-DELEGATES_TO- DTMethod <-INVOKES- FormMethod <-HAS_METHOD- Form <-HAS_STEP- BusinessProcess (shortcut: Table <-USES_TABLE- Form)",
     "use_for": "what breaks if a table/column/SP changes"},
    {"name": "lateral",
     "path": "Form -SHARES_TABLE- Form ; Form -USES_TABLE-> Table <-USES_TABLE- Form ; Form -EMBEDS-> UserControl <-EMBEDS- Form ; BusinessConcept -RELATED_TO- BusinessConcept",
     "use_for": "how forms relate / conflict"},
    {"name": "semantic jump",
     "path": "similar(id) or search(query, labels=[...])",
     "use_for": "no edge connects what you need, or you need an entry point"},
]

TIPS = [
    "Start with search() to get entry ids, read hop_hints, then expand() only the relationship types you need.",
    "Derived shortcut edges (derived=true) skip long chains; walk the full chain only when you need the code-level detail.",
    "Use get_node(id, detail='code') only for nodes whose code you must read; summaries are usually enough to decide the next hop.",
    "Forms with status=planned are placeholders for screens not built yet; they carry process context but no code.",
    "SQL ids are lowercase: table:masterdata.munitmaster, sp:masterdata.mmumsave, column:masterdata.munitmaster.unitname. SP parameters are a property of the SP, not nodes.",
    "Raw numbers in SP code (StatusNo = 3) are translated by StoredProcedure -USES_ENUM_VALUE-> EnumValue (label = the name); confidence=low means several lookup lists share the column name, so check all candidates.",
    "WRITES edges with error_handling=true are CATCH-block error logging, not business writes.",
]

RESPONSE_RULES = [
    "Use simple, plain language: write the way you would explain it to a new colleague. Prefer everyday words and short sentences. Simplicity and clarity matter more than perfect grammar or formal/technical terminology.",
    "Explain, don't just list: say what a thing does and why it matters in business terms (e.g. 'this screen is where users create a new unit; when they click Save, the data goes into the munitmaster (Table)'). Describe flows as simple step-by-step sentences rather than raw edge chains.",
    "Explain jargon on first use: if you must use a technical term (Stored Procedure, DT/DA layer, Control, Column, derived edge, etc.), add a short plain-words meaning the first time, e.g. 'mmumsave (Stored Procedure - a saved database script that writes the data)'. Avoid graph/tool vocabulary like 'node', 'hop' or 'expand' in the answer unless the user uses it first.",
    "Be brief: give a short, to-the-point answer to exactly what was asked. Short does not mean cryptic - a few clear explanatory sentences beat a terse list. Elaborate (details, chains, code, lineage) only when the user asks for it.",
    "Clarify before answering: if the question looks incomplete, or could mean two similar things (e.g. similarly named tables, columns, SPs, forms, controls or properties), ask a short follow-up to confirm what the user meant instead of guessing.",
    "Always label graph objects with their type: every object you mention from the graph must carry its node type, e.g. 'munitmaster (Table)', 'mmumsave (Stored Procedure)', 'Unit Master (Form)', 'txtUnitName (Control)'. Take the type from each result's 'label'/'kind' field (or the id prefix, e.g. table:, sp:, form:); never present a bare name without its type.",
]


def instructions_text() -> str:
    """Always-on operating contract. Kept short: the full strategies, tips and response rules are returned by
    describe_graph() and kg://schema, so they cost tokens only when a client asks for them."""
    return "\n".join([
        "SpectrumERP knowledge graph (~400 forms, 10 modules, report catalogue). Agentic RAG: you choose the route.",
        "Workflow: search (entry points) -> read hop_hints -> expand only the relationships you need -> get_node for details.",
        "Use get_node(detail='code') only when you must read code (bounded; page with next_cursor).",
        "Full map, strategies, tips and response rules: describe_graph or kg://schema. Do not call it at every session start.",
        "Profiles: compact (default, small limits), standard, detailed. truncated=true or next_cursor means more results exist.",
        "Derived edges (derived=true) are shortcuts. WRITES with error_handling=true is error logging, not a business write.",
        "Answer style: plain language, explain what things do in business terms, label each graph object with its type.",
    ])
