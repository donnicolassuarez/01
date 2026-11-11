# PROYECTO — estado y registro

## Objetivo
Sistema para investigar y producir documentos académicos (docx, xlsx,
prompts de diapositivas) que complete cada encargo de principio a fin,
no entregue nada sin verificar y se ajuste de pregrado a
postdoctorado.

## Estado al 2026-11-10
| Pieza | Estado |
|---|---|
| Reglas consolidadas (`reglas/CLAUDE.md`) | Instaladas en `~/.claude` |
| Cinco subagentes (`agents/`) | Instalados; sin probar con un encargo real |
| Skill niveles-academicos | Instalada |
| `verificar_referencias.py` | Probado: 2 reales halladas, 1 inventada detectada |
| Capas 1 y 2 (herramientas y controles) | Por construir; ver `docs/plan_construccion.md` |
| Capas 3 y 4 (skills por tipo y método, banco de pruebas) | Por construir; requieren insumos del usuario |

## Decisiones tomadas
- 2026-11-09: plataforma Claude Code; director más subagentes y
  verificador independiente.
- 2026-11-09: agentes a nivel de usuario (`~/.claude/agents`) para que
  carguen desde cualquier carpeta.
- 2026-11-09: una sola pregunta de alcance al inicio; docx por código.
- 2026-11-09: el nivel es parámetro del encargo; pregrado si no se
  indica. Revisor obligatorio de maestría hacia arriba.
- 2026-11-10: este repositorio es la fuente; se instala con
  `instalar.ps1`. La construcción sigue en Claude Code.

## Sin resolver
- Trabajos "para jota": ¿mismas normas que Don Nico o las suyas?
- Modelo por defecto en `settings.json` sigue en Haiku.
- Retiro del ecosistema de Jota, plugins y skills duplicadas: después
  de la primera prueba real.
