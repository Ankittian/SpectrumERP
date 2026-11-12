# **using-the-erp-knowledge-base**

## **Getting the most from the SpectrumERP knowledge base**

12 Nov 2026 · advisory for Alok Chandra Shahi · covers the 10 questions asked in the project thread.

### **0. What you already own (the starting point)**

Everything below builds on assets that already exist. You do not need new analysis to start; you need to wire these together.

| **Asset** | **Where** | **What it gives you** |
| --- | --- | --- |
| Rules for every session | migration/CLAUDE.md | No-assumption rule, citation rule, token discipline |
| Plan, decisions, roadmap | migration/PLAN.md, decisions.md, roadmap.md | Scope, owner answers, estimates, migration order |
| Functional docs | migration/functional-docs/ (426 files) | Per-form purpose, steps, validations, rules, in business language |
| Module briefs + HLDs | migration/briefs/, migration/hld/, migration/modules/ | Module-level architecture and risks |
| Indexes | migration/index/ (sp-index.csv ~9,900 SPs, encrypted-objects.csv, unresolved-dynamic-calls.csv, confidence.json, per-object JSON) | Countable facts without reading source |
| Nested SP analysis | migration/analysis/nested-sp/ | 79,876 SP→SP/table edges, hubs, cycles, dynamic SQL sites |
| Save patterns, API analysis | migration/analysis/save-patterns.*, sp-api/ | How screens save; candidate API surface |
| Forms index | migration/forms/index.csv (1,088 forms) | Phase, difficulty, save pattern, SPs, status per form |
| **Combined knowledge graph, Phases 0–13** | D:\Coding\migration\kg-all-phases\ and migration/kg-all-phases/spectrum-kg-all-phases.zip | 90,733 nodes, 508,940 edges, 402 forms, full code on nodes, embedding text (Qwen3-Embedding-0.6B) |
| KG query server | the local spectrum-kg MCP server on your PC | search, similar, expand, find_paths, get_node, run_cypher, describe_graph |
| KB design | migration/kb/KB-DESIGN.md | One source, two views (technical/functional), same IDs as the graph |

**First fix (today, ~15 minutes):** the spectrum-kg server I can reach right now reports an older graph: 56 forms, built 11 Nov from the early phases. The combined build has 402 forms. Point the server's config at the kg-all-phases graph and reload it, then ask Claude to run describe_graph and confirm the Form count is ~402. Every idea below gets much better once that is done.

### **1. Using this project efficiently, with fewer tokens, now and later**

#### **How tokens get spent today**

Most cost comes from (a) re-reading large source or CSV files a previous thread already summarised, (b) long threads where every turn re-sends the whole history, and (c) asking the model to "look around" instead of pointing it at a file or a graph node.

#### **Habits that save the most**

**Ask the graph, not the source.** For "what does form X save, which SP, which table, which rule" use the spectrum-kg tools: search → expand → get_node(detail='summary'). Only ask for detail='code' on the one node you must read. A graph hop costs a few hundred tokens; reading a form's .vb file costs tens of thousands.

**One goal per thread.** Start a new thread per form, per module, or per question type. Short threads are cheap; a 100-turn thread re-pays its whole history on every message. When a thread finishes, its output should be a file in migration/, so the next thread reads the file, not the conversation.

**Write once, read many.** Rule 7 of CLAUDE.md already says this. Keep it: every finding lands in a doc (functional-docs/, forms/, decisions.md), and later threads start from that doc.

**Name the file or node in your ask.** "Using functional-docs/Functional_Doc_fBankJournal.md and the KG, list the validations missing from the web spec" is far cheaper than "tell me about bank journal".

**Scripts for bulk, the model for judgement.** Counting, listing, diffing, regenerating indexes: a Python script in migration/tools/. The model only writes meaning (purpose, rules, risks). The repo already follows this; keep doing it.

**Pick the model by task.** Bulk summaries, doc formatting, quiz generation from existing docs: a smaller model (Sonnet/Haiku). Architecture, specs, tricky SP logic, code: the strongest model.

**Keep CLAUDE.md short and current.** It is read at the start of every session, so every line costs tokens every time. Move history to decisions.md; keep CLAUDE.md to rules, facts and pointers. Fill in the "Open facts" as soon as you know them, so no thread has to ask again.

#### **Making the knowledge last beyond this project**

**Project memory is off** in this project (it follows your Claude memory setting, which was off when this session started). That means no thread remembers the previous one on its own. Two ways to compensate:

