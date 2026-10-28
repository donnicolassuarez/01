// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'base_datos.dart';

// ignore_for_file: type=lint
class $NinosTable extends Ninos with TableInfo<$NinosTable, Nino> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $NinosTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _codigoMeta = const VerificationMeta('codigo');
  @override
  late final GeneratedColumn<String> codigo = GeneratedColumn<String>(
    'codigo',
    aliasedName,
    false,
    additionalChecks: GeneratedColumn.checkTextLength(
      minTextLength: 1,
      maxTextLength: 40,
    ),
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fechaNacimientoMeta = const VerificationMeta(
    'fechaNacimiento',
  );
  @override
  late final GeneratedColumn<DateTime> fechaNacimiento =
      GeneratedColumn<DateTime>(
        'fecha_nacimiento',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  static const VerificationMeta _tramoMeta = const VerificationMeta('tramo');
  @override
  late final GeneratedColumn<String> tramo = GeneratedColumn<String>(
    'tramo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _creadoEnMeta = const VerificationMeta(
    'creadoEn',
  );
  @override
  late final GeneratedColumn<DateTime> creadoEn = GeneratedColumn<DateTime>(
    'creado_en',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    codigo,
    fechaNacimiento,
    tramo,
    creadoEn,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'ninos';
  @override
  VerificationContext validateIntegrity(
    Insertable<Nino> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('codigo')) {
      context.handle(
        _codigoMeta,
        codigo.isAcceptableOrUnknown(data['codigo']!, _codigoMeta),
      );
    } else if (isInserting) {
      context.missing(_codigoMeta);
    }
    if (data.containsKey('fecha_nacimiento')) {
      context.handle(
        _fechaNacimientoMeta,
        fechaNacimiento.isAcceptableOrUnknown(
          data['fecha_nacimiento']!,
          _fechaNacimientoMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_fechaNacimientoMeta);
    }
    if (data.containsKey('tramo')) {
      context.handle(
        _tramoMeta,
        tramo.isAcceptableOrUnknown(data['tramo']!, _tramoMeta),
      );
    } else if (isInserting) {
      context.missing(_tramoMeta);
    }
    if (data.containsKey('creado_en')) {
      context.handle(
        _creadoEnMeta,
        creadoEn.isAcceptableOrUnknown(data['creado_en']!, _creadoEnMeta),
      );
    } else if (isInserting) {
      context.missing(_creadoEnMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Nino map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Nino(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      codigo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}codigo'],
      )!,
      fechaNacimiento: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}fecha_nacimiento'],
      )!,
      tramo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}tramo'],
      )!,
      creadoEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}creado_en'],
      )!,
    );
  }

  @override
  $NinosTable createAlias(String alias) {
    return $NinosTable(attachedDatabase, alias);
  }
}

