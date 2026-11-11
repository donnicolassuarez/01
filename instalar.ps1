# Instala agentes, skills y reglas en la carpeta de usuario de Claude Code.
# Uso: powershell -ExecutionPolicy Bypass -File instalar.ps1
$origen  = $PSScriptRoot
$destino = Join-Path $env:USERPROFILE ".claude"
$marca   = Get-Date -Format "yyyyMMdd_HHmmss"

New-Item -ItemType Directory -Force (Join-Path $destino "agents"), (Join-Path $destino "skills") | Out-Null

# Respaldo de las reglas vigentes antes de reemplazarlas
$reglas = Join-Path $destino "CLAUDE.md"
if (Test-Path $reglas) { Copy-Item $reglas "$reglas.$marca.bak" }

Copy-Item (Join-Path $origen "agents\*.md") (Join-Path $destino "agents") -Force
Copy-Item (Join-Path $origen "skills\*") (Join-Path $destino "skills") -Recurse -Force
Copy-Item (Join-Path $origen "reglas\CLAUDE.md") $reglas -Force

Write-Output "Instalado en $destino"
Get-ChildItem (Join-Path $destino "agents") -Filter *.md | ForEach-Object { "  agente: " + $_.BaseName }
