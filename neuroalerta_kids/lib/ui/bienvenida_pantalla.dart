import 'package:flutter/material.dart';

import 'comunes.dart';
import 'consentimiento_pantalla.dart';

class BienvenidaPantalla extends StatelessWidget {
  const BienvenidaPantalla({super.key});

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    return Scaffold(
      body: CuerpoPantalla(
        pie: BotonPrincipal(
          etiqueta: 'Comenzar',
          onPressed: () => Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => const ConsentimientoPantalla(),
            ),
          ),
        ),
        children: [
          const SizedBox(height: 24),
          Icon(Icons.child_care, size: 72, color: tema.colorScheme.primary),
          const SizedBox(height: 16),
          Text(
            nombreApp,
            textAlign: TextAlign.center,
            style: tema.textTheme.headlineMedium,
          ),
          const SizedBox(height: 12),
          Text(
            'Anote lo que observa en el desarrollo de su hijo o hija, responda unas preguntas sencillas '
            'y reciba una orientación sobre qué hacer después.',
            textAlign: TextAlign.center,
            style: tema.textTheme.bodyLarge,
          ),
          const SizedBox(height: 24),
          const AvisoOrientacion(),
          const SizedBox(height: 16),
          Text(
            'Es un piloto. Funciona sin internet y los datos se quedan en este teléfono.',
            textAlign: TextAlign.center,
            style: tema.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}
