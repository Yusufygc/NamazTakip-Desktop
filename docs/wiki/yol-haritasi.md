# Yol Haritası ve Riskler

Aşamalar sırayla yapılır; her aşamanın sonunda `ruff` temiz ve `pytest` yeşil olmalı, ardından **rapor verilip durulur** ([[calisma-duzeni]]). Kapsam: [[proje-ozeti]]; kararlar: [[kararlar]].

| Faz | İş | Bitti sayılır |
|---|---|---|
| **0** İskele | `git init`; `.gitattributes`, `.editorconfig`, `.gitignore`, `LICENSE`; `venv`; üç ayrık `requirements`; `ruff.toml`, `pytest.ini`, `conftest.py`; P012'den iskelet (`main.py`, container, logger, tepsi bileşeni); boş QML penceresi; `test_wiki`. **15 dakikalık deneme:** paketlenmiş exe'de tepsi + `showMessage` + tıklama | `python main.py` pencere açar; `pytest` + `ruff` yeşil; bildirim denemesinin sonucu [[bildirim-ve-tepsi]]'ne yazıldı |
| **1** Vakit hesabı (**tamam**, 2026-10-29) | `PrayerTimeService` (adhanpy + 90 sn güneş kuralı); `golden_times.json` üretimi | Golden test eşit: 1060 satırın hepsi saniye düzeyinde ([[vakit-hesabi]]) |
| **2** Domain + veri (**tamam**, 2026-10-29) | `dates`, `prayer_day`, `next_prayer`, modeller, `database.py`, repository'ler, ayarlar, kaza türetme, borç planlayıcı, 81 il | Mobil senaryolarıyla aynı sonuçlar ([[test-stratejisi]]) |
| **3** Servisler + bridge (**tamam**, 2026-10-30) | Servisler, `ClockService`, bridge'ler, `AppContainer` | Konsolda/test ile sıradaki vakit ve takip günü doğru |
| **4** Vakitler ekranı (**tamam**, 2026-10-30) | Şehir seçici, geri sayım, 6 vakit, işaretleme diyaloğu, geçmiş gün gezinme, tema altyapısı, motif yöntemi seçimi | Namaz işaretlenir, yeniden açılışta kalır |
| **5** Kaza ekranı (**tamam**, 2026-10-31) | Liste, Kaza Et, borç planlayıcı, hedef ve tahmini bitiş | "2 gün × 5 = 10 kaza" senaryosu aynı sonucu verir |
| **6** Ayarlar | Bildirim, hatırlatma, şehir, yöntem, 5 tema, masaüstü anahtarları | Tüm ayarlar yeniden açılışta korunur |
| **7** Masaüstü katmanı | Bildirim, tepsi, pencere davranışı, autostart, tek örnek, günlük yedek | Elle kontrol listesi geçer ([[dagitim]]) |
| **8** Paketleme | Simge, sürüm, `--onedir` çıktısı, zip, wiki ve log | Temiz bir klasörde exe çalışır |

