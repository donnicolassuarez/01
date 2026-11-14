# PROYECTO — estado y registro

## Objetivo
Sistema para investigar y producir documentos académicos (docx, xlsx,
prompts de diapositivas) que complete cada encargo de principio a fin,
no entregue nada sin verificar y se ajuste de pregrado a
postdoctorado.

## Estado al 2026-11-14
| Pieza | Estado |
|---|---|
| Reglas consolidadas (`reglas/CLAUDE.md`) | Instaladas en `~/.claude`; falta reinstalar por el cambio en la sección 9 |
| Cinco subagentes (`agents/`) | Actualizados para usar las herramientas; falta reinstalar y probar con un encargo real |
| Skill niveles-academicos | Actualizada con la sección de herramientas; falta reinstalar |
| Capa 1: buscar, descargar y extraer | Probados con casos reales en Linux |
| Capa 1: `zotero_apa.py` | Probado solo con biblioteca sintética; falta la biblioteca real |
| Capa 2: cruce de citas, similitud, constructor, verificador de formato y control final | Probados en Linux con casos reales y defectos sembrados |
| Capa 2: hook de bloqueo | Probado en Linux (24 casos); no está activo: falta fusionar `hooks/settings_hook.json` en `settings.json` |
| Prueba de aceptación de las capas 1 y 2 | Corrida en la nube el 2026-11-14: aprobada en la segunda vuelta. Falta repetirla en el equipo del usuario con los agentes instalados |
| Capa 3: comando `/encargo` (ítem 13) | `encargo.py` probado en Linux (51 casos); el comando falta probarlo en una sesión real |
| Capa 3: skills por tipo de trabajo (ítem 10) | Probadas en Linux (50 casos); informe, artículo, perfil y tesis son convención general a confirmar |
| Capa 3: análisis de datos (ítem 12) | Probado con dos conjuntos de datos reales (51 casos); falta Excel |
| Límites conocidos de las capas 1 y 2 | Corregidos y probados (37 casos) |
| Índice automático en el constructor | Probado en Linux (25 casos); falta abrirlo y actualizarlo en Word |
| Capa 3: skills por método (ítem 11) | Por construir; falta el insumo del usuario |
| Capa 4: banco de pruebas (ítem 14) | Por construir; falta el insumo del usuario |

El detalle de cada prueba, lo que quedó sin probar y los límites
conocidos están en `docs/pruebas_capas_1_2.md`.

## Prueba de aceptación (2026-11-14)
Ensayo de pregrado de 5 páginas, "Los incendios en Pando y su costo
climático". Cadena investigador → redactor → productor → verificador,
con el director coordinando. Archivos en
`pruebas/aceptacion/ensayo_incendios/` (sin los PDF de las fuentes).

- Investigador: 7 artículos arbitrados leídos y fichados; fuentes
  bolivianas y oficiales no alcanzables desde el contenedor,
  registradas como vacío.
- Productor: docx de 5 páginas exactas; control mecánico aprobado.
- Verificador, vuelta 1: NO APROBADO por una afirmación sobre Pando
  que la fuente respaldaba solo en parte. El control mecánico no
  podía verla; la encontró la comprobación de cita contra pasaje.
- Vuelta 2, tras corregir el redactor: APROBADO, 18 de 18 citas
  respaldadas. El hook bloqueó mientras el informe era anterior al
  archivo y dejó pasar al final.
- Límite de la corrida: las 7 fuentes están en inglés y ninguna es
  norma o dato oficial boliviano; el perfil de pregrado pide mayoría
  en español.
- Fallos de herramientas hallados y corregidos: descarga de PLOS,
  nombre de archivo con autor equivocado, motivo de descarte tapado
  por la falta de clave, y referencias marcadas "no encontrada"
  cuando Crossref solo había limitado las peticiones.

## Pasos pendientes en el equipo del usuario
1. Traer la rama y ejecutar `instalar.ps1` (ahora copia también el
   comando `/encargo` y las skills nuevas). Instalar `matplotlib`.
   Si el Escritorio está redirigido, definir `ENCARGOS_RAIZ`.
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
- 2026-11-14: la skill verificar-docx-generado empieza por
  `verificar_formato.py`; el chequeo manual del XML queda como
  respaldo, porque no ve el espaciado definido en los estilos.
- 2026-11-14: la estructura de cada tipo de trabajo vive en un solo
  archivo, `skills/tipos-de-trabajo/tipos.json`, que leen el
  constructor y el verificador. La monografía por capítulos es una
  variante que se elige con `estructura: capitulos` en `encargo.md`;
  no está activa por defecto.
- 2026-11-14: si un encargo tiene análisis de datos, una cifra del
  texto que no cuadra con el análisis bloquea la entrega.
- 2026-11-14: los encargos se inician y retoman con `/encargo`; el
  estado "aprobado" solo se puede anotar con informe APROBADO y
  controles en regla sobre el mismo archivo.
- 2026-11-11: márgenes, sangrías y espaciados del constructor fijados
  en `docs/pruebas_capas_1_2.md`, a falta de norma UAP escrita.

## Sin resolver
- ¿`/encargo` puede activarse solo ante un pedido de trabajo, o
  únicamente cuando se escribe? Hoy puede activarse solo.
- Confirmar con el reglamento de la carrera la estructura de informe,
  artículo, perfil y tesis.
- Confirmar márgenes y espaciados del formato UAP.
- ¿La regla de portada en blanco e Introducción, Desarrollo y
  Conclusiones vale para monografías con capítulos?
- ¿El hook debe insistir hasta que se corrija, en lugar de bloquear
  una sola vez por turno?
- Trabajos "para jota": ¿mismas normas que Don Nico o las suyas?
- Modelo por defecto en `settings.json` sigue en Haiku.
- Retiro del ecosistema de Jota, plugins y skills duplicadas: después
  de la primera prueba real.
