# Diagnóstico del entorno (2026-11-09 y 10)

## Claude Code antes de este proyecto
- No existía `C:\Users\Usuario\.claude\agents`. No había agentes
  propios activos.
- Seis agentes (TRIAP-INVESTIGADOR, ANALISTA, PRODUCTOR, AUDITOR,
  OBSERVATORIO-FRONTERA, CAFE-NAVIGATOR) en
  `Downloads\jota-uap-ecosystem\jota-ecosystem\.claude\agents`. Son de
  nivel proyecto y todas las sesiones registradas arrancan en
  `C:\Users\Usuario`, así que no se cargaban. Están hechos para otro
  perfil: nivel doctoral, MLA 9, salida HTML.
- El pipeline RI-PANDO de cinco agentes solo se halló como
  documentación en `Desktop\JP\ACADEMIA_CLAUDE\09_RESPALDO_DESARROLLO`.
- `settings.json`: modelo por defecto Haiku; plugins
  claude-scientific-writer (sin actualizar desde junio de 2026) y
  superpowers 7.0.0; hook de RTK sobre Bash.
- `CLAUDE.md` global contenía solo `@RTK.md`. Las reglas vivían en
  unas 70 notas de `~/.claude/projects/C--Users-Usuario/memory/`.
- Skills propias: clasificadores-presupuestarios-bolivia, notebooklm,
  prospectiva-bolivia-2045, verificar-docx-generado.

## Entorno técnico
- Python 3.14.6. Instalados: python-docx, openpyxl, PyMuPDF, requests.
  Faltan: pandas, pyzotero.
- LibreOffice en `C:\Program Files\LibreOffice\program\soffice.exe`,
  fuera del PATH: invocarlo por ruta completa para renderizar a PDF.
- Zotero con biblioteca local en `C:\Users\Usuario\Zotero\zotero.sqlite`.
- git 2.54; GitHub CLI instalado pero sin sesión iniciada.

## Contradicciones que se resolvieron en las reglas
- Citas: APA 7 (no MLA).
- Confirmación: una pregunta de alcance al inicio, ninguna después.
- Word: generar por código; pasos manuales solo a pedido.
- Guardado: `don_nico\trabajos\<categoría>\<trabajo>`.
