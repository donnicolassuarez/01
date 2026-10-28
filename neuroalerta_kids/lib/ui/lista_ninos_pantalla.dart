import 'package:flutter/material.dart';

import '../data/base_datos.dart';
import '../domain/tramo.dart';
import '../servicios/servicios.dart';
import 'alta_nino_pantalla.dart';
import 'comunes.dart';
import 'exportacion_pantalla.dart';
import 'nino_pantalla.dart';

class ListaNinosPantalla extends StatefulWidget {
  const ListaNinosPantalla({super.key});

  @override
  State<ListaNinosPantalla> createState() => _ListaNinosPantallaState();
}

class _ListaNinosPantallaState extends State<ListaNinosPantalla> {
  late Future<List<Nino>> _ninos;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _ninos = ServiciosScope.of(context).repo.listarNinos();
  }

  void _recargar() {
    final futuro = ServiciosScope.of(context).repo.listarNinos();
    setState(() {
      _ninos = futuro;
    });
  }

  Future<void> _abrir(Widget pantalla) async {
    await Navigator.of(context)
        .push(MaterialPageRoute<void>(builder: (_) => pantalla));
    if (mounted) _recargar();
  }

  @override
  Widget build(BuildContext context) {
    final ahora = ServiciosScope.of(context).ahora();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mis niños y niñas'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (_) => _abrir(const ExportacionPantalla()),
            itemBuilder: (_) => const [
              PopupMenuItem(
                value: 'exportar',
                child: Text('Exportación (uso del equipo)'),
              ),
            ],
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('agregar_nino'),
        onPressed: () => _abrir(const AltaNinoPantalla()),
        icon: const Icon(Icons.add),
        label: const Text('Agregar'),
      ),
      body: FutureBuilder<List<Nino>>(
        future: _ninos,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final ninos = snap.data ?? const [];
          if (ninos.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(32),
                child: Text(
                  'Todavía no hay niños ni niñas registrados.\nToque «Agregar» para empezar.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 17),
                ),
              ),
            );
          }
          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 96),
            children: [
              for (final n in ninos)
                Card(
                  child: ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.child_care)),
                    title: Text(n.codigo),
                    subtitle: Text(
                      Tramo.desdeEdadMeses(
                            edadEnMeses(n.fechaNacimiento, ahora),
                          )?.etiqueta ??
                          'Fuera del rango de edad',
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _abrir(NinoPantalla(ninoId: n.id)),
                  ),
                ),
              const SizedBox(height: 12),
              const AvisoOrientacion(),
            ],
          );
        },
      ),
    );
  }
}
