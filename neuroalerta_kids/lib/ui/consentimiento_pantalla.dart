import 'package:flutter/material.dart';

import '../servicios/servicios.dart';
import 'comunes.dart';
import 'lista_ninos_pantalla.dart';

class ConsentimientoPantalla extends StatefulWidget {
  const ConsentimientoPantalla({super.key});

  @override
  State<ConsentimientoPantalla> createState() => _ConsentimientoPantallaState();
}

class _ConsentimientoPantallaState extends State<ConsentimientoPantalla> {
  bool _acepto = false;
  bool _guardando = false;

  Future<void> _aceptar() async {
    final s = ServiciosScope.of(context);
    setState(() => _guardando = true);
    await s.repo.registrarConsentimiento(s.textos.consentimiento.version);
    if (!mounted) return;
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute<void>(builder: (_) => const ListaNinosPantalla()),
      (_) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    final c = ServiciosScope.of(context).textos.consentimiento;
    final tema = Theme.of(context);

    Widget lista(String titulo, List<String> filas) => Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        Text(titulo, style: tema.textTheme.titleMedium),
        const SizedBox(height: 6),
        for (final f in filas)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 3),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('•  '),
                Expanded(child: Text(f, style: tema.textTheme.bodyLarge)),
              ],
            ),
          ),
      ],
    );

    return Scaffold(
      appBar: AppBar(title: Text(c.titulo)),
      body: CuerpoPantalla(
        pie: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CheckboxListTile(
              key: const Key('casilla_consentimiento'),
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              value: _acepto,
              onChanged: _guardando
                  ? null
                  : (v) => setState(() => _acepto = v ?? false),
              title: const Text('He leído y estoy de acuerdo'),
            ),
            BotonPrincipal(
              etiqueta: c.aceptacion,
              icono: Icons.check,
              onPressed: _acepto && !_guardando ? _aceptar : null,
            ),
          ],
        ),
        children: [
          for (final t in c.texto)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(t, style: tema.textTheme.bodyLarge),
            ),
          lista('Qué se guarda', c.seGuarda),
          lista('Cómo se protege', c.privacidad),
          const SizedBox(height: 12),
          Text(
            'Versión del texto: ${c.version}',
            style: tema.textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}
