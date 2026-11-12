# SpectrumERP Knowledge Graph — Setup Guide

This repo contains a **knowledge graph of the SpectrumERP codebase** (all 14 delivery phases, 0-13: about 400 forms
across Material Management, Plant Maintenance, Finance, Sales and Distribution, Production Planning, Master Data,
Weigh Bridge, Discrete Raw Material, Settings and the report catalogue) and an **MCP server** called `spectrum-kg` that lets Claude (or any other MCP client) explore it: business processes, forms,
code methods, stored procedures, tables and columns.

This guide takes you from `git clone` to asking Claude questions about the ERP.

```
 Your AI client (Claude Code / Claude Desktop / VS Code / Cursor ...)
          │  MCP (stdio or HTTP)
          ▼
 spectrum-kg MCP server  (Python, in KnowledgeGraph/)
          │  Bolt / neo4j+s://
          ▼
 Neo4j database (Aura cloud)  ← holds the graph
```

> **Key point:** the MCP server does not contain the data. It reads from a Neo4j database. You either
> **connect to the team's existing Neo4j instance** (fastest — ask for the credentials) or **build your own graph**
> (needs the source bundles, see [Part B](#part-b-optional--build-your-own-graph)).

---

## Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the repo](#2-clone-the-repo)
3. [Install the Python environment](#3-install-the-python-environment)
4. [Configure `.env`](#4-configure-env)
5. [Check the connection](#5-check-the-connection)
6. [Start the MCP server](#6-start-the-mcp-server)
7. [Connect a client](#7-connect-a-client) — Claude Code, Claude Desktop, VS Code, Cursor, others
8. [Try it](#8-try-it)
9. [Share the server on your network (HTTP)](#9-share-the-server-on-your-network-http)
10. [Troubleshooting](#10-troubleshooting)
- [Part B (optional) — build your own graph](#part-b-optional--build-your-own-graph)

---

## 1. Prerequisites

| Need | Version | Check with | Get it |
|---|---|---|---|
| Git | any | `git --version` | https://git-scm.com/downloads |
| Python | **3.11 or newer** (3.13 recommended) | `py -3.13 --version` (Windows) / `python3 --version` | https://www.python.org/downloads/ |
| Neo4j credentials | — | — | Ask the team for the URI / username / password, **or** create a free instance at https://neo4j.com/cloud/aura/ and follow Part B |
| Disk space | ~3 GB | — | For PyTorch + the local embedding model |
| Node.js *(optional)* | 18+ | `node --version` | Only for the MCP Inspector or `mcp-remote` |
| .NET SDK *(Part B only)* | 8+ | `dotnet --version` | Only needed to **build** a graph |

> On Windows, tick **"Add python.exe to PATH"** when installing Python. The `py` launcher comes with it.

---

## 2. Clone the repo

```powershell
git clone https://github.com/Ankittian/SpectrumERP.git
cd SpectrumERP\KnowledgeGraph
```

Everything below is run from the `KnowledgeGraph` folder unless stated otherwise.

The examples use `D:\SpectrumERP` as the clone location. **If you cloned somewhere else, replace that path
everywhere in this guide.**

---

## 3. Install the Python environment

The launcher scripts expect the virtual environment to be at `KnowledgeGraph\.venv`, so create it exactly there.

> **Always create `.venv` on the machine that uses it — never copy it from someone else.** A virtual environment
> stores absolute paths (to the Python install and to `src\`), so a copied one fails with
> `No Python at '...'` or `No module named 'spectrum_kg'`. If you received a `.venv` folder, delete it and run the
> commands below. When sharing the folder, leave out `.venv`, `.cache` and `__pycache__`.

**Windows (PowerShell):**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

**macOS / Linux:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
```

This installs the `kg` command and all dependencies (neo4j, mcp, sentence-transformers / PyTorch, ...). It takes a few
minutes the first time — PyTorch is large.

Check it worked:

```powershell
.\.venv\Scripts\kg --help        # macOS/Linux: .venv/bin/kg --help
```

---

## 4. Configure `.env`

Copy the template and open it in an editor:

```powershell
copy .env.example .env           # macOS/Linux: cp .env.example .env
notepad .env
```

Fill in at least these values:

```ini
# Neo4j — from the team, or from the credentials file Aura gives you when you create an instance
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=

# Embeddings used for search queries. MUST match how the graph was built.
# The shared graph was built with the local model below, so keep these defaults:
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B
EMBEDDING_DIMENSIONS=1024

# Only needed if you run the HTTP server (section 9)
# KG_MCP_TOKEN=some-long-random-string
```

| Variable | Required | Meaning |
|---|---|---|
| `NEO4J_URI` | yes | Address of the Neo4j database |
| `NEO4J_USERNAME` | yes | Usually `neo4j` |
| `NEO4J_PASSWORD` | yes | Database password |
| `NEO4J_DATABASE` | no | Leave empty for the default database |
| `EMBEDDING_PROVIDER` | no | `local` (default, runs on your PC, free) or `voyage` (cloud API) |
| `LOCAL_EMBEDDING_MODEL` | no | Model for `local`. Downloaded automatically (~1.2 GB) on the first search |
| `VOYAGE_API_KEY` | only if `voyage` | Key from https://dashboard.voyageai.com/ |
| `KG_MCP_TOKEN` | only for HTTP | Password that network clients must send |

> `.env` is git-ignored. **Never commit it** — it contains your database password.

---

## 5. Check the connection

This one-liner connects to Neo4j and reads the graph's summary (Windows; on macOS/Linux use `.venv/bin/python`):

```powershell
.\.venv\Scripts\python -c "from spectrum_kg.config import load_settings; from spectrum_kg.queries import KGClient; d=KGClient(load_settings()).describe_graph(); print('Connected. Built', d['built_at'], 'with', d['embedding_model'], '-', sum(l['count'] for l in d['labels']), 'nodes')"
```

Expected output (about 20K nodes for the full graph):

```
Connected. Built 2026-11-05T13:32:01+00:00 with Qwen/Qwen3-Embedding-0.6B - 20178 nodes
```

- **You see `Connected`** → the database has a graph. Check the model name matches `LOCAL_EMBEDDING_MODEL` in `.env`, then continue to step 6.
- **Error about `NEO4J_URI is not set`** → `.env` is missing or not in the `KnowledgeGraph` folder.
- **Connection / auth error** → check the URI and password; Aura Free instances pause after a few days without use —
  resume it at https://console.neo4j.io.
- **`0 nodes` / `with None`** → the database is empty; build the graph with [Part B](#part-b-optional--build-your-own-graph).

---

## 6. Start the MCP server

You usually **don't start it by hand**: the client (Claude etc.) launches it automatically when configured as in
step 7. Running it manually is just a quick test.

**Windows:**

```powershell
.\run-mcp.cmd
```

**macOS / Linux:**

```bash
.venv/bin/python -m spectrum_kg.mcp_server
```

It will print nothing and wait — that is correct. In stdio mode the server talks over stdin/stdout to the client.
Press `Ctrl+C` to stop it.

To see the tools interactively in a browser, use the **MCP Inspector** (needs Node.js):

```powershell
npx @modelcontextprotocol/inspector cmd /c D:\SpectrumERP\KnowledgeGraph\run-mcp.cmd
# macOS/Linux:
npx @modelcontextprotocol/inspector /path/to/SpectrumERP/KnowledgeGraph/.venv/bin/python -m spectrum_kg.mcp_server
```

Open the URL it prints, click **Connect → Tools → List Tools**, then run `describe_graph`.

---

## 7. Connect a client

Pick the client you use. In every example, replace `D:\SpectrumERP` with your clone path.

### 7a. Claude Code (CLI / VS Code extension / desktop app)

**Windows:**

```powershell
claude mcp add spectrum-kg --scope user -- cmd /c D:\SpectrumERP\KnowledgeGraph\run-mcp.cmd
```

**macOS / Linux:**

```bash
claude mcp add spectrum-kg --scope user -- /path/to/SpectrumERP/KnowledgeGraph/.venv/bin/python -m spectrum_kg.mcp_server
```

`--scope user` makes it available in every project; drop it to register for the current folder only.

Verify:

```powershell
claude mcp list          # spectrum-kg should show "✓ Connected"
```

Inside a Claude Code session, type `/mcp` to see the server and its tools.

To remove it later: `claude mcp remove spectrum-kg`.

### 7b. Claude Desktop

1. Open Claude Desktop → **Settings → Developer → Edit Config**. This opens `claude_desktop_config.json`
   (Windows: `%APPDATA%\Claude\claude_desktop_config.json`, macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`).
2. Add the server (merge with any existing `mcpServers` entries):

   **Windows:**

   ```json
   {
     "mcpServers": {
       "spectrum-kg": {
         "command": "cmd",
         "args": ["/c", "D:\\SpectrumERP\\KnowledgeGraph\\run-mcp.cmd"]
       }
     }
   }
   ```

   **macOS / Linux:**

   ```json
   {
     "mcpServers": {
       "spectrum-kg": {
         "command": "/path/to/SpectrumERP/KnowledgeGraph/.venv/bin/python",
         "args": ["-m", "spectrum_kg.mcp_server"]
       }
     }
   }
   ```

   Note the **double backslashes** in Windows paths inside JSON.
3. **Fully quit** Claude Desktop (system tray → Quit) and reopen it. The tools appear under the 🔨 / tools icon in the
   chat box.

### 7c. VS Code (GitHub Copilot agent mode)

Create `.vscode/mcp.json` in your workspace (or run **MCP: Add Server** from the command palette):

```json
{
  "servers": {
    "spectrum-kg": {
      "type": "stdio",
      "command": "cmd",
      "args": ["/c", "D:\\SpectrumERP\\KnowledgeGraph\\run-mcp.cmd"]
    }
  }
}
```

Click **Start** above the server entry, then open Copilot Chat in **Agent** mode.

### 7d. Cursor / Windsurf / other clients

Most clients use the same `mcpServers` JSON as Claude Desktop (7b). For Cursor put it in `~/.cursor/mcp.json`
(global) or `.cursor/mcp.json` (project), then enable the server under **Settings → MCP**.

Any MCP client works if you give it:

| Setting | Value (Windows) | Value (macOS/Linux) |
|---|---|---|
| Transport | stdio | stdio |
| Command | `cmd` | `<clone>/KnowledgeGraph/.venv/bin/python` |
| Arguments | `/c <clone>\KnowledgeGraph\run-mcp.cmd` | `-m spectrum_kg.mcp_server` |

For clients on **another machine**, use the HTTP server in [section 9](#9-share-the-server-on-your-network-http).

---

## 8. Try it

Start a new chat in your client and ask, for example:

- *"Using spectrum-kg, describe the graph."*
- *"Which business process does the Purchase Order form belong to, and what are its steps?"*
- *"Which stored procedures write to `masterdata.munitmaster`, and which forms call them?"*
- *"Trace the Unit Name field on fUnitMaster from the control down to the database column."*
- *"If I change the column `masterdata.munitmaster.unitname`, which forms are affected?"*

The first search may take 30–60 seconds while the local embedding model downloads; after that it is fast.

### Tools the server provides

| Tool | What it does |
|---|---|
| `describe_graph` | The map: node labels, relationship types, counts, id conventions, traversal strategies |
| `search` | Find entry points by text (hybrid / vector / fulltext); filter by labels or module |
| `get_node` | One node's details (`summary`, `full`, or `code`) plus hints about where to go next |
| `expand` | Follow relationships one hop out from a set of nodes |
| `find_paths` | Shortest paths between two nodes |
| `similar` | Semantically similar nodes |
| `run_cypher` | Read-only Cypher query (escape hatch) |

The server never writes to the database. More detail on the graph model: [`KnowledgeGraph/README.md`](KnowledgeGraph/README.md)
and [`docs/reference/graph-build-spec.md`](docs/reference/graph-build-spec.md).

---

## 9. Share the server on your network (HTTP)

Run the server once on one PC and let teammates connect without installing anything except their client.

**On the host PC:**

1. Add a shared secret to `KnowledgeGraph\.env`:

   ```ini
   KG_MCP_TOKEN=pick-a-long-random-string
   ```

   (Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.)
2. Start the HTTP server:

   ```powershell
   .\run-mcp-http.cmd
   # macOS/Linux:
   .venv/bin/python -m spectrum_kg.mcp_server --transport http --host 0.0.0.0 --port 8765
   ```

   It prints `spectrum-kg MCP listening on http://0.0.0.0:8765/mcp`. Leave the window open.
3. Find the host's IP address: `ipconfig` (Windows) → *IPv4 Address*, e.g. `192.168.1.50`.
4. Allow the port through Windows Firewall (run PowerShell **as Administrator**, once):

   ```powershell
   New-NetFirewallRule -DisplayName "spectrum-kg MCP" -Direction Inbound -Protocol TCP -LocalPort 8765 -Action Allow
   ```

Options: `--port 9000` to change the port, `--host 127.0.0.1` for this PC only, `--token xyz` instead of the `.env` value.
Without a token the server warns that anyone on the network can query it.

**On each client machine** (replace the IP and token):

- **Claude Code:**

  ```powershell
  claude mcp add --transport http spectrum-kg http://192.168.1.50:8765/mcp --header "Authorization: Bearer pick-a-long-random-string"
  ```

- **VS Code** (`.vscode/mcp.json`):

  ```json
  {
    "servers": {
      "spectrum-kg": {
        "type": "http",
        "url": "http://192.168.1.50:8765/mcp",
        "headers": { "Authorization": "Bearer pick-a-long-random-string" }
      }
    }
  }
  ```

- **Cursor** (`mcp.json`):

  ```json
  {
    "mcpServers": {
      "spectrum-kg": {
        "url": "http://192.168.1.50:8765/mcp",
        "headers": { "Authorization": "Bearer pick-a-long-random-string" }
      }
    }
  }
  ```

- **Claude Desktop** (needs Node.js; it bridges HTTP to stdio):

  ```json
  {
    "mcpServers": {
      "spectrum-kg": {
        "command": "npx",
        "args": ["-y", "mcp-remote", "http://192.168.1.50:8765/mcp", "--allow-http",
                 "--header", "Authorization: Bearer pick-a-long-random-string"]
      }
    }
  }
  ```

Quick test from a client machine — a `401 unauthorized` response means the server is reachable and the token check works:

```powershell
curl.exe -i http://192.168.1.50:8765/mcp
```

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `py` is not recognized | Reinstall Python with "Add to PATH", or use the full path to `python.exe` |
| `run-mcp.cmd` fails / "system cannot find the path" | The venv must be at `KnowledgeGraph\.venv` (step 3). Re-create it there |
| `NEO4J_URI is not set` | `.env` must be inside `KnowledgeGraph\`, next to `kg.yaml` |
| Neo4j `ServiceUnavailable` / auth errors | Check URI/password; resume a paused Aura instance at https://console.neo4j.io; corporate firewalls must allow port 7687 |
| Client shows the server as failed | Run the exact command from step 6 in a terminal to see the error. Make sure paths in JSON use `\\` |
| Server works in terminal but not in Claude Desktop | Fully quit Desktop from the system tray and reopen; check logs in `%APPDATA%\Claude\logs\mcp*.log` |
| First `search` is very slow or times out | The embedding model is downloading (~1.2 GB). Wait, or run `.\.venv\Scripts\python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('Qwen/Qwen3-Embedding-0.6B')"` once beforehand |
| Search results look random | `EMBEDDING_PROVIDER` / `LOCAL_EMBEDDING_MODEL` in `.env` don't match the model the graph was built with. `describe_graph` shows the `embedding_model` used |
| HTTP clients get `401` | Token mismatch — the header must be exactly `Authorization: Bearer <KG_MCP_TOKEN>` |
| HTTP clients can't connect at all | Host server not running, wrong IP, or firewall rule missing (section 9, step 4) |

---

## Part B (optional) — load the graph into your own Neo4j

Only needed if you have your **own empty Neo4j instance**, or want to reload or re-embed the shared graph.

The graph itself is built on the machine that has the ERP source (phases 0-13 in one build) and delivered as
`KnowledgeGraph/graph/graph.json` (about 275 MB, **not in git**, get it from the team). `kg.yaml` points at it
(`graph_json: graph/graph.json`), so every `kg` command loads that file; no source code or .NET is needed here.
How it was built, and its counts and checks, are in `KnowledgeGraph/graph/MANIFEST.md`.

From `KnowledgeGraph\`:

```powershell
.\.venv\Scripts\kg stats         # node/edge counts of graph.json (offline)
.\.venv\Scripts\kg build         # embeds every node and loads everything into Neo4j
```

Then re-run the connection check from step 5 to confirm the graph is in Neo4j.

- `kg build` is safe to re-run; only new or changed texts are re-embedded (vectors are cached in `.cache/`).
- With `EMBEDDING_PROVIDER=local` embedding runs on your PC (a GPU helps; CPU works but is slower). To load first and
  embed in resumable slices: `kg build --embed-budget 0`, then `kg embed-step` until it prints `COMPLETE`.
- `kg export-html` writes `kg-graph.html`, an offline interactive viewer of the graph (no Neo4j needed).
- To rebuild the graph from source (new forms, changed domain docs), see
  [`KnowledgeGraph/README.md`](KnowledgeGraph/README.md#building-from-source).

Run the tests:

```powershell
.\.venv\Scripts\python -m pytest -m "not live"   # offline tests (need graph/graph.json)
.\.venv\Scripts\python -m pytest -m live         # tests against your Neo4j (need .env)
```

---

## Repo layout

```
SpectrumERP/
  README.md                        this guide
  KnowledgeGraph/                  MCP server + graph builder (Python package spectrum_kg)
    run-mcp.cmd                    start MCP server (stdio)        - used by local clients
    run-mcp-http.cmd               start MCP server (HTTP :8765)   - for network clients
    .env.example                   settings template -> copy to .env
    kg.yaml                        build config (graph source, extraction settings)
    graph/                         the combined phase 0-13 graph: MANIFEST.md, stats, build log, form/phase lists
                                   (graph.json itself is not in git)
    domain/                        curated functional layer the graph was built with (modules, processes,
                                   concepts, rules, one doc per form)
    src/spectrum_kg/               server + builder source
    tests/, eval/                  tests and agentic-RAG evaluation questions
    tools/RoslynExtractor/         .NET code extractor (only for building from source)
  docs/
    reference/                     graph model, embedding-text templates, MCP token usage, build spec, KG map
    plans/                         EC2 pipeline, roles + observability, the original plan
    templates/                     functional / technical documentation templates
    history/kg-gaps/               gap log of the phase 0-1 graph (6 Nov 2026)
```
