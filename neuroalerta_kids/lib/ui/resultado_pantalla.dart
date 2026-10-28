import 'package:flutter/material.dart';

import '../data/base_datos.dart';
import '../domain/protocolo.dart';
import '../domain/tramo.dart';
import '../servicios/servicios.dart';
import 'comunes.dart';

class _DatosResultado {
  const _DatosResultado(
    this.sesion,
    this.resultado,
    this.respuestas,
    this.focos,
  );
  final Sesion sesion;
  final Resultado resultado;
  final Map<String, Opcion> respuestas;
  final Set<String> focos;
}

class ResultadoPantalla extends StatelessWidget {
  const ResultadoPantalla({super.key, required this.sesionId});

  final int sesionId;

  Future<_DatosResultado> _cargar(Servicios s) async {
    final sesion = await s.repo.sesion(sesionId);
    final resultado = (await s.repo.resultadoDe(sesionId))!;
    final respuestas = await s.repo.respuestasDe(sesionId);
    final focos = resultado.focosRojos.isEmpty
        ? <String>{}
        : resultado.focosRojos.split(',').toSet();
    return _DatosResultado(sesion, resultado, respuestas, focos);
  }

  @override
  Widget build(BuildContext context) {
    final s = ServiciosScope.of(context);
    final tema = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Orientación')),
      body: FutureBuilder<_DatosResultado>(
        future: _cargar(s),
        builder: (context, snap) {
          final d = snap.data;
          if (d == null) {
            return const Center(child: CircularProgressIndicator());
          }
          final protocolo = s.protocolos[Tramo.desdeId(d.sesion.tramo)]!;
          final nivel = NivelOrientacion.desdeId(d.resultado.nivel);
          final texto = s.textos.niveles[nivel]!;
          final esquema = tema.colorScheme;
          final colorNivel = switch (nivel) {
            NivelOrientacion.sinSenales => esquema.primaryContainer,
            NivelOrientacion.comentarControl => esquema.tertiaryContainer,
            NivelOrientacion.consultarPronto => esquema.errorContainer,
          };
          final observados = <String, List<String>>{};
          for (final item in protocolo.items) {
            final r = d.respuestas[item.id];
            if (r == Opcion.casiSiempre || r == Opcion.aVeces) {
              observados
                  .putIfAbsent(item.areaId, () => [])
                  .add('${item.texto} (${r!.etiqueta.toLowerCase()})');
            }
          }
          final focosTexto = [
            for (final f in protocolo.focosRojos)
              if (d.focos.contains(f.id)) f.texto,
          ];
          final hayNoSe = d.resultado.noSe > 0;
          final muchosNoSe =
              hayNoSe &&
              d.resultado.noSe /
                      protocolo.itemsPara(d.sesion.edadMeses).length >=
                  protocolo.umbralNoSe;
          final pocas =
              (d.respuestas.length - d.resultado.noSe) <
              protocolo.minimoRespondidas;

          return CuerpoPantalla(
            pie: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const AvisoOrientacion(),
                const SizedBox(height: 6),
                Text(
                  'Versión del protocolo: ${d.resultado.versionProtocolo}',
                  key: const Key('version_protocolo'),
                  style: tema.textTheme.bodySmall,
                ),
                const SizedBox(height: 8),
                BotonPrincipal(
                  etiqueta: 'Volver al inicio',
                  icono: Icons.home_outlined,
                  onPressed: () =>
                      Navigator.of(context).popUntil((r) => r.isFirst),
                ),
              ],
            ),
            children: [
              Container(
                key: const Key('nivel_orientacion'),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: colorNivel,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(texto.titulo, style: tema.textTheme.titleLarge),
                    const SizedBox(height: 8),
                    Text(texto.resumen, style: tema.textTheme.bodyLarge),
                  ],
                ),
              ),
              if (focosTexto.isNotEmpty) ...[
                const SizedBox(height: 20),
                Text(
                  'Situaciones que usted marcó',
                  style: tema.textTheme.titleMedium,
                ),
                for (final t in focosTexto) _Punto(t),
              ],
              const SizedBox(height: 20),
              Text('Lo que usted observó', style: tema.textTheme.titleMedium),
              const SizedBox(height: 4),
              if (observados.isEmpty)
                const Text('No marcó señales en las preguntas respondidas.')
              else
                for (final e in observados.entries) ...[
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Text(
                      protocolo.area(e.key).nombre,
                      style: tema.textTheme.titleSmall,
                    ),
                  ),
                  for (final t in e.value) _Punto(t),
                ],
              if (muchosNoSe) ...[
                const SizedBox(height: 16),
                Text(s.textos.notaNoSe),
              ],
              if (pocas) ...[
                const SizedBox(height: 16),
                Text(s.textos.notaPocasRespuestas),
              ],
              const SizedBox(height: 20),
              Text('Paso recomendado', style: tema.textTheme.titleMedium),
              const SizedBox(height: 4),
              Text(texto.paso, style: tema.textTheme.bodyLarge),
            ],
          );
        },
      ),
    );
  }
}

class _Punto extends StatelessWidget {
  const _Punto(this.texto);
  final String texto;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('•  '),
        Expanded(
          child: Text(texto, style: Theme.of(context).textTheme.bodyLarge),
        ),
      ],
    ),
  );
}