class Nino extends DataClass implements Insertable<Nino> {
  final int id;
  final String codigo;
  final DateTime fechaNacimiento;
  final String tramo;
  final DateTime creadoEn;
  const Nino({
    required this.id,
    required this.codigo,
    required this.fechaNacimiento,
    required this.tramo,
    required this.creadoEn,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['codigo'] = Variable<String>(codigo);
    map['fecha_nacimiento'] = Variable<DateTime>(fechaNacimiento);
    map['tramo'] = Variable<String>(tramo);
    map['creado_en'] = Variable<DateTime>(creadoEn);
    return map;
  }

  NinosCompanion toCompanion(bool nullToAbsent) {
    return NinosCompanion(
      id: Value(id),
      codigo: Value(codigo),
      fechaNacimiento: Value(fechaNacimiento),
      tramo: Value(tramo),
      creadoEn: Value(creadoEn),
    );
  }

  factory Nino.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Nino(
      id: serializer.fromJson<int>(json['id']),
      codigo: serializer.fromJson<String>(json['codigo']),
      fechaNacimiento: serializer.fromJson<DateTime>(json['fechaNacimiento']),
      tramo: serializer.fromJson<String>(json['tramo']),
      creadoEn: serializer.fromJson<DateTime>(json['creadoEn']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'codigo': serializer.toJson<String>(codigo),
      'fechaNacimiento': serializer.toJson<DateTime>(fechaNacimiento),
      'tramo': serializer.toJson<String>(tramo),
      'creadoEn': serializer.toJson<DateTime>(creadoEn),
    };
  }

  Nino copyWith({
    int? id,
    String? codigo,
    DateTime? fechaNacimiento,
    String? tramo,
    DateTime? creadoEn,
  }) => Nino(
    id: id ?? this.id,
    codigo: codigo ?? this.codigo,
    fechaNacimiento: fechaNacimiento ?? this.fechaNacimiento,
    tramo: tramo ?? this.tramo,
    creadoEn: creadoEn ?? this.creadoEn,
  );
  Nino copyWithCompanion(NinosCompanion data) {
    return Nino(
      id: data.id.present ? data.id.value : this.id,
      codigo: data.codigo.present ? data.codigo.value : this.codigo,
      fechaNacimiento: data.fechaNacimiento.present
          ? data.fechaNacimiento.value
          : this.fechaNacimiento,
      tramo: data.tramo.present ? data.tramo.value : this.tramo,
      creadoEn: data.creadoEn.present ? data.creadoEn.value : this.creadoEn,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Nino(')
          ..write('id: $id, ')
          ..write('codigo: $codigo, ')
          ..write('fechaNacimiento: $fechaNacimiento, ')
          ..write('tramo: $tramo, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, codigo, fechaNacimiento, tramo, creadoEn);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Nino &&
          other.id == this.id &&
          other.codigo == this.codigo &&
          other.fechaNacimiento == this.fechaNacimiento &&
          other.tramo == this.tramo &&
          other.creadoEn == this.creadoEn);
}

class NinosCompanion extends UpdateCompanion<Nino> {
  final Value<int> id;
  final Value<String> codigo;
  final Value<DateTime> fechaNacimiento;
  final Value<String> tramo;
  final Value<DateTime> creadoEn;
  const NinosCompanion({
    this.id = const Value.absent(),
    this.codigo = const Value.absent(),
    this.fechaNacimiento = const Value.absent(),
    this.tramo = const Value.absent(),
    this.creadoEn = const Value.absent(),
  });
  NinosCompanion.insert({
    this.id = const Value.absent(),
    required String codigo,
    required DateTime fechaNacimiento,
    required String tramo,
    required DateTime creadoEn,
  }) : codigo = Value(codigo),
       fechaNacimiento = Value(fechaNacimiento),
       tramo = Value(tramo),
       creadoEn = Value(creadoEn);
  static Insertable<Nino> custom({
    Expression<int>? id,
    Expression<String>? codigo,
    Expression<DateTime>? fechaNacimiento,
    Expression<String>? tramo,
    Expression<DateTime>? creadoEn,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (codigo != null) 'codigo': codigo,
      if (fechaNacimiento != null) 'fecha_nacimiento': fechaNacimiento,
      if (tramo != null) 'tramo': tramo,
      if (creadoEn != null) 'creado_en': creadoEn,
    });
  }

  NinosCompanion copyWith({
    Value<int>? id,
    Value<String>? codigo,
    Value<DateTime>? fechaNacimiento,
    Value<String>? tramo,
    Value<DateTime>? creadoEn,
  }) {
    return NinosCompanion(
      id: id ?? this.id,
      codigo: codigo ?? this.codigo,
      fechaNacimiento: fechaNacimiento ?? this.fechaNacimiento,
      tramo: tramo ?? this.tramo,
      creadoEn: creadoEn ?? this.creadoEn,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (codigo.present) {
      map['codigo'] = Variable<String>(codigo.value);
    }
    if (fechaNacimiento.present) {
      map['fecha_nacimiento'] = Variable<DateTime>(fechaNacimiento.value);
    }
    if (tramo.present) {
      map['tramo'] = Variable<String>(tramo.value);
    }
    if (creadoEn.present) {
      map['creado_en'] = Variable<DateTime>(creadoEn.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('NinosCompanion(')
          ..write('id: $id, ')
          ..write('codigo: $codigo, ')
          ..write('fechaNacimiento: $fechaNacimiento, ')
          ..write('tramo: $tramo, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }
}

class $ConsentimientosTable extends Consentimientos
    with TableInfo<$ConsentimientosTable, Consentimiento> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ConsentimientosTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _versionTextoMeta = const VerificationMeta(
    'versionTexto',
  );
  @override
  late final GeneratedColumn<String> versionTexto = GeneratedColumn<String>(
    'version_texto',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _aceptadoEnMeta = const VerificationMeta(
    'aceptadoEn',
  );
  @override
  late final GeneratedColumn<DateTime> aceptadoEn = GeneratedColumn<DateTime>(
    'aceptado_en',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [id, versionTexto, aceptadoEn];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'consentimientos';
  @override
  VerificationContext validateIntegrity(
    Insertable<Consentimiento> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('version_texto')) {
      context.handle(
        _versionTextoMeta,
        versionTexto.isAcceptableOrUnknown(
          data['version_texto']!,
          _versionTextoMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_versionTextoMeta);
    }
    if (data.containsKey('aceptado_en')) {
      context.handle(
        _aceptadoEnMeta,
        aceptadoEn.isAcceptableOrUnknown(data['aceptado_en']!, _aceptadoEnMeta),
      );
    } else if (isInserting) {
      context.missing(_aceptadoEnMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Consentimiento map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Consentimiento(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      versionTexto: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}version_texto'],
      )!,
      aceptadoEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}aceptado_en'],
      )!,
    );
  }

  @override
  $ConsentimientosTable createAlias(String alias) {
    return $ConsentimientosTable(attachedDatabase, alias);
  }
}

class Consentimiento extends DataClass implements Insertable<Consentimiento> {
  final int id;
  final String versionTexto;
  final DateTime aceptadoEn;
  const Consentimiento({
    required this.id,
    required this.versionTexto,
    required this.aceptadoEn,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['version_texto'] = Variable<String>(versionTexto);
    map['aceptado_en'] = Variable<DateTime>(aceptadoEn);
    return map;
  }

  ConsentimientosCompanion toCompanion(bool nullToAbsent) {
    return ConsentimientosCompanion(
      id: Value(id),
      versionTexto: Value(versionTexto),
      aceptadoEn: Value(aceptadoEn),
    );
  }

  factory Consentimiento.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Consentimiento(
      id: serializer.fromJson<int>(json['id']),
      versionTexto: serializer.fromJson<String>(json['versionTexto']),
      aceptadoEn: serializer.fromJson<DateTime>(json['aceptadoEn']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'versionTexto': serializer.toJson<String>(versionTexto),
      'aceptadoEn': serializer.toJson<DateTime>(aceptadoEn),
    };
  }

  Consentimiento copyWith({
    int? id,
    String? versionTexto,
    DateTime? aceptadoEn,
  }) => Consentimiento(
    id: id ?? this.id,
    versionTexto: versionTexto ?? this.versionTexto,
    aceptadoEn: aceptadoEn ?? this.aceptadoEn,
  );
  Consentimiento copyWithCompanion(ConsentimientosCompanion data) {
    return Consentimiento(
      id: data.id.present ? data.id.value : this.id,
      versionTexto: data.versionTexto.present
          ? data.versionTexto.value
          : this.versionTexto,
      aceptadoEn: data.aceptadoEn.present
          ? data.aceptadoEn.value
          : this.aceptadoEn,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Consentimiento(')
          ..write('id: $id, ')
          ..write('versionTexto: $versionTexto, ')
          ..write('aceptadoEn: $aceptadoEn')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, versionTexto, aceptadoEn);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Consentimiento &&
          other.id == this.id &&
          other.versionTexto == this.versionTexto &&
          other.aceptadoEn == this.aceptadoEn);
}

class ConsentimientosCompanion extends UpdateCompanion<Consentimiento> {
  final Value<int> id;
  final Value<String> versionTexto;
  final Value<DateTime> aceptadoEn;
  const ConsentimientosCompanion({
    this.id = const Value.absent(),
    this.versionTexto = const Value.absent(),
    this.aceptadoEn = const Value.absent(),
  });
  ConsentimientosCompanion.insert({
    this.id = const Value.absent(),
    required String versionTexto,
    required DateTime aceptadoEn,
  }) : versionTexto = Value(versionTexto),
       aceptadoEn = Value(aceptadoEn);
  static Insertable<Consentimiento> custom({
    Expression<int>? id,
    Expression<String>? versionTexto,
    Expression<DateTime>? aceptadoEn,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (versionTexto != null) 'version_texto': versionTexto,
      if (aceptadoEn != null) 'aceptado_en': aceptadoEn,
    });
  }

  ConsentimientosCompanion copyWith({
    Value<int>? id,
    Value<String>? versionTexto,
    Value<DateTime>? aceptadoEn,
  }) {
    return ConsentimientosCompanion(
      id: id ?? this.id,
      versionTexto: versionTexto ?? this.versionTexto,
      aceptadoEn: aceptadoEn ?? this.aceptadoEn,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (versionTexto.present) {
      map['version_texto'] = Variable<String>(versionTexto.value);
    }
    if (aceptadoEn.present) {
      map['aceptado_en'] = Variable<DateTime>(aceptadoEn.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ConsentimientosCompanion(')
          ..write('id: $id, ')
          ..write('versionTexto: $versionTexto, ')
          ..write('aceptadoEn: $aceptadoEn')
          ..write(')'))
        .toString();
  }
}

class $SesionesTable extends Sesiones with TableInfo<$SesionesTable, Sesion> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SesionesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _ninoIdMeta = const VerificationMeta('ninoId');
  @override
  late final GeneratedColumn<int> ninoId = GeneratedColumn<int>(
    'nino_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'REFERENCES ninos (id)',
    ),
  );
  static const VerificationMeta _tramoMeta = const VerificationMeta('tramo');
  @override
  late final GeneratedColumn<String> tramo = GeneratedColumn<String>(
    'tramo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _edadMesesMeta = const VerificationMeta(
    'edadMeses',
  );
  @override
  late final GeneratedColumn<int> edadMeses = GeneratedColumn<int>(
    'edad_meses',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _versionProtocoloMeta = const VerificationMeta(
    'versionProtocolo',
  );
  @override
  late final GeneratedColumn<String> versionProtocolo = GeneratedColumn<String>(
    'version_protocolo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _iniciadaEnMeta = const VerificationMeta(
    'iniciadaEn',
  );
  @override
  late final GeneratedColumn<DateTime> iniciadaEn = GeneratedColumn<DateTime>(
    'iniciada_en',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _cerradaEnMeta = const VerificationMeta(
    'cerradaEn',
  );
  @override
  late final GeneratedColumn<DateTime> cerradaEn = GeneratedColumn<DateTime>(
    'cerrada_en',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _focosMarcadosMeta = const VerificationMeta(
    'focosMarcados',
  );
  @override
  late final GeneratedColumn<String> focosMarcados = GeneratedColumn<String>(
    'focos_marcados',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    ninoId,
    tramo,
    edadMeses,
    versionProtocolo,
    iniciadaEn,
    cerradaEn,
    focosMarcados,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sesiones';
  @override
  VerificationContext validateIntegrity(
    Insertable<Sesion> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('nino_id')) {
      context.handle(
        _ninoIdMeta,
        ninoId.isAcceptableOrUnknown(data['nino_id']!, _ninoIdMeta),
      );
    } else if (isInserting) {
      context.missing(_ninoIdMeta);
    }
    if (data.containsKey('tramo')) {
      context.handle(
        _tramoMeta,
        tramo.isAcceptableOrUnknown(data['tramo']!, _tramoMeta),
      );
    } else if (isInserting) {
      context.missing(_tramoMeta);
    }
    if (data.containsKey('edad_meses')) {
      context.handle(
        _edadMesesMeta,
        edadMeses.isAcceptableOrUnknown(data['edad_meses']!, _edadMesesMeta),
      );
    } else if (isInserting) {
      context.missing(_edadMesesMeta);
    }
    if (data.containsKey('version_protocolo')) {
      context.handle(
        _versionProtocoloMeta,
        versionProtocolo.isAcceptableOrUnknown(
          data['version_protocolo']!,
          _versionProtocoloMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_versionProtocoloMeta);
    }
    if (data.containsKey('iniciada_en')) {
      context.handle(
        _iniciadaEnMeta,
        iniciadaEn.isAcceptableOrUnknown(data['iniciada_en']!, _iniciadaEnMeta),
      );
    } else if (isInserting) {
      context.missing(_iniciadaEnMeta);
    }
    if (data.containsKey('cerrada_en')) {
      context.handle(
        _cerradaEnMeta,
        cerradaEn.isAcceptableOrUnknown(data['cerrada_en']!, _cerradaEnMeta),
      );
    }
    if (data.containsKey('focos_marcados')) {
      context.handle(
        _focosMarcadosMeta,
        focosMarcados.isAcceptableOrUnknown(
          data['focos_marcados']!,
          _focosMarcadosMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Sesion map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Sesion(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      ninoId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}nino_id'],
      )!,
      tramo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}tramo'],
      )!,
      edadMeses: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}edad_meses'],
      )!,
      versionProtocolo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}version_protocolo'],
      )!,
      iniciadaEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}iniciada_en'],
      )!,
      cerradaEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}cerrada_en'],
      ),
      focosMarcados: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}focos_marcados'],
      )!,
    );
  }

  @override
  $SesionesTable createAlias(String alias) {
    return $SesionesTable(attachedDatabase, alias);
  }
}

class Sesion extends DataClass implements Insertable<Sesion> {
  final int id;
  final int ninoId;
  final String tramo;
  final int edadMeses;
  final String versionProtocolo;
  final DateTime iniciadaEn;
  final DateTime? cerradaEn;

  /// Ids de focos rojos marcados, separados por coma.
  final String focosMarcados;
  const Sesion({
    required this.id,
    required this.ninoId,
    required this.tramo,
    required this.edadMeses,
    required this.versionProtocolo,
    required this.iniciadaEn,
    this.cerradaEn,
    required this.focosMarcados,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['nino_id'] = Variable<int>(ninoId);
    map['tramo'] = Variable<String>(tramo);
    map['edad_meses'] = Variable<int>(edadMeses);
    map['version_protocolo'] = Variable<String>(versionProtocolo);
    map['iniciada_en'] = Variable<DateTime>(iniciadaEn);
    if (!nullToAbsent || cerradaEn != null) {
      map['cerrada_en'] = Variable<DateTime>(cerradaEn);
    }
    map['focos_marcados'] = Variable<String>(focosMarcados);
    return map;
  }

  SesionesCompanion toCompanion(bool nullToAbsent) {
    return SesionesCompanion(
      id: Value(id),
      ninoId: Value(ninoId),
      tramo: Value(tramo),
      edadMeses: Value(edadMeses),
      versionProtocolo: Value(versionProtocolo),
      iniciadaEn: Value(iniciadaEn),
      cerradaEn: cerradaEn == null && nullToAbsent
          ? const Value.absent()
          : Value(cerradaEn),
      focosMarcados: Value(focosMarcados),
    );
  }

  factory Sesion.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Sesion(
      id: serializer.fromJson<int>(json['id']),
      ninoId: serializer.fromJson<int>(json['ninoId']),
      tramo: serializer.fromJson<String>(json['tramo']),
      edadMeses: serializer.fromJson<int>(json['edadMeses']),
      versionProtocolo: serializer.fromJson<String>(json['versionProtocolo']),
      iniciadaEn: serializer.fromJson<DateTime>(json['iniciadaEn']),
      cerradaEn: serializer.fromJson<DateTime?>(json['cerradaEn']),
      focosMarcados: serializer.fromJson<String>(json['focosMarcados']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'ninoId': serializer.toJson<int>(ninoId),
      'tramo': serializer.toJson<String>(tramo),
      'edadMeses': serializer.toJson<int>(edadMeses),
      'versionProtocolo': serializer.toJson<String>(versionProtocolo),
      'iniciadaEn': serializer.toJson<DateTime>(iniciadaEn),
      'cerradaEn': serializer.toJson<DateTime?>(cerradaEn),
      'focosMarcados': serializer.toJson<String>(focosMarcados),
    };
  }

  Sesion copyWith({
    int? id,
    int? ninoId,
    String? tramo,
    int? edadMeses,
    String? versionProtocolo,
    DateTime? iniciadaEn,
    Value<DateTime?> cerradaEn = const Value.absent(),
    String? focosMarcados,
  }) => Sesion(
    id: id ?? this.id,
    ninoId: ninoId ?? this.ninoId,
    tramo: tramo ?? this.tramo,
    edadMeses: edadMeses ?? this.edadMeses,
    versionProtocolo: versionProtocolo ?? this.versionProtocolo,
    iniciadaEn: iniciadaEn ?? this.iniciadaEn,
    cerradaEn: cerradaEn.present ? cerradaEn.value : this.cerradaEn,
    focosMarcados: focosMarcados ?? this.focosMarcados,
  );
  Sesion copyWithCompanion(SesionesCompanion data) {
    return Sesion(
      id: data.id.present ? data.id.value : this.id,
      ninoId: data.ninoId.present ? data.ninoId.value : this.ninoId,
      tramo: data.tramo.present ? data.tramo.value : this.tramo,
      edadMeses: data.edadMeses.present ? data.edadMeses.value : this.edadMeses,
      versionProtocolo: data.versionProtocolo.present
          ? data.versionProtocolo.value
          : this.versionProtocolo,
      iniciadaEn: data.iniciadaEn.present
          ? data.iniciadaEn.value
          : this.iniciadaEn,
      cerradaEn: data.cerradaEn.present ? data.cerradaEn.value : this.cerradaEn,
      focosMarcados: data.focosMarcados.present
          ? data.focosMarcados.value
          : this.focosMarcados,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Sesion(')
          ..write('id: $id, ')
          ..write('ninoId: $ninoId, ')
          ..write('tramo: $tramo, ')
          ..write('edadMeses: $edadMeses, ')
          ..write('versionProtocolo: $versionProtocolo, ')
          ..write('iniciadaEn: $iniciadaEn, ')
          ..write('cerradaEn: $cerradaEn, ')
          ..write('focosMarcados: $focosMarcados')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    ninoId,
    tramo,
    edadMeses,
    versionProtocolo,
    iniciadaEn,
    cerradaEn,
    focosMarcados,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Sesion &&
          other.id == this.id &&
          other.ninoId == this.ninoId &&
          other.tramo == this.tramo &&
          other.edadMeses == this.edadMeses &&
          other.versionProtocolo == this.versionProtocolo &&
          other.iniciadaEn == this.iniciadaEn &&
          other.cerradaEn == this.cerradaEn &&
          other.focosMarcados == this.focosMarcados);
}

class SesionesCompanion extends UpdateCompanion<Sesion> {
  final Value<int> id;
  final Value<int> ninoId;
  final Value<String> tramo;
  final Value<int> edadMeses;
  final Value<String> versionProtocolo;
  final Value<DateTime> iniciadaEn;
  final Value<DateTime?> cerradaEn;
  final Value<String> focosMarcados;
  const SesionesCompanion({
    this.id = const Value.absent(),
    this.ninoId = const Value.absent(),
    this.tramo = const Value.absent(),
    this.edadMeses = const Value.absent(),
    this.versionProtocolo = const Value.absent(),
    this.iniciadaEn = const Value.absent(),
    this.cerradaEn = const Value.absent(),
    this.focosMarcados = const Value.absent(),
  });
  SesionesCompanion.insert({
    this.id = const Value.absent(),
    required int ninoId,
    required String tramo,
    required int edadMeses,
    required String versionProtocolo,
    required DateTime iniciadaEn,
    this.cerradaEn = const Value.absent(),
    this.focosMarcados = const Value.absent(),
  }) : ninoId = Value(ninoId),
       tramo = Value(tramo),
       edadMeses = Value(edadMeses),
       versionProtocolo = Value(versionProtocolo),
       iniciadaEn = Value(iniciadaEn);
  static Insertable<Sesion> custom({
    Expression<int>? id,
    Expression<int>? ninoId,
    Expression<String>? tramo,
    Expression<int>? edadMeses,
    Expression<String>? versionProtocolo,
    Expression<DateTime>? iniciadaEn,
    Expression<DateTime>? cerradaEn,
    Expression<String>? focosMarcados,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (ninoId != null) 'nino_id': ninoId,
      if (tramo != null) 'tramo': tramo,
      if (edadMeses != null) 'edad_meses': edadMeses,
      if (versionProtocolo != null) 'version_protocolo': versionProtocolo,
      if (iniciadaEn != null) 'iniciada_en': iniciadaEn,
      if (cerradaEn != null) 'cerrada_en': cerradaEn,
      if (focosMarcados != null) 'focos_marcados': focosMarcados,
    });
  }

  SesionesCompanion copyWith({
    Value<int>? id,
    Value<int>? ninoId,
    Value<String>? tramo,
    Value<int>? edadMeses,
    Value<String>? versionProtocolo,
    Value<DateTime>? iniciadaEn,
    Value<DateTime?>? cerradaEn,
    Value<String>? focosMarcados,
  }) {
    return SesionesCompanion(
      id: id ?? this.id,
      ninoId: ninoId ?? this.ninoId,
      tramo: tramo ?? this.tramo,
      edadMeses: edadMeses ?? this.edadMeses,
      versionProtocolo: versionProtocolo ?? this.versionProtocolo,
      iniciadaEn: iniciadaEn ?? this.iniciadaEn,
      cerradaEn: cerradaEn ?? this.cerradaEn,
      focosMarcados: focosMarcados ?? this.focosMarcados,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (ninoId.present) {
      map['nino_id'] = Variable<int>(ninoId.value);
    }
    if (tramo.present) {
      map['tramo'] = Variable<String>(tramo.value);
    }
    if (edadMeses.present) {
      map['edad_meses'] = Variable<int>(edadMeses.value);
    }
    if (versionProtocolo.present) {
      map['version_protocolo'] = Variable<String>(versionProtocolo.value);
    }
    if (iniciadaEn.present) {
      map['iniciada_en'] = Variable<DateTime>(iniciadaEn.value);
    }
    if (cerradaEn.present) {
      map['cerrada_en'] = Variable<DateTime>(cerradaEn.value);
    }
    if (focosMarcados.present) {
      map['focos_marcados'] = Variable<String>(focosMarcados.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SesionesCompanion(')
          ..write('id: $id, ')
          ..write('ninoId: $ninoId, ')
          ..write('tramo: $tramo, ')
          ..write('edadMeses: $edadMeses, ')
          ..write('versionProtocolo: $versionProtocolo, ')
          ..write('iniciadaEn: $iniciadaEn, ')
          ..write('cerradaEn: $cerradaEn, ')
          ..write('focosMarcados: $focosMarcados')
          ..write(')'))
        .toString();
  }
}

class $RespuestasTable extends Respuestas
    with TableInfo<$RespuestasTable, Respuesta> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $RespuestasTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _sesionIdMeta = const VerificationMeta(
    'sesionId',
  );
  @override
  late final GeneratedColumn<int> sesionId = GeneratedColumn<int>(
    'sesion_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'REFERENCES sesiones (id)',
    ),
  );
  static const VerificationMeta _itemIdMeta = const VerificationMeta('itemId');
  @override
  late final GeneratedColumn<String> itemId = GeneratedColumn<String>(
    'item_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _opcionMeta = const VerificationMeta('opcion');
  @override
  late final GeneratedColumn<String> opcion = GeneratedColumn<String>(
    'opcion',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _puntosMeta = const VerificationMeta('puntos');
  @override
  late final GeneratedColumn<int> puntos = GeneratedColumn<int>(
    'puntos',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [id, sesionId, itemId, opcion, puntos];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'respuestas';
  @override
  VerificationContext validateIntegrity(
    Insertable<Respuesta> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('sesion_id')) {
      context.handle(
        _sesionIdMeta,
        sesionId.isAcceptableOrUnknown(data['sesion_id']!, _sesionIdMeta),
      );
    } else if (isInserting) {
      context.missing(_sesionIdMeta);
    }
    if (data.containsKey('item_id')) {
      context.handle(
        _itemIdMeta,
        itemId.isAcceptableOrUnknown(data['item_id']!, _itemIdMeta),
      );
    } else if (isInserting) {
      context.missing(_itemIdMeta);
    }
    if (data.containsKey('opcion')) {
      context.handle(
        _opcionMeta,
        opcion.isAcceptableOrUnknown(data['opcion']!, _opcionMeta),
      );
    } else if (isInserting) {
      context.missing(_opcionMeta);
    }
    if (data.containsKey('puntos')) {
      context.handle(
        _puntosMeta,
        puntos.isAcceptableOrUnknown(data['puntos']!, _puntosMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  List<Set<GeneratedColumn>> get uniqueKeys => [
    {sesionId, itemId},
  ];
  @override
  Respuesta map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Respuesta(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      sesionId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}sesion_id'],
      )!,
      itemId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}item_id'],
      )!,
      opcion: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}opcion'],
      )!,
      puntos: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}puntos'],
      ),
    );
  }

  @override
  $RespuestasTable createAlias(String alias) {
    return $RespuestasTable(attachedDatabase, alias);
  }
}

class Respuesta extends DataClass implements Insertable<Respuesta> {
  final int id;
  final int sesionId;
  final String itemId;

  /// 'casi_siempre', 'a_veces', 'casi_nunca' o 'no_se'.
  final String opcion;

  /// Puntos (2, 1 o 0); nulo cuando la respuesta fue "No sé".
  final int? puntos;
  const Respuesta({
    required this.id,
    required this.sesionId,
    required this.itemId,
    required this.opcion,
    this.puntos,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['sesion_id'] = Variable<int>(sesionId);
    map['item_id'] = Variable<String>(itemId);
    map['opcion'] = Variable<String>(opcion);
    if (!nullToAbsent || puntos != null) {
      map['puntos'] = Variable<int>(puntos);
    }
    return map;
  }

  RespuestasCompanion toCompanion(bool nullToAbsent) {
    return RespuestasCompanion(
      id: Value(id),
      sesionId: Value(sesionId),
      itemId: Value(itemId),
      opcion: Value(opcion),
      puntos: puntos == null && nullToAbsent
          ? const Value.absent()
          : Value(puntos),
    );
  }

  factory Respuesta.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Respuesta(
      id: serializer.fromJson<int>(json['id']),
      sesionId: serializer.fromJson<int>(json['sesionId']),
      itemId: serializer.fromJson<String>(json['itemId']),
      opcion: serializer.fromJson<String>(json['opcion']),
      puntos: serializer.fromJson<int?>(json['puntos']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'sesionId': serializer.toJson<int>(sesionId),
      'itemId': serializer.toJson<String>(itemId),
      'opcion': serializer.toJson<String>(opcion),
      'puntos': serializer.toJson<int?>(puntos),
    };
  }

  Respuesta copyWith({
    int? id,
    int? sesionId,
    String? itemId,
    String? opcion,
    Value<int?> puntos = const Value.absent(),
  }) => Respuesta(
    id: id ?? this.id,
    sesionId: sesionId ?? this.sesionId,
    itemId: itemId ?? this.itemId,
    opcion: opcion ?? this.opcion,
    puntos: puntos.present ? puntos.value : this.puntos,
  );
  Respuesta copyWithCompanion(RespuestasCompanion data) {
    return Respuesta(
      id: data.id.present ? data.id.value : this.id,
      sesionId: data.sesionId.present ? data.sesionId.value : this.sesionId,
      itemId: data.itemId.present ? data.itemId.value : this.itemId,
      opcion: data.opcion.present ? data.opcion.value : this.opcion,
      puntos: data.puntos.present ? data.puntos.value : this.puntos,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Respuesta(')
          ..write('id: $id, ')
          ..write('sesionId: $sesionId, ')
          ..write('itemId: $itemId, ')
          ..write('opcion: $opcion, ')
          ..write('puntos: $puntos')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, sesionId, itemId, opcion, puntos);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Respuesta &&
          other.id == this.id &&
          other.sesionId == this.sesionId &&
          other.itemId == this.itemId &&
          other.opcion == this.opcion &&
          other.puntos == this.puntos);
}

class RespuestasCompanion extends UpdateCompanion<Respuesta> {
  final Value<int> id;
  final Value<int> sesionId;
  final Value<String> itemId;
  final Value<String> opcion;
  final Value<int?> puntos;
  const RespuestasCompanion({
    this.id = const Value.absent(),
    this.sesionId = const Value.absent(),
    this.itemId = const Value.absent(),
    this.opcion = const Value.absent(),
    this.puntos = const Value.absent(),
  });
  RespuestasCompanion.insert({
    this.id = const Value.absent(),
    required int sesionId,
    required String itemId,
    required String opcion,
    this.puntos = const Value.absent(),
  }) : sesionId = Value(sesionId),
       itemId = Value(itemId),
       opcion = Value(opcion);
  static Insertable<Respuesta> custom({
    Expression<int>? id,
    Expression<int>? sesionId,
    Expression<String>? itemId,
    Expression<String>? opcion,
    Expression<int>? puntos,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (sesionId != null) 'sesion_id': sesionId,
      if (itemId != null) 'item_id': itemId,
      if (opcion != null) 'opcion': opcion,
      if (puntos != null) 'puntos': puntos,
    });
  }

  RespuestasCompanion copyWith({
    Value<int>? id,
    Value<int>? sesionId,
    Value<String>? itemId,
    Value<String>? opcion,
    Value<int?>? puntos,
  }) {
    return RespuestasCompanion(
      id: id ?? this.id,
      sesionId: sesionId ?? this.sesionId,
      itemId: itemId ?? this.itemId,
      opcion: opcion ?? this.opcion,
      puntos: puntos ?? this.puntos,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (sesionId.present) {
      map['sesion_id'] = Variable<int>(sesionId.value);
    }
    if (itemId.present) {
      map['item_id'] = Variable<String>(itemId.value);
    }
    if (opcion.present) {
      map['opcion'] = Variable<String>(opcion.value);
    }
    if (puntos.present) {
      map['puntos'] = Variable<int>(puntos.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('RespuestasCompanion(')
          ..write('id: $id, ')
          ..write('sesionId: $sesionId, ')
          ..write('itemId: $itemId, ')
          ..write('opcion: $opcion, ')
          ..write('puntos: $puntos')
          ..write(')'))
        .toString();
  }
}

class $ResultadosTable extends Resultados
    with TableInfo<$ResultadosTable, Resultado> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ResultadosTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _sesionIdMeta = const VerificationMeta(
    'sesionId',
  );
  @override
  late final GeneratedColumn<int> sesionId = GeneratedColumn<int>(
    'sesion_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'UNIQUE REFERENCES sesiones (id)',
    ),
  );
  static const VerificationMeta _puntajesPorAreaMeta = const VerificationMeta(
    'puntajesPorArea',
  );
  @override
  late final GeneratedColumn<String> puntajesPorArea = GeneratedColumn<String>(
    'puntajes_por_area',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _puntosTotalMeta = const VerificationMeta(
    'puntosTotal',
  );
  @override
  late final GeneratedColumn<int> puntosTotal = GeneratedColumn<int>(
    'puntos_total',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _maximoTotalMeta = const VerificationMeta(
    'maximoTotal',
  );
  @override
  late final GeneratedColumn<int> maximoTotal = GeneratedColumn<int>(
    'maximo_total',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _noSeMeta = const VerificationMeta('noSe');
  @override
  late final GeneratedColumn<int> noSe = GeneratedColumn<int>(
    'no_se',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nivelMeta = const VerificationMeta('nivel');
  @override
  late final GeneratedColumn<String> nivel = GeneratedColumn<String>(
    'nivel',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _focosRojosMeta = const VerificationMeta(
    'focosRojos',
  );
  @override
  late final GeneratedColumn<String> focosRojos = GeneratedColumn<String>(
    'focos_rojos',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  static const VerificationMeta _versionProtocoloMeta = const VerificationMeta(
    'versionProtocolo',
  );
  @override
  late final GeneratedColumn<String> versionProtocolo = GeneratedColumn<String>(
    'version_protocolo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _estadoProtocoloMeta = const VerificationMeta(
    'estadoProtocolo',
  );
  @override
  late final GeneratedColumn<String> estadoProtocolo = GeneratedColumn<String>(
    'estado_protocolo',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _creadoEnMeta = const VerificationMeta(
    'creadoEn',
  );
  @override
  late final GeneratedColumn<DateTime> creadoEn = GeneratedColumn<DateTime>(
    'creado_en',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    sesionId,
    puntajesPorArea,
    puntosTotal,
    maximoTotal,
    noSe,
    nivel,
    focosRojos,
    versionProtocolo,
    estadoProtocolo,
    creadoEn,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'resultados';
  @override
  VerificationContext validateIntegrity(
    Insertable<Resultado> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('sesion_id')) {
      context.handle(
        _sesionIdMeta,
        sesionId.isAcceptableOrUnknown(data['sesion_id']!, _sesionIdMeta),
      );
    } else if (isInserting) {
      context.missing(_sesionIdMeta);
    }
    if (data.containsKey('puntajes_por_area')) {
      context.handle(
        _puntajesPorAreaMeta,
        puntajesPorArea.isAcceptableOrUnknown(
          data['puntajes_por_area']!,
          _puntajesPorAreaMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_puntajesPorAreaMeta);
    }
    if (data.containsKey('puntos_total')) {
      context.handle(
        _puntosTotalMeta,
        puntosTotal.isAcceptableOrUnknown(
          data['puntos_total']!,
          _puntosTotalMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_puntosTotalMeta);
    }
    if (data.containsKey('maximo_total')) {
      context.handle(
        _maximoTotalMeta,
        maximoTotal.isAcceptableOrUnknown(
          data['maximo_total']!,
          _maximoTotalMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_maximoTotalMeta);
    }
    if (data.containsKey('no_se')) {
      context.handle(
        _noSeMeta,
        noSe.isAcceptableOrUnknown(data['no_se']!, _noSeMeta),
      );
    } else if (isInserting) {
      context.missing(_noSeMeta);
    }
    if (data.containsKey('nivel')) {
      context.handle(
        _nivelMeta,
        nivel.isAcceptableOrUnknown(data['nivel']!, _nivelMeta),
      );
    } else if (isInserting) {
      context.missing(_nivelMeta);
    }
    if (data.containsKey('focos_rojos')) {
      context.handle(
        _focosRojosMeta,
        focosRojos.isAcceptableOrUnknown(data['focos_rojos']!, _focosRojosMeta),
      );
    }
    if (data.containsKey('version_protocolo')) {
      context.handle(
        _versionProtocoloMeta,
        versionProtocolo.isAcceptableOrUnknown(
          data['version_protocolo']!,
          _versionProtocoloMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_versionProtocoloMeta);
    }
    if (data.containsKey('estado_protocolo')) {
      context.handle(
        _estadoProtocoloMeta,
        estadoProtocolo.isAcceptableOrUnknown(
          data['estado_protocolo']!,
          _estadoProtocoloMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_estadoProtocoloMeta);
    }
    if (data.containsKey('creado_en')) {
      context.handle(
        _creadoEnMeta,
        creadoEn.isAcceptableOrUnknown(data['creado_en']!, _creadoEnMeta),
      );
    } else if (isInserting) {
      context.missing(_creadoEnMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Resultado map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Resultado(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      sesionId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}sesion_id'],
      )!,
      puntajesPorArea: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}puntajes_por_area'],
      )!,
      puntosTotal: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}puntos_total'],
      )!,
      maximoTotal: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}maximo_total'],
      )!,
      noSe: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}no_se'],
      )!,
      nivel: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}nivel'],
      )!,
      focosRojos: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}focos_rojos'],
      )!,
      versionProtocolo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}version_protocolo'],
      )!,
      estadoProtocolo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}estado_protocolo'],
      )!,
      creadoEn: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}creado_en'],
      )!,
    );
  }

  @override
  $ResultadosTable createAlias(String alias) {
    return $ResultadosTable(attachedDatabase, alias);
  }
}

