# Plan: Shared Claude Harness + Neo4j KG on EC2 with a React Front End

## 0. Can we reuse the existing MCP (`spectrum-kg`)?

**Yes, most likely, and we should.** Your current config is:

```json
"spectrum-kg": { "type": "http", "url": "http://192.168.0.59:8765/mcp" }
```

It is a **streamable-HTTP MCP server on a LAN host with no auth header**. That makes it easy to move:

| Aspect | Status | Action |
|---|---|---|
| Transport | HTTP, so it is network-addressable | Run it on the EC2 box (or a sibling container) and point the agent at `http://localhost:8765/mcp` or an internal DNS name. No code change if it reads the Neo4j URL from config/env. |
| Neo4j connection | Presumably points at a local or LAN Neo4j | Change the Bolt URI, user and password to the new Dockerised Neo4j (env vars, secrets from AWS Secrets Manager). |
| Auth | **None** (open on the LAN) | Never expose port 8765 publicly. Bind to localhost or a private subnet. Only the backend and agent worker may reach it. User login lives in the backend, not the MCP. |
| Write safety | Unknown. **Must verify** | Check its tools. If any tool can run write Cypher, make it read-only (see section 4.3). |
| Identity per user | None | Either add a header (e.g. `X-User-Role`, set by the backend and not the model) that the MCP honours, or run it with a read-only DB user shared by all. |
| Current state | It **timed out on connect this session** (`CONNECT_TIMEOUT`, version-negotiation probe, 5 s) | The LAN host `192.168.0.59` is probably down or unreachable. Confirm the server is running and reachable before migrating. |

**Checklist before reuse**
1. Start the server and confirm it answers: `curl -i http://192.168.0.59:8765/mcp`.
2. List its tools and confirm none can mutate the graph.
3. Check where it reads Neo4j credentials from (env or hard-coded).
4. Check that it handles concurrent sessions (stateless HTTP is ideal).
5. Check that it caps result size and sets query timeouts. Add them if not.

**Conclusion:** keep the MCP, move it next to Neo4j on EC2, wrap it with auth in the backend, and harden it. A rewrite is only worth it if step 2 shows unsafe write tools that can't be disabled.

---

## 1. Goal

Run Neo4j (Docker) and a Claude agent harness on one EC2 instance. Put a React app in front of it so everyone uses the **same harness, tools, prompt and model**, behind a **login**. Nobody gets the MCP directly.

## 2. Target architecture

```
Browser (React SPA)
   │  HTTPS + OIDC login (Cognito / Entra / Okta / Keycloak)
   ▼
ALB / Nginx  (TLS, WAF, rate-limit, SSE/WebSocket support)
   ▼
Backend API (FastAPI or Node)
   │  validates JWT -> user_id, role
   │  starts a per-session agent (Claude Agent SDK)
   ▼
Agent worker (sandboxed container per session)
   ├─ Claude API key / Amazon Bedrock   (NOT a personal subscription)
   └─ spectrum-kg MCP (existing, hardened, localhost only)
          ▼
       Neo4j (Docker, EBS volume, private, S3 backups)
```

Rule: the browser never talks to Claude, the MCP or Neo4j directly.

---

## 3. Challenges and rectifications

### 3.1 Licensing / "same Claude plan"  (highest priority)
**Challenge:** Sharing one Pro/Max login across many users through a custom app is not what consumer subscriptions are for. It risks a ToS violation, rate-limit collisions and account suspension.

**Fix, in order of preference:**

| Option | Pros | Cons |
|---|---|---|
| Claude API key + Agent SDK (recommended) | Built for this, per-token billing, spend limits | Variable cost |
| Amazon Bedrock | IAM auth, no keys, AWS billing, VPC endpoints | Model and feature lag |
| Claude Team/Enterprise seats + remote MCP connector | SSO, predictable cost, little code | No custom UI |
| Shared subscription via Claude Code CLI | Quick | **Avoid.** ToS risk |

Confirm the current terms with Anthropic or your account rep.

### 3.2 Authentication and authorization
**Challenge:** MCP has no user identity. The agent could run anything for anyone.

**Fix**
- OIDC provider (Cognito if AWS-native, Entra/Okta for corporate SSO, Keycloak if self-hosted). Short-lived JWT, refresh token in an httpOnly cookie.
- Backend validates the JWT on every request and derives `user_id`, `role`, `tenant`.
- Identity is injected **server-side** (header or env to the MCP). The model never supplies it.
- Roles map to tool sets (e.g. viewer: `search`/`neighbors`; analyst: adds custom Cypher).
- Neo4j Community has no fine-grained RBAC, so enforce limits in the MCP layer. Enterprise supports roles and impersonation.
- Alternative: OAuth 2.1 on the MCP itself, if external MCP clients need access later.

### 3.3 Prompt injection and data exfiltration
**Challenge:** Text in the KG or typed by users can steer the agent into harmful queries.

**Fix**
- Read-only Neo4j user plus driver `READ` access mode.
- Validate Cypher. Reject `CREATE|MERGE|DELETE|SET|REMOVE|DROP|CALL dbms|apoc.* writes|LOAD CSV`.
- Query timeout, row cap, character cap per tool result.
- Agent SDK `allowedTools` set to the KG MCP tools only. Disable Bash, file write and web fetch.
- Egress allow-list: workers can reach only the Claude/Bedrock endpoint and the MCP.
- Safest alternative: curated parameterised tools (`find_entity`, `neighbors`, `shortest_path`) with no raw Cypher.

