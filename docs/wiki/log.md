# Log

Kronolojik kayıt, en yeni üstte. Biçim: `## [YYYY-AA-GG] [İŞLEM_TİPİ] | Kısa açıklama`.

## [2026-10-30] INGEST | Faz 6: Ayarlar ekranı (QML)
Ayarlar sayfası (bildirimler + hatırlatma süresi, şehir + 6 hesaplama yöntemi, masaüstü anahtarları, 5 tema kartı) ve `SettingsSection`, `SwitchRow`, `ChoiceChips`, `RadioRow`, `ThemeCard`; `strings.settings`. Seçimler açılır liste yerine düğme grubu/radyo listesi (karar 21). Autostart ve tepsiye küçült anahtarları yalnızca ayarı saklar; etkisi Faz 7'de. Faz 1–5 daha önce beş commit olarak kaydedildi. 278 test, `ruff` temiz. Ayrıntı: [[ekranlar]], [[kararlar]], [[test-stratejisi]], [[yol-haritasi]], [[bildirim-ve-tepsi]].

## [2026-10-30] INGEST | Faz 5: Kaza ekranı (QML)
Kaza sayfası (özet kartı, geçmiş borç, açılır gün kartları, Kaza Et onayı, borç planlayıcı) ve ortak `NumberField`; `strings.qaza`. Ekran görüntüleri iki hata yakaladı: (1) `Theme.onPrimary` QML'de geçersiz renk döndürüp düğme yazısını ve simgeyi açık temalarda siyah çiziyordu (Faz 4'ten beri; `textOnPrimary`/`textOnHero` olarak yeniden adlandırıldı, `test_ui_theme` ile korunuyor); (2) küçük pencerede planlayıcının Kaydet düğmesi kaydırma alanında kayboluyordu (alta sabitlendi). Kaza rozeti dolgusu kontrast için %10'dan %6'ya indi. 259 test, `ruff` temiz. Ayrıntı: [[ekranlar]], [[test-stratejisi]], [[kararlar]], [[yol-haritasi]].

## [2026-10-30] INGEST | Faz 4: Vakitler sayfası (QML)
`app/ui/qml/` altında kabuk, `Theme` (5 tema) ve `Icons`, ortak bileşenler, Vakitler sayfası, işaretleme diyaloğu, şehir seçici; `ui_strings()` ile merkezi metin; `HomeBridge`'e `dialogTitle`, `isFuture`. Gerçek pencerede ekran görüntüleri 5 temada kontrol edildi ve iki sorun bulundu: (1) ilk şehir seçiminden sonra sayaç boş kalıyordu (`countdownChanged` yayınlanmıyordu; düzeltildi, regresyon testi mutasyonla doğrulandı); (2) ham `secondary` rengi küçük yazıda AA'yı geçmiyordu (`secondaryText`, `heroAccent` belirteçleri eklendi, `test_contrast` 5 temada 21 çifti sınıyor). 238 test, `ruff` temiz. Kaza ve Ayarlar sayfaları geçici. Ayrıntı: [[ekranlar]], [[mimari]], [[test-stratejisi]], [[kararlar]], [[yol-haritasi]].

## [2026-10-30] INGEST | Faz 3: servisler, saat servisi, bridge'ler, container
`app/services/` (ayar, vakit/işaretleme, kaza, saat), `app/bridge/` (`homeBridge`, `qazaBridge`, `settingsBridge`), `app/container.py`, `app/core/strings.py`, `formatters.py`, `clock.py`; `main.py` container'a bağlandı. Saat mantığı (`ClockLogic`) Qt'siz ve sahte saatle test edildi: 60 sn tetik penceresi, hatırlatma, gün değişimi. "Sıradaki" vurgusu tarihi de karşılaştırır (mobildeki gece 00:00–04:00 tutarsızlığı yok). Katman yönü AST testiyle korunuyor. QML'den okuma ve slot çağrısı ekransız doğrulandı. 203 test, `ruff` temiz; beş mutasyon yakalandı. Bildirimin ekranda gösterimi, tepsi ve autostart kaydı Faz 7'de. Ayrıntı: [[mimari]], [[ekranlar]], [[bildirim-ve-tepsi]], [[test-stratejisi]], [[kararlar]], [[yol-haritasi]].

