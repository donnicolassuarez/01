#!/bin/bash
# Script para descargar todas las imágenes del proyecto Convenio 169 OIT

echo "================================"
echo "Descargando imágenes del proyecto"
echo "================================"

# SLIDE 1 - Logo OIT
echo "1. Descargando Logo OIT..."
curl -s -L -o "slide-01-logo-oit.svg" "https://upload.wikimedia.org/wikipedia/en/a/a3/Logo-ILO.svg"

# SLIDE 1 - Wiphala (intentar Wikimedia)
echo "2. Intentando descargar Wiphala..."
curl -s -L -o "slide-01-wiphala.png" "https://upload.wikimedia.org/wikipedia/commons/9/96/Wiphala.svg" 2>/dev/null || echo "⚠️ Wiphala - descarga manual requerida"

# SLIDE 6 - Bandera Bolivia
echo "3. Descargando Bandera Bolivia..."
curl -s -L -o "slide-06-bandera-bolivia.svg" "https://upload.wikimedia.org/wikipedia/commons/4/48/Flag_of_Bolivia.svg"

# SLIDE 14 - Mapa Bolivia
echo "4. Intentando descargar Mapa Bolivia..."
curl -s -L -o "slide-14-mapa-bolivia.svg" "https://upload.wikimedia.org/wikipedia/commons/f/f6/Bolivia_location_map.svg" 2>/dev/null || echo "⚠️ Mapa - descarga manual requerida"

echo ""
echo "================================"
echo "Descargas completadas"
echo "================================"
echo ""
echo "Para descargar las imágenes restantes:"
echo "- Ve a: 02-IMAGENES-URLS/IMAGENES-CLASIFICADAS-POR-SLIDE.md"
echo "- Haz clic en cada link"
echo "- Descarga y guarda en esta carpeta"
echo ""
