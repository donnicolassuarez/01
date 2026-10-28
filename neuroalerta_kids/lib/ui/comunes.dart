import 'package:flutter/material.dart';

import '../servicios/servicios.dart';

const nombreApp = 'NeuroAlerta Kids';

/// Recuadro con el aviso de orientación, presente en bienvenida y resultados.
class AvisoOrientacion extends StatelessWidget {
  const AvisoOrientacion({super.key});

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Container(
      key: const Key('aviso_orientacion'),
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: esquema.secondaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, color: esquema.onSecondaryContainer),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              ServiciosScope.of(context).textos.aviso,
              style: TextStyle(
                color: esquema.onSecondaryContainer,
                fontSize: 15,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class CuerpoPantalla extends StatelessWidget {
  const CuerpoPantalla({super.key, required this.children, this.pie});

  final List<Widget> children;
  final Widget? pie;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
              children: children,
            ),
          ),
          if (pie != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
              child: pie,
            ),
        ],
      ),
    );
  }
}

class BotonPrincipal extends StatelessWidget {
  const BotonPrincipal({
    super.key,
    required this.etiqueta,
    required this.onPressed,
    this.icono,
  });

  final String etiqueta;
  final VoidCallback? onPressed;
  final IconData? icono;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(54),
          textStyle: const TextStyle(fontSize: 17),
        ),
        onPressed: onPressed,
        icon: Icon(icono ?? Icons.arrow_forward),
        label: Text(etiqueta),
      ),
    );
  }
}

String fechaCorta(DateTime d) =>
    '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

void avisar(BuildContext context, String mensaje) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(mensaje)));
}