class Resultado extends DataClass implements Insertable<Resultado> {
  final int id;
  final int sesionId;

  /// JSON {areaId: {puntos, maximo, respondidas, no_se}}.
  final String puntajesPorArea;
  final int puntosTotal;
  final int maximoTotal;
  final int noSe;
  final String nivel;
  final String focosRojos;
  final String versionProtocolo;
  final String estadoProtocolo;
  final DateTime creadoEn;
  const Resultado({
    required this.id,
    required this.sesionId,
    required this.puntajesPorArea,
    required this.puntosTotal,
    required this.maximoTotal,
    required this.noSe,
    required this.nivel,
    required this.focosRojos,
    required this.versionProtocolo,
    required this.estadoProtocolo,
    required this.creadoEn,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['sesion_id'] = Variable<int>(sesionId);
    map['puntajes_por_area'] = Variable<String>(puntajesPorArea);
    map['puntos_total'] = Variable<int>(puntosTotal);
    map['maximo_total'] = Variable<int>(maximoTotal);
    map['no_se'] = Variable<int>(noSe);
    map['nivel'] = Variable<String>(nivel);
    map['focos_rojos'] = Variable<String>(focosRojos);
    map['version_protocolo'] = Variable<String>(versionProtocolo);
    map['estado_protocolo'] = Variable<String>(estadoProtocolo);
    map['creado_en'] = Variable<DateTime>(creadoEn);
    return map;
  }

  ResultadosCompanion toCompanion(bool nullToAbsent) {
    return ResultadosCompanion(
      id: Value(id),
      sesionId: Value(sesionId),
      puntajesPorArea: Value(puntajesPorArea),
      puntosTotal: Value(puntosTotal),
      maximoTotal: Value(maximoTotal),
      noSe: Value(noSe),
      nivel: Value(nivel),
      focosRojos: Value(focosRojos),
      versionProtocolo: Value(versionProtocolo),
      estadoProtocolo: Value(estadoProtocolo),
      creadoEn: Value(creadoEn),
    );
  }

  factory Resultado.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Resultado(
      id: serializer.fromJson<int>(json['id']),
      sesionId: serializer.fromJson<int>(json['sesionId']),
      puntajesPorArea: serializer.fromJson<String>(json['puntajesPorArea']),
      puntosTotal: serializer.fromJson<int>(json['puntosTotal']),
      maximoTotal: serializer.fromJson<int>(json['maximoTotal']),
      noSe: serializer.fromJson<int>(json['noSe']),
      nivel: serializer.fromJson<String>(json['nivel']),
      focosRojos: serializer.fromJson<String>(json['focosRojos']),
      versionProtocolo: serializer.fromJson<String>(json['versionProtocolo']),
      estadoProtocolo: serializer.fromJson<String>(json['estadoProtocolo']),
      creadoEn: serializer.fromJson<DateTime>(json['creadoEn']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'sesionId': serializer.toJson<int>(sesionId),
      'puntajesPorArea': serializer.toJson<String>(puntajesPorArea),
      'puntosTotal': serializer.toJson<int>(puntosTotal),
      'maximoTotal': serializer.toJson<int>(maximoTotal),
      'noSe': serializer.toJson<int>(noSe),
      'nivel': serializer.toJson<String>(nivel),
      'focosRojos': serializer.toJson<String>(focosRojos),
      'versionProtocolo': serializer.toJson<String>(versionProtocolo),
      'estadoProtocolo': serializer.toJson<String>(estadoProtocolo),
      'creadoEn': serializer.toJson<DateTime>(creadoEn),
    };
  }

  Resultado copyWith({
    int? id,
    int? sesionId,
    String? puntajesPorArea,
    int? puntosTotal,
    int? maximoTotal,
    int? noSe,
    String? nivel,
    String? focosRojos,
    String? versionProtocolo,
    String? estadoProtocolo,
    DateTime? creadoEn,
  }) => Resultado(
    id: id ?? this.id,
    sesionId: sesionId ?? this.sesionId,
    puntajesPorArea: puntajesPorArea ?? this.puntajesPorArea,
    puntosTotal: puntosTotal ?? this.puntosTotal,
    maximoTotal: maximoTotal ?? this.maximoTotal,
    noSe: noSe ?? this.noSe,
    nivel: nivel ?? this.nivel,
    focosRojos: focosRojos ?? this.focosRojos,
    versionProtocolo: versionProtocolo ?? this.versionProtocolo,
    estadoProtocolo: estadoProtocolo ?? this.estadoProtocolo,
    creadoEn: creadoEn ?? this.creadoEn,
  );
  Resultado copyWithCompanion(ResultadosCompanion data) {
    return Resultado(
      id: data.id.present ? data.id.value : this.id,
      sesionId: data.sesionId.present ? data.sesionId.value : this.sesionId,
      puntajesPorArea: data.puntajesPorArea.present
          ? data.puntajesPorArea.value
          : this.puntajesPorArea,
      puntosTotal: data.puntosTotal.present
          ? data.puntosTotal.value
          : this.puntosTotal,
      maximoTotal: data.maximoTotal.present
          ? data.maximoTotal.value
          : this.maximoTotal,
      noSe: data.noSe.present ? data.noSe.value : this.noSe,
      nivel: data.nivel.present ? data.nivel.value : this.nivel,
      focosRojos: data.focosRojos.present
          ? data.focosRojos.value
          : this.focosRojos,
      versionProtocolo: data.versionProtocolo.present
          ? data.versionProtocolo.value
          : this.versionProtocolo,
      estadoProtocolo: data.estadoProtocolo.present
          ? data.estadoProtocolo.value
          : this.estadoProtocolo,
      creadoEn: data.creadoEn.present ? data.creadoEn.value : this.creadoEn,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Resultado(')
          ..write('id: $id, ')
          ..write('sesionId: $sesionId, ')
          ..write('puntajesPorArea: $puntajesPorArea, ')
          ..write('puntosTotal: $puntosTotal, ')
          ..write('maximoTotal: $maximoTotal, ')
          ..write('noSe: $noSe, ')
          ..write('nivel: $nivel, ')
          ..write('focosRojos: $focosRojos, ')
          ..write('versionProtocolo: $versionProtocolo, ')
          ..write('estadoProtocolo: $estadoProtocolo, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    sesionId,
    puntajesPorArea,
    puntosTotal,
    maximoTotal,
    noSe,
    nivel,
    focosRojos,
    versionProtocolo,
    estadoProtocolo,
    creadoEn,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Resultado &&
          other.id == this.id &&
          other.sesionId == this.sesionId &&
          other.puntajesPorArea == this.puntajesPorArea &&
          other.puntosTotal == this.puntosTotal &&
          other.maximoTotal == this.maximoTotal &&
          other.noSe == this.noSe &&
          other.nivel == this.nivel &&
          other.focosRojos == this.focosRojos &&
          other.versionProtocolo == this.versionProtocolo &&
          other.estadoProtocolo == this.estadoProtocolo &&
          other.creadoEn == this.creadoEn);
}

class ResultadosCompanion extends UpdateCompanion<Resultado> {
  final Value<int> id;
  final Value<int> sesionId;
  final Value<String> puntajesPorArea;
  final Value<int> puntosTotal;
  final Value<int> maximoTotal;
  final Value<int> noSe;
  final Value<String> nivel;
  final Value<String> focosRojos;
  final Value<String> versionProtocolo;
  final Value<String> estadoProtocolo;
  final Value<DateTime> creadoEn;
  const ResultadosCompanion({
    this.id = const Value.absent(),
    this.sesionId = const Value.absent(),
    this.puntajesPorArea = const Value.absent(),
    this.puntosTotal = const Value.absent(),
    this.maximoTotal = const Value.absent(),
    this.noSe = const Value.absent(),
    this.nivel = const Value.absent(),
    this.focosRojos = const Value.absent(),
    this.versionProtocolo = const Value.absent(),
    this.estadoProtocolo = const Value.absent(),
    this.creadoEn = const Value.absent(),
  });
  ResultadosCompanion.insert({
    this.id = const Value.absent(),
    required int sesionId,
    required String puntajesPorArea,
    required int puntosTotal,
    required int maximoTotal,
    required int noSe,
    required String nivel,
    this.focosRojos = const Value.absent(),
    required String versionProtocolo,
    required String estadoProtocolo,
    required DateTime creadoEn,
  }) : sesionId = Value(sesionId),
       puntajesPorArea = Value(puntajesPorArea),
       puntosTotal = Value(puntosTotal),
       maximoTotal = Value(maximoTotal),
       noSe = Value(noSe),
       nivel = Value(nivel),
       versionProtocolo = Value(versionProtocolo),
       estadoProtocolo = Value(estadoProtocolo),
       creadoEn = Value(creadoEn);
  static Insertable<Resultado> custom({
    Expression<int>? id,
    Expression<int>? sesionId,
    Expression<String>? puntajesPorArea,
    Expression<int>? puntosTotal,
    Expression<int>? maximoTotal,
    Expression<int>? noSe,
    Expression<String>? nivel,
    Expression<String>? focosRojos,
    Expression<String>? versionProtocolo,
    Expression<String>? estadoProtocolo,
    Expression<DateTime>? creadoEn,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (sesionId != null) 'sesion_id': sesionId,
      if (puntajesPorArea != null) 'puntajes_por_area': puntajesPorArea,
      if (puntosTotal != null) 'puntos_total': puntosTotal,
      if (maximoTotal != null) 'maximo_total': maximoTotal,
      if (noSe != null) 'no_se': noSe,
      if (nivel != null) 'nivel': nivel,
      if (focosRojos != null) 'focos_rojos': focosRojos,
      if (versionProtocolo != null) 'version_protocolo': versionProtocolo,
      if (estadoProtocolo != null) 'estado_protocolo': estadoProtocolo,
      if (creadoEn != null) 'creado_en': creadoEn,
    });
  }

  ResultadosCompanion copyWith({
    Value<int>? id,
    Value<int>? sesionId,
    Value<String>? puntajesPorArea,
    Value<int>? puntosTotal,
    Value<int>? maximoTotal,
    Value<int>? noSe,
    Value<String>? nivel,
    Value<String>? focosRojos,
    Value<String>? versionProtocolo,
    Value<String>? estadoProtocolo,
    Value<DateTime>? creadoEn,
  }) {
    return ResultadosCompanion(
      id: id ?? this.id,
      sesionId: sesionId ?? this.sesionId,
      puntajesPorArea: puntajesPorArea ?? this.puntajesPorArea,
      puntosTotal: puntosTotal ?? this.puntosTotal,
      maximoTotal: maximoTotal ?? this.maximoTotal,
      noSe: noSe ?? this.noSe,
      nivel: nivel ?? this.nivel,
      focosRojos: focosRojos ?? this.focosRojos,
      versionProtocolo: versionProtocolo ?? this.versionProtocolo,
      estadoProtocolo: estadoProtocolo ?? this.estadoProtocolo,
      creadoEn: creadoEn ?? this.creadoEn,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (sesionId.present) {
      map['sesion_id'] = Variable<int>(sesionId.value);
    }
    if (puntajesPorArea.present) {
      map['puntajes_por_area'] = Variable<String>(puntajesPorArea.value);
    }
    if (puntosTotal.present) {
      map['puntos_total'] = Variable<int>(puntosTotal.value);
    }
    if (maximoTotal.present) {
      map['maximo_total'] = Variable<int>(maximoTotal.value);
    }
    if (noSe.present) {
      map['no_se'] = Variable<int>(noSe.value);
    }
    if (nivel.present) {
      map['nivel'] = Variable<String>(nivel.value);
    }
    if (focosRojos.present) {
      map['focos_rojos'] = Variable<String>(focosRojos.value);
    }
    if (versionProtocolo.present) {
      map['version_protocolo'] = Variable<String>(versionProtocolo.value);
    }
    if (estadoProtocolo.present) {
      map['estado_protocolo'] = Variable<String>(estadoProtocolo.value);
    }
    if (creadoEn.present) {
      map['creado_en'] = Variable<DateTime>(creadoEn.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ResultadosCompanion(')
          ..write('id: $id, ')
          ..write('sesionId: $sesionId, ')
          ..write('puntajesPorArea: $puntajesPorArea, ')
          ..write('puntosTotal: $puntosTotal, ')
          ..write('maximoTotal: $maximoTotal, ')
          ..write('noSe: $noSe, ')
          ..write('nivel: $nivel, ')
          ..write('focosRojos: $focosRojos, ')
          ..write('versionProtocolo: $versionProtocolo, ')
          ..write('estadoProtocolo: $estadoProtocolo, ')
          ..write('creadoEn: $creadoEn')
          ..write(')'))
        .toString();
  }
}

class $FotosTable extends Fotos with TableInfo<$FotosTable, Foto> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $FotosTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<int> id = GeneratedColumn<int>(
    'id',
    aliasedName,
    false,
    hasAutoIncrement: true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'PRIMARY KEY AUTOINCREMENT',
    ),
  );
  static const VerificationMeta _ninoIdMeta = const VerificationMeta('ninoId');
  @override
  late final GeneratedColumn<int> ninoId = GeneratedColumn<int>(
    'nino_id',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'REFERENCES ninos (id)',
    ),
  );
  static const VerificationMeta _rutaMeta = const VerificationMeta('ruta');
  @override
  late final GeneratedColumn<String> ruta = GeneratedColumn<String>(
    'ruta',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _fechaMeta = const VerificationMeta('fecha');
  @override
  late final GeneratedColumn<DateTime> fecha = GeneratedColumn<DateTime>(
    'fecha',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _notaMeta = const VerificationMeta('nota');
  @override
  late final GeneratedColumn<String> nota = GeneratedColumn<String>(
    'nota',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(''),
  );
  @override
  List<GeneratedColumn> get $columns => [id, ninoId, ruta, fecha, nota];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'fotos';
  @override
  VerificationContext validateIntegrity(
    Insertable<Foto> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    }
    if (data.containsKey('nino_id')) {
      context.handle(
        _ninoIdMeta,
        ninoId.isAcceptableOrUnknown(data['nino_id']!, _ninoIdMeta),
      );
    } else if (isInserting) {
      context.missing(_ninoIdMeta);
    }
    if (data.containsKey('ruta')) {
      context.handle(
        _rutaMeta,
        ruta.isAcceptableOrUnknown(data['ruta']!, _rutaMeta),
      );
    } else if (isInserting) {
      context.missing(_rutaMeta);
    }
    if (data.containsKey('fecha')) {
      context.handle(
        _fechaMeta,
        fecha.isAcceptableOrUnknown(data['fecha']!, _fechaMeta),
      );
    } else if (isInserting) {
      context.missing(_fechaMeta);
    }
    if (data.containsKey('nota')) {
      context.handle(
        _notaMeta,
        nota.isAcceptableOrUnknown(data['nota']!, _notaMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Foto map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Foto(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}id'],
      )!,
      ninoId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}nino_id'],
      )!,
      ruta: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}ruta'],
      )!,
      fecha: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}fecha'],
      )!,
      nota: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}nota'],
      )!,
    );
  }

  @override
  $FotosTable createAlias(String alias) {
    return $FotosTable(attachedDatabase, alias);
  }
}

