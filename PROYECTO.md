# PROYECTO — estado y registro

## Objetivo
Sistema para investigar y producir documentos académicos (docx, xlsx,
prompts de diapositivas) que complete cada encargo de principio a fin,
no entregue nada sin verificar y se ajuste de pregrado a
postdoctorado.

## Estado al 2026-11-11
| Pieza | Estado |
|---|---|
| Reglas consolidadas (`reglas/CLAUDE.md`) | Instaladas en `~/.claude`; falta reinstalar por el cambio en la sección 9 |
| Cinco subagentes (`agents/`) | Actualizados para usar las herramientas; falta reinstalar y probar con un encargo real |
| Skill niveles-academicos | Actualizada con la sección de herramientas; falta reinstalar |
| Capa 1: buscar, descargar y extraer | Probados con casos reales en Linux |
| Capa 1: `zotero_apa.py` | Probado solo con biblioteca sintética; falta la biblioteca real |
| Capa 2: cruce de citas, similitud, constructor, verificador de formato y control final | Probados en Linux con casos reales y defectos sembrados |
| Capa 2: hook de bloqueo | Probado en Linux (24 casos); no está activo: falta fusionar `hooks/settings_hook.json` en `settings.json` |
| Prueba de aceptación de las capas 1 y 2 | Pendiente: encargo real de pregrado en el equipo del usuario |
| Capas 3 y 4 (skills por tipo y método, banco de pruebas) | Por construir; requieren insumos del usuario |

El detalle de cada prueba, lo que quedó sin probar y los límites
conocidos están en `docs/pruebas_capas_1_2.md`.

## Pasos pendientes en el equipo del usuario
1. Traer la rama y ejecutar `instalar.ps1`.
2. Revisar `hooks/settings_hook.json` y fusionarlo en
   `C:\Users\Usuario\.claude\settings.json` junto al hook de RTK.
3. Definir las variables de entorno opcionales: `OPENALEX_API_KEY`
   (clave gratuita), `AGENTE_ACADEMICO_CORREO` (activa Unpaywall) y
   `S2_API_KEY`.
4. Correr `zotero_apa.py --todo` sobre la biblioteca real.
5. Correr la prueba de aceptación y registrar aquí el resultado.

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
- 2026-11-11: el cierre de un encargo exige control mecánico
  aprobado (`control_final.py`) y dictamen APROBADO del verificador
  sobre el mismo archivo; el hook compara la huella del entregable.
- 2026-11-11: `verificar_referencias.py` no bloquea por sí solo:
  libros, leyes y documentos oficiales no están en Crossref. Lo no
  encontrado pasa al verificador, que lo comprueba contra `fuentes/`.
- 2026-11-11: no se fuerzan los controles antibots de ningún sitio
  (buscador de SciELO, MDPI, SciELO Brasil); esas fuentes se informan
  al usuario.
- 2026-11-11: márgenes, sangrías y espaciados del constructor fijados
  en `docs/pruebas_capas_1_2.md`, a falta de norma UAP escrita.

## Sin resolver
- Confirmar márgenes y espaciados del formato UAP.
- ¿La regla de portada en blanco e Introducción, Desarrollo y
  Conclusiones vale para monografías con capítulos?
- ¿El hook debe insistir hasta que se corrija, en lugar de bloquear
  una sola vez por turno?
- Trabajos "para jota": ¿mismas normas que Don Nico o las suyas?
- Modelo por defecto en `settings.json` sigue en Haiku.
- Retiro del ecosistema de Jota, plugins y skills duplicadas: después
  de la primera prueba real.