Turn memory on in your Claude settings if you want threads to carry preferences and facts forward automatically.

Independently of that, treat migration/CLAUDE.md + decisions.md as the project's long-term memory. They are files, they survive every thread, and you control them.

**Project instructions** (Project settings): put three or four lines there, e.g. "Read migration/CLAUDE.md first. Use the spectrum-kg MCP before reading source. Write results under migration/. Cite sources." This applies to every new thread for free.

**Start a git repo for D:\Coding\migration\** (local is enough). You get history of every doc and can see what changed between analysis runs.

**Skills:** turn your repeated procedures into Claude skills, for example "document a form" (template forms/_TEMPLATE.md + KG queries + checklist) or "answer an ERP question from the KG". A skill loads only when needed, so it costs nothing until used.

### **2. Building an architectural, technical and functional KB, plus quizzes and a course**

#### **The KB itself**

kb/KB-DESIGN.md is already the right design: Markdown pages with front matter, audience: technical | functional, and page IDs equal to graph IDs. Suggested build order:

**Generate the skeleton from the graph.** A script walks the KG and writes one page per Module, BusinessProcess, BusinessConcept, Form and "important" SP/table (hubs from nested-sp/README.md: masterdata.DocumentNumberGeneration, finance.VoucherDelete, etc.). Generated blocks: callers, tables touched, rules, controls, process steps.

**Pour in the written meaning** from functional-docs/ (426 forms), briefs/, hld/ and decisions.md. Do not rewrite them; link or include them.

**Publish it as a static site.** MkDocs Material or Docusaurus over the Markdown folder, with two navigation trees (Functional / Technical) and built-in search. Host it on your intranet. Zero AI cost for people reading it.

**Three layers, mapped to the graph:**

*Architectural:* module map, target HLD, services catalog (api-catalog.md), cross-cutting (auth, numbering, posting, printing), decisions.

*Technical:* form → method → DT → DA → SP → table lineage, save patterns, encrypted objects, dynamic SQL, data dictionary (Column nodes).

*Functional:* processes (Procure-to-Pay, Payment Flow…), concepts with synonyms, 840 business rules, step-by-step screen guides.

**Validation:** kb/kb-validation-plan.md already exists; run it per phase so every page has a reviewer and a status.

#### **Quizzes**

The 840 BusinessRule nodes and 426 functional docs are ready-made question banks.

Ask Claude (a smaller model is fine) per module: "From these functional docs and the rules in the KG for module MM, write 20 multiple-choice questions with the answer, an explanation and the source doc/rule id." Save as CSV/JSON in migration/kb/quiz/<module>.csv.

Mix three levels: *functional* ("What happens to the in-process amount when a bank payment is saved?"), *technical* ("Which SP numbers documents?"), *architectural* ("Why does the web app keep the same database?").

Run quizzes in Google Forms, Moodle, or a simple Claude-built quiz page (an Artifact) that your team opens in the browser.

#### **A course for your team**

Suggested tracks (each a sequence of KB pages + a quiz + a hands-on task):

| **Track** | **For** | **Content** | **Hands-on task** |
| --- | --- | --- | --- |
| ERP basics | everyone | modules, processes, concepts, menu/rights | walk one business process end to end on the dev DB |
| Functional per module | consultants, support | process pages, screen guides, rules | answer 10 real client questions using the KB |
| Legacy technical | developers, support devs | session model (session-flow.md), form→SP lineage, save patterns, numbering, posting | trace one field from screen to column using the KG |
| Migration architecture | API/UI developers | target HLD, API catalog, decisions, spec+TDD rules | build one master screen (e.g. fUnitMaster) against the spec |

Generate each lesson from the KB with Claude, then have a senior person review it once. Record short screen videos of the desktop app for the functional track; they are the one thing the KB cannot generate.

### **3. A "Jarvis" that answers any question about the ERP**

You already have 80% of it: the graph, the embeddings, and an MCP server with search and traversal. What is missing is a front door for people who do not use Claude Code.

#### **Architecture**

User (web chat / Teams / Slack / voice later)
   │
   ▼
Assistant service (Claude API, tool use)
   ├── KG tools: search, similar, expand, find_paths, get_node, run_cypher   ← spectrum-kg
   ├── Docs search: vector index over functional-docs, briefs, HLD, decisions
   ├── Read-only SQL on a DEV/REPORTING copy (optional, whitelisted views only)
   └── Guardrails: cite node ids / doc paths, say "not in the KB" when unsure

