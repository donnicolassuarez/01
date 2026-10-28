import 'dart:io';

import 'package:flutter/material.dart';

import '../data/base_datos.dart';
import '../servicios/servicios.dart';
import 'comunes.dart';

class FotosPantalla extends StatefulWidget {
  const FotosPantalla({super.key, required this.ninoId});

  final int ninoId;

  @override
  State<FotosPantalla> createState() => _FotosPantallaState();
}

class _FotosPantallaState extends State<FotosPantalla> {
  late Future<List<Foto>> _fotos;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _fotos = ServiciosScope.of(context).repo.fotosDe(widget.ninoId);
  }

  void _recargar() {
    final futuro = ServiciosScope.of(context).repo.fotosDe(widget.ninoId);
    setState(() {
      _fotos = futuro;
    });
  }

  Future<void> _agregar() async {
    final s = ServiciosScope.of(context);
    final camara = await showModalBottomSheet<bool>(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              key: const Key('foto_camara'),
              leading: const Icon(Icons.photo_camera),
              title: const Text('Tomar una foto'),
              onTap: () => Navigator.pop(context, true),
            ),
            ListTile(
              key: const Key('foto_galeria'),
              leading: const Icon(Icons.photo_library),
              title: const Text('Elegir una foto del teléfono'),
              onTap: () => Navigator.pop(context, false),
            ),
          ],
        ),
      ),
    );
    if (camara == null) return;
    final origen = await s.selectorFotos.elegir(camara: camara);
    if (origen == null || !mounted) return;

    final detalle = await showDialog<({DateTime fecha, String nota})>(
      context: context,
      builder: (_) => _DialogoDetalleFoto(inicial: s.ahora()),
    );
    if (detalle == null) {
      // Se canceló: no queda ninguna copia temporal en el teléfono.
      try {
        await File(origen).delete();
      } on FileSystemException {
        // El temporal ya no existe o no se puede borrar; no hay nada más que limpiar.
      }
      return;
    }
    final ruta = await s.almacenFotos.guardar(origen);
    await s.repo.agregarFoto(
      ninoId: widget.ninoId,
      ruta: ruta,
      fecha: detalle.fecha,
      nota: detalle.nota,
    );
    if (mounted) _recargar();
  }

  Future<void> _ver(Foto foto) async {
    final s = ServiciosScope.of(context);
    final eliminar = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(fechaCorta(foto.fecha)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Image.file(
                File(foto.ruta),
                errorBuilder: (_, _, _) =>
                    const Text('No se pudo mostrar la foto.'),
              ),
              const SizedBox(height: 12),
              Text(foto.nota.isEmpty ? 'Sin nota' : foto.nota),
            ],
          ),
        ),
        actions: [
          TextButton(
            key: const Key('eliminar_foto'),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Eliminar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cerrar'),
          ),
        ],
      ),
    );
    if (eliminar != true || !mounted) return;
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('¿Eliminar esta foto?'),
        content: const Text('Se borrará del teléfono y no se podrá recuperar.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            key: const Key('confirmar_eliminar'),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Eliminar'),
          ),
        ],
      ),
    );
    if (confirmar != true) return;
    await s.almacenFotos.eliminar(foto.ruta);
    await s.repo.eliminarFoto(foto.id);
    if (mounted) _recargar();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Fotos de conductas')),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('agregar_foto'),
        onPressed: _agregar,
        icon: const Icon(Icons.add_a_photo),
        label: const Text('Agregar foto'),
      ),
      body: FutureBuilder<List<Foto>>(
        future: _fotos,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final fotos = snap.data!;
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
            children: [
              const Text(
                'Las fotos quedan solo en este teléfono y no aparecen en la galería. Pueden ayudar a mostrar una conducta al profesional de salud.',
              ),
              const SizedBox(height: 12),
              if (fotos.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(24),
                  child: Center(child: Text('Todavía no hay fotos.')),
                ),
              for (final f in fotos)
                Card(
                  child: ListTile(
                    leading: SizedBox(
                      width: 56,
                      height: 56,
                      child: Image.file(
                        File(f.ruta),
                        fit: BoxFit.cover,
                        cacheWidth: 112,
                        errorBuilder: (_, _, _) =>
                            const Icon(Icons.broken_image_outlined),
                      ),
                    ),
                    title: Text(fechaCorta(f.fecha)),
                    subtitle: Text(
                      f.nota.isEmpty ? 'Sin nota' : f.nota,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    onTap: () => _ver(f),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _DialogoDetalleFoto extends StatefulWidget {
  const _DialogoDetalleFoto({required this.inicial});
  final DateTime inicial;

  @override
  State<_DialogoDetalleFoto> createState() => _DialogoDetalleFotoState();
}

class _DialogoDetalleFotoState extends State<_DialogoDetalleFoto> {
  late DateTime _fecha = widget.inicial;
  final _nota = TextEditingController();

  @override
  void dispose() {
    _nota.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Detalles de la foto'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          OutlinedButton.icon(
            onPressed: () async {
              final f = await showDatePicker(
                context: context,
                initialDate: _fecha,
                firstDate: DateTime(widget.inicial.year - 13),
                lastDate: widget.inicial,
              );
              if (f != null) setState(() => _fecha = f);
            },
            icon: const Icon(Icons.event),
            label: Text(fechaCorta(_fecha)),
          ),
          const SizedBox(height: 12),
          TextField(
            key: const Key('nota_foto'),
            controller: _nota,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Nota (qué se ve, cuándo ocurre)',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          key: const Key('guardar_foto'),
          onPressed: () =>
              Navigator.pop(context, (fecha: _fecha, nota: _nota.text)),
          child: const Text('Guardar'),
        ),
      ],
    );
  }
}
