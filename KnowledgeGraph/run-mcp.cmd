@echo off
rem Starts the spectrum-kg MCP server over stdio (registered in Claude Code as "spectrum-kg").
rem Do not echo anything here: stdout is the MCP protocol channel.
setlocal
set "KG_DIR=%~dp0"
"%KG_DIR%.venv\Scripts\python.exe" -m spectrum_kg.mcp_server
