# Node Types: Embedded Text

Every one of the 16 node labels has a text field that is embedded (stored as `embedding`, model `Qwen/Qwen3-Embedding-0.6B`). That text is a short header plus a summary and label-specific facts.

Relationships are **not** part of the vector. They are graph edges, and only some of them are also written into the text as plain lists.

## Embedded text by label

Sampled one node per label, so the exact composition may vary.

| Label | Layer | Text includes | Attached via edges |
|---|---|---|---|
| Module | functional | name, summary, process/form lists | HAS_PROCESS, HAS_FORM, HAS_CONCEPT |
| BusinessProcess | functional | summary, module, concepts, leads-to, rules | HAS_STEP→Form, LEADS_TO, INVOLVES→Concept, GOVERNS←Rule |
| BusinessConcept | functional | summary, used-by forms (+N more), stored-in tables, evidence | MANAGES/USES_CONCEPT←Form, PARENT_OF, RELATED_TO, APPLIES_TO←Rule, PERSISTED_IN→Table (derived) |
| BusinessRule | functional | rule description, applies-to list, evidence | APPLIES_TO→Form/UC/Concept, IMPLEMENTED_BY→SP/FormMethod/Table/Column, GOVERNS→Process |
| Form | bridge | summary, processes, managed concepts, SPs, tables | HAS_STEP←Process, MANAGES/USES_CONCEPT→Concept, HAS_CONTROL, HAS_METHOD, EMBEDS→UC, USES_TABLE and SHARES_TABLE (derived), CALLS_SP (derived) |
| UserControl | bridge | summary, SPs, tables | EMBEDS←Form, HAS_CONTROL, HAS_METHOD, USES_CONCEPT |
| FormMethod | code | method header, code | HAS_METHOD←Form/UC, HANDLES→Control, CALLS, REFERENCES→Control, INVOKES→DTMethod, SETS→DTProperty |
| Control | code | name, type, label, parent | HAS_CONTROL←Form/UC, LABELS, BINDS_TO→DTProperty, HANDLES←FormMethod |
| DTClass | code | method list | HAS_METHOD, HAS_PROPERTY |
| DTProperty | code | property name, type | HAS_PROPERTY←DTClass, BINDS_TO←Control, SETS←FormMethod, PASSES→DAMethod |
| DTMethod | code | delegates-to, code | HAS_METHOD←DTClass, INVOKES←FormMethod, DELEGATES_TO→DAMethod |
| DAClass | code | method list | HAS_METHOD |
| DAMethod | code | SP executed, parameters | EXECUTES→SP, PASSES←DTProperty |
| StoredProcedure | data | author, description, writes, parameters, rules, code | EXECUTES←DAMethod, READS/WRITES→Table, USES_COLUMN→Column, CALLS_SP, DYNAMIC_EXEC→Table, IMPLEMENTED_BY←Rule |
| Table | data | business concept, used-by forms, writers, readers, columns | HAS_COLUMN→Column, READS/WRITES←SP, USES_TABLE←Form, PERSISTED_IN←Concept |
| Column | data | table, SPs that use it | USES_COLUMN←SP, IMPLEMENTED_BY←Rule |

---

Counts match across the board, so every node has an embedding. There is no separate `search_text` field.