#### **Steps**

**Load the full graph** (see section 0) into the MCP server, with the embeddings.

**Index the docs** (functional-docs, briefs, HLD, decisions, KB pages) into the same vector store, chunked by heading, each chunk tagged with its graph id. Use the same embedding model (Qwen3-Embedding-0.6B) so graph and doc search share one space.

**Write the system prompt** from CLAUDE.md Rule 1: answer only from tools, cite every claim, list unknowns. Add the describe_graph strategies (functional top-down, technical drill-down, field lineage, impact analysis) so the model knows which hops to use.

**Build the front end.** Cheapest options, in order: (a) use Claude Desktop/Claude Code with the MCP server for your own team today; (b) a small web app (FastAPI + Claude API with tool use + prompt caching) for wider use; (c) a Teams/Slack bot over the same service. Voice is a thin layer on top (speech-to-text in, text-to-speech out) once text works.

**Two personas** in one system: functional mode (answers in business language from docs/rules) and technical mode (lineage, SPs, code), chosen by the user or by the question.

**Evaluate it.** Collect 50–100 real questions from support and developers with known answers; re-run them after every graph rebuild. This is your regression test for the assistant.

#### **Token/cost control for the assistant**

Prompt caching for the system prompt and graph description.

Summaries first, code only on request (get_node detail levels).

A smaller model for routing and simple lookups; the strongest model only for multi-hop reasoning.

### **4. Finding bugs, missing cases and enhancements**

The graph already flags many issues; turn each flag into a report.

| **Check** | **How (KG / existing file)** | **What it finds** |
| --- | --- | --- |
| Write conflicts | SHARES_TABLE edges with write_conflict=true; MANIFEST warning "two forms write the same table, no integrity rule covers both" (76) | Two screens updating the same table without a shared rule: lost updates, inconsistent data |
| Params never passed | StoredProcedure.params_not_passed | Screen relies on an SQL default; possible missing input or dead parameter |
| Ambiguous columns | StoredProcedure.ambiguous_columns | Latent SQL bugs when schemas change |
| CATCH-only error handling | WRITES with error_handling=true vs SPs with no TRY/CATCH and no transaction (sp-index.csv flags) | Partial saves on failure |
| Cycles | AutoAdjustVoucher ↔ VoucherSaveAfterInsert, FIRVSaveJob ↔ FIRVSaveOnDate | Recursion risk, double posting |
| Hard-coded DB names | ERPV2 references (nested-sp/README.md) | Breaks on another client database |
| Dynamic SQL | nested-sp/dynamic-sites-resolved.csv, index/unresolved-dynamic-calls.csv | SQL injection risk, untestable paths |
| Mandatory field gaps | Control.mandatory vs the SP's NOT NULL use and the functional doc's validations | Validation in UI but not in SP (or the reverse) |
| Rules without enforcement | BusinessRule nodes with no IMPLEMENTED_BY edge | A rule people believe in, but code does not enforce |
| Unreferenced objects | index/sp-unreferenced.csv | Dead code to drop from the migration (confirm per CLAUDE.md first) |
| Encrypted logic | encrypted-objects.csv | Untestable black boxes; a risk list |

**Workflow:** one thread per module, prompt: "Run these checks for module X using the KG; write migration/reviews/<module>-findings.md with each finding, its evidence (node ids, file:line), severity, and a suggested test." Then each finding becomes either a bug ticket for the desktop product or a test case for the web version.

**Enhancements:** ask per process "which steps are manual, repeated or re-keyed across forms?" (use SHARES_TABLE and process steps). Typical wins: auto-fill from upstream documents, approval workflows, dashboards over existing vw* views, mobile screens for gate entry/weighbridge.

### **5. Faster development**

**Spec from the graph.** For each form, generate specs/<form>.md from the KG (controls, validations, save SP chain, tables, rules) plus the functional doc. You have done this for 4 forms already (migration/forms/); turn it into a skill and run it per phase.

**Characterisation tests from the SP chain.** The save path (FormMethod → DTMethod → DAMethod → SP → Table) tells you exactly which tables to snapshot before and after a save on the dev DB. Generate those tests before writing new code (Rule 4).

**Code generation.** The PASSES edges (DT property → SP parameter) and BINDS_TO (control → property) give you everything needed to generate typed API request models, SP client wrappers and form field definitions. Generate the boilerplate; humans review the logic.

**Impact analysis before every change.** "What breaks if I change inventory.LotMain?" → Table <-USES_TABLE- Form in one query. Use it in code review.

