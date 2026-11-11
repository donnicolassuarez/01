# Instala agentes, skills, hooks y reglas en la carpeta de usuario de Claude Code.
# Uso: powershell -ExecutionPolicy Bypass -File instalar.ps1
# No modifica settings.json: el hook se activa a mano (ver aviso final).
$origen  = $PSScriptRoot
$destino = Join-Path $env:USERPROFILE ".claude"
$marca   = Get-Date -Format "yyyyMMdd_HHmmss"

New-Item -ItemType Directory -Force (Join-Path $destino "agents"), (Join-Path $destino "skills"), (Join-Path $destino "hooks") | Out-Null

# Respaldo de las reglas vigentes antes de reemplazarlas
$reglas = Join-Path $destino "CLAUDE.md"
if (Test-Path $reglas) { Copy-Item $reglas "$reglas.$marca.bak" }

Copy-Item (Join-Path $origen "agents\*.md") (Join-Path $destino "agents") -Force
Copy-Item (Join-Path $origen "skills\*") (Join-Path $destino "skills") -Recurse -Force
Copy-Item (Join-Path $origen "hooks\*.py") (Join-Path $destino "hooks") -Force
Copy-Item (Join-Path $origen "reglas\CLAUDE.md") $reglas -Force

Write-Output "Instalado en $destino"
Get-ChildItem (Join-Path $destino "agents") -Filter *.md | ForEach-Object { "  agente: " + $_.BaseName }
Get-ChildItem (Join-Path $destino "hooks") -Filter *.py | ForEach-Object { "  hook: " + $_.Name }

Write-Output ""
Write-Output "AVISO: el hook de bloqueo NO queda activo con esta instalacion."
Write-Output "  Para activarlo, fusionar hooks\settings_hook.json en $(Join-Path $destino 'settings.json')"
Write-Output "  (agregar la clave Stop dentro de ""hooks"", sin borrar el hook PreToolUse existente)."
Write-Output "  Prueba manual: python ""$(Join-Path $destino 'hooks\bloqueo_entrega.py')"" --comprobar <carpeta del encargo>"
