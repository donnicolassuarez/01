import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import '../servicios/servicios.dart';
import 'bienvenida_pantalla.dart';
import 'comunes.dart';
import 'lista_ninos_pantalla.dart';

class NeuroAlertaApp extends StatelessWidget {
  const NeuroAlertaApp({super.key, required this.servicios});

  final Servicios servicios;

  @override
  Widget build(BuildContext context) {
    return ServiciosScope(
      servicios: servicios,
      child: MaterialApp(
        title: nombreApp,
        debugShowCheckedModeBanner: false,
        locale: const Locale('es'),
        supportedLocales: const [Locale('es')],
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2A7F8E)),
          useMaterial3: true,
          cardTheme: const CardThemeData(
            margin: EdgeInsets.symmetric(vertical: 6),
          ),
        ),
        home: const _PuertaInicial(),
      ),
    );
  }
}

/// Decide si se muestra la bienvenida con el consentimiento o la lista de niños.
class _PuertaInicial extends StatelessWidget {
  const _PuertaInicial();

  @override
  Widget build(BuildContext context) {
    final s = ServiciosScope.of(context);
    return FutureBuilder(
      future: s.repo.consentimientoVigente(s.textos.consentimiento.version),
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }
        return snap.data == null
            ? const BienvenidaPantalla()
            : const ListaNinosPantalla();
      },
    );
  }
}
