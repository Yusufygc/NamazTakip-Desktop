// Mobil `PrayerTimeService.compute` davranışını (adhan_dart 2.0.1) tekrarlayıp golden vektör üretir.
//
// Kullanım (tools/golden_times klasöründe):
//   dart run bin/golden.dart <turkish_cities.dart yolu> <çıktı json yolu>
//
// Vakitler UTC epoch saniyesi olarak yazılır (saat diliminden bağımsız). Sıra:
// fajr, sunrise, dhuhr, asr, maghrib, isha. Güneş doğuşu mobil kuralıyla verilir
// (precision:true, -90 sn, saniye kesilir).
import 'dart:convert';
import 'dart:io';

import 'package:adhan_dart/adhan_dart.dart' as adhan;

const _dates = [
  '2026-01-01', '2026-02-28', '2026-03-21', '2026-05-10', '2026-06-21',
  '2026-08-01', '2026-09-23', '2026-10-26', '2026-12-21', '2028-02-29',
];

// Diyanet tüm illerde; diğer yöntemler bu şehirlerde.
const _otherMethodCities = ['İstanbul', 'Ankara', 'Antalya', 'Kars', 'Hakkâri'];
const _otherMethods = ['mwl', 'egyptian', 'karachi', 'ummalqura', 'isna'];

adhan.CalculationParameters _params(String key) {
  switch (key) {
    case 'diyanet':
      return adhan.CalculationMethodParameters.turkiye();
    case 'mwl':
      return adhan.CalculationMethodParameters.muslimWorldLeague();
    case 'egyptian':
      return adhan.CalculationMethodParameters.egyptian();
    case 'karachi':
      return adhan.CalculationMethodParameters.karachi();
    case 'ummalqura':
      return adhan.CalculationMethodParameters.ummAlQura();
    case 'isna':
      return adhan.CalculationMethodParameters.northAmerica();
  }
  throw ArgumentError(key);
}

int _epoch(DateTime t) => t.millisecondsSinceEpoch ~/ 1000;

List<int> _compute(double lat, double lon, DateTime day, String method) {
  final coords = adhan.Coordinates(lat, lon);
  final params = _params(method);
  final rounded = adhan.PrayerTimes(
      coordinates: coords, date: day, calculationParameters: params, precision: false);
  final precise = adhan.PrayerTimes(
      coordinates: coords, date: day, calculationParameters: params, precision: true);
  final cautious = precise.sunrise.toLocal().subtract(const Duration(seconds: 90));
  final sunrise = DateTime(cautious.year, cautious.month, cautious.day, cautious.hour, cautious.minute);
  return [
    _epoch(rounded.fajr.toLocal()),
    _epoch(sunrise),
    _epoch(rounded.dhuhr.toLocal()),
    _epoch(rounded.asr.toLocal()),
    _epoch(rounded.maghrib.toLocal()),
    _epoch(rounded.isha.toLocal()),
  ];
}

void main(List<String> args) {
  if (args.length != 2) {
    stderr.writeln('Kullanım: dart run bin/golden.dart <turkish_cities.dart> <çıktı.json>');
    exit(64);
  }
  final source = File(args[0]).readAsStringSync(encoding: utf8);
  final pattern = RegExp(
      r"latitude:\s*([\d.]+),\s*longitude:\s*([\d.]+),\s*city:\s*'([^']+)'");
  final cities = [
    for (final m in pattern.allMatches(source))
      {'city': m.group(3)!, 'lat': double.parse(m.group(1)!), 'lon': double.parse(m.group(2)!)},
  ];
  if (cities.length != 81) {
    stderr.writeln('81 il bekleniyordu, ${cities.length} bulundu.');
    exit(65);
  }

  final rows = <String>[];
  for (var ci = 0; ci < cities.length; ci++) {
    final city = cities[ci];
    final methods = ['diyanet', if (_otherMethodCities.contains(city['city'])) ..._otherMethods];
    for (final method in methods) {
      for (final ds in _dates) {
        final p = ds.split('-').map(int.parse).toList();
        final times = _compute(
            city['lat'] as double, city['lon'] as double, DateTime(p[0], p[1], p[2]), method);
        rows.add(jsonEncode({'c': ci, 'd': ds, 'm': method, 't': times}));
      }
    }
  }

  final meta = jsonEncode({
    'adhan_dart': '2.0.1',
    'kaynak': 'mobil turkish_cities.dart ve PrayerTimeService.compute',
    'aciklama': 't = UTC epoch saniyesi: fajr, sunrise(-90sn, kesilmis), dhuhr, asr, maghrib, isha',
  });
  final cityJson = jsonEncode(cities);
  File(args[1]).writeAsStringSync(
      '{"meta":$meta,\n"cities":$cityJson,\n"rows":[\n${rows.join(',\n')}\n]}\n',
      encoding: utf8);
  stdout.writeln('${rows.length} satır, ${cities.length} il yazıldı: ${args[1]}');
}
