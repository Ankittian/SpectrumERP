@echo off
rem One slice of the Voyage free-tier embedding backlog (run hourly by the "SpectrumKG-Embed" scheduled task).
rem Embeds up to ~480K tokens (about 53 min at the 10K tokens/min free-tier limit), writes the vectors to Neo4j, and
rem removes the scheduled task once every node has a vector. A lock folder stops overlapping runs.
setlocal
set "KG_DIR=%~dp0.."
cd /d "%KG_DIR%"
set "LOG=%KG_DIR%\.cache\embed-job.log"
set "LOCK=%KG_DIR%\.cache\embed.lock"
rem a lock is stale when the vector cache has not been written for 20 minutes (crashed or killed run)
if exist "%LOCK%" powershell -NoProfile -Command "if (((Get-Date) - (Get-Item '%KG_DIR%\.cache\embeddings-voyage-code-3-1024.jsonl').LastWriteTime).TotalMinutes -gt 20) { Remove-Item '%LOCK%' -Recurse -Force }"
mkdir "%LOCK%" 2>nul || exit /b 0
echo ===== %date% %time% >> "%LOG%"
".venv\Scripts\kg.exe" embed-step --budget 480000 >> "%LOG%" 2>&1
rmdir "%LOCK%"
findstr /C:"COMPLETE: every node has a vector" "%LOG%" >nul && (
  echo all nodes embedded, removing scheduled task >> "%LOG%"
  schtasks /Delete /TN "SpectrumKG-Embed" /F >> "%LOG%" 2>&1
)
