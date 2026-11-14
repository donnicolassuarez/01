# Control mecánico final

- Archivo controlado: `entrega/Los_incendios_en_Pando_y_su_costo_climatico.docx`
- Huella sha256: `7a345917c7e589cc46c73f47b047dbdd920f5b81bb9aaa1306321e9884b2eda9`
- Fecha: 2026-11-14T04:04:53+00:00
- Encargo: nivel pregrado; tipo ensayo; páginas 5; estado «en verificación»

**Resultado del control mecánico: superado.**

Esto no es el dictamen del verificador: solo dice si los controles automáticos están en regla para este archivo exacto. Si el archivo cambia, hay que volver a correr control_final.py.

| Control | Estado | Resumen |
|---|---|---|
| citas | ok | 18 citas, 7 referencias; sin referencia 0, no citadas 0, discordantes 0; lista (orden/duplicadas) 0 |
| similitud | ok | 7 fuentes comparadas; copia 0, casi idéntica 0, entre comillas 0 |
| formato | ok | 0 errores, 0 avisos; páginas: 5 (pedido: 5) |
| referencias | aviso | encontrada 5, dudosa 0, no encontrada 2 |
| fuentes | ok | 7 referencias: con archivo 7, con ficha 7 |

## Qué bloquea

- Nada.

## Pendientes para el verificador (comprobar a mano)

No bloquean por sí solos; el verificador decide. Abrir el archivo de `fuentes/` (o buscarlo) y confirmar que la obra existe y dice lo citado.

- Ke, P., Ciais, P., Sitch, S., Li, W., Bastos, A., Liu, Z., Xu, Y., Gui, X., Bian, J., Goll, D. S., Xi, Y., Li, W., O'Sullivan, M., Souza, J. G. de, Friedlingstein, P., & Chevallier, F. (2024). Low la…
  - verificar_referencias: NO ENCONTRADA (en_crossref: HTTP Error 404: Not Found; en_openalex: HTTP Error 401: Unauthorized (falta la variable OPENALEX_API_KEY)); comprobar contra el archivo de fuentes/
- Zhou, Y., Yan, H., & Luo, J.-J. (2021). Impacts of Amazon fire aerosols on the subseasonal circulations of the mid-high latitudes. Frontiers in Earth Science, 8, Artículo 609554. https://doi.org/10.3…
  - verificar_referencias: NO ENCONTRADA (en_crossref: HTTP Error 429: Too Many Requests; en_openalex: HTTP Error 401: Unauthorized (falta la variable OPENALEX_A…); comprobar contra el archivo de fuentes/

## Avisos (no bloquean)

- Ninguno.

## Lo que este control no cubre

- Cita contra pasaje: que cada fuente diga lo que el texto le atribuye (`extraer_texto.py --buscar "frase" fuentes`).
- Cifras frente al script de análisis o la fuente.
- Ortografía, concordancia, voz y nivel del texto.
- Número y tipo de fuentes según el perfil del nivel.
