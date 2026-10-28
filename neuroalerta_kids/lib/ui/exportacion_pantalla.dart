import 'package:flutter/material.dart';

import '../servicios/servicios.dart';
import 'comunes.dart';

/// Pantalla de uso del equipo del proyecto: genera un CSV sin datos de identificación y lo comparte.
class ExportacionPantalla extends StatefulWidget {
  const ExportacionPantalla({super.key});

  @override
  State<ExportacionPantalla> createState() => _ExportacionPantallaState();
}

class _ExportacionPantallaState extends State<ExportacionPantalla> {
  bool _trabajando = false;

  Future<void> _exportar() async {
    final s = ServiciosScope.of(context);
    setState(() => _trabajando = true);
    try {
      await s.exportarCsv();
    } catch (e) {
      if (mounted) {
        avisar(context, 'No se pudo generar el archivo. Intente de nuevo.');
      }
    } finally {
      if (mounted) setState(() => _trabajando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Exportación (uso del equipo)')),
      body: CuerpoPantalla(
        pie: BotonPrincipal(
          etiqueta: 'Generar y compartir CSV',
          icono: Icons.ios_share,
          onPressed: _trabajando ? null : _exportar,
        ),
        children: [
          Text(
            'Archivo para el equipo del proyecto',
            style: tema.textTheme.titleLarge,
          ),
          const SizedBox(height: 12),
          Text(
            'Genera un archivo CSV con las respuestas y orientaciones de los cuestionarios completados. '
            'Se comparte con el selector de Android: usted elige a dónde enviarlo.',
            style: tema.textTheme.bodyLarge,
          ),
          const SizedBox(height: 12),
          Text(
            'El archivo no incluye nombres, alias, fecha de nacimiento exacta ni fotos.',
            style: tema.textTheme.bodyLarge,
          ),
          const SizedBox(height: 12),
          Text(
            'Los cortes y preguntas son provisionales, y el archivo lo indica en cada fila.',
            style: tema.textTheme.bodyLarge,
          ),
        ],
      ),
    );
  }
}
