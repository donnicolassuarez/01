import 'package:flutter/material.dart';

import '../data/base_datos.dart';
import '../domain/protocolo.dart';
import '../domain/tramo.dart';
import '../servicios/servicios.dart';
import 'comunes.dart';
import 'resultado_pantalla.dart';

/// Una pregunta por pantalla. Antes de las preguntas se muestra la lista de situaciones de atención.
/// Cada respuesta se guarda al momento, así que se puede salir y retomar.
class CuestionarioPantalla extends StatefulWidget {
  const CuestionarioPantalla({super.key, required this.ninoId});

  final int ninoId;

  @override
  State<CuestionarioPantalla> createState() => _CuestionarioPantallaState();
}

class _CuestionarioPantallaState extends State<CuestionarioPantalla> {
  static const _paginaFocos = -1;

  Protocolo? _protocolo;
  Sesion? _sesion;
  List<ItemProtocolo> _items = const [];
  List<FocoRojo> _focos = const [];
  Map<String, Opcion> _respuestas = {};
  Set<String> _focosMarcados = {};
  int _pagina = _paginaFocos;
  bool _avisoGraveMostrado = false;
  bool _ocupado = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_protocolo == null) _iniciar();
  }

  Future<void> _iniciar() async {
    final s = ServiciosScope.of(context);
    final nino = await s.repo.nino(widget.ninoId);
    final tramo = Tramo.desdeEdadMeses(
      edadEnMeses(nino.fechaNacimiento, s.ahora()),
    )!;
    final protocolo = s.protocolos[tramo]!;
    final sesion = await s.repo.iniciarOReanudarSesion(
      nino: nino,
      protocolo: protocolo,
    );
    final respuestas = await s.repo.respuestasDe(sesion.id);
    final items = protocolo.itemsPara(sesion.edadMeses);
    final primeraSinResponder = items.indexWhere(
      (i) => !respuestas.containsKey(i.id),
    );
    if (!mounted) return;
    setState(() {
      _protocolo = protocolo;
      _sesion = sesion;
      _items = items;
      _focos = protocolo.focosPara(sesion.edadMeses);
      _respuestas = respuestas;
      _focosMarcados = s.repo.focosDe(sesion);
      _pagina = respuestas.isEmpty
          ? _paginaFocos
          : (primeraSinResponder == -1
                ? items.length - 1
                : primeraSinResponder);
    });
  }

  Future<void> _continuarDesdeFocos() async {
    final s = ServiciosScope.of(context);
    await s.repo.guardarFocos(_sesion!.id, _focosMarcados);
    final grave = _focos.any((f) => f.grave && _focosMarcados.contains(f.id));
    if (grave && !_avisoGraveMostrado) {
      _avisoGraveMostrado = true;
      if (!mounted) return;
      final verAhora = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (_) => AlertDialog(
          key: const Key('aviso_foco_grave'),
          icon: const Icon(Icons.priority_high),
          title: const Text('Conviene consultar pronto'),
          content: Text(s.textos.focoGrave),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Seguir con las preguntas'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Ver la orientación'),
            ),
          ],
        ),
      );
      if (verAhora == true) {
        await _finalizar();
        return;
      }
    }
    if (mounted) setState(() => _pagina = 0);
  }

  Future<void> _responder(Opcion opcion) async {
    if (_ocupado) return;
    _ocupado = true;
    try {
      final s = ServiciosScope.of(context);
      final item = _items[_pagina];
      await s.repo.guardarRespuesta(
        sesionId: _sesion!.id,
        item: item,
        opcion: opcion,
      );
      _respuestas = {..._respuestas, item.id: opcion};
      if (_pagina == _items.length - 1) {
        await _finalizar();
      } else if (mounted) {
        setState(() => _pagina += 1);
      }
    } finally {
      _ocupado = false;
    }
  }

  Future<void> _finalizar() async {
    final s = ServiciosScope.of(context);
    final resultado = s.motor.evaluar(
      protocolo: _protocolo!,
      edadMeses: _sesion!.edadMeses,
      respuestas: _respuestas,
      focosMarcados: _focosMarcados,
    );
    await s.repo.cerrarSesion(_sesion!.id, resultado);
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute<void>(
        builder: (_) => ResultadoPantalla(sesionId: _sesion!.id),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_protocolo == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Cuestionario')),
      body: _pagina == _paginaFocos
          ? _construirFocos(context)
          : _construirPregunta(context),
    );
  }

  Widget _construirFocos(BuildContext context) {
    final tema = Theme.of(context);
    return CuerpoPantalla(
      pie: BotonPrincipal(
        etiqueta: 'Continuar',
        onPressed: _continuarDesdeFocos,
      ),
      children: [
        Text('Antes de empezar', style: tema.textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text(
          'Marque si ha notado alguna de estas situaciones. Si no ha notado ninguna, deje todo sin marcar.',
          style: tema.textTheme.bodyLarge,
        ),
        const SizedBox(height: 12),
        for (final f in _focos)
          CheckboxListTile(
            key: Key('foco_${f.id}'),
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _focosMarcados.contains(f.id),
            onChanged: (v) => setState(() {
              _focosMarcados = v == true
                  ? {..._focosMarcados, f.id}
                  : ({..._focosMarcados}..remove(f.id));
            }),
            title: Text(f.texto),
          ),
      ],
    );
  }

  Widget _construirPregunta(BuildContext context) {
    final tema = Theme.of(context);
    final item = _items[_pagina];
    final actual = _respuestas[item.id];
    final area = _protocolo!.area(item.areaId);
    return CuerpoPantalla(
      pie: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          for (final o in Opcion.values)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 3),
              child: SizedBox(
                width: double.infinity,
                child: o == actual
                    ? FilledButton(
                        key: Key('opcion_${o.id}'),
                        style: FilledButton.styleFrom(
                          minimumSize: const Size.fromHeight(50),
                          textStyle: const TextStyle(fontSize: 17),
                        ),
                        onPressed: () => _responder(o),
                        child: Text(o.etiqueta),
                      )
                    : OutlinedButton(
                        key: Key('opcion_${o.id}'),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size.fromHeight(50),
                          textStyle: const TextStyle(fontSize: 17),
                        ),
                        onPressed: () => _responder(o),
                        child: Text(o.etiqueta),
                      ),
              ),
            ),
          Row(
            children: [
              TextButton.icon(
                key: const Key('anterior'),
                onPressed: () => setState(() => _pagina -= 1),
                icon: const Icon(Icons.arrow_back),
                label: const Text('Anterior'),
              ),
              const Spacer(),
              Text(
                'Pregunta ${_pagina + 1} de ${_items.length}',
                style: tema.textTheme.bodyMedium,
              ),
            ],
          ),
        ],
      ),
      children: [
        LinearProgressIndicator(value: (_pagina + 1) / _items.length),
        const SizedBox(height: 20),
        Chip(label: Text(area.nombre)),
        const SizedBox(height: 12),
        Text(
          '¿Con qué frecuencia pasa esto?',
          style: tema.textTheme.titleSmall,
        ),
        const SizedBox(height: 8),
        Text(
          item.texto,
          key: const Key('texto_pregunta'),
          style: tema.textTheme.headlineSmall,
        ),
      ],
    );
  }
}