### 3.4 Concurrency and isolation
**Challenge:** One shared Claude Code process is stateful, so contexts can mix and calls collide.

**Fix**
- Treat the harness as a service: one SDK session per conversation, `session_id` stored in your DB.
- Per-session container or isolated working directory.
- Queue (SQS/Redis) with caps per user and globally. Backoff on rate limits and a "queued" state in the UI.
- "Same harness" = a **versioned shared config in git**: system prompt, `CLAUDE.md`, allowed tools, model, MCP config.
- Alternative: Claude Managed Agents, if you don't want to run workers.

### 3.5 Cost control
- Cap rows and characters per tool result.
- Set `max_turns` and a token budget per request.
- Prompt caching for the system prompt and schema.
- Cheaper model for lookups and a stronger one on demand.
- Per-user daily quotas, usage logged per user. AWS Budgets or an API spend cap.

### 3.6 Streaming and UX
- SSE or WebSocket, with ALB idle timeout of at least 120 s.
- Stream tool-call events ("querying graph...") and support cancel.
- Persist chats so a refresh doesn't lose them.

### 3.7 Neo4j in Docker on EC2
- Data on a dedicated **EBS volume** mounted at `/data`.
- Bolt 7687 and HTTP 7474 on localhost or a private subnet only.
- Heap and pagecache at roughly 50-60% of RAM. Start with 16 GB or more (r6i.large/xlarge).
- Daily `neo4j-admin database dump` to S3 plus EBS snapshots. **Test restores.**
- Auth on. Secrets in Secrets Manager or SSM. Pin the image tag. `restart: unless-stopped`.
- Alternatives: Neo4j AuraDB (managed), or a separate EC2 for the DB so workers scale independently.

### 3.8 EC2 hardening
Private subnets, only the ALB public, IMDSv2, SSM Session Manager (no open SSH), least-privilege IAM role, WAF and rate limits, TLS via ACM. Audit log of user, question, Cypher run and tokens, shipped to CloudWatch.

### 3.9 Reliability
A single instance is a single point of failure. Start there, but use Terraform or an AMI so it is rebuildable, add health checks, and plan to split the API, workers and DB later. Monitor latency, errors, token spend, Neo4j heap and page cache.

### 3.10 KG query quality
Provide the schema through a `get_schema` tool or the cached prompt. Add few-shot Cypher and a domain glossary. Log failed queries and feed them back into the prompt. Consider vector indexes for entity lookup.

### 3.11 Compliance and privacy
Decide what data may go to the Claude API (PII, client data). Use Bedrock if data must stay in AWS. Mask sensitive properties in the MCP layer. Set log-retention rules.

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
  kg-mcp:                            # the existing spectrum-kg MCP
    build: ./spectrum-kg-mcp
    restart: unless-stopped
    environment:
      NEO4J_URI: bolt://neo4j:7687
      NEO4J_USER: kg_reader          # read-only user
      NEO4J_PASSWORD: ${KG_READER_PASSWORD}
    ports: ["127.0.0.1:8765:8765"]
```

### 4.2 Migrate the existing graph
Dump from the current Neo4j (`neo4j-admin database dump`), copy to S3, restore on EC2 (`neo4j-admin database load`). Create a read-only role and user for the MCP.

### 4.3 Harden the MCP
Read-only DB user, Cypher validator, timeout, row and char limits, optional identity header, structured logging.

### 4.4 Backend
Endpoints: `POST /chat` (SSE stream), `GET /sessions`, `DELETE /sessions/:id`. Uses the Agent SDK with `mcp_servers={"spectrum-kg": {"type": "http", "url": "http://localhost:8765/mcp"}}` and `allowedTools=["mcp__spectrum-kg__*"]`. Store users, sessions, messages and usage in Postgres.

### 4.5 React app
Login via OIDC (PKCE), chat UI with streaming and tool-call display, session history, admin page for users, roles and usage.

---

## 5. Phased rollout

| Phase | Deliverable | Time |
|---|---|---|
| 0 | Decisions: Claude auth (API/Bedrock), IdP, data sensitivity, instance size. Fix or confirm the MCP host. | 1 wk |
| 1 | EC2, Docker Neo4j, EBS, backups, networking, graph restored | 1 wk |
| 2 | Reuse and harden the `spectrum-kg` MCP (read-only, limits, tests) | 1 wk |
| 3 | Agent backend: sessions, streaming, usage logging | 1-2 wk |
| 4 | OIDC login and React UI, role-based tools | 1-2 wk |
| 5 | Hardening: WAF, quotas, audit, load test, restore drill | 1 wk |
| 6 | Pilot, then general availability | ongoing |

## 6. Alternatives to the whole design

1. **Claude Team/Enterprise + remote MCP connector with OAuth.** Least code, and SSO and billing come built in. You don't control the UI.
2. **Bedrock Agents / AgentCore + Neo4j.** Fully AWS-native, IAM and Cognito integration.
3. **LangGraph or a custom tool-calling loop** in place of the Agent SDK, for tighter control.

## 7. Recommendation

Claude Agent SDK with an **API key or Bedrock**, behind a **FastAPI backend with OIDC login**, reusing the **existing `spectrum-kg` MCP** (hardened, localhost-only), per-session sandboxed workers, quotas and audit logs, and Neo4j in Docker on EBS with S3 backups. Settle licensing (3.1) first, and fix the MCP connectivity issue before migrating.
