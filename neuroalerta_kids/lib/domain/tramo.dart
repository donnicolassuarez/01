/// Grupos de edad que cubre el piloto.
enum Tramo {
  meses0a36('0_36', '0 a 36 meses'),
  anios3a6('3_6', '3 a 6 años'),
  anios7a12('7_12', '7 a 12 años');

  const Tramo(this.id, this.etiqueta);

  final String id;
  final String etiqueta;

  static Tramo desdeId(String id) => Tramo.values.firstWhere(
    (t) => t.id == id,
    orElse: () => throw ArgumentError('Tramo desconocido: $id'),
  );

  /// Devuelve el tramo para una edad en meses, o null si queda fuera del piloto.
  static Tramo? desdeEdadMeses(int meses) {
    if (meses < 0) return null;
    if (meses <= 36) return Tramo.meses0a36;
    if (meses < 84) return Tramo.anios3a6;
    if (meses < 156) return Tramo.anios7a12;
    return null;
  }
}

/// Edad completa en meses entre [nacimiento] y [hoy].
int edadEnMeses(DateTime nacimiento, DateTime hoy) {
  var meses =
      (hoy.year - nacimiento.year) * 12 + (hoy.month - nacimiento.month);
  if (hoy.day < nacimiento.day) meses -= 1;
  return meses;
}
