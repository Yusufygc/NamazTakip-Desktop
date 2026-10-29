# Mobil Referans

Mobil uygulama bu projenin **ham kaynağıdır** (salt okunur, kopyalanmaz). Burada hangi şeyin nerede olduğu ve masaüstünde hangi sayfaya karşılık geldiği yazılır. Proje özeti: [[proje-ozeti]].

**Mobil kök:** `C:\2UYGULAMALAR\P008-NamazTakip-Mobil\prayer-tracker\` (aşağıdaki yollar buna göredir). Wiki girişi: `docs/wiki/index.md`.

## Kod dosyaları (spesifikasyon olarak okunur)

| Mobil dosya | Ne içerir | Bu wiki'de |
|---|---|---|
| `packages/namaz_backend/lib/src/domain/dates.dart` | `prayerDay`, `nextPrayer`, tarih yardımcıları | [[takip-gunu-ve-kaza]] |
| `packages/namaz_backend/lib/src/domain/prayer.dart` | `PrayerType`, `PrayerStatus`, `DayTimes`, `NextPrayer` | [[takip-gunu-ve-kaza]] |
| `packages/namaz_backend/lib/src/domain/prayer_time_service.dart` | `AppLocation`, `CalcMethod`, vakit hesabı, 90 sn güneş payı | [[vakit-hesabi]] |
| `packages/namaz_backend/lib/src/domain/models.dart` | `PrayerRecord`, `QazaItem`, `QazaDebtPlan`, `AppSettings` | [[takip-gunu-ve-kaza]] |
| `packages/namaz_backend/lib/src/data/app_database.dart` | Şema, açılış, bozuk dosya yedeği | [[veri-katmani]] |
| `packages/namaz_backend/lib/src/data/prayer_repository.dart` | İşaretleme, `qazaItems` | [[takip-gunu-ve-kaza]] |
| `packages/namaz_backend/lib/src/data/settings_repository.dart` | Ayar anahtarları, kaza borcu okuma/yazma | [[veri-katmani]] |
| `packages/namaz_backend/lib/src/data/turkish_cities.dart` | 81 il, koordinatlar | [[vakit-hesabi]], [[ekranlar]] |
| `packages/namaz_backend/lib/src/application/namaz_backend_impl.dart` | `trackingDay`, `trackingStart`, kaza borcu işlemleri | [[takip-gunu-ve-kaza]] |
| `packages/namaz_backend/test/domain_test.dart` | `prayerDay`, `nextPrayer`, vakit servisi senaryoları | [[test-stratejisi]] |
| `packages/namaz_backend/test/prayer_repository_test.dart` | Kaza türetme, tekrar işaretleme, bozuk DB | [[test-stratejisi]] |
| `lib/core/theme/app_theme.dart` | 5 tema, tam palet | [[ekranlar]] |
| `lib/core/strings/*.dart` | Merkezi metinler (prayer, qaza, settings, common, date, nav, home, prayer_dialog, location, notification, startup) | [[ekranlar]] |
| `lib/core/format/text_utils.dart` | `turkishUpper`, `foldTurkish` | [[ekranlar]] |
| `lib/providers/providers.dart` | `QazaNotifier`, `QazaDebtNotifier`, `TrackingDayNotifier` | [[takip-gunu-ve-kaza]] |
| `lib/ui/screens/{home,qaza,settings,city_picker}_screen.dart` | Ekranlar | [[ekranlar]] |
| `lib/ui/widgets/{prayer_card,countdown_card,prayer_dialog,qaza_debt_sheet,islamic_pattern}.dart` | Kartlar, diyalog, planlayıcı, motif | [[ekranlar]] |

**Taşınmayanlar:** istatistik, seri/rozet, zikir, kıble, hicri takvim, widget, Gemini, paylaşım, arka plan görevi, GPS konum, bildirim planlayıcısı (`notification_plan.dart` vb.). Gerekçe: [[proje-ozeti]].

## Mobil wiki sayfaları (`docs/wiki/`)

`namaz-vakitleri.md` ([[vakit-hesabi]]), `takip-gunu-ve-sayac.md` ve `kaza-sistemi.md` ([[takip-gunu-ve-kaza]]), `namaz-isaretleme.md`, `veri-katmani.md` ve `ayarlar-ve-kalicilik.md` ([[veri-katmani]]), `konum.md`, `tema-sistemi.md` ve `erisilebilirlik-ve-kontrast.md` ([[ekranlar]]), `bildirimler.md` ([[bildirim-ve-tepsi]]), `bilinen-sorunlar.md`, `kararlar/003-iso-tarih-formati.md`, `kararlar/005-kaza-turetilir.md`.

## İskelet referansı: P012-focustracker

`C:\2UYGULAMALAR\P012-focustracker\` aynı yığınla (Python 3.10, PySide6/QML, SQLite) yazılmış çalışan bir uygulamadır. Bu projede referans alınanlar:

| P012 | Kullanım |
|---|---|
| `main.py`, `app/core/container.py` | QML motoru + IoC container başlatma deseni |
| `app/ui/qml/components/AppTrayIcon.qml` | Tepsi simgesi ve menü |
| `app/core/strings.py`, `app/core/logger.py`, `app/core/database.py` | Merkezi metin, loglama, DB bağlantısı |
| `app/bridge/`, `app/services/`, `app/core/repositories/` | Katman düzeni ([[mimari]]) |
| `build_exe.py`, `installer.iss`, `tools/release.py`, `.github/workflows/` | Paketleme ve yayın ([[dagitim]]) |
| `CLAUDE.md`, `RULES.md`, `docs/wiki/` | Wiki anayasası ve kurallar |

Eksik olanlar: tek örnek kilidi ve autostart (P012'de bulunamadı).

## Bakım

Mobil kodun dosya yolları ve adları zamanla değişebilir; yol değiştiğinde bu tablo güncellenir.