class Foto extends DataClass implements Insertable<Foto> {
  final int id;
  final int ninoId;

  /// Ruta dentro del almacenamiento privado de la aplicación.
  final String ruta;
  final DateTime fecha;
  final String nota;
  const Foto({
    required this.id,
    required this.ninoId,
    required this.ruta,
    required this.fecha,
    required this.nota,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<int>(id);
    map['nino_id'] = Variable<int>(ninoId);
    map['ruta'] = Variable<String>(ruta);
    map['fecha'] = Variable<DateTime>(fecha);
    map['nota'] = Variable<String>(nota);
    return map;
  }

  FotosCompanion toCompanion(bool nullToAbsent) {
    return FotosCompanion(
      id: Value(id),
      ninoId: Value(ninoId),
      ruta: Value(ruta),
      fecha: Value(fecha),
      nota: Value(nota),
    );
  }

  factory Foto.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Foto(
      id: serializer.fromJson<int>(json['id']),
      ninoId: serializer.fromJson<int>(json['ninoId']),
      ruta: serializer.fromJson<String>(json['ruta']),
      fecha: serializer.fromJson<DateTime>(json['fecha']),
      nota: serializer.fromJson<String>(json['nota']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<int>(id),
      'ninoId': serializer.toJson<int>(ninoId),
      'ruta': serializer.toJson<String>(ruta),
      'fecha': serializer.toJson<DateTime>(fecha),
      'nota': serializer.toJson<String>(nota),
    };
  }

  Foto copyWith({
    int? id,
    int? ninoId,
    String? ruta,
    DateTime? fecha,
    String? nota,
  }) => Foto(
    id: id ?? this.id,
    ninoId: ninoId ?? this.ninoId,
    ruta: ruta ?? this.ruta,
    fecha: fecha ?? this.fecha,
    nota: nota ?? this.nota,
  );
  Foto copyWithCompanion(FotosCompanion data) {
    return Foto(
      id: data.id.present ? data.id.value : this.id,
      ninoId: data.ninoId.present ? data.ninoId.value : this.ninoId,
      ruta: data.ruta.present ? data.ruta.value : this.ruta,
      fecha: data.fecha.present ? data.fecha.value : this.fecha,
      nota: data.nota.present ? data.nota.value : this.nota,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Foto(')
          ..write('id: $id, ')
          ..write('ninoId: $ninoId, ')
          ..write('ruta: $ruta, ')
          ..write('fecha: $fecha, ')
          ..write('nota: $nota')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(id, ninoId, ruta, fecha, nota);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Foto &&
          other.id == this.id &&
          other.ninoId == this.ninoId &&
          other.ruta == this.ruta &&
          other.fecha == this.fecha &&
          other.nota == this.nota);
}

class FotosCompanion extends UpdateCompanion<Foto> {
  final Value<int> id;
  final Value<int> ninoId;
  final Value<String> ruta;
  final Value<DateTime> fecha;
  final Value<String> nota;
  const FotosCompanion({
    this.id = const Value.absent(),
    this.ninoId = const Value.absent(),
    this.ruta = const Value.absent(),
    this.fecha = const Value.absent(),
    this.nota = const Value.absent(),
  });
  FotosCompanion.insert({
    this.id = const Value.absent(),
    required int ninoId,
    required String ruta,
    required DateTime fecha,
    this.nota = const Value.absent(),
  }) : ninoId = Value(ninoId),
       ruta = Value(ruta),
       fecha = Value(fecha);
  static Insertable<Foto> custom({
    Expression<int>? id,
    Expression<int>? ninoId,
    Expression<String>? ruta,
    Expression<DateTime>? fecha,
    Expression<String>? nota,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (ninoId != null) 'nino_id': ninoId,
      if (ruta != null) 'ruta': ruta,
      if (fecha != null) 'fecha': fecha,
      if (nota != null) 'nota': nota,
    });
  }

  FotosCompanion copyWith({
    Value<int>? id,
    Value<int>? ninoId,
    Value<String>? ruta,
    Value<DateTime>? fecha,
    Value<String>? nota,
  }) {
    return FotosCompanion(
      id: id ?? this.id,
      ninoId: ninoId ?? this.ninoId,
      ruta: ruta ?? this.ruta,
      fecha: fecha ?? this.fecha,
      nota: nota ?? this.nota,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<int>(id.value);
    }
    if (ninoId.present) {
      map['nino_id'] = Variable<int>(ninoId.value);
    }
    if (ruta.present) {
      map['ruta'] = Variable<String>(ruta.value);
    }
    if (fecha.present) {
      map['fecha'] = Variable<DateTime>(fecha.value);
    }
    if (nota.present) {
      map['nota'] = Variable<String>(nota.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('FotosCompanion(')
          ..write('id: $id, ')
          ..write('ninoId: $ninoId, ')
          ..write('ruta: $ruta, ')
          ..write('fecha: $fecha, ')
          ..write('nota: $nota')
          ..write(')'))
        .toString();
  }
}

abstract class _$BaseDatos extends GeneratedDatabase {
  _$BaseDatos(QueryExecutor e) : super(e);
  $BaseDatosManager get managers => $BaseDatosManager(this);
  late final $NinosTable ninos = $NinosTable(this);
  late final $ConsentimientosTable consentimientos = $ConsentimientosTable(
    this,
  );
  late final $SesionesTable sesiones = $SesionesTable(this);
  late final $RespuestasTable respuestas = $RespuestasTable(this);
  late final $ResultadosTable resultados = $ResultadosTable(this);
  late final $FotosTable fotos = $FotosTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    ninos,
    consentimientos,
    sesiones,
    respuestas,
    resultados,
    fotos,
  ];
}

typedef $$NinosTableCreateCompanionBuilder = NinosCompanion Function({
  Value<int> id,
  required String codigo,
  required DateTime fechaNacimiento,
  required String tramo,
  required DateTime creadoEn,
});
typedef $$NinosTableUpdateCompanionBuilder = NinosCompanion Function({
  Value<int> id,
  Value<String> codigo,
  Value<DateTime> fechaNacimiento,
  Value<String> tramo,
  Value<DateTime> creadoEn,
});

final class $$NinosTableReferences
    extends BaseReferences<_$BaseDatos, $NinosTable, Nino> {
  $$NinosTableReferences(super.$_db, super.$_table, super.$_typedResult);

  static MultiTypedResultKey<$SesionesTable, List<Sesion>> _sesionesRefsTable(
    _$BaseDatos db,
  ) => MultiTypedResultKey.fromTable(
    db.sesiones,
    aliasName: 'ninos__id__sesiones__nino_id',
  );

  $$SesionesTableProcessedTableManager get sesionesRefs {
    final manager = $$SesionesTableTableManager(
      $_db,
      $_db.sesiones,
    ).filter((f) => f.ninoId.id.sqlEquals($_itemColumn<int>('id')!));

    final cache = $_typedResult.readTableOrNull(_sesionesRefsTable($_db));
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: cache),
    );
  }

