# Decisiones guardadas para revisar después

## La opción de respuesta «No sé» (29/10/2026)

**Contexto.** El encargo define cuatro respuestas: Casi siempre / A veces / Casi nunca / No sé. «No sé» no suma puntos y se
cuenta aparte. El equipo decidió que toda la fase se desarrolla con Claude Code, **sin aplicación a personas**, así que
quedó descartado el análisis de «No sé» por pregunta para validar con padres (idea del asistente, no de las fuentes).

**Qué decidió el equipo: opción C.** Se mantiene la respuesta, con otro texto visible.

| | Opción | Qué implica | Estado |
| --- | --- | --- | --- |
| A | Mantener «No sé» tal cual y no construir el registro de uso | Sin cambios. Conserva la regla del encargo | Guardada |
| B | Quitar la respuesta por completo | Cambia la regla del encargo. Toca protocolo, motor, base de datos, CSV, avisos, pantallas y pruebas. Toda pregunta suma puntos; quien no sabe debe elegir otra respuesta | Guardada |
| **C** | **Mantenerla y cambiar el texto a «Todavía no lo he observado»** | Solo cambia la etiqueta y el aviso que la menciona. El identificador `no_se`, el puntaje y el CSV no cambian | **Aplicada** |

**Por qué no se recomendó B.** Simulación con el motor real (3 a 6 años, 19 preguntas; 13 observadas «a veces» y 6 dudosas):

| Cómo se responden las 6 dudosas | Puntaje | Nivel |
| --- | --- | --- |
| Respuesta de duda (hoy; no suma ni cuenta en el máximo) | 13 de 26 (0,50) | Consultar pronto |
| Sin esa respuesta, elige «Casi nunca» | 13 de 38 (0,34) | Comentar en el próximo control |
| Sin esa respuesta, elige «A veces» | 19 de 38 (0,50) | Consultar pronto |
| Sin esa respuesta, elige «Casi siempre» | 25 de 38 (0,66) | Consultar pronto |

Quien no sabe y elige «Casi nunca» baja la orientación un nivel (falsa tranquilidad). Es un caso construido, no un dato de
cómo contestan las familias. No se verificó en esta investigación cómo tratan los instrumentos conocidos las preguntas que el
padre no sabe contestar.

**Cuándo reconsiderar.** Si más adelante hay datos de uso real, revisar entre A, B y C con esos datos. Para pasar a B, hacerlo
como un cambio explícito de la regla del encargo, con versión nueva del protocolo y migración de las respuestas guardadas.