**Durum (2026-10-29):** Faz 0'dan `venv` (Python 3.10.11), `requirements*.txt` ve araç kurulumu (PySide6, adhanpy, pytest, ruff, PyInstaller) tamam. adhanpy'nin Diyanet çıktısı `adhan_dart` ile 3 tarihte karşılaştırıldı ([[vakit-hesabi]]). Sonra yapıldı (aynı gün): `git init` (dal `main`, commit yok), `.gitignore`/`.gitattributes`/`.editorconfig`, `ruff.toml`, `pytest.ini`, `tests/conftest.py` (veri yalıtımı), `app/core/paths.py` ve `logger.py`, `main.py` + boş `Main.qml` penceresi (900×600 minimum, başlık uygulama adı), bekçi testleri (BOM, sessiz `except`, domain'de Qt yok, `sqlite3` yalnız veri katmanında), `test_wiki`, `test_logger`, `test_main`. `ruff` temiz, 15 test geçiyor (`PYTHONWARNDEFAULTENCODING=1` ile de); `python main.py` ekransız 4 sn çalıştı ve log yazdı. Kalanlar: tepsi simgesi + `showMessage` denemesi (simge dosyası gerekir), `LICENSE`/`THIRD_PARTY_NOTICES` (şimdilik gerekmiyor, kişisel kullanım).

**Faz 2 (2026-10-29):** `core/domain/` altında `dates` (takip günü, sıradaki vakit, tarih yardımcıları), `models`, `qaza` (kaza türetme, borç hesapları); `core/text_utils.py`; `core/database.py` (şema v1, bozuk dosya kurtarma, sürüm denetimi); `core/repositories/` altında `prayer_repository` ve `settings_repository`. Mobil `domain_test.dart` ve `prayer_repository_test.dart` senaryoları portlandı. Toplam 120 test, `ruff` temiz; üç mutasyon (bugün kuralı, 04:00 sınırı, upsert cemaat alanı) testlerce yakalandı. Sırada: Faz 3 (servisler, saat servisi, bridge'ler). Günlük yedek ([[veri-katmani]]) henüz yazılmadı.

**Faz 3 (2026-10-30):** `app/services/` altında `settings_service`, `prayer_service` (vakit önbelleği, takip günü, işaretleme), `qaza_service`, `clock_service`; `app/bridge/` altında `home_bridge`, `qaza_bridge`, `settings_bridge`; `app/container.py`; `app/core/` altında `strings.py`, `formatters.py`, `clock.py`; `main.py` container'a bağlandı. 203 test, `ruff` temiz; beş mutasyon yakalandı; `python main.py` ekransız 5 sn çalıştı, veritabanı ve log oluştu. Sırada: Faz 4 (Vakitler sayfası: QML, tema altyapısı). Bildirimin gösterimi, tepsi, autostart kaydı ve günlük yedek henüz yok.

**Faz 4 (2026-10-30):** `app/ui/qml/` altında `Main.qml`, `theme/` (Theme, Icons), `components/` (SideBar, CountdownCard, PrayerRow, PrayerDialog, CityPickerDialog, DayNavigator, AppButton, IconButton, Card, AppIcon), `pages/` (HomePage, PlaceholderPage); `ui_strings()` ve `strings` bağlamı; `HomeBridge`'e `dialogTitle` ve `isFuture`. 238 test, `ruff` temiz. Gerçek Windows penceresinde ekran görüntüleri alınıp 5 tema, diyalog, şehir seçici ve gelecek gün kontrol edildi; `python main.py` gerçek pencerede 6 sn hatasız çalıştı (stderr boş). "Yeniden açılışta kalır" ölçütü veri katmanı testleriyle (dosyalı veritabanı, `install_date`, işaretler) doğrulandı; arayüzden elle işaretleyip uygulamayı yeniden açma denenmedi. Sırada: Faz 5 (Kaza ekranı). Kaza ve Ayarlar sekmeleri şimdilik geçici sayfadır.

**Faz 5 (2026-10-31):** `pages/QazaPage.qml`, `components/DayCard`, `QazaConfirmDialog`, `QazaPlannerDialog`, `NumberField`; `AppButton` "light" varyantı; `Icons`'a `mihrab` ve `chevronDown`; `strings.qaza` (27 metin). "2 gün × 5 = 10 kaza" ölçütü arayüzde de doğrulandı (24 Ekim'de kurulup 26 Ekim'de açılan uygulama: özet "10", iki gün kartı, her kartta 5 vakit). 259 test, `ruff` temiz; gerçek pencerede ekran görüntüleri kontrol edildi. Ekran görüntüleri iki hata yakaladı (`onPrimary` rengi, planlayıcıda alt düğmelerin küçük pencerede kaydırmayla kaybolması); ikisi de düzeltildi, ilki için regresyon testi var. Sırada: Faz 6 (Ayarlar ekranı). Ayarlar sekmesi hâlâ geçici sayfa.

## Riskler

1. **Vakit doğruluğu (en büyük risk).** Python portu mobille aynı sonucu vermezse güvenilmez olur. Golden test bu yüzden Faz 1'dedir. Ayrıca resmî Diyanet tablosuyla birebir karşılaştırma yapılmamıştır; fark en çok ~2 dk ([[vakit-hesabi]]).
2. **Bildirim güvenilirliği.** `showMessage` toast'ı Windows sürümüne ve Odaklanma ayarlarına bağlı olabilir; doğrulanmadı ([[bildirim-ve-tepsi]]). Faz 0 denemesi bu yüzden erkene alındı.
3. **QML arayüzün sıfırdan yazımı.** 5 tema, Selçuklu motifleri ve mihrap zemini en çok emek isteyen kısım ([[ekranlar]]).
4. **Türkçe büyük/küçük harf** hataları ([[ekranlar]], [[test-stratejisi]]).
5. **Paket boyutu ve SAC.** Qt'li exe büyüktür; imzasız exe SAC'a takılabilir ([[dagitim]]).
6. **Python 3.10.** Destek takvimi bu ay bitiyor olabilir (PEP 619, doğrulanmadı). Karar verildi ([[kararlar]] 11); PySide6 6.11.0 bu sürümde çalışıyor.
7. **İki kod tabanı.** Vakit mantığındaki bir düzeltme mobilde ve masaüstünde ayrı yapılır; domain dosyalarının başına "Kaynak: mobil `<dosya>` <tarih>" yorumu eklenir.

## v1 sonrası fikirler

JSON dışa/içe aktarma (yeni bilgisayara geçiş), istatistik, otomatik güncelleme, bildirimde eylem düğmesi, ezan sesi. Hiçbiri v1 kapsamında değildir.
