#!/bin/bash
# Descargar TODAS las imágenes - Sin pedir nada al usuario

cd /home/user/01/Convenio-169-OIT-Deck/05-IMAGENES-DESCARGADAS

echo "Descargando TODAS las imágenes..."
echo ""

# Slide 5 - Comunidad Indígena
echo "Descargando Slide 5..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-05-comunidad-indigena.jpg" \
  "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-05-comunidad-indigena.jpg" \
  "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-05-comunidad-indigena.jpg" \
  "https://cdn.pixabay.com/photo/2016/11/14/04/45/person-1822569_640.jpg" 2>/dev/null

[ -f "slide-05-comunidad-indigena.jpg" ] && echo "✓ Slide 5" || echo "✗ Slide 5 - intentando alternativa"

# Slide 8 - Reunión/Consulta
echo "Descargando Slide 8..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-08-reunion-consulta.jpg" \
  "https://images.unsplash.com/photo-1552664730-d307ca884978?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-08-reunion-consulta.jpg" \
  "https://images.unsplash.com/photo-1552664730-d307ca884978?w=600" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-08-reunion-consulta.jpg" \
  "https://cdn.pixabay.com/photo/2018/09/07/09/26/business-3660521_640.jpg" 2>/dev/null

[ -f "slide-08-reunion-consulta.jpg" ] && echo "✓ Slide 8" || echo "✗ Slide 8"

# Slide 9 - Acuerdo/Diálogo
echo "Descargando Slide 9..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-09-acuerdo-dialogo.jpg" \
  "https://images.unsplash.com/photo-1552664730-d307ca884978?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-09-acuerdo-dialogo.jpg" \
  "https://cdn.pixabay.com/photo/2014/02/27/16/10/handshake-276087_640.jpg" 2>/dev/null

[ -f "slide-09-acuerdo-dialogo.jpg" ] && echo "✓ Slide 9" || echo "✗ Slide 9"

# Slide 10 - Bosque/Naturaleza
echo "Descargando Slide 10..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-10-bosque-territorio.jpg" \
  "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-10-bosque-territorio.jpg" \
  "https://cdn.pixabay.com/photo/2015/12/01/20/28/forest-1072828_640.jpg" 2>/dev/null

[ -f "slide-10-bosque-territorio.jpg" ] && echo "✓ Slide 10" || echo "✗ Slide 10"

# Slide 11 - Comunidad/Asamblea
echo "Descargando Slide 11..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-11-comunidad-asamblea.jpg" \
  "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-11-comunidad-asamblea.jpg" \
  "https://cdn.pixabay.com/photo/2015/07/02/10/59/meeting-829215_640.jpg" 2>/dev/null

[ -f "slide-11-comunidad-asamblea.jpg" ] && echo "✓ Slide 11" || echo "✗ Slide 11"

# Slide 15 - Recursos Naturales
echo "Descargando Slide 15..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-15-recursos-naturales.jpg" \
  "https://images.unsplash.com/photo-1469022563149-aa64dbd37dae?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-15-recursos-naturales.jpg" \
  "https://cdn.pixabay.com/photo/2016/10/23/15/53/mining-1764176_640.jpg" 2>/dev/null

[ -f "slide-15-recursos-naturales.jpg" ] && echo "✓ Slide 15" || echo "✗ Slide 15"

# Slide 16 - Paz/Comunidad
echo "Descargando Slide 16..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-16-paz-comunidad.jpg" \
  "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=400" 2>/dev/null || \
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-16-paz-comunidad.jpg" \
  "https://cdn.pixabay.com/photo/2018/04/27/03/26/people-3357278_640.jpg" 2>/dev/null

[ -f "slide-16-paz-comunidad.jpg" ] && echo "✓ Slide 16" || echo "✗ Slide 16"

# Slide 12 - Comparación (opcional)
echo "Descargando Slide 12..."
timeout 10 curl -s -L -A "Mozilla/5.0" -o "slide-12-comparacion-icono.png" \
  "https://cdn.pixabay.com/photo/2013/07/13/13/47/compare-159320_640.png" 2>/dev/null

[ -f "slide-12-comparacion-icono.png" ] && echo "✓ Slide 12" || echo "✓ Slide 12 (opcional)"

echo ""
echo "Verificando descargas..."
echo "Imágenes descargadas: $(ls -1 slide-*.{jpg,png,svg} 2>/dev/null | wc -l)/17"
ls -1 slide-*.{jpg,png,svg} 2>/dev/null | while read f; do 
  size=$(ls -lh "$f" | awk '{print $5}')
  echo "  ✓ $f ($size)"
done
