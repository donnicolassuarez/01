# agente-academico

Repositorio fuente del sistema de investigación y producción de
documentos académicos de Don Nico (pregrado a postdoctorado).

## Cómo está organizado
- `agents/` — los cinco subagentes: investigador, redactor,
  productor, verificador, revisor.
- `commands/` — comando `/encargo` (director: inicia, retoma y
  cierra encargos).
- `skills/` — niveles-academicos (perfiles, rúbrica, scripts),
  tipos-de-trabajo (estructura por tipo), analisis-de-datos
  (análisis reproducible y xlsx) y verificar-docx-generado.
- `hooks/` — hook de bloqueo de entrega (evento Stop) y el fragmento
  de `settings.json` que lo activa.
- `pruebas/` — casos de prueba, generadores de casos y salidas de
  las pruebas de cada herramienta.
- `reglas/CLAUDE.md` — reglas globales de trabajo del usuario.
- `docs/` — diagnóstico, plan de construcción y bibliografía.
- `PROYECTO.md` — estado y registro de decisiones. Leerlo primero.
- `instalar.ps1` — copia agentes, comandos, skills y reglas a
  `C:\Users\Usuario\.claude\`.

## Reglas para trabajar en este repositorio
- Este repositorio es la fuente. Se edita aquí y se instala con
  `instalar.ps1`; no editar directamente en `~/.claude`.
- Antes de empezar, leer `PROYECTO.md` y `docs/plan_construccion.md`.
- Cada herramienta nueva se prueba con un caso real antes de pasar
  a la siguiente. Sin prueba no se marca como hecha.
- Scripts en Python, solo biblioteca estándar cuando sea posible;
  si hace falta una librería, anotarla en `requirements.txt`.
- Mostrar al usuario todo cambio a `settings.json` antes de
  aplicarlo.
- Al cerrar cada sesión: actualizar `PROYECTO.md` y hacer commit.
- Las reglas del usuario en `reglas/CLAUDE.md` también valen aquí.