**Reuse the hub services.** Build numbering, posting, lot transaction and voucher delete once (P0/P3 in roadmap.md); the graph shows 297 SPs depend on DocumentNumberGeneration alone.

**Claude Code in the new repo** with a CLAUDE.md that points to the KG MCP server, so coding sessions query lineage instead of reading legacy source.

### **6. A support system**

**Tier 0 (self-service):** the KB site and the "Jarvis" assistant in functional mode, for client admins and consultants. Answers how-to questions with screen guides and rules.

**Tier 1 (support desk):** the same assistant in a support mode that, given an error message or a symptom, searches rules, SPs and docs and returns: likely cause, which form/SP, what to check, and a known-fix article if one exists.

**Tier 2 (developers):** technical mode with lineage and code, plus read-only queries on a copy of the client DB.

**Ticket loop:** connect your ticket tool (email, Freshdesk, Jira, or a Google Sheet to start). Each resolved ticket becomes a KB "known issue" page tied to the form/SP node id. Over time the assistant answers repeat tickets itself.

**Proactive support:** schedule a monthly job that runs the section 4 checks and the notification/job health queries, and posts a summary.

**Per-client knowledge:** modules/clientforks.md and the client packs (EROS, VTPL, HariOm…) should be tagged in the KB so answers respect which client the question is about.

### **7. What else you can get from it**

**Pre-sales and onboarding:** process maps and feature lists per module for proposals; new-client implementation checklists from the process steps.

**Client configuration audits:** which settings and custom fields each client uses, from globaldata and the client packs.

**Data migration and integration:** column-level lineage helps build import templates, Tally/GST integrations and data-quality checks.

**Documentation for clients:** user manuals generated from functional docs, per client pack.

**Performance tuning:** SPs with cursors, dynamic SQL and wide table access (sp-index.csv flags) are the first tuning candidates.

**Security review:** dynamic SQL sites, rights from FormMaster, and auth in session-flow.md give a ready list for a security audit.

**Product roadmap:** usage of forms (if you add logging) plus the graph shows which modules are central and which are rarely touched.

**Estimating:** estimates/ and forms/index.csv already let you quote migration or customisation work per screen; re-run after the Material Issue pilot.

### **8. Giving others access to the KB so they can ask questions**

Split access by **what** people can see, not only **who** they are.

| **Audience** | **What they get** | **How** |
| --- | --- | --- |
| Functional users, client admins, consultants | Functional pages + assistant in functional mode (no code, no SP bodies) | KB site and chat app behind company login (SSO: Microsoft 365 / Google) |
| Support desk | Functional + rule/SP *summaries*, no source code | Same app, support role |
| Developers (internal) | Everything, including code lineage and SP text | Same app developer role, or Claude Code / Claude Desktop with the MCP server |
| Clients (later) | Only their client pack + common modules | Separate tenant/filter by client tag |

Practical options, cheapest first:

**Now, for a few internal people:** share the published KB site (MkDocs) on the intranet/VPN, and give developers Claude (Team/Enterprise seats) connected to the spectrum-kg MCP server running on an internal machine.

**Next, for everyone:** the assistant web app from section 3, with login, roles and an audit log of questions. Role decides which tools and which node fields the model may see (e.g. strip code properties for non-developer roles at the tool layer, not in the prompt).

**Inside Teams/Slack:** a bot over the same service, so people ask where they already work.

Rules: never put the graph or code in a public chatbot; log every question and answer (useful for the KB, and for audit); review the top unanswered questions monthly and turn them into KB pages.

### **9. Keeping the code secure, and a scalable design**

#### **Principles**

**Code and the full graph never leave your controlled environment.** The KG (with full code on nodes) lives on an internal server, not on laptops or shared drives.

**Two graphs, two exposures:** a *full* graph (code, SP bodies) for developers, and a *redacted* graph (summaries, rules, lineage names, no code) for everyone else. Generate the redacted one in the build script by dropping code and SQL text fields. Most users only ever touch the redacted one.

**Least privilege at the tool layer.** The assistant's tools enforce role filters; the model cannot "talk its way" to code it was never given.

**No production database access** from the assistant. Use the dev export or a read-only reporting copy, whitelisted views only, no credentials in prompts, docs or repos (already Rule 1 in CLAUDE.md).

**Source control:** private Git (Azure DevOps, GitHub private, or self-hosted GitLab) with branch protection, MFA, and secret scanning. Retire shared folders as the master copy.

