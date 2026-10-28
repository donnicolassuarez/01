import 'package:drift/drift.dart';

part 'base_datos.g.dart';

class Ninos extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get codigo => text().withLength(min: 1, max: 40)();
  DateTimeColumn get fechaNacimiento => dateTime()();
  TextColumn get tramo => text()();
  DateTimeColumn get creadoEn => dateTime()();
}

class Consentimientos extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get versionTexto => text()();
  DateTimeColumn get aceptadoEn => dateTime()();
}

@DataClassName('Sesion')
class Sesiones extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get ninoId => integer().references(Ninos, #id)();
  TextColumn get tramo => text()();
  IntColumn get edadMeses => integer()();
  TextColumn get versionProtocolo => text()();
  DateTimeColumn get iniciadaEn => dateTime()();
  DateTimeColumn get cerradaEn => dateTime().nullable()();

  /// Ids de focos rojos marcados, separados por coma.
  TextColumn get focosMarcados => text().withDefault(const Constant(''))();
}

class Respuestas extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get sesionId => integer().references(Sesiones, #id)();
  TextColumn get itemId => text()();

  /// 'casi_siempre', 'a_veces', 'casi_nunca' o 'no_se'.
  TextColumn get opcion => text()();

  /// Puntos (2, 1 o 0); nulo cuando la respuesta fue "No sé".
  IntColumn get puntos => integer().nullable()();

  @override
  List<Set<Column>> get uniqueKeys => [
    {sesionId, itemId},
  ];
}

class Resultados extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get sesionId => integer().references(Sesiones, #id).unique()();

  /// JSON {areaId: {puntos, maximo, respondidas, no_se}}.
  TextColumn get puntajesPorArea => text()();
  IntColumn get puntosTotal => integer()();
  IntColumn get maximoTotal => integer()();
  IntColumn get noSe => integer()();
  TextColumn get nivel => text()();
  TextColumn get focosRojos => text().withDefault(const Constant(''))();
  TextColumn get versionProtocolo => text()();
  TextColumn get estadoProtocolo => text()();
  DateTimeColumn get creadoEn => dateTime()();
}

class Fotos extends Table {
  IntColumn get id => integer().autoIncrement()();
  IntColumn get ninoId => integer().references(Ninos, #id)();

  /// Ruta dentro del almacenamiento privado de la aplicación.
  TextColumn get ruta => text()();
  DateTimeColumn get fecha => dateTime()();
  TextColumn get nota => text().withDefault(const Constant(''))();
}

@DriftDatabase(
  tables: [Ninos, Consentimientos, Sesiones, Respuestas, Resultados, Fotos],
)
class BaseDatos extends _$BaseDatos {
  BaseDatos(super.e);

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    beforeOpen: (details) async {
      await customStatement('PRAGMA foreign_keys = ON');
    },
  );
}
