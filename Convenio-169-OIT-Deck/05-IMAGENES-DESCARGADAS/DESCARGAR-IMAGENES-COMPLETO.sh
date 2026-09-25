#!/bin/bash
# Script mejorado para descargar todas las imágenes del proyecto Convenio 169 OIT

set -e

echo "================================"
echo "Descargando imágenes - PACK COMPLETO"
echo "================================"
echo ""

# SLIDE 1 - Logo OIT (ya descargado)
if [ ! -f "slide-01-logo-oit.svg" ]; then
    echo "1. Descargando Logo OIT..."
    curl -s -L -o "slide-01-logo-oit.svg" "https://upload.wikimedia.org/wikipedia/en/a/a3/Logo-ILO.svg"
    echo "   ✓ Logo OIT"
fi

# SLIDE 1 - Wiphala (ya descargado)
if [ ! -f "slide-01-wiphala.png" ]; then
    echo "2. Descargando Wiphala..."
    curl -s -L -o "slide-01-wiphala.png" "https://upload.wikimedia.org/wikipedia/commons/9/96/Wiphala.svg" 2>/dev/null || echo "   ⚠️ Wiphala - requiere descarga manual"
fi

# SLIDE 2 - Logo/Edificio OIT (reutilizar logo existente)
if [ ! -f "slide-02-oit-logo.svg" ]; then
    echo "3. Preparando imagen OIT para Slide 2 (copia de logo)..."
    cp "slide-01-logo-oit.svg" "slide-02-oit-logo.svg"
    echo "   ✓ Slide 2 - OIT Logo"
fi

# SLIDE 3 - Tripartismo (3 personas/colaboración)
if [ ! -f "slide-03-tripartismo.png" ]; then
    echo "4. Descargando imagen Tripartismo..."
    # Intentar Wikimedia Commons
    curl -s -L -o "slide-03-tripartismo.png" "https://upload.wikimedia.org/wikipedia/commons/d/d6/People_holding_hands.png" 2>/dev/null || \
    curl -s -L -o "slide-03-tripartismo.png" "https://pixabay.com/get/gcecc4a7099ec94bff35b7d1b1ef55f7e1138c0d2144f5b21f3cc83c59a3c6f39_640.png" 2>/dev/null || \
    echo "   ⚠️ Tripartismo - requiere descarga manual desde Pixabay"
    [ -f "slide-03-tripartismo.png" ] && echo "   ✓ Slide 3 - Tripartismo"
fi

# SLIDE 4 - Documento/Símbolo Legal
if [ ! -f "slide-04-documento.png" ]; then
    echo "5. Descargando imagen Documento..."
    curl -s -L -o "slide-04-documento.png" "https://upload.wikimedia.org/wikipedia/commons/d/d3/Document_icon_%28the_noun_project%29.svg" 2>/dev/null || \
    echo "   ⚠️ Documento - requiere descarga manual desde Unsplash/Pixabay"
    [ -f "slide-04-documento.png" ] && echo "   ✓ Slide 4 - Documento"
fi

# SLIDE 5 - Comunidad Indígena
if [ ! -f "slide-05-comunidad-indigena.jpg" ]; then
    echo "6. Descargando imagen Comunidad Indígena..."
    echo "   ⚠️ Slide 5 - Comunidad Indígena - requiere descarga manual desde Unsplash"
fi

# SLIDE 6 - Bandera Bolivia (ya descargado)
if [ ! -f "slide-06-bandera-bolivia.svg" ]; then
    echo "7. Descargando Bandera Bolivia..."
    curl -s -L -o "slide-06-bandera-bolivia.svg" "https://upload.wikimedia.org/wikipedia/commons/4/48/Flag_of_Bolivia.svg"
    echo "   ✓ Bandera Bolivia"
fi

# SLIDE 7 - Icono Constitución
if [ ! -f "slide-07-constitucion-icono.png" ]; then
    echo "8. Descargando icono Constitución..."
    curl -s -L -o "slide-07-constitucion-icono.png" "https://upload.wikimedia.org/wikipedia/commons/f/f5/Constitution.png" 2>/dev/null || \
    echo "   ⚠️ Constitución - requiere descarga manual desde Pixabay"
    [ -f "slide-07-constitucion-icono.png" ] && echo "   ✓ Slide 7 - Constitución"
