import 'package:flutter/material.dart';

import '../data/base_datos.dart';
import '../domain/tramo.dart';
import '../servicios/servicios.dart';
import 'comunes.dart';
import 'cuestionario_pantalla.dart';
import 'fotos_pantalla.dart';
import 'historial_pantalla.dart';

class NinoPantalla extends StatelessWidget {
  const NinoPantalla({super.key, required this.ninoId});

  final int ninoId;

  @override
  Widget build(BuildContext context) {
    final s = ServiciosScope.of(context);
    return FutureBuilder<Nino>(
      future: s.repo.nino(ninoId),
      builder: (context, snap) {
        final nino = snap.data;
        if (nino == null) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        final tramo = Tramo.desdeEdadMeses(
          edadEnMeses(nino.fechaNacimiento, s.ahora()),
        );
        void abrir(Widget p) =>
            Navigator.of(context)
                .push(MaterialPageRoute<void>(builder: (_) => p));
        return Scaffold(
          appBar: AppBar(title: Text(nino.codigo)),
          body: CuerpoPantalla(
            children: [
              Text(
                tramo?.etiqueta ?? 'Fuera del rango de edad',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 16),
              if (tramo == null)
                const Text(
                  'Este niño o niña ya no está en el rango de edad de la aplicación (0 a 12 años).',
                )
              else
                BotonPrincipal(
                  etiqueta: 'Responder el cuestionario',
                  icono: Icons.fact_check_outlined,
                  onPressed: () => abrir(CuestionarioPantalla(ninoId: nino.id)),
                ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(54),
                ),
                onPressed: () => abrir(HistorialPantalla(ninoId: nino.id)),
                icon: const Icon(Icons.history),
                label: const Text('Historial'),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size.fromHeight(54),
                ),
                onPressed: () => abrir(FotosPantalla(ninoId: nino.id)),
                icon: const Icon(Icons.photo_camera_outlined),
                label: const Text('Fotos de conductas'),
              ),
              const SizedBox(height: 24),
              const AvisoOrientacion(),
            ],
          ),
        );
      },
    );
  }
}
