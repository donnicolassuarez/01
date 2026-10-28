import 'package:flutter/material.dart';

import '../data/repositorio.dart';
import '../domain/tramo.dart';
import '../servicios/servicios.dart';
import 'comunes.dart';

class AltaNinoPantalla extends StatefulWidget {
  const AltaNinoPantalla({super.key});

  @override
  State<AltaNinoPantalla> createState() => _AltaNinoPantallaState();
}

class _AltaNinoPantallaState extends State<AltaNinoPantalla> {
  final _formulario = GlobalKey<FormState>();
  final _codigo = TextEditingController();
  DateTime? _nacimiento;
  String? _errorFecha;
  bool _guardando = false;

  @override
  void dispose() {
    _codigo.dispose();
    super.dispose();
  }

  Tramo? _tramo(DateTime ahora) => _nacimiento == null
      ? null
      : Tramo.desdeEdadMeses(edadEnMeses(_nacimiento!, ahora));

  String? _validarCodigo(String? v) {
    final t = (v ?? '').trim();
    if (t.isEmpty) return 'Escriba un código o alias';
    if (t.length > 24) return 'Use como máximo 24 letras';
    if (t.split(RegExp(r'\s+')).length > 2) {
      return 'Use un código o alias corto, no el nombre completo';
    }
    return null;
  }

  Future<void> _elegirFecha() async {
    final ahora = ServiciosScope.of(context).ahora();
    final fecha = await showDatePicker(
      context: context,
      initialDate: _nacimiento ?? DateTime(ahora.year - 4, ahora.month, 1),
      firstDate: DateTime(ahora.year - 13, ahora.month, ahora.day),
      lastDate: ahora,
      helpText: 'Fecha de nacimiento',
    );
    if (fecha != null) {
      setState(() {
        _nacimiento = fecha;
        _errorFecha = null;
      });
    }
  }

  Future<void> _guardar() async {
    final s = ServiciosScope.of(context);
    final valido = _formulario.currentState!.validate();
    if (_nacimiento == null) {
      setState(() => _errorFecha = 'Elija la fecha de nacimiento');
    }
    if (!valido || _nacimiento == null) return;
    if (_tramo(s.ahora()) == null) {
      setState(() => _errorFecha = 'La edad debe estar entre 0 y 12 años');
      return;
    }
    setState(() => _guardando = true);
    try {
      await s.repo.crearNino(
        codigo: _codigo.text,
        fechaNacimiento: _nacimiento!,
      );
      if (mounted) Navigator.of(context).pop();
    } on EdadFueraDeRango {
      if (mounted) {
        setState(() => _errorFecha = 'La edad debe estar entre 0 y 12 años');
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = ServiciosScope.of(context);
    final tramo = _tramo(s.ahora());
    return Scaffold(
      appBar: AppBar(title: const Text('Agregar niño o niña')),
      body: CuerpoPantalla(
        pie: BotonPrincipal(
          etiqueta: 'Guardar',
          icono: Icons.check,
          onPressed: _guardando ? null : _guardar,
        ),
        children: [
          Form(
            key: _formulario,
            child: TextFormField(
              key: const Key('campo_codigo'),
              controller: _codigo,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Código o alias',
                helperText:
                    'No escriba el nombre completo. Por ejemplo: «Peque 1».',
                border: OutlineInputBorder(),
              ),
              validator: _validarCodigo,
            ),
          ),
          const SizedBox(height: 20),
          OutlinedButton.icon(
            key: const Key('elegir_fecha'),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size.fromHeight(54),
            ),
            onPressed: _elegirFecha,
            icon: const Icon(Icons.cake_outlined),
            label: Text(
              _nacimiento == null
                  ? 'Fecha de nacimiento'
                  : fechaCorta(_nacimiento!),
            ),
          ),
          if (_errorFecha != null)
            Padding(
              padding: const EdgeInsets.only(top: 8, left: 12),
              child: Text(
                _errorFecha!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          if (tramo != null)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(
                'Grupo de edad: ${tramo.etiqueta}',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
        ],
      ),
    );
  }
}