fi

# SLIDE 8 - Reunión/Consulta
if [ ! -f "slide-08-reunion-consulta.jpg" ]; then
    echo "9. Descargando imagen Reunión/Consulta..."
    echo "   ⚠️ Slide 8 - Reunión/Consulta - requiere descarga manual desde Unsplash"
fi

# SLIDE 9 - Acuerdo/Diálogo
if [ ! -f "slide-09-acuerdo-dialogo.jpg" ]; then
    echo "10. Descargando imagen Acuerdo/Diálogo..."
    echo "   ⚠️ Slide 9 - Acuerdo/Diálogo - requiere descarga manual desde Unsplash/Pixabay"
fi

# SLIDE 10 - Bosque/Naturaleza
if [ ! -f "slide-10-bosque-territorio.jpg" ]; then
    echo "11. Descargando imagen Bosque/Territorio..."
    echo "   ⚠️ Slide 10 - Bosque/Territorio - requiere descarga manual desde Unsplash"
fi

# SLIDE 11 - Comunidad/Asamblea
if [ ! -f "slide-11-comunidad-asamblea.jpg" ]; then
    echo "12. Descargando imagen Comunidad/Asamblea..."
    echo "   ⚠️ Slide 11 - Comunidad/Asamblea - requiere descarga manual desde Unsplash"
fi

# SLIDE 13 - Mapa Bolivia con TIPNIS (ya descargado como mapa general)
if [ ! -f "slide-13-mapa-tipnis.png" ]; then
    echo "13. Preparando mapa para Slide 13..."
    cp "slide-14-mapa-bolivia.svg" "slide-13-mapa-tipnis.svg" 2>/dev/null || \
    echo "   ⚠️ Mapa TIPNIS - requiere descarga manual desde Wikimedia"
    [ -f "slide-13-mapa-tipnis.svg" ] && echo "   ✓ Slide 13 - Mapa"
fi

# SLIDE 14 - Mapa Bolivia (ya descargado)
if [ ! -f "slide-14-mapa-bolivia.svg" ]; then
    echo "14. Descargando Mapa Bolivia..."
    curl -s -L -o "slide-14-mapa-bolivia.svg" "https://upload.wikimedia.org/wikipedia/commons/f/f6/Bolivia_location_map.svg"
    echo "   ✓ Mapa Bolivia"
fi

# SLIDE 15 - Recursos Naturales/Minería
if [ ! -f "slide-15-recursos-naturales.jpg" ]; then
    echo "15. Descargando imagen Recursos Naturales..."
    echo "   ⚠️ Slide 15 - Recursos Naturales - requiere descarga manual desde Unsplash"
fi

# SLIDE 16 - Paz/Comunidad
if [ ! -f "slide-16-paz-comunidad.jpg" ]; then
    echo "16. Descargando imagen Paz/Comunidad..."
    echo "   ⚠️ Slide 16 - Paz/Comunidad - requiere descarga manual desde Unsplash"
fi

# SLIDE 17 - Logo OIT + Wiphala (reutilizar)
if [ ! -f "slide-17-cierre.txt" ]; then
    echo "17. Preparando cierre (mismo que portada)..."
    echo "Reutilizar: slide-01-logo-oit.svg + slide-01-wiphala.png" > "slide-17-cierre.txt"
    echo "   ✓ Slide 17 - Cierre (reutilizar Slide 1)"
fi

echo ""
echo "================================"
echo "Descarga completada"
echo "================================"
echo ""
echo "Imágenes automaticamente descargadas:"
ls -1 slide-*.{svg,png,jpg} 2>/dev/null | wc -l
echo ""
echo "Para completar el pack:"
echo "1. Abre: 02-IMAGENES-URLS/IMAGENES-CLASIFICADAS-POR-SLIDE.md"
echo "2. Descarga manualmente las imágenes de Unsplash y Pixabay"
echo "3. Guarda en esta carpeta con los nombres: slide-XX-descripcion.ext"
echo ""