## [2026-10-29] INGEST | Faz 2: domain kuralları ve veri katmanı
`app/core/domain/` altında `dates`, `models`, `qaza`; `core/text_utils.py`; `core/database.py` (şema v1, `PRAGMA user_version`, bozuk dosya yedekleme, daha yeni sürüm koruması); `core/repositories/` altında `prayer_repository` (upsert `ON CONFLICT DO UPDATE`) ve `settings_repository` (`settings` tablosu; `autostart` yokken `None`). Mobil `domain_test.dart` ve `prayer_repository_test.dart` senaryoları portlandı. Hata anında bağlantının kapatılması testle doğrulandı (açık bağlantı Windows'ta dosya silmeyi engelliyordu). 120 test, `ruff` temiz; üç mutasyon yakalandı. Ayrıntı: [[takip-gunu-ve-kaza]], [[veri-katmani]], [[test-stratejisi]], [[yol-haritasi]].

## [2026-10-29] INGEST | Faz 1: vakit servisi ve golden test
`app/core/domain/` altında `prayer.py` (modeller), `prayer_times.py` (`PrayerTimeService`, `CalcMethod`, `AppLocation`), `cities.py` (81 il). `adhanpy`'nin yuvarlaması mobilden farklı çıktı (stok yuvarlamayla 1060 satırın 154'ü farklı); `_rounded_minute` ezilip yuvarlama mobil kuralıyla yapıldı. `tools/golden_times` (Dart) ile `tests/data/golden_times.json` üretildi; Python servisi 1060 satırın hepsini saniye düzeyinde birebir verdi (mutasyonla ayırt ediciliği doğrulandı: 90→60 sn ile 557 satır kırmızı). Toplam 38 test, `ruff` temiz. Ayrıntı: [[vakit-hesabi]], [[test-stratejisi]], [[yol-haritasi]].

## [2026-10-29] KURULUM | Faz 0 iskeleti: git, altyapı dosyaları, main.py, testler
`git init` (dal `main`, commit yok), `.gitignore`, `.gitattributes`, `.editorconfig`, `ruff.toml`, `pytest.ini`; `app/` iskeleti (`version`, `core/paths`, `core/logger`), `main.py` ve boş `Main.qml`; `tests/` altında `conftest.py` (veri yalıtımı), `test_logger`, `test_main`, `test_architecture`, `test_wiki`. `ruff` temiz, 15 test geçti (`PYTHONWARNDEFAULTENCODING=1` ile de); `python main.py` ekransız çalıştı ve log yazdı. Gerçek ekranda pencere ve tepsi denenmedi. Ayrıntı: [[yol-haritasi]], [[altyapi-kontrol-listesi]].

## [2026-10-29] KARAR | Autostart ilk açılışta sorulur; kapat tepsiye küçültür
Kararlar 12 ve 13. Ayarlara `tray_hint_shown` eklendi. Ayrıntı: [[kararlar]], [[bildirim-ve-tepsi]], [[veri-katmani]].

## [2026-10-29] DOĞRULAMA | adhanpy, adhan_dart ile karşılaştırıldı
Özel Diyanet parametreli `adhanpy 1.0.5`, geçici Dart projesinde çalıştırılan `adhan_dart 2.0.1` ile İstanbul'da 26 Ekim, 21 Haziran, 21 Aralık için karşılaştırıldı: 26 Ekim'de beş vakit aynı, üç tarihte güneş doğuşu ham değeri aynı. Mobil belgesindeki "Güneş 07:21" değeri 90 sn payı öncesi yuvarlak değer; mobil kod kuralı 07:19 üretiyor. Ayrıntı: [[vakit-hesabi]].

## [2026-10-29] KARAR | adhanpy, PyInstaller (yerel), Python 3.10.11
Vakit kütüphanesi `adhanpy`, dağıtım yalnızca PyInstaller `--onedir` (GitHub, CI, yayın ve güncelleme yok), Python 3.10.11 ile proje içi `venv`. Ayrıntı: [[kararlar]], [[dagitim]].

## [2026-10-29] KURULUM | `venv` ve bağımlılıklar
`venv/` Python 3.10.11 ile oluşturuldu. Kurulanlar: PySide6 6.11.0 (+Addons, Essentials, shiboken6), adhanpy 1.0.5, pytest 9.2.0, ruff 0.17.3, pyinstaller 6.22.3. `pip check` temiz. Sabit sürümler `requirements.txt`, `requirements-dev.txt`, `requirements-build.txt` dosyalarında; bkz. [[mimari]].

## [2026-10-29] INGEST | `proje-altyapi-rehberi.md` içeriği özetlendi
Kaynak: `D002-HazirPromptlar/proje-altyapi-rehberi.md`. Bu projeye uyanlar [[altyapi-kontrol-listesi]], [[test-stratejisi]] ve [[calisma-duzeni]] sayfalarına işlendi. Rehberdeki araç sürümleri örnek; Faz 0'da doğrulanacak.

## [2026-10-29] KARAR | Yığın PySide6 + QML + SQLite oldu
Flutter yerine Python + PySide6/QML + SQLite seçildi; mobil kod kopyalanmaz, referans alınır. Vakit hesabı Python'a taşınır, golden testle doğrulanır. Ayrıntı: [[kararlar]], [[mimari]], [[vakit-hesabi]].

## [2026-10-29] INGEST | Wiki sıfırdan kuruldu
Önceki Flutter varsayımlı 8 dosyalık taşıma rehberi (`desktop/*.md`) atıldı. Yerine `CLAUDE.md` anayasası ve `docs/wiki/` oluşturuldu. İçerik mobil kod (`prayer-tracker`) ve `adhan_dart 2.0.1` kaynağıyla karşılaştırılarak yazıldı: Diyanet düzeltmeleri, şema, kaza kuralları ve ayar anahtarları doğrulandı. Gerçek Windows'ta denenmeyen davranışlar "doğrulanmadı" diye işaretli ([[bildirim-ve-tepsi]]). Sayfalar: [[index]].