**AI provider data handling:** use a commercial/business plan (Claude Team/Enterprise or the API), where inputs are not used for training by default; check the current terms with your account. If policy requires, run it through AWS Bedrock or Google Vertex in your own cloud account and region.

#### **Reference architecture (scales from 5 to 500 users)**

Users ──SSO──► Web app / Teams bot ──► Assistant API (stateless, FastAPI/.NET, containers)
                                          │  role filter, audit log, rate limits, prompt caching
                                          ├─► Graph DB (Neo4j/Memgraph)  full + redacted graphs
                                          ├─► Vector store (pgvector/Qdrant) docs + node embeddings
                                          ├─► Docs store (Git repo of KB Markdown → static site)
                                          └─► Claude API (Bedrock/Vertex/Anthropic)
Build pipeline (CI, internal): source + DB export ─► spectrum_kg build ─► validate ─► redact ─► load

**Scalable:** the API is stateless, so add containers behind a load balancer; graph and vector DB scale separately; cache common answers.

**Repeatable:** the graph build (build_all.py, merge_domain.py) runs in CI on every new export, never on someone's laptop.

**Observable:** log question, tools used, nodes returned, answer, user, role; dashboards for cost and unanswered questions.

**Where to host:** one internal VM/VPS to start (Docker Compose: API + Neo4j + Postgres/pgvector), then Kubernetes or a managed container service when usage grows.

### **10. Using it for the migration plan**

The graph turns the plan from estimates into something you can query and re-run.

**Order by dependency, not by guess.** Query hubs and shared tables (SHARES_TABLE, CALLS_SP, nested SP hubs) to confirm the P0→P9 order in roadmap.md: services everything depends on (numbering, posting, lots) go first; screens with write conflicts move together.

**Wave planning.** Group forms that write the same tables into the same release, so desktop and web never fight over a table. The 76 "two forms write the same table without a shared rule" warnings are the list to resolve first.

**Re-estimate from facts.** Feed per-form counts (controls, methods, SPs, tables, save pattern, encrypted SPs) from the graph into estimates/tools/est.py, and recalibrate with the Material Issue pilot actuals.

**Risk register from the graph.** Encrypted objects, dynamic SQL, cycles, cross-DB references and hard-coded ERPV2 become risk items per module, feeding the confidence score in decisions.md section 4.

**Per-form migration pack.** For each form: spec + lineage + tests + API endpoints, generated from the graph (section 5), reviewed by a person, then built.

**Progress tracking.** Add a status (not started / spec / tests / built / live per client) to forms/index.csv and to Form nodes; a dashboard shows % done by phase and module.

**Cut-over checks.** Before switching a module off on desktop for a client, query which other forms still write its tables, and which reports (vw* views, .rdl) read them.

**Keep it current.** Rebuild the graph from each new code/DB export and diff it against the previous build: new or changed SPs show which specs need updating.

### **11. Recommended next steps (in order)**

| **#** | **Step** | **Effort (estimate)** | **Who** |
| --- | --- | --- | --- |
| 1 | Point the spectrum-kg MCP server at the kg-all-phases build and confirm ~402 forms | 15 min | you, Claude checks |
| 2 | Add 3–4 lines of project instructions (section 1); trim CLAUDE.md; decide on turning memory on | 30 min | you |
| 3 | git init in D:\Coding\migration\ | 10 min | you |
| 4 | Collect 50 real questions (support + developers) with known answers | 1–2 days | your team |
| 5 | Run the section 4 checks for one module (Supply, since the pilot is there) | 1 thread | Claude |
| 6 | Generate the KB skeleton from the graph and publish with MkDocs | 2–4 days | Claude + 1 developer |
| 7 | Quiz bank for one module; trial with the team | 1 thread | Claude |
| 8 | Prototype the assistant (Claude API + MCP tools) and score it on the 50 questions | 1–2 weeks | 1 developer + Claude |
| 9 | Turn "document a form", "spec a form" and "module checks" into skills | 1 thread | Claude |
| 10 | Support loop: tickets → known-issue pages | ongoing | support team |
| 11 | Add a redaction step to the graph build (no code for non-developer roles) | 1 thread | Claude |
| 12 | Move the master copy of code to a private Git host with MFA and branch protection | 1 day | you |
| 13 | Feed graph counts into the estimate script and add status tracking to forms/index.csv | 1 thread | Claude |

Effort figures are estimates and depend on team availability and on step 1 working.