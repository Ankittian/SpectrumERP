# Plan: Shared Claude Harness + Neo4j KG on EC2 with a React Front End

*Revision 2, 2026-11-12. Merges in `KnowledgeGraph/PLAN-roles-observability.md` (roles and audit inside the MCP) and
adds a concrete solution for every open issue. Changes from revision 1 are listed in section 9.*

## 0. Reusing the existing MCP (`spectrum-kg`)

**Yes, reuse it.** Current config:

```json
"spectrum-kg": { "type": "http", "url": "http://192.168.0.59:8765/mcp" }
```

It is a streamable-HTTP MCP server with these tools: `describe_graph`, `search`, `get_node`, `expand`, `find_paths`,
`similar`, `run_cypher`. The graph it serves (built 2026-11-12) has about 90,700 nodes and 509,000 relationships across
10 modules, 402 forms and 4,927 business rules. It answered queries from the dev machine on 2026-11-12, so the earlier
connect timeout was a host availability problem, not a design problem.

| Aspect | Status | Solution |
|---|---|---|
| Transport | HTTP, network-addressable | Run it on the EC2 box (or a sibling container). Point the agent at `http://localhost:8765/mcp`. |
| Neo4j connection | Local or LAN Neo4j | New Bolt URI and credentials from env vars, secrets from AWS Secrets Manager. |
| Auth | None today | Roles plan: bearer token mapped to user and role server-side (section 3.2). Port 8765 is never public. |
| Write safety | `run_cypher` runs in a READ transaction and rejects write clauses | Also connect with a **read-only Neo4j user** so a bug cannot write. Verify with a write attempt in the test suite. |
| Identity per user | None | Backend holds one service token per role; the MCP maps token to role. A trusted-backend token may pass the end user's id for audit (section 3.2). |
| Roles | One view for everybody | Functional, technical and product roles, enforced in the data layer (section 3.2). |
| Audit | None | JSON-lines audit log on every tool call, shipped to CloudWatch (section 3.8). |

**Pre-migration checklist**
1. `curl -i http://<host>:8765/mcp` answers.
2. Tools list matches the table above and nothing can mutate the graph (try a `CREATE` through `run_cypher`).
3. Neo4j credentials come from env or config, not hard-coded.
4. Stateless HTTP handles concurrent sessions.
5. Result size and query timeout are capped (add them if not).
6. Spike: three role apps behind one parent ASGI app work on the installed `mcp` 2.3.0 (see 3.2).

**Conclusion:** keep the MCP, move it next to Neo4j on EC2, add the roles and audit work, and make it read-only at the
database level. A rewrite is not needed.

---

## 1. Goal

Run Neo4j (Docker) and a Claude agent harness on one EC2 instance. Put a React app in front so everyone uses the **same
harness, tools, prompt and model**, behind a **login**, and each person sees only what their role allows (business
users get business language only; developers get code-level detail). Nobody reaches the MCP or Neo4j directly.

## 2. Target architecture

```
Browser (React SPA)
   │  HTTPS + OIDC login (Cognito / Entra / Okta / Keycloak)
   ▼
ALB / Nginx  (TLS, WAF, rate-limit, SSE/WebSocket support)
   ▼
Backend API (FastAPI or Node)
   │  validates JWT -> user_id, IdP group -> role (functional | technical | product)
   │  picks the service token for that role, starts a per-session agent (Claude Agent SDK)
   ▼
Agent worker (sandboxed container per session)
   ├─ Claude API key / Amazon Bedrock   (NOT a personal subscription)
   └─ spectrum-kg MCP, HTTP, localhost only
        ├─ token check -> role -> one of three role views
        ├─ audit log (JSON lines -> CloudWatch)
        ▼
     Neo4j (Docker, EBS volume, read-only user, private, S3 backups)
```

Rule: the browser never talks to Claude, the MCP or Neo4j directly.

---

## 3. Challenges and solutions

### 3.1 Licensing / "same Claude plan"  (highest priority)
**Challenge:** sharing one Pro/Max login through a custom app is not what consumer subscriptions are for. It risks a
ToS violation, rate-limit collisions and suspension.

**Solution:** use the Claude API with the Agent SDK (recommended) or Amazon Bedrock.

| Option | Pros | Cons |
|---|---|---|
| Claude API key + Agent SDK (recommended) | Built for this, per-token billing, spend limits | Variable cost |
| Amazon Bedrock | IAM auth, no keys, AWS billing, VPC endpoints | Model and feature lag |
| Claude Team/Enterprise seats + remote MCP connector | SSO, predictable cost, little code | No custom UI |
| Shared subscription via Claude Code CLI | Quick | **Avoid.** ToS risk |

Confirm the current terms with Anthropic or your account rep before Phase 3.

### 3.2 Authentication, authorization and roles
**Challenge:** the MCP must know who is calling and what they may see. The model must never choose its own identity or
role.

**Solution, in three layers**

1. **Users log in with OIDC in the backend.** Short-lived JWT, refresh token in an httpOnly cookie. The backend derives
   `user_id` and `role` from the IdP group (`kg-functional`, `kg-technical`, `kg-product`). A user with no group is denied.
2. **The backend is the only MCP client.** It holds **three service tokens**, one per role, stored in Secrets Manager.
   After validating the JWT it connects to the MCP with the token for that user's role. End users never see an MCP token.
   The MCP side is the roles plan: `access.yaml` stores only SHA-256 hashes, compared with `hmac.compare_digest`.
   Tokens carry an `expires` date, and a `kg user rotate` command swaps a token with no downtime (old and new both valid
   for a short overlap window).
3. **The MCP enforces the role in its data layer, not just the prompt.**

| Role | Sees | Tools | Answer style |
|---|---|---|---|
| functional | Modules, business processes, concepts, rules, screens (by business title only). No code, files, SPs, tables, columns. | `describe_graph`, `search`, `get_node`, `expand`, `find_paths`, `similar` (`run_cypher` not registered) | Plain business language |
| technical | Everything | All seven tools | Code-first: exact ids, chains, lineage |
| product | Everything (today's behaviour) | All seven tools | Plain language, brief |

How the functional view works (from the roles plan, with the fixes below):
- Allowlist of labels, relationships and properties. A hidden node returns the same "no node" error as a missing one.
- Screens appear as `screen:unit-master`, never `form:fUnitMaster`. Text is scrubbed (`Source:` lines, `through
  schema.Proc` clauses, code names, file names, graph ids, control-prefixed names).
- `expand`, `search` and `find_paths` push the allowed label and relationship sets into the Cypher itself, so
  pagination and limits stay correct.

**Solutions to issues found in the roles plan**

| Issue | Solution |
|---|---|
| Static token file vs OIDC users | Only three service tokens exist (one per role). User identity comes from the backend. |
| Per-user audit is lost behind shared tokens | Add a **trusted-backend** flag on a token entry. Calls from a trusted token may carry `x-kg-user` and `x-kg-session` (the backend's session id), which the MCP records. For every other token these headers are stripped, so they cannot be spoofed. |
| Regex scrubbing is best effort | Treat the **leak test as a release gate**: project every functional node and assert no technical identifier (SP, table, column, method, form code name, file name; case-insensitive, length 5 or more) appears. Run it in CI and after every graph rebuild. Add a second layer: functional answers are built only from curated `summary` and `doc` fields, never `code`. |
| Search could leak through ranking or scores | Build a **separate functional embedding set** from curated summary and doc text only. Functional `search` and `similar` use only that set and drop scores that point at hidden nodes. Verify with a test that functional `search("stored procedure")` returns no code-layer hits. |
| Screen id slugs may collide or change | Slug = title slug, plus a short stable hash of the form code when two titles collide. Store the map in the graph build output, not recomputed per request. Round-trip test for all 402 forms. |
| One database, application-level enforcement | Read-only Neo4j user. Optionally a second, functional-only database or a pre-filtered export if the leak test ever fails in production. |
| stdio `--role` lets a local user pick any role | Disable the stdio transport on EC2. Only token-authenticated HTTP runs there. |
| Per-role prompts in the backend | Keep the Agent SDK system prompt and `CLAUDE.md` identical across roles. The role-specific text comes from the MCP instructions. Set `allowedTools = ["mcp__spectrum-kg__*"]` only. No Bash, file or web tools, so the functional agent has no path around the scrubbing. |
| Three role apps behind one parent app on `mcp` 2.3.0 | First spike (half a day). If the session managers do not coexist, run three processes on ports 8765-8767 behind the same token check. |
| No per-token rate limit | Add a request cap per token per minute in the MCP, as a backstop to the backend quotas (3.5). |

### 3.3 Prompt injection and data exfiltration
**Challenge:** text in the KG (4,900 rules, 400 concepts, curated docs) or typed by users can steer the agent.

**Solution**
- Read-only Neo4j user plus driver READ mode (already true for `run_cypher`).
- Validate Cypher. Reject `CREATE|MERGE|DELETE|SET|REMOVE|DROP|CALL dbms|apoc.* writes|LOAD CSV`.
- Query timeout, row cap and character cap per tool result.
- Functional role has no `run_cypher` at all, which removes the largest injection surface for business users.
- Agent SDK `allowedTools` limited to the KG MCP tools. Disable Bash, file write and web fetch.
- Egress allow-list: workers reach only the Claude/Bedrock endpoint and the MCP.
- Treat all tool results as data. The MCP instructions say so, and the backend system prompt repeats it.

### 3.4 Concurrency and isolation
**Challenge:** one shared Claude Code process is stateful, so contexts can mix and calls collide.

**Solution**
- Treat the harness as a service: one SDK session per conversation, `session_id` stored in Postgres.
- Per-session container or isolated working directory.
- Queue (SQS/Redis) with caps per user and globally. Backoff on rate limits and a "queued" state in the UI.
- "Same harness" means a **versioned shared config in git**: system prompt, `CLAUDE.md`, allowed tools, model, MCP
  config, and the MCP role definitions. One release tag covers all of them.
- Alternative: Claude Managed Agents, if you do not want to run workers.

### 3.5 Cost control
- Cap rows and characters per tool result.
- `max_turns` and a token budget per request.
- Prompt caching for the system prompt and the role's `describe_graph` output.
- Cheaper model for lookups, stronger model on demand.
- Per-user daily quotas, usage logged per user. AWS Budgets or an API spend cap.

### 3.6 Streaming and UX
- SSE or WebSocket with an ALB idle timeout of at least 120 s.
- Stream tool-call events ("searching business rules...") and support cancel. For the functional role, show business
  labels for tool steps, not tool names or ids.
- Persist chats so a refresh does not lose them.

### 3.7 Neo4j in Docker on EC2
- Data on a dedicated **EBS volume** at `/data`.
- Bolt 7687 and HTTP 7474 on localhost or a private subnet only.
- Heap and pagecache at roughly 50-60% of RAM. The graph is about 91k nodes and 509k relationships, which fits easily;
  start at 16 GB (r6i.large) and measure before sizing up.
- Daily `neo4j-admin database dump` to S3 plus EBS snapshots. **Test restores.**
- Auth on. Secrets in Secrets Manager or SSM. Pin the image tag. `restart: unless-stopped`.
- Embeddings (1,024 dimensions, Qwen3-Embedding-0.6B) ship with the graph. Keep the model name and version in `KGMeta`
  so a restore cannot silently mix embedding models.
- Alternatives: Neo4j AuraDB, or a separate EC2 for the database.

### 3.8 Observability, audit and EC2 hardening
**Audit (from the roles plan)**
- `audited(tool)` wrapper on every tool records: timestamp, user, role, session id, transport, request id, tool,
  arguments (truncated), duration, result count, error, and denied/filtered/scrubbed counts. The token is never logged.
- JSON lines in `logs/mcp-audit.jsonl`, rotated daily. On EC2 the CloudWatch agent ships them; retention is set per
  3.11. Never write to stdout (the stdio protocol channel).
- `kg usage --since 7d --by user|role|tool` reports calls, error rate, p50/p95 latency, denied counts, top search
  queries and recent 401s.
- Join key: the backend's `session_id` is in both the MCP audit and the Postgres usage table, so one question can be
  traced from browser to Cypher.
- Alerts: spike in 401s, any `denied` count on the functional role above a threshold, error rate above 5%.

**Hardening:** private subnets, only the ALB public, IMDSv2, SSM Session Manager (no open SSH), least-privilege IAM
role, WAF and rate limits, TLS via ACM.

### 3.9 Reliability
A single instance is a single point of failure. Start there, but use Terraform or an AMI so it is rebuildable, add
health checks, and plan to split API, workers and database later. Monitor latency, errors, token spend, Neo4j heap and
page cache. Graph rebuilds are a release step: build, run the leak test, snapshot, then swap.

### 3.10 KG query quality
`describe_graph` is the cached schema, one per role. Add few-shot examples and a domain glossary (the graph already
holds concept synonyms). Log failed and empty searches (the audit log has them) and feed them back into the prompt.

### 3.11 Compliance and privacy
Decide what data may go to the Claude API (PII, client data). Use Bedrock if data must stay in AWS. The functional
role's property allowlist and scrubbing are the masking layer. Set audit-log retention (suggest 90 days hot, then
archive) and make sure user ids in logs are pseudonymous if policy requires it.

---

## 4. Implementation steps

### 4.1 EC2 and Neo4j
```yaml
# docker-compose.yml (sketch)
services:
  neo4j:
    image: neo4j:5-community        # pin an exact tag
    restart: unless-stopped
    ports: ["127.0.0.1:7687:7687", "127.0.0.1:7474:7474"]
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_server_memory_heap_max__size: 6G
      NEO4J_server_memory_pagecache_size: 6G
    volumes: ["/mnt/neo4j-data:/data", "/mnt/neo4j-logs:/logs"]
  kg-mcp:                            # the existing spectrum-kg MCP, HTTP transport only
    build: ./spectrum-kg-mcp
    restart: unless-stopped
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: kg_reader          # read-only user
      NEO4J_PASSWORD: ${KG_READER_PASSWORD}
      KG_ACCESS_FILE: /run/secrets/access.yaml   # hashed service tokens
      KG_AUDIT_LOG: /var/log/kg/mcp-audit.jsonl
    volumes: ["/var/log/kg:/var/log/kg"]
    ports: ["127.0.0.1:8765:8765"]
```

### 4.2 Migrate the existing graph
Dump from the current Neo4j (`neo4j-admin database dump`), copy to S3, restore on EC2 (`neo4j-admin database load`).
Create the read-only role and user. Run the leak test against the restored graph before opening access.

### 4.3 Harden the MCP (the roles plan, as exit criteria)
- `access.py`, `roles.py`, `observe.py`, `build_server(role)` and the parent ASGI app, per the roles plan.
- Trusted-backend token flag, token expiry and `kg user rotate`, per-token rate cap.
- Functional-only embedding set.
- Tests: leak test, `scrub_text` unit tests, `RoleView` with a fake client, stdio handshake (6 vs 7 tools), HTTP 401 and
  header-spoof tests, a write-attempt test against the read-only user.

### 4.4 Backend
Endpoints: `POST /chat` (SSE stream), `GET /sessions`, `DELETE /sessions/:id`. Per request:
1. Validate the JWT, map the IdP group to a role.
2. Fetch that role's service token. Connect with the Agent SDK:
   `mcp_servers={"spectrum-kg": {"type": "http", "url": "http://localhost:8765/mcp", "headers": {"Authorization": "Bearer <role token>", "x-kg-user": "<user_id>", "x-kg-session": "<session_id>"}}}`
   and `allowedTools=["mcp__spectrum-kg__*"]`.
3. Store users, sessions, messages and usage in Postgres.

### 4.5 React app
Login via OIDC (PKCE), chat UI with streaming and tool-step display, session history, and an admin page for users,
roles, usage and the MCP audit summary. Never show technical ids to functional users.

---

## 5. Phased rollout

| Phase | Deliverable | Time |
|---|---|---|
| 0 | Decisions: Claude auth (API/Bedrock), IdP and group-to-role map, data sensitivity, instance size. Confirm the MCP host. Spike: three role apps on `mcp` 2.3.0. | 1 wk |
| 1 | EC2, Docker Neo4j, EBS, backups, networking, graph restored | 1 wk |
| 2 | Harden the MCP: read-only user, limits, **roles, tokens, audit, leak test** (exit criterion: leak test green) | 2 wk |
| 3 | Agent backend: sessions, streaming, usage logging, role-to-token mapping, `session_id` audit join | 1-2 wk |
| 4 | OIDC login and React UI | 1-2 wk |
| 5 | Hardening: WAF, quotas, CloudWatch alerts, load test, restore drill, token rotation drill | 1 wk |
| 6 | Pilot (one team per role), then general availability | ongoing |

## 6. Alternatives to the whole design

1. **Claude Team/Enterprise + remote MCP connector with OAuth.** Least code, SSO and billing built in. You do not control
   the UI, and the role-based views would need the MCP to do OAuth per user.
2. **Bedrock Agents / AgentCore + Neo4j.** Fully AWS-native, IAM and Cognito integration.
3. **LangGraph or a custom tool-calling loop** in place of the Agent SDK, for tighter control.

## 7. Recommendation

Claude Agent SDK with an **API key or Bedrock**, behind a **FastAPI backend with OIDC login**, reusing the **existing
`spectrum-kg` MCP** with **role views (functional, technical, product), service tokens per role, and an audit log**,
running localhost-only against a **read-only** Neo4j user. Per-session sandboxed workers, quotas, and Neo4j in Docker
on EBS with S3 backups. Settle licensing (3.1) first, and make the leak test a release gate.

## 8. Risk register

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| Functional user sees a code identifier | Medium | High | Leak test as CI and release gate; curated-only text; functional embedding set | MCP dev |
| Service token leaked | Low | High | Secrets Manager, expiry, rotation drill, localhost-only MCP, 401 alerts | Platform |
| Role mapping wrong (user gets technical view) | Low | High | Deny by default, group-to-role tests, admin page shows effective role | Backend dev |
| Claude licensing or ToS issue | Medium | High | API or Bedrock only, written confirmation before Phase 3 | Product |
| Graph rebuild changes ids or titles | Medium | Medium | Rebuild pipeline runs leak test and slug round trip before swap | MCP dev |
| Cost overrun | Medium | Medium | Quotas, `max_turns`, caching, budgets | Platform |
| Single instance outage | Medium | Medium | Terraform, snapshots, restore drill | Platform |
| MCP SDK cannot host three role apps in one process | Low | Low | Fall back to three processes | MCP dev |

## 9. Changes from revision 1

- Section 0 now lists the real tools and the current graph size, and replaces "no auth" with the roles design.
- Section 3.2 rewritten: OIDC in the backend, three service tokens, trusted-backend header for per-user audit,
  role table, and a solution table for each issue found in the roles plan.
- Stale tool names (`neighbors`, `find_entity`) removed.
- Section 3.8 expanded into audit and observability with CloudWatch, join key and alerts.
- Phase 2 now includes roles, tokens, audit and the leak test; its exit criterion is a green leak test.
- Added the risk register (section 8) and this change list.
- Not yet verified against the code: whether `mcp` 2.3.0 hosts three role apps in one process, and whether the current
  embeddings include code text. Both are scheduled as Phase 0 and Phase 2 checks.
