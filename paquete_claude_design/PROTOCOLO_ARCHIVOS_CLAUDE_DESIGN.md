# Protocolo de Archivos para Claude Design

Análisis de qué formatos de este paquete son seguros de subir y cuáles tienen riesgo real, con las correcciones ya aplicadas.

---

## 1. Hallazgo real (verificado, no teórico)

Convertí los 4 archivos `.svg` del paquete a `.png` para probar su compatibilidad. Resultado:

| Archivo | Resultado |
|---|---|
| `OMS_S1_portada_logo.svg` (logo OMS) | ✅ Perfecto |
| `UNESCO_S1_portada_logo.svg` (logo UNESCO) | ✅ Perfecto |
| `UNESCO_S3_..._emblema-patrimonio-mundial.svg` | ✅ Perfecto (texto circular nítido) |
| `OMS_S3_..._mapa-cobertura-mundial.svg` (mapa de vacunación) | ❌ **Roto** — la leyenda del mapa (el texto que explica cada color) se renderizó como glifos ilegibles |

**Causa:** ese SVG específico dependía de una fuente que no estaba incrustada en el archivo. Los logos no tuvieron ese problema porque son formas vectoriales puras, sin texto dependiente de fuente externa.

**Acción tomada:** eliminé ese archivo (`OMS_S3_...svg` y su versión `.png`) de `imagenes_OMS/`. La diapositiva 3 de OMS ya no lleva imagen adjunta — la instrucción en `PEGAR_EN_CLAUDE_DESIGN.md` fue actualizada para pedirle a Claude Design que genere un grid de 4 iconos simples en su lugar (ya no depende de un archivo externo).

---

## 2. Regla general por tipo de archivo

| Formato | Riesgo | Recomendación |
|---|---|---|
| `.jpg` / `.png` | Ninguno — soportado universalmente por cualquier herramienta de diseño | Usar sin dudar. Son la mayoría del paquete (9 de 11 imágenes restantes). |
| `.svg` **sin texto** (logos, íconos, formas puras) | Bajo | Seguro en la mayoría de plataformas; si falla, usar la versión `.png` incluida como respaldo (ya generada para los 3 logos restantes: `OMS_S1`, `UNESCO_S1`, `UNESCO_S2`, `UNESCO_S3`). |
| `.svg` **con texto/leyendas** (mapas, gráficos con etiquetas) | **Alto** | Evitar subir el SVG directamente. Si se necesita ese tipo de imagen, mejor pedirle a Claude Design que la genere nativamente (texto real, no vectorizado) en lugar de importar un archivo externo. |
| `.md` (documentos de texto: `PEGAR_EN_CLAUDE_DESIGN.md`, `ESPECIFICACION_DISENO.md`, etc.) | Medio | No se suben como archivo — se **copian y pegan** como texto. Riesgo real: si Claude Design no interpreta sintaxis Markdown, los `**dobles asteriscos**` de negrita pueden aparecer literalmente en el texto pegado. Si eso ocurre, quitarlos manualmente o pedir que se ignoren como formato. |
| `.docx` (el informe) | Ninguno | No es para las diapositivas — es material de referencia aparte, no se sube a Claude Design. |

---

## 3. Checklist antes de pegar/subir en Claude Design

- [ ] Subir únicamente `.jpg` y `.png` cuando sea posible (máxima compatibilidad)
- [ ] Para los 3 logos restantes en SVG, si Claude Design los rechaza o los renderiza mal, usar el `.png` que está junto a cada uno (mismo nombre, extensión distinta)
- [ ] La diapositiva 3 de OMS no lleva imagen — confirmar que se generó el grid de iconos en su lugar
- [ ] Al pegar `PEGAR_EN_CLAUDE_DESIGN.md`, revisar que los `**` no queden visibles como texto; si Claude Design no los interpreta, reemplazarlos por negrita manual en la herramienta
- [ ] Verificar que las 12 imágenes restantes (de las 13 originales) coincidan en cantidad con lo que se sube — un archivo fue retirado intencionalmente por el defecto de la leyenda

---

## 4. Inventario final de imágenes (después de la corrección)

**`imagenes_OMS/`** (6 archivos, antes 7):
`OMS_S1_portada_logo.svg` (+ `.png`), `OMS_S2_...sede-ginebra.jpg`, `OMS_S4_...skyline-lapaz.jpg`, `OMS_S5_...bacteria-microscopio.jpg`, `OMS_S6_...vacuna-mmr.jpg`, `OMS_S7_...mapa-departamentos-bolivia.png`

**`imagenes_UNESCO/`** (8 archivos, sin cambios):
`UNESCO_S1_portada_logo.svg` (+ `.png`), `UNESCO_S2_...logo.svg` (+ `.png`), `UNESCO_S3_...emblema-patrimonio-mundial.svg` (+ `.png`), `UNESCO_S4_...mapa-departamentos.png`, `UNESCO_S5a_...puerta-del-sol.jpg`, `UNESCO_S5b_...templo-kalasasaya.jpg`, `UNESCO_S6_...diablada.jpg`, `UNESCO_S7_...templo-kalasasaya.jpg`
