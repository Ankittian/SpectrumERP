# EC2 Server Cheat Sheet (SpectrumERP Knowledge Graph)

Server: `13.127.244.207` (Ubuntu, user `ubuntu`, key `D:\FIPL-AI.pem`)

What runs here:
- **Neo4j** (the graph database) in Docker, folder `~/SpectrumERP/neo4j`
- **MCP server** (lets Claude query the graph) as a systemd service `spectrum-kg-mcp`, code in `~/SpectrumERP/repo/KnowledgeGraph`

Both listen on localhost only (7474, 7687, 8765). Nothing is open to the internet.

---

## 1. Connect

```bash
ssh 13.127.244.207
```

Tunnel so your PC can reach the MCP (keep the window open):

```bash
ssh -N -L 8765:127.0.0.1:8765 13.127.244.207
```

Get the MCP token:

```bash
grep KG_MCP_TOKEN ~/SpectrumERP/repo/KnowledgeGraph/.env
```

Add to Claude Code on your PC (replace `<TOKEN>`):

```bash
claude mcp add --transport http spectrum-kg-remote http://localhost:8765/mcp --header "Authorization: Bearer <TOKEN>"
```

---

## 2. Neo4j (Docker)

Run these inside `~/SpectrumERP/neo4j`.

| What it does | Command |
|---|---|
| Show status | `docker compose ps` |
| Live logs | `docker compose logs -f --tail 100` |
| Restart | `docker compose restart` |
| Stop (data is kept) | `docker compose down` |
| Start | `docker compose up -d` |
| Upgrade the image | `docker compose pull && docker compose up -d` |
| CPU and RAM use | `docker stats --no-stream` |
| Open the Cypher shell | `. ./.env; docker exec -it spectrum-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD"` |

If `docker` says permission denied, log out and back in once, or put `sudo` in front.

Password is in `~/SpectrumERP/neo4j/.env`. Data is in `~/SpectrumERP/neo4j/data`.

---

## 3. MCP service (systemd)

| What it does | Command |
|---|---|
| Show status | `systemctl status spectrum-kg-mcp` |
| Restart | `sudo systemctl restart spectrum-kg-mcp` |
| Stop | `sudo systemctl stop spectrum-kg-mcp` |
| Start | `sudo systemctl start spectrum-kg-mcp` |
| Live logs | `journalctl -u spectrum-kg-mcp -f` |
| Logs from the last hour | `journalctl -u spectrum-kg-mcp --since "1 hour ago" --no-pager` |

The service restarts itself after a crash and starts on boot.
Settings are in `~/SpectrumERP/repo/KnowledgeGraph/.env`. Restart the service after you change them.

---

## 4. Update the code

```bash
cd ~/SpectrumERP/repo && git pull
cd KnowledgeGraph
~/.local/bin/uv pip install --python .venv/bin/python -e .   # only if dependencies changed
sudo systemctl restart spectrum-kg-mcp
```

Loading or rebuilding the graph (`kg build`) is slow on this server (2 CPUs). Run it on your GPU PC through a tunnel to port 7687 instead:

```bash
ssh -N -L 17687:127.0.0.1:7687 13.127.244.207
```

---

## 5. Health checks

| What it checks | Command |
|---|---|
| MCP is up (401 means it is alive and wants a token) | `curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8765/mcp` |
| Ports are listening | `ss -ltn \| grep -E "7474\|7687\|8765"` |
| Neo4j answers | `. ~/SpectrumERP/neo4j/.env; docker exec spectrum-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1"` |
| Node count in the graph | `. ~/SpectrumERP/neo4j/.env; docker exec spectrum-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "MATCH (n) RETURN count(n)"` |

---

## 6. System monitoring

| What it shows | Command |
|---|---|
| Live CPU and RAM | `htop` (install: `sudo apt install htop`) |
| RAM and swap | `free -h` |
| Disk space | `df -h /` |
| What uses disk | `du -sh ~/SpectrumERP/* \| sort -h` |
| Load average and uptime | `uptime` |
| Docker disk use | `docker system df` |
| Out-of-memory kills | `sudo dmesg \| grep -i -E "killed process\|out of memory"` |
| System errors since boot | `sudo journalctl -p err -b --no-pager \| tail` |

RAM is tight (3.8 GB). If searches get slow or things get killed, resize the instance to 8 GB.

---

## 7. Backup and cleanup

Back up Neo4j (stops it for a moment):

```bash
cd ~/SpectrumERP/neo4j
docker compose down
sudo tar czf ~/neo4j-backup-$(date +%F).tgz data
docker compose up -d
```

Free disk space:

```bash
docker system prune -f
```

Update the system and reboot (both services come back on their own):

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## 8. Handy extras

```bash
tmux new -s work       # session that survives a disconnect
tmux a -t work         # reattach
sudo ufw status        # firewall (the EC2 security group is the main one)
```
