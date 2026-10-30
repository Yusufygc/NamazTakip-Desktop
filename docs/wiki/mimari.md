# Mimari

Yığın ve katman kuralları. Alan mantığı: [[vakit-hesabi]], [[takip-gunu-ve-kaza]]. Veri: [[veri-katmani]]. Arayüz: [[ekranlar]]. Kalite kuralları: [[altyapi-kontrol-listesi]].

## Teknoloji

| Konu | Seçim | Not |
|---|---|---|
| Dil / arayüz | Python + PySide6 (QML, Qt Quick Controls "Basic" stili) | P012 ile aynı: `QT_QUICK_CONTROLS_STYLE=Basic` |
| Veritabanı | stdlib `sqlite3` | Ayarlar da burada ([[kararlar]] 6) |
| Vakit hesabı | `adhanpy 1.0.5` (özel Diyanet parametreleriyle) | [[vakit-hesabi]] |
| Tepsi | `Qt.labs.platform.SystemTrayIcon` | P012 `AppTrayIcon.qml` deseni |
| Bildirim | `SystemTrayIcon.showMessage()` | [[bildirim-ve-tepsi]]; Windows'ta davranış doğrulanmadı |
| Zamanlayıcı | `QTimer` | Tek 1 sn'lik saat servisi |
| Test | `pytest` | [[test-stratejisi]] |
| Paketleme | PyInstaller `--onedir` kararlı exe + Inno Setup kurulum dosyası; isteğe bağlı taşınabilir `--onefile` | [[dagitim]] |

Python 3.10.11, proje kökünde `venv/`. Bağımlılıklar üç dosyada tam sürümle sabit: `requirements.txt` (PySide6 6.11.0 ve eklentileri, shiboken6, adhanpy 1.0.5), `requirements-dev.txt` (pytest 9.2.0, ruff 0.17.3), `requirements-build.txt` (pyinstaller 6.22.3). Kurulum ve `pip check` temiz (2026-10-29). Ayrıntı: [[altyapi-kontrol-listesi]].

## Katmanlar

Bağımlılık yönü tek yönlüdür:

```
ui/qml  →  bridge  →  services  →  core/repositories  →  core/domain
```

| Katman | Görev | Kural |
|---|---|---|
| `core/domain` | Modeller, tarih yardımcıları, vakit hesabı, `prayer_day`, `next_prayer`, kaza ve borç hesabı | PySide6 içe aktarmaz; saf fonksiyonlar; önce burada yazılır ve test edilir |
| `core/repositories` | SQLite okuma/yazma (işaretler, ayarlar) | SQL yalnızca burada, parametrik |
| `services` | Ayar, vakit/işaretleme ve kaza servisleri (Qt'siz); saat servisi (`ClockLogic` Qt'siz, `ClockService` `QTimer` sarmalayıcısı) | Bridge'i bilmez; Qt'a yalnızca `ClockService` bağımlı. Bildirim *kararı* burada verilir, *gösterimi* Faz 7'de tepsiye bağlanır |
| `bridge` | QML'e açılan `QObject`'ler (`Property`, `Signal`, `Slot`) | İş kuralı içermez; yalnızca servisi çağırır. QML'in context property'leri zayıf referanstır, bridge'ler Python'da canlı tutulur ([[test-stratejisi]]) |
| `ui/qml` | Sayfalar ve bileşenler | Sabit metin ve sabit ikon yok |

Bu kurallar `tests/` altındaki mimari testle zorunlu kılınır ([[test-stratejisi]]).

## Klasör yapısı (planlanan)

```
P008-NamazTakip-Desktop/
  main.py                      # QGuiApplication, QML motoru, container, tepsi
  CLAUDE.md
  requirements.txt  requirements-dev.txt  requirements-build.txt
  ruff.toml  pytest.ini  .gitattributes  .editorconfig  .gitignore  LICENSE
  app/
    version.py                 # tek sürüm kaynağı
    core/
      domain/                  # prayer, prayer_times, cities, dates, models, qaza (yazıldı)
      repositories/            # prayer_repository, settings_repository (yazıldı)
      strings.py  formatters.py  clock.py   # merkezi metin, saat/süre biçimi, saat kaynağı (yazıldı)
      paths.py  logger.py  database.py  text_utils.py  backup.py   # yazıldı
    container.py               # bağımlılık kökü: her şeyi kurar ve bağlar (katman kuralına tabi değil)
    services/                  # settings, prayer, qaza, clock, autostart, single_instance, missed_prayer (yazıldı)
    bridge/                    # home, qaza, settings, shell, missed (yazıldı)
    ui/qml/                    # Main.qml; theme/ (Theme, Icons + qmldir), components/, pages/ (HomePage, QazaPage, SettingsPage)
  tests/
    conftest.py  data/golden_times.json
  tools/                       # release, simge üretimi
  packaging/
  docs/wiki/  docs/raw/
```