  static MultiTypedResultKey<$FotosTable, List<Foto>> _fotosRefsTable(
    _$BaseDatos db,
  ) => MultiTypedResultKey.fromTable(
    db.fotos,
    aliasName: 'ninos__id__fotos__nino_id',
  );

  $$FotosTableProcessedTableManager get fotosRefs {
    final manager = $$FotosTableTableManager(
      $_db,
      $_db.fotos,
    ).filter((f) => f.ninoId.id.sqlEquals($_itemColumn<int>('id')!));

    final cache = $_typedResult.readTableOrNull(_fotosRefsTable($_db));
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: cache),
    );
  }
}

class $$NinosTableFilterComposer extends Composer<_$BaseDatos, $NinosTable> {
  $$NinosTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get fechaNacimiento => $composableBuilder(
    column: $table.fechaNacimiento,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get tramo => $composableBuilder(
    column: $table.tramo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnFilters(column),
  );

  Expression<bool> sesionesRefs(
    Expression<bool> Function($$SesionesTableFilterComposer f) f,
  ) {
    final $$SesionesTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.ninoId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableFilterComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }

  Expression<bool> fotosRefs(
    Expression<bool> Function($$FotosTableFilterComposer f) f,
  ) {
    final $$FotosTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.fotos,
      getReferencedColumn: (t) => t.ninoId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$FotosTableFilterComposer(
            $db: $db,
            $table: $db.fotos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }
}

class $$NinosTableOrderingComposer extends Composer<_$BaseDatos, $NinosTable> {
  $$NinosTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get codigo => $composableBuilder(
    column: $table.codigo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get fechaNacimiento => $composableBuilder(
    column: $table.fechaNacimiento,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tramo => $composableBuilder(
    column: $table.tramo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$NinosTableAnnotationComposer
    extends Composer<_$BaseDatos, $NinosTable> {
  $$NinosTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get codigo =>
      $composableBuilder(column: $table.codigo, builder: (column) => column);

  GeneratedColumn<DateTime> get fechaNacimiento => $composableBuilder(
    column: $table.fechaNacimiento,
    builder: (column) => column,
  );

  GeneratedColumn<String> get tramo =>
      $composableBuilder(column: $table.tramo, builder: (column) => column);

  GeneratedColumn<DateTime> get creadoEn =>
      $composableBuilder(column: $table.creadoEn, builder: (column) => column);

  Expression<T> sesionesRefs<T extends Object>(
    Expression<T> Function($$SesionesTableAnnotationComposer a) f,
  ) {
    final $$SesionesTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.ninoId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableAnnotationComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }

  Expression<T> fotosRefs<T extends Object>(
    Expression<T> Function($$FotosTableAnnotationComposer a) f,
  ) {
    final $$FotosTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.fotos,
      getReferencedColumn: (t) => t.ninoId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$FotosTableAnnotationComposer(
            $db: $db,
            $table: $db.fotos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }
}

class $$NinosTableTableManager
    extends
        RootTableManager<
          _$BaseDatos,
          $NinosTable,
          Nino,
          $$NinosTableFilterComposer,
          $$NinosTableOrderingComposer,
          $$NinosTableAnnotationComposer,
          $$NinosTableCreateCompanionBuilder,
          $$NinosTableUpdateCompanionBuilder,
          (Nino, $$NinosTableReferences),
          Nino,
          PrefetchHooks Function({bool sesionesRefs, bool fotosRefs})
        > {
  $$NinosTableTableManager(_$BaseDatos db, $NinosTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$NinosTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$NinosTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$NinosTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> codigo = const Value.absent(),
                Value<DateTime> fechaNacimiento = const Value.absent(),
                Value<String> tramo = const Value.absent(),
                Value<DateTime> creadoEn = const Value.absent(),
              }) => NinosCompanion(
                id: id,
                codigo: codigo,
                fechaNacimiento: fechaNacimiento,
                tramo: tramo,
                creadoEn: creadoEn,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String codigo,
                required DateTime fechaNacimiento,
                required String tramo,
                required DateTime creadoEn,
              }) => NinosCompanion.insert(
                id: id,
                codigo: codigo,
                fechaNacimiento: fechaNacimiento,
                tramo: tramo,
                creadoEn: creadoEn,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$NinosTable, Nino>(table),
                  $$NinosTableReferences(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: ({sesionesRefs = false, fotosRefs = false}) {
            return PrefetchHooks(
              db: db,
              explicitlyWatchedTables: [
                if (sesionesRefs) db.sesiones,
                if (fotosRefs) db.fotos,
              ],
              addJoins: null,
              getPrefetchedDataCallback: (items) async {
                return [
                  if (sesionesRefs)
                    await $_getPrefetchedDataByColumns<
                      Nino,
                      $NinosTable,
                      Sesion,
                      $SesionesTable
                    >(
                      currentTable: table,
                      referencedTable: $$NinosTableReferences
                          ._sesionesRefsTable(db),
                      managerFromTypedResult: (p0) =>
                          $$NinosTableReferences(db, table, p0).sesionesRefs,
                      currentColumn: 'id',
                      referencedColumn: 'nino_id',
                      typedResults: items,
                    ),
                  if (fotosRefs)
                    await $_getPrefetchedDataByColumns<
                      Nino,
                      $NinosTable,
                      Foto,
                      $FotosTable
                    >(
                      currentTable: table,
                      referencedTable: $$NinosTableReferences._fotosRefsTable(
                        db,
                      ),
                      managerFromTypedResult: (p0) =>
                          $$NinosTableReferences(db, table, p0).fotosRefs,
                      currentColumn: 'id',
                      referencedColumn: 'nino_id',
                      typedResults: items,
                    ),
                ];
              },
            );
          },
        ),
      );
}

typedef $$NinosTableProcessedTableManager =
    ProcessedTableManager<
      _$BaseDatos,
      $NinosTable,
      Nino,
      $$NinosTableFilterComposer,
      $$NinosTableOrderingComposer,
      $$NinosTableAnnotationComposer,
      $$NinosTableCreateCompanionBuilder,
      $$NinosTableUpdateCompanionBuilder,
      (Nino, $$NinosTableReferences),
      Nino,
      PrefetchHooks Function({bool sesionesRefs, bool fotosRefs})
    >;
typedef $$ConsentimientosTableCreateCompanionBuilder =
    ConsentimientosCompanion Function({
      Value<int> id,
      required String versionTexto,
      required DateTime aceptadoEn,
    });
typedef $$ConsentimientosTableUpdateCompanionBuilder =
    ConsentimientosCompanion Function({
      Value<int> id,
      Value<String> versionTexto,
      Value<DateTime> aceptadoEn,
    });

class $$ConsentimientosTableFilterComposer
    extends Composer<_$BaseDatos, $ConsentimientosTable> {
  $$ConsentimientosTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get versionTexto => $composableBuilder(
    column: $table.versionTexto,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get aceptadoEn => $composableBuilder(
    column: $table.aceptadoEn,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ConsentimientosTableOrderingComposer
    extends Composer<_$BaseDatos, $ConsentimientosTable> {
  $$ConsentimientosTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get versionTexto => $composableBuilder(
    column: $table.versionTexto,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get aceptadoEn => $composableBuilder(
    column: $table.aceptadoEn,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ConsentimientosTableAnnotationComposer
    extends Composer<_$BaseDatos, $ConsentimientosTable> {
  $$ConsentimientosTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get versionTexto => $composableBuilder(
    column: $table.versionTexto,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get aceptadoEn => $composableBuilder(
    column: $table.aceptadoEn,
    builder: (column) => column,
  );
}

class $$ConsentimientosTableTableManager
    extends
        RootTableManager<
          _$BaseDatos,
          $ConsentimientosTable,
          Consentimiento,
          $$ConsentimientosTableFilterComposer,
          $$ConsentimientosTableOrderingComposer,
          $$ConsentimientosTableAnnotationComposer,
          $$ConsentimientosTableCreateCompanionBuilder,
          $$ConsentimientosTableUpdateCompanionBuilder,
          (
            Consentimiento,
            BaseReferences<_$BaseDatos, $ConsentimientosTable, Consentimiento>,
          ),
          Consentimiento,
          PrefetchHooks Function()
        > {
  $$ConsentimientosTableTableManager(
    _$BaseDatos db,
    $ConsentimientosTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ConsentimientosTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ConsentimientosTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ConsentimientosTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<String> versionTexto = const Value.absent(),
                Value<DateTime> aceptadoEn = const Value.absent(),
              }) => ConsentimientosCompanion(
                id: id,
                versionTexto: versionTexto,
                aceptadoEn: aceptadoEn,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required String versionTexto,
                required DateTime aceptadoEn,
              }) => ConsentimientosCompanion.insert(
                id: id,
                versionTexto: versionTexto,
                aceptadoEn: aceptadoEn,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$ConsentimientosTable, Consentimiento>(table),
                  BaseReferences<
                    _$BaseDatos,
                    $ConsentimientosTable,
                    Consentimiento
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ConsentimientosTableProcessedTableManager =
    ProcessedTableManager<
      _$BaseDatos,
      $ConsentimientosTable,
      Consentimiento,
      $$ConsentimientosTableFilterComposer,
      $$ConsentimientosTableOrderingComposer,
      $$ConsentimientosTableAnnotationComposer,
      $$ConsentimientosTableCreateCompanionBuilder,
      $$ConsentimientosTableUpdateCompanionBuilder,
      (
        Consentimiento,
        BaseReferences<_$BaseDatos, $ConsentimientosTable, Consentimiento>,
      ),
      Consentimiento,
      PrefetchHooks Function()
    >;
typedef $$SesionesTableCreateCompanionBuilder = SesionesCompanion Function({
  Value<int> id,
  required int ninoId,
  required String tramo,
  required int edadMeses,
  required String versionProtocolo,
  required DateTime iniciadaEn,
  Value<DateTime?> cerradaEn,
  Value<String> focosMarcados,
});
typedef $$SesionesTableUpdateCompanionBuilder = SesionesCompanion Function({
  Value<int> id,
  Value<int> ninoId,
  Value<String> tramo,
  Value<int> edadMeses,
  Value<String> versionProtocolo,
  Value<DateTime> iniciadaEn,
  Value<DateTime?> cerradaEn,
  Value<String> focosMarcados,
});

final class $$SesionesTableReferences
    extends BaseReferences<_$BaseDatos, $SesionesTable, Sesion> {
  $$SesionesTableReferences(super.$_db, super.$_table, super.$_typedResult);

  static $NinosTable _ninoIdTable(_$BaseDatos db) =>
      db.ninos.createAlias('sesiones__nino_id__ninos__id');

  $$NinosTableProcessedTableManager get ninoId {
    final $_column = $_itemColumn<int>('nino_id')!;

    final manager = $$NinosTableTableManager(
      $_db,
      $_db.ninos,
    ).filter((f) => f.id.sqlEquals($_column));
    final item = $_typedResult.readTableOrNull(_ninoIdTable($_db));
    if (item == null) return manager;
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: [item]),
    );
  }

  static MultiTypedResultKey<$RespuestasTable, List<Respuesta>>
  _respuestasRefsTable(_$BaseDatos db) => MultiTypedResultKey.fromTable(
    db.respuestas,
    aliasName: 'sesiones__id__respuestas__sesion_id',
  );

  $$RespuestasTableProcessedTableManager get respuestasRefs {
    final manager = $$RespuestasTableTableManager(
      $_db,
      $_db.respuestas,
    ).filter((f) => f.sesionId.id.sqlEquals($_itemColumn<int>('id')!));

    final cache = $_typedResult.readTableOrNull(_respuestasRefsTable($_db));
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: cache),
    );
  }

  static MultiTypedResultKey<$ResultadosTable, List<Resultado>>
  _resultadosRefsTable(_$BaseDatos db) => MultiTypedResultKey.fromTable(
    db.resultados,
    aliasName: 'sesiones__id__resultados__sesion_id',
  );

  $$ResultadosTableProcessedTableManager get resultadosRefs {
    final manager = $$ResultadosTableTableManager(
      $_db,
      $_db.resultados,
    ).filter((f) => f.sesionId.id.sqlEquals($_itemColumn<int>('id')!));

    final cache = $_typedResult.readTableOrNull(_resultadosRefsTable($_db));
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: cache),
    );
  }
}

class $$SesionesTableFilterComposer
    extends Composer<_$BaseDatos, $SesionesTable> {
  $$SesionesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get tramo => $composableBuilder(
    column: $table.tramo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get edadMeses => $composableBuilder(
    column: $table.edadMeses,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get versionProtocolo => $composableBuilder(
    column: $table.versionProtocolo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get iniciadaEn => $composableBuilder(
    column: $table.iniciadaEn,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get cerradaEn => $composableBuilder(
    column: $table.cerradaEn,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get focosMarcados => $composableBuilder(
    column: $table.focosMarcados,
    builder: (column) => ColumnFilters(column),
  );

  $$NinosTableFilterComposer get ninoId {
    final $$NinosTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.ninoId,
      referencedTable: $db.ninos,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$NinosTableFilterComposer(
            $db: $db,
            $table: $db.ninos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }

  Expression<bool> respuestasRefs(
    Expression<bool> Function($$RespuestasTableFilterComposer f) f,
  ) {
    final $$RespuestasTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.respuestas,
      getReferencedColumn: (t) => t.sesionId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$RespuestasTableFilterComposer(
            $db: $db,
            $table: $db.respuestas,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }

  Expression<bool> resultadosRefs(
    Expression<bool> Function($$ResultadosTableFilterComposer f) f,
  ) {
    final $$ResultadosTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.resultados,
      getReferencedColumn: (t) => t.sesionId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$ResultadosTableFilterComposer(
            $db: $db,
            $table: $db.resultados,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }
}

class $$SesionesTableOrderingComposer
    extends Composer<_$BaseDatos, $SesionesTable> {
  $$SesionesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tramo => $composableBuilder(
    column: $table.tramo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get edadMeses => $composableBuilder(
    column: $table.edadMeses,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get versionProtocolo => $composableBuilder(
    column: $table.versionProtocolo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get iniciadaEn => $composableBuilder(
    column: $table.iniciadaEn,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get cerradaEn => $composableBuilder(
    column: $table.cerradaEn,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get focosMarcados => $composableBuilder(
    column: $table.focosMarcados,
    builder: (column) => ColumnOrderings(column),
  );

  $$NinosTableOrderingComposer get ninoId {
    final $$NinosTableOrderingComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.ninoId,
      referencedTable: $db.ninos,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$NinosTableOrderingComposer(
            $db: $db,
            $table: $db.ninos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$SesionesTableAnnotationComposer
    extends Composer<_$BaseDatos, $SesionesTable> {
  $$SesionesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get tramo =>
      $composableBuilder(column: $table.tramo, builder: (column) => column);

  GeneratedColumn<int> get edadMeses =>
      $composableBuilder(column: $table.edadMeses, builder: (column) => column);

  GeneratedColumn<String> get versionProtocolo => $composableBuilder(
    column: $table.versionProtocolo,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get iniciadaEn => $composableBuilder(
    column: $table.iniciadaEn,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get cerradaEn =>
      $composableBuilder(column: $table.cerradaEn, builder: (column) => column);

  GeneratedColumn<String> get focosMarcados => $composableBuilder(
    column: $table.focosMarcados,
    builder: (column) => column,
  );

  $$NinosTableAnnotationComposer get ninoId {
    final $$NinosTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.ninoId,
      referencedTable: $db.ninos,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$NinosTableAnnotationComposer(
            $db: $db,
            $table: $db.ninos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }

  Expression<T> respuestasRefs<T extends Object>(
    Expression<T> Function($$RespuestasTableAnnotationComposer a) f,
  ) {
    final $$RespuestasTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.respuestas,
      getReferencedColumn: (t) => t.sesionId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$RespuestasTableAnnotationComposer(
            $db: $db,
            $table: $db.respuestas,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }

  Expression<T> resultadosRefs<T extends Object>(
    Expression<T> Function($$ResultadosTableAnnotationComposer a) f,
  ) {
    final $$ResultadosTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.id,
      referencedTable: $db.resultados,
      getReferencedColumn: (t) => t.sesionId,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$ResultadosTableAnnotationComposer(
            $db: $db,
            $table: $db.resultados,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return f(composer);
  }
}

class $$SesionesTableTableManager
    extends
        RootTableManager<
          _$BaseDatos,
          $SesionesTable,
          Sesion,
          $$SesionesTableFilterComposer,
          $$SesionesTableOrderingComposer,
          $$SesionesTableAnnotationComposer,
          $$SesionesTableCreateCompanionBuilder,
          $$SesionesTableUpdateCompanionBuilder,
          (Sesion, $$SesionesTableReferences),
          Sesion,
          PrefetchHooks Function({
            bool ninoId,
            bool respuestasRefs,
            bool resultadosRefs,
          })
        > {
  $$SesionesTableTableManager(_$BaseDatos db, $SesionesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SesionesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SesionesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SesionesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int> ninoId = const Value.absent(),
                Value<String> tramo = const Value.absent(),
                Value<int> edadMeses = const Value.absent(),
                Value<String> versionProtocolo = const Value.absent(),
                Value<DateTime> iniciadaEn = const Value.absent(),
                Value<DateTime?> cerradaEn = const Value.absent(),
                Value<String> focosMarcados = const Value.absent(),
              }) => SesionesCompanion(
                id: id,
                ninoId: ninoId,
                tramo: tramo,
                edadMeses: edadMeses,
                versionProtocolo: versionProtocolo,
                iniciadaEn: iniciadaEn,
                cerradaEn: cerradaEn,
                focosMarcados: focosMarcados,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required int ninoId,
                required String tramo,
                required int edadMeses,
                required String versionProtocolo,
                required DateTime iniciadaEn,
                Value<DateTime?> cerradaEn = const Value.absent(),
                Value<String> focosMarcados = const Value.absent(),
              }) => SesionesCompanion.insert(
                id: id,
                ninoId: ninoId,
                tramo: tramo,
                edadMeses: edadMeses,
                versionProtocolo: versionProtocolo,
                iniciadaEn: iniciadaEn,
                cerradaEn: cerradaEn,
                focosMarcados: focosMarcados,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SesionesTable, Sesion>(table),
                  $$SesionesTableReferences(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback:
              ({
                ninoId = false,
                respuestasRefs = false,
                resultadosRefs = false,
              }) {
                return PrefetchHooks(
                  db: db,
                  explicitlyWatchedTables: [
                    if (respuestasRefs) db.respuestas,
                    if (resultadosRefs) db.resultados,
                  ],
                  addJoins:
                      <
                        T extends TableManagerState<
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic,
                          dynamic
                        >
                      >(state) {
                        if (ninoId) {
                          state = state.withJoin(
                            currentTable: table,
                            currentColumn: table.ninoId,
                            referencedTable: $$SesionesTableReferences
                                ._ninoIdTable(db),
                            referencedColumn: $$SesionesTableReferences
                                ._ninoIdTable(db)
                                .id,
                          ) as T;
                        }

                        return state;
                      },
                  getPrefetchedDataCallback: (items) async {
                    return [
                      if (respuestasRefs)
                        await $_getPrefetchedDataByColumns<
                          Sesion,
                          $SesionesTable,
                          Respuesta,
                          $RespuestasTable
                        >(
                          currentTable: table,
                          referencedTable: $$SesionesTableReferences
                              ._respuestasRefsTable(db),
                          managerFromTypedResult: (p0) =>
                              $$SesionesTableReferences(
                                db,
                                table,
                                p0,
                              ).respuestasRefs,
                          currentColumn: 'id',
                          referencedColumn: 'sesion_id',
                          typedResults: items,
                        ),
                      if (resultadosRefs)
                        await $_getPrefetchedDataByColumns<
                          Sesion,
                          $SesionesTable,
                          Resultado,
                          $ResultadosTable
                        >(
                          currentTable: table,
                          referencedTable: $$SesionesTableReferences
                              ._resultadosRefsTable(db),
                          managerFromTypedResult: (p0) =>
                              $$SesionesTableReferences(
                                db,
                                table,
                                p0,
                              ).resultadosRefs,
                          currentColumn: 'id',
                          referencedColumn: 'sesion_id',
                          typedResults: items,
                        ),
                    ];
                  },
                );
              },
        ),
      );
}

typedef $$SesionesTableProcessedTableManager =
    ProcessedTableManager<
      _$BaseDatos,
      $SesionesTable,
      Sesion,
      $$SesionesTableFilterComposer,
      $$SesionesTableOrderingComposer,
      $$SesionesTableAnnotationComposer,
      $$SesionesTableCreateCompanionBuilder,
      $$SesionesTableUpdateCompanionBuilder,
      (Sesion, $$SesionesTableReferences),
      Sesion,
      PrefetchHooks Function({
        bool ninoId,
        bool respuestasRefs,
        bool resultadosRefs,
      })
    >;
typedef $$RespuestasTableCreateCompanionBuilder = RespuestasCompanion Function({
  Value<int> id,
  required int sesionId,
  required String itemId,
  required String opcion,
  Value<int?> puntos,
});
typedef $$RespuestasTableUpdateCompanionBuilder = RespuestasCompanion Function({
  Value<int> id,
  Value<int> sesionId,
  Value<String> itemId,
  Value<String> opcion,
  Value<int?> puntos,
});

final class $$RespuestasTableReferences
    extends BaseReferences<_$BaseDatos, $RespuestasTable, Respuesta> {
  $$RespuestasTableReferences(super.$_db, super.$_table, super.$_typedResult);

  static $SesionesTable _sesionIdTable(_$BaseDatos db) =>
      db.sesiones.createAlias('respuestas__sesion_id__sesiones__id');

  $$SesionesTableProcessedTableManager get sesionId {
    final $_column = $_itemColumn<int>('sesion_id')!;

    final manager = $$SesionesTableTableManager(
      $_db,
      $_db.sesiones,
    ).filter((f) => f.id.sqlEquals($_column));
    final item = $_typedResult.readTableOrNull(_sesionIdTable($_db));
    if (item == null) return manager;
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: [item]),
    );
  }
}

class $$RespuestasTableFilterComposer
    extends Composer<_$BaseDatos, $RespuestasTable> {
  $$RespuestasTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get itemId => $composableBuilder(
    column: $table.itemId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get opcion => $composableBuilder(
    column: $table.opcion,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get puntos => $composableBuilder(
    column: $table.puntos,
    builder: (column) => ColumnFilters(column),
  );

  $$SesionesTableFilterComposer get sesionId {
    final $$SesionesTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.sesionId,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableFilterComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$RespuestasTableOrderingComposer
    extends Composer<_$BaseDatos, $RespuestasTable> {
  $$RespuestasTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get itemId => $composableBuilder(
    column: $table.itemId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get opcion => $composableBuilder(
    column: $table.opcion,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get puntos => $composableBuilder(
    column: $table.puntos,
    builder: (column) => ColumnOrderings(column),
  );

  $$SesionesTableOrderingComposer get sesionId {
    final $$SesionesTableOrderingComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.sesionId,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableOrderingComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$RespuestasTableAnnotationComposer
    extends Composer<_$BaseDatos, $RespuestasTable> {
  $$RespuestasTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get itemId =>
      $composableBuilder(column: $table.itemId, builder: (column) => column);

  GeneratedColumn<String> get opcion =>
      $composableBuilder(column: $table.opcion, builder: (column) => column);

  GeneratedColumn<int> get puntos =>
      $composableBuilder(column: $table.puntos, builder: (column) => column);

  $$SesionesTableAnnotationComposer get sesionId {
    final $$SesionesTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.sesionId,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableAnnotationComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$RespuestasTableTableManager
    extends
        RootTableManager<
          _$BaseDatos,
          $RespuestasTable,
          Respuesta,
          $$RespuestasTableFilterComposer,
          $$RespuestasTableOrderingComposer,
          $$RespuestasTableAnnotationComposer,
          $$RespuestasTableCreateCompanionBuilder,
          $$RespuestasTableUpdateCompanionBuilder,
          (Respuesta, $$RespuestasTableReferences),
          Respuesta,
          PrefetchHooks Function({bool sesionId})
        > {
  $$RespuestasTableTableManager(_$BaseDatos db, $RespuestasTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$RespuestasTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$RespuestasTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$RespuestasTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int> sesionId = const Value.absent(),
                Value<String> itemId = const Value.absent(),
                Value<String> opcion = const Value.absent(),
                Value<int?> puntos = const Value.absent(),
              }) => RespuestasCompanion(
                id: id,
                sesionId: sesionId,
                itemId: itemId,
                opcion: opcion,
                puntos: puntos,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required int sesionId,
                required String itemId,
                required String opcion,
                Value<int?> puntos = const Value.absent(),
              }) => RespuestasCompanion.insert(
                id: id,
                sesionId: sesionId,
                itemId: itemId,
                opcion: opcion,
                puntos: puntos,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$RespuestasTable, Respuesta>(table),
                  $$RespuestasTableReferences(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: ({sesionId = false}) {
            return PrefetchHooks(
              db: db,
              explicitlyWatchedTables: [],
              addJoins:
                  <
                    T extends TableManagerState<
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic
                    >
                  >(state) {
                    if (sesionId) {
                      state = state.withJoin(
                        currentTable: table,
                        currentColumn: table.sesionId,
                        referencedTable: $$RespuestasTableReferences
                            ._sesionIdTable(db),
                        referencedColumn: $$RespuestasTableReferences
                            ._sesionIdTable(db)
                            .id,
                      ) as T;
                    }

                    return state;
                  },
              getPrefetchedDataCallback: (items) async {
                return [];
              },
            );
          },
        ),
      );
}

typedef $$RespuestasTableProcessedTableManager =
    ProcessedTableManager<
      _$BaseDatos,
      $RespuestasTable,
      Respuesta,
      $$RespuestasTableFilterComposer,
      $$RespuestasTableOrderingComposer,
      $$RespuestasTableAnnotationComposer,
      $$RespuestasTableCreateCompanionBuilder,
      $$RespuestasTableUpdateCompanionBuilder,
      (Respuesta, $$RespuestasTableReferences),
      Respuesta,
      PrefetchHooks Function({bool sesionId})
    >;
typedef $$ResultadosTableCreateCompanionBuilder = ResultadosCompanion Function({
  Value<int> id,
  required int sesionId,
  required String puntajesPorArea,
  required int puntosTotal,
  required int maximoTotal,
  required int noSe,
  required String nivel,
  Value<String> focosRojos,
  required String versionProtocolo,
  required String estadoProtocolo,
  required DateTime creadoEn,
});
typedef $$ResultadosTableUpdateCompanionBuilder = ResultadosCompanion Function({
  Value<int> id,
  Value<int> sesionId,
  Value<String> puntajesPorArea,
  Value<int> puntosTotal,
  Value<int> maximoTotal,
  Value<int> noSe,
  Value<String> nivel,
  Value<String> focosRojos,
  Value<String> versionProtocolo,
  Value<String> estadoProtocolo,
  Value<DateTime> creadoEn,
});

final class $$ResultadosTableReferences
    extends BaseReferences<_$BaseDatos, $ResultadosTable, Resultado> {
  $$ResultadosTableReferences(super.$_db, super.$_table, super.$_typedResult);

  static $SesionesTable _sesionIdTable(_$BaseDatos db) =>
      db.sesiones.createAlias('resultados__sesion_id__sesiones__id');

  $$SesionesTableProcessedTableManager get sesionId {
    final $_column = $_itemColumn<int>('sesion_id')!;

    final manager = $$SesionesTableTableManager(
      $_db,
      $_db.sesiones,
    ).filter((f) => f.id.sqlEquals($_column));
    final item = $_typedResult.readTableOrNull(_sesionIdTable($_db));
    if (item == null) return manager;
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: [item]),
    );
  }
}

class $$ResultadosTableFilterComposer
    extends Composer<_$BaseDatos, $ResultadosTable> {
  $$ResultadosTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get puntajesPorArea => $composableBuilder(
    column: $table.puntajesPorArea,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get puntosTotal => $composableBuilder(
    column: $table.puntosTotal,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get maximoTotal => $composableBuilder(
    column: $table.maximoTotal,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get noSe => $composableBuilder(
    column: $table.noSe,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nivel => $composableBuilder(
    column: $table.nivel,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get focosRojos => $composableBuilder(
    column: $table.focosRojos,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get versionProtocolo => $composableBuilder(
    column: $table.versionProtocolo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get estadoProtocolo => $composableBuilder(
    column: $table.estadoProtocolo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnFilters(column),
  );

  $$SesionesTableFilterComposer get sesionId {
    final $$SesionesTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.sesionId,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableFilterComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$ResultadosTableOrderingComposer
    extends Composer<_$BaseDatos, $ResultadosTable> {
  $$ResultadosTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get puntajesPorArea => $composableBuilder(
    column: $table.puntajesPorArea,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get puntosTotal => $composableBuilder(
    column: $table.puntosTotal,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get maximoTotal => $composableBuilder(
    column: $table.maximoTotal,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get noSe => $composableBuilder(
    column: $table.noSe,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nivel => $composableBuilder(
    column: $table.nivel,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get focosRojos => $composableBuilder(
    column: $table.focosRojos,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get versionProtocolo => $composableBuilder(
    column: $table.versionProtocolo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get estadoProtocolo => $composableBuilder(
    column: $table.estadoProtocolo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get creadoEn => $composableBuilder(
    column: $table.creadoEn,
    builder: (column) => ColumnOrderings(column),
  );

  $$SesionesTableOrderingComposer get sesionId {
    final $$SesionesTableOrderingComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.sesionId,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableOrderingComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$ResultadosTableAnnotationComposer
    extends Composer<_$BaseDatos, $ResultadosTable> {
  $$ResultadosTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get puntajesPorArea => $composableBuilder(
    column: $table.puntajesPorArea,
    builder: (column) => column,
  );

  GeneratedColumn<int> get puntosTotal => $composableBuilder(
    column: $table.puntosTotal,
    builder: (column) => column,
  );

  GeneratedColumn<int> get maximoTotal => $composableBuilder(
    column: $table.maximoTotal,
    builder: (column) => column,
  );

  GeneratedColumn<int> get noSe =>
      $composableBuilder(column: $table.noSe, builder: (column) => column);

  GeneratedColumn<String> get nivel =>
      $composableBuilder(column: $table.nivel, builder: (column) => column);

  GeneratedColumn<String> get focosRojos => $composableBuilder(
    column: $table.focosRojos,
    builder: (column) => column,
  );

  GeneratedColumn<String> get versionProtocolo => $composableBuilder(
    column: $table.versionProtocolo,
    builder: (column) => column,
  );

  GeneratedColumn<String> get estadoProtocolo => $composableBuilder(
    column: $table.estadoProtocolo,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get creadoEn =>
      $composableBuilder(column: $table.creadoEn, builder: (column) => column);

  $$SesionesTableAnnotationComposer get sesionId {
    final $$SesionesTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.sesionId,
      referencedTable: $db.sesiones,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$SesionesTableAnnotationComposer(
            $db: $db,
            $table: $db.sesiones,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$ResultadosTableTableManager
    extends
        RootTableManager<
          _$BaseDatos,
          $ResultadosTable,
          Resultado,
          $$ResultadosTableFilterComposer,
          $$ResultadosTableOrderingComposer,
          $$ResultadosTableAnnotationComposer,
          $$ResultadosTableCreateCompanionBuilder,
          $$ResultadosTableUpdateCompanionBuilder,
          (Resultado, $$ResultadosTableReferences),
          Resultado,
          PrefetchHooks Function({bool sesionId})
        > {
  $$ResultadosTableTableManager(_$BaseDatos db, $ResultadosTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ResultadosTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ResultadosTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ResultadosTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int> sesionId = const Value.absent(),
                Value<String> puntajesPorArea = const Value.absent(),
                Value<int> puntosTotal = const Value.absent(),
                Value<int> maximoTotal = const Value.absent(),
                Value<int> noSe = const Value.absent(),
                Value<String> nivel = const Value.absent(),
                Value<String> focosRojos = const Value.absent(),
                Value<String> versionProtocolo = const Value.absent(),
                Value<String> estadoProtocolo = const Value.absent(),
                Value<DateTime> creadoEn = const Value.absent(),
              }) => ResultadosCompanion(
                id: id,
                sesionId: sesionId,
                puntajesPorArea: puntajesPorArea,
                puntosTotal: puntosTotal,
                maximoTotal: maximoTotal,
                noSe: noSe,
                nivel: nivel,
                focosRojos: focosRojos,
                versionProtocolo: versionProtocolo,
                estadoProtocolo: estadoProtocolo,
                creadoEn: creadoEn,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required int sesionId,
                required String puntajesPorArea,
                required int puntosTotal,
                required int maximoTotal,
                required int noSe,
                required String nivel,
                Value<String> focosRojos = const Value.absent(),
                required String versionProtocolo,
                required String estadoProtocolo,
                required DateTime creadoEn,
              }) => ResultadosCompanion.insert(
                id: id,
                sesionId: sesionId,
                puntajesPorArea: puntajesPorArea,
                puntosTotal: puntosTotal,
                maximoTotal: maximoTotal,
                noSe: noSe,
                nivel: nivel,
                focosRojos: focosRojos,
                versionProtocolo: versionProtocolo,
                estadoProtocolo: estadoProtocolo,
                creadoEn: creadoEn,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$ResultadosTable, Resultado>(table),
                  $$ResultadosTableReferences(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: ({sesionId = false}) {
            return PrefetchHooks(
              db: db,
              explicitlyWatchedTables: [],
              addJoins:
                  <
                    T extends TableManagerState<
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic
                    >
                  >(state) {
                    if (sesionId) {
                      state = state.withJoin(
                        currentTable: table,
                        currentColumn: table.sesionId,
                        referencedTable: $$ResultadosTableReferences
                            ._sesionIdTable(db),
                        referencedColumn: $$ResultadosTableReferences
                            ._sesionIdTable(db)
                            .id,
                      ) as T;
                    }

                    return state;
                  },
              getPrefetchedDataCallback: (items) async {
                return [];
              },
            );
          },
        ),
      );
}

typedef $$ResultadosTableProcessedTableManager =
    ProcessedTableManager<
      _$BaseDatos,
      $ResultadosTable,
      Resultado,
      $$ResultadosTableFilterComposer,
      $$ResultadosTableOrderingComposer,
      $$ResultadosTableAnnotationComposer,
      $$ResultadosTableCreateCompanionBuilder,
      $$ResultadosTableUpdateCompanionBuilder,
      (Resultado, $$ResultadosTableReferences),
      Resultado,
      PrefetchHooks Function({bool sesionId})
    >;
typedef $$FotosTableCreateCompanionBuilder = FotosCompanion Function({
  Value<int> id,
  required int ninoId,
  required String ruta,
  required DateTime fecha,
  Value<String> nota,
});
typedef $$FotosTableUpdateCompanionBuilder = FotosCompanion Function({
  Value<int> id,
  Value<int> ninoId,
  Value<String> ruta,
  Value<DateTime> fecha,
  Value<String> nota,
});

final class $$FotosTableReferences
    extends BaseReferences<_$BaseDatos, $FotosTable, Foto> {
  $$FotosTableReferences(super.$_db, super.$_table, super.$_typedResult);

  static $NinosTable _ninoIdTable(_$BaseDatos db) =>
      db.ninos.createAlias('fotos__nino_id__ninos__id');

  $$NinosTableProcessedTableManager get ninoId {
    final $_column = $_itemColumn<int>('nino_id')!;

    final manager = $$NinosTableTableManager(
      $_db,
      $_db.ninos,
    ).filter((f) => f.id.sqlEquals($_column));
    final item = $_typedResult.readTableOrNull(_ninoIdTable($_db));
    if (item == null) return manager;
    return ProcessedTableManager(
      manager.$state.copyWith(prefetchedData: [item]),
    );
  }
}

class $$FotosTableFilterComposer extends Composer<_$BaseDatos, $FotosTable> {
  $$FotosTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get ruta => $composableBuilder(
    column: $table.ruta,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get fecha => $composableBuilder(
    column: $table.fecha,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get nota => $composableBuilder(
    column: $table.nota,
    builder: (column) => ColumnFilters(column),
  );

  $$NinosTableFilterComposer get ninoId {
    final $$NinosTableFilterComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.ninoId,
      referencedTable: $db.ninos,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$NinosTableFilterComposer(
            $db: $db,
            $table: $db.ninos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$FotosTableOrderingComposer extends Composer<_$BaseDatos, $FotosTable> {
  $$FotosTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<int> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get ruta => $composableBuilder(
    column: $table.ruta,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get fecha => $composableBuilder(
    column: $table.fecha,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get nota => $composableBuilder(
    column: $table.nota,
    builder: (column) => ColumnOrderings(column),
  );

  $$NinosTableOrderingComposer get ninoId {
    final $$NinosTableOrderingComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.ninoId,
      referencedTable: $db.ninos,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$NinosTableOrderingComposer(
            $db: $db,
            $table: $db.ninos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$FotosTableAnnotationComposer
    extends Composer<_$BaseDatos, $FotosTable> {
  $$FotosTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<int> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get ruta =>
      $composableBuilder(column: $table.ruta, builder: (column) => column);

  GeneratedColumn<DateTime> get fecha =>
      $composableBuilder(column: $table.fecha, builder: (column) => column);

  GeneratedColumn<String> get nota =>
      $composableBuilder(column: $table.nota, builder: (column) => column);

  $$NinosTableAnnotationComposer get ninoId {
    final $$NinosTableAnnotationComposer composer = $composerBuilder(
      composer: this,
      getCurrentColumn: (t) => t.ninoId,
      referencedTable: $db.ninos,
      getReferencedColumn: (t) => t.id,
      builder:
          (
            joinBuilder, {
            $addJoinBuilderToRootComposer,
            $removeJoinBuilderFromRootComposer,
          }) => $$NinosTableAnnotationComposer(
            $db: $db,
            $table: $db.ninos,
            $addJoinBuilderToRootComposer: $addJoinBuilderToRootComposer,
            joinBuilder: joinBuilder,
            $removeJoinBuilderFromRootComposer:
                $removeJoinBuilderFromRootComposer,
          ),
    );
    return composer;
  }
}

class $$FotosTableTableManager
    extends
        RootTableManager<
          _$BaseDatos,
          $FotosTable,
          Foto,
          $$FotosTableFilterComposer,
          $$FotosTableOrderingComposer,
          $$FotosTableAnnotationComposer,
          $$FotosTableCreateCompanionBuilder,
          $$FotosTableUpdateCompanionBuilder,
          (Foto, $$FotosTableReferences),
          Foto,
          PrefetchHooks Function({bool ninoId})
        > {
  $$FotosTableTableManager(_$BaseDatos db, $FotosTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$FotosTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$FotosTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$FotosTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                Value<int> ninoId = const Value.absent(),
                Value<String> ruta = const Value.absent(),
                Value<DateTime> fecha = const Value.absent(),
                Value<String> nota = const Value.absent(),
              }) => FotosCompanion(
                id: id,
                ninoId: ninoId,
                ruta: ruta,
                fecha: fecha,
                nota: nota,
              ),
          createCompanionCallback:
              ({
                Value<int> id = const Value.absent(),
                required int ninoId,
                required String ruta,
                required DateTime fecha,
                Value<String> nota = const Value.absent(),
              }) => FotosCompanion.insert(
                id: id,
                ninoId: ninoId,
                ruta: ruta,
                fecha: fecha,
                nota: nota,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$FotosTable, Foto>(table),
                  $$FotosTableReferences(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: ({ninoId = false}) {
            return PrefetchHooks(
              db: db,
              explicitlyWatchedTables: [],
              addJoins:
                  <
                    T extends TableManagerState<
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic,
                      dynamic
                    >
                  >(state) {
                    if (ninoId) {
                      state = state.withJoin(
                        currentTable: table,
                        currentColumn: table.ninoId,
                        referencedTable: $$FotosTableReferences._ninoIdTable(
                          db,
                        ),
                        referencedColumn: $$FotosTableReferences
                            ._ninoIdTable(db)
                            .id,
                      ) as T;
                    }

                    return state;
                  },
              getPrefetchedDataCallback: (items) async {
                return [];
              },
            );
          },
        ),
      );
}

typedef $$FotosTableProcessedTableManager =
    ProcessedTableManager<
      _$BaseDatos,
      $FotosTable,
      Foto,
      $$FotosTableFilterComposer,
      $$FotosTableOrderingComposer,
      $$FotosTableAnnotationComposer,
      $$FotosTableCreateCompanionBuilder,
      $$FotosTableUpdateCompanionBuilder,
      (Foto, $$FotosTableReferences),
      Foto,
      PrefetchHooks Function({bool ninoId})
    >;

class $BaseDatosManager {
  final _$BaseDatos _db;
  $BaseDatosManager(this._db);
  $$NinosTableTableManager get ninos =>
      $$NinosTableTableManager(_db, _db.ninos);
  $$ConsentimientosTableTableManager get consentimientos =>
      $$ConsentimientosTableTableManager(_db, _db.consentimientos);
  $$SesionesTableTableManager get sesiones =>
      $$SesionesTableTableManager(_db, _db.sesiones);
  $$RespuestasTableTableManager get respuestas =>
      $$RespuestasTableTableManager(_db, _db.respuestas);
  $$ResultadosTableTableManager get resultados =>
      $$ResultadosTableTableManager(_db, _db.resultados);
  $$FotosTableTableManager get fotos =>
      $$FotosTableTableManager(_db, _db.fotos);
}
