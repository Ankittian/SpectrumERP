@echo off
rem Serves the spectrum-kg MCP server over HTTP so other machines on the LAN can connect.
rem Clients connect to http://<this-pc-ip>:8765/mcp with header "Authorization: Bearer %KG_MCP_TOKEN%".
rem Set KG_MCP_TOKEN in .env or the environment before starting (or pass --token).
setlocal
set "KG_DIR=%~dp0"
cd /d "%KG_DIR%"
"%KG_DIR%.venv\Scripts\python.exe" -m spectrum_kg.mcp_server --transport http --host 0.0.0.0 --port 8765 %*
