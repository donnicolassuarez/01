# Especificación de Diseño Visual — OMS y UNESCO en Bolivia

## Dirección de estilo

Base editorial/institucional limpia (la que usan los propios informes de OMS/PAHO y UNESCO) + acentos geométricos andinos extraídos del contenido real (patrón escalonado de Tiwanaku, iconografía solar de la Puerta del Sol, paleta textil aymara). El deck de OMS se mantiene más clínico/institucional; el deck de UNESCO lleva la identidad andina con más fuerza — esa asimetría es intencional: salud = global/clínico, cultura = local/arraigado. Ambos comparten fondo y tipografía para que se sientan como un mismo proyecto en dos partes.

---

## 1. Paleta de colores

### Base compartida (ambos decks)
| Uso | Color | Hex |
|---|---|---|
| Fondo | Crema cálido (no blanco puro — evoca la piedra arenisca de Tiwanaku) | `#F7F3EC` |
| Texto principal | Negro cálido (no negro puro) | `#2B2620` |
| Líneas/bordes sutiles | Gris piedra | `#C9C0B3` |

### Acento deck OMS (clínico/institucional)
| Uso | Color | Hex |
|---|---|---|
| Primario (títulos, iconos, barras) | Azul OMS/ONU | `#0072BC` |
| Secundario (datos positivos, logros) | Verde-azulado salud | `#2E8B7E` |
| Alerta/dato crítico (ej. "+20% incidencia", brechas de cobertura) | Terracota | `#C1440E` |

### Acento deck UNESCO (cultural/patrimonial)
| Uso | Color | Hex |
|---|---|---|
| Primario (títulos, marcos) | Terracota/ocre de piedra Tiwanaku | `#B5651D` |
| Secundario (detalles, tablas) | Oro/mostaza textil andino | `#CC9B36` |
| Acento festivo (solo Carnaval de Oruro) | Índigo profundo | `#1B3A4B` |

*Nota: el terracota aparece en ambos decks (como alerta en OMS, como color primario en UNESCO) — es el hilo conductor que une visualmente las dos presentaciones.*

---

## 2. Tipografía

- **Títulos y encabezados:** Montserrat (Bold/SemiBold) — geométrica, disponible en Google Slides/Canva/PowerPoint (Google Fonts), transmite carácter institucional sin ser genérica.
- **Cuerpo de texto y tablas:** Lato (Regular/Light) — muy legible a tamaños pequeños, buen contraste con Montserrat.
- **Cifras destacadas** (ej. "105", "3.3x", "68%"): Montserrat Bold, tamaño grande, en el color de acento correspondiente.

Ambas fuentes son estándar en Google Fonts — Claude Design/Canva/Google Slides deberían tenerlas disponibles sin instalación adicional.

---

## 3. Motivos gráficos y su origen

| Motivo | De dónde viene | Uso sugerido |
|---|---|---|
| **Patrón escalonado** | Perfil del Templo Kalasasaya | Bordes, separadores entre secciones, marco de portada |
| **Disco solar radial** | Puerta del Sol | Elemento de fondo (marca de agua, opacidad baja) detrás de fotos de Tiwanaku |
| **Franjas de color textil** | Aguayo/textiles aymara | Barra de acento lateral o inferior, nunca como fondo completo (evitar saturación) |
| **Línea de tiempo horizontal con puntos** | — (recurso editorial estándar) | Slide 6 OMS (sarampión) y cualquier cronología |

**Regla general:** los motivos andinos son acentos (5-15% del espacio de la diapositiva), nunca fondo dominante — así se evita el efecto "folclórico de cliché" y se mantiene la seriedad académica.

**Regla explícita anti-infantilización (aplica a cualquier elemento que Claude Design deba generar, no solo motivos andinos):** "iconos de línea simple" significa el estilo de librerías profesionales tipo Material Icons, Feather o Lucide — trazo fino, monocromático, sin relleno de colores saturados, sin caras, sin efectos 3D ni sombras gruesas. "Línea de tiempo con puntos" significa una línea delgada horizontal con círculos pequeños y sólidos del tamaño de una viñeta (no burbujas grandes de colores) — el estilo de un infográfico editorial (The Economist, Pew Research), no un póster escolar. Si Claude Design ofrece variantes "playful"/"fun"/con emojis o mascotas, rechazarlas.

---

## 4. Motivo por diapositiva

### DECK OMS
| Slide | Tratamiento visual |
|---|---|
| 1. Portada | Fondo crema, logo OMS centrado, línea delgada azul debajo del título |
| 2. ¿Qué es la OMS? | Foto sede Ginebra a la derecha (50%), texto a la izquierda, barra azul vertical separadora |
| 3. ¿Qué hace la OMS? | Grid de 4 iconos de línea simple (documento/balanza, lupa, apretón de manos, libro) en azul, uno por función |
| 4. OMS en Bolivia | Foto La Paz full-width en la mitad superior, lista de desafíos abajo con viñetas en terracota |
| 5. Caso TB | Foto bacteria a un lado; tabla con encabezado azul, fila de alerta ("+20%") resaltada en terracota |
| 6. Caso Sarampión | Línea de tiempo horizontal (2000–2012–2023–2025) con puntos, el punto de 2025 en terracota; foto vacuna pequeña en la esquina |
| 7. Conclusión | Mapa de Bolivia con acento verde-azulado, cita final en cuadro con borde izquierdo azul |

### DECK UNESCO
| Slide | Tratamiento visual |
|---|---|
| 1. Portada | Fondo crema, logo UNESCO centrado, marco con patrón escalonado en las cuatro esquinas (ocre) |
| 2. ¿Qué es UNESCO? | Layout simple, línea ocre bajo el título |
| 3. ¿Qué hace UNESCO? | Emblema Patrimonio Mundial como elemento central, 4 pilares alrededor |
| 4. UNESCO en Bolivia | Tabla de 7 sitios con encabezado ocre/mostaza; mapa de Bolivia al lado |
| 5. Tiwanaku | Disco solar (Puerta del Sol) como marca de agua de fondo, muy sutil; dos fotos (Puerta del Sol + Kalasasaya) en collage |
| 6. Carnaval de Oruro | Aquí se permite más color: franja de colores textiles (ocre + terracota + índigo) en el borde inferior; foto de la Diablada como imagen principal, grande |
| 7. Conclusión | Vuelve a paleta calma; foto Kalasasaya con overlay de color crema al 20% para que el texto final resalte encima |

---

## 5. Reglas de layout generales

- Márgenes generosos: mínimo 60px/0.6" en los cuatro lados.
- Una idea visual dominante por diapositiva (foto O tabla como protagonista, no ambas compitiendo al mismo tamaño).
- Texto en viñetas: máximo 5 líneas visibles por diapositiva — el resto queda en notas del presentador (ya incluidas en `PEGAR_EN_CLAUDE_DESIGN.md`).
- Tablas: encabezado con color de acento del deck, filas alternas en un tono más claro del fondo (`#FBF8F3`) para legibilidad.
- Cifras clave (105, 3.3x, 68%, 95%, etc.): siempre en tamaño grande (40-60pt), color de acento, nunca en el mismo peso que el texto corrido.

---

## Cómo combinarlo con el resto del paquete

Este archivo se usa junto con `PEGAR_EN_CLAUDE_DESIGN.md` (contenido de texto) y las carpetas `imagenes_OMS/` / `imagenes_UNESCO/` (archivos a adjuntar). Pega este documento completo como instrucción de estilo antes o junto con el contenido de texto, para que Claude Design aplique la paleta y los motivos al construir cada diapositiva.