Bu düzen `P012-focustracker/app/` yapısını izler; fark: alan kuralları `core/domain/` altında ayrıdır. Uygulama içi saat (`ClockService`) ve bildirim için bkz. [[bildirim-ve-tepsi]].

**Katman yönü teste bağlıdır:** `tests/test_architecture.py::test_katman_yonu_ihlal_edilmez` içe aktarmaları AST ile tarar. `core/domain` Qt, `sqlite3`, repository, servis ve bridge'i; `core/repositories` Qt, servis ve bridge'i; `services` bridge ve container'ı; `bridge` `sqlite3`, repository, veritabanı ve container'ı içe aktaramaz.

**Köprü sözleşmesi (QML'e açılan yüzey):** bridge'ler `homeBridge`, `qazaBridge`, `settingsBridge` adlarıyla `engine.rootContext()`'e eklenir (`AppContainer.register_context_properties`). Listeler `QVariantList` (sözlük listesi), özet `QVariantMap` olarak döner; metinler Python tarafında `strings.py`'dan çözülür, QML yalnızca gösterir. Durum anahtarları (`pending`, `performed`, `missed`, `compensated`) ve vakit anahtarları (`fajr`…`isha`, Güneş için `sunrise`) metin değil kimliktir; QML bunlara göre simge ve renk seçer. Ayrıntı: [[ekranlar]].

**Kabuk köprüsü:** `shellBridge` (tepsi bildirimi, bildirime tıklama, gösterme ve çıkış istekleri, gizli başlatma bayrağı, tepsi simgesi adresi) QML'e `AppContainer.register_context_properties` ile açılır; `main.py` komut satırını (`--autostart`), tek örneği ve `quitRequested → app.quit` bağlantısını kurar.

**QML yapısı:** `main.build_engine(container)` motoru kurar; QML `import "theme"` / `"components"` / `"pages"` dizin içe aktarmalarıyla çalışır (`theme/qmldir` iki singleton tanımlar). `Theme` singleton'ı kök bağlam özelliklerine güvenmez; seçili tema `Main.qml`'deki `Binding { target: Theme; property: "themeKey"; value: settingsBridge.themeKey }` ile verilir. Metinler singleton değil, `strings` bağlam özelliğidir (iç içe sözlük). Qt Quick Controls "Basic" stili ve özel `background`/`contentItem` kullanılır; odak halkası ve erişilebilirlik adı her etkileşimli bileşende vardır.

## Masaüstüne özgü notlar

- **Saat dilimi:** `datetime.astimezone()` ile sistem saat dilimi kullanılır; ek paket gerekmez. Vakit hesabı UTC üretir, yerel saate çevrilir. **Domain'deki tüm anlar saat dilimli (aware) datetime'dır**: `now` için `datetime.now().astimezone()` kullanılır; naive ve aware karşılaştırması `TypeError` verir, bu yüzden ikisi karıştırılmaz. Takvim günleri için `datetime.date` kullanılır, gün eklemek `timedelta(days=1)` ile yapılır (yaz/kış saatinden etkilenmez).
- **Uykudan dönüş:** Saat her tikte `datetime.now()` ile karşılaştırır, yani uyku sonrası kendiliğinden düzelir ([[bildirim-ve-tepsi]]).
- **Tek örnek:** İkinci exe açılırsa mevcut pencereyi öne getirir (`QLockFile` + `QLocalServer`, `app/services/single_instance.py`); yazıldı ve gerçek süreçlerle doğrulandı ([[bildirim-ve-tepsi]]).
- **Pencere:** Minimum 900×600, varsayılan 1100×760; çoklu pencere yok.
