import 'package:flutter/material.dart';

import '../data/repositorio.dart';
import '../domain/protocolo.dart';
import '../domain/tramo.dart';
import '../servicios/servicios.dart';
import 'comunes.dart';
import 'resultado_pantalla.dart';

class HistorialPantalla extends StatelessWidget {
  const HistorialPantalla({super.key, required this.ninoId});

  final int ninoId;

  @override
  Widget build(BuildContext context) {
    final s = ServiciosScope.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Historial')),
      body: FutureBuilder<List<SesionConResultado>>(
        future: s.repo.historial(ninoId),
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final filas = snap.data!.where((f) => f.resultado != null).toList();
          if (filas.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Text(
                  'Todavía no hay cuestionarios completados.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              for (final f in filas)
                Card(
                  child: ListTile(
                    title: Text(
                      s
                          .textos
                          .niveles[NivelOrientacion.desdeId(
                            f.resultado!.nivel,
                          )]!
                          .titulo,
                    ),
                    subtitle: Text(
                      '${fechaCorta(f.sesion.iniciadaEn)} · ${Tramo.desdeId(f.sesion.tramo).etiqueta}\n'
                      'Protocolo ${f.resultado!.versionProtocolo}',
                    ),
                    isThreeLine: true,
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) =>
                            ResultadoPantalla(sesionId: f.sesion.id),
                      ),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
