# Test Stratejisi

Araç: `pytest`. Kurulum ve yalıtım: [[altyapi-kontrol-listesi]]. Kural kaynakları: [[takip-gunu-ve-kaza]], [[vakit-hesabi]]. Plan: [[yol-haritasi]].

## Durum (2026-10-30)

**Faz 6 sonrası: 278 test**, `ruff` temiz. Faz 6 ile eklenenler: `test_ui_settings` (bildirim anahtarı ve hatırlatma süresinin saat servisine yansıması, şehir seçici ve Vakitler ekranının güncellenmesi, 6 yöntem, masaüstü anahtarları, 5 tema kartı ve pencere renginin değişmesi), `ui_strings` tema testi, iki yeni kontrast çifti. QML test notları: `Switch.toggle()` `toggled` sinyalini yayınlamaz, kullanıcı tıklamasını `click()` taklit eder (`onToggled` bağlamaları ancak böyle sınanır); `property("x")` bir QML nesnesi için `QJSValue`, bir bağlam sözlüğü için `dict` döner (`.toVariant()` yalnızca ilkinde).

**Faz 5 sonrası: 259 test**, `ruff` temiz. Faz 5 ile eklenenler: `test_ui_kaza` (boş/dolu durum, gün kartları ve açık durumun korunması, Kaza Et onayı ve iptali, geçmiş borç ve "1 Kaza Düş", planlayıcı: süreden hesapla, kaydet, iptal, boş alan, hedef kırpma, mevcut planı yükleme), `test_ui_theme` (aşağıda), `qaza` metin yer tutucu testleri, iki yeni kontrast çifti (kaza rozeti, açık düğme).

**Ekran görüntüsünün yakaladığı ikinci hata (Faz 5):** `Theme.onPrimary` QML'de geçersiz renk (siyah) veriyordu; `on` + büyük harfle başlayan özellik adı sinyal işleyici adı gibi okunur. Düğme yazısı ve işaret simgesi Faz 4'ten beri açık temalarda siyah çiziliyordu; ilk ekran görüntülerinde gözden kaçmış, Kaza sayfasının görüntüsünde fark edildi. QML uyarı vermediği için hiçbir test görmemişti. Düzeltme: `textOnPrimary`, `textOnHero`. Regresyon: `tests/test_ui_theme.py` — her renk belirtecinin 5 temada QML'den geçerli renk çözdüğünü, kaynakta kullanılan her `Theme.x` üyesinin tanımlı olduğunu ve `onXxx` biçiminde özellik adı bulunmadığını sınar (eski ad geri getirilince 7 test kırmızı oluyor).

Aşağıdaki özet Faz 4 sonundaki durumdur.

**Faz 4 sonrası: 238 test**, `ruff` temiz. Faz 4 ile eklenenler: `test_ui_qml` (gerçek `Main.qml` ekransız yüklenir; vakit satırları, diyalog, gün gezinme, şehir seçici, sayfa ve tema değişimi), `test_contrast` (5 temada 21 çift, WCAG AA 4,5:1), `test_qml_sabit_metin_yok` ve dedektör testi, `ui_strings` testleri; `tests/qml_support.py` yardımcıları. Aşağıdaki özet Faz 3 sonundaki 203 testlik durumdur.

203 test, `ruff` temiz (`PYTHONWARNDEFAULTENCODING=1` ile de). Dosyalar: `test_dates`, `test_qaza`, `test_prayer_repository`, `test_database`, `test_settings_repository`, `test_text_utils`, `test_prayer_times` (golden), `test_logger`, `test_main`, `test_architecture`, `test_wiki` (Faz 0–2); `test_strings_formatters`, `test_services` (ayar, vakit, kaza servisleri), `test_clock_service` (60 sn kuralı, hatırlatma, gün değişimi, `QTimer` sarmalayıcısı), `test_bridges` (üç bridge + QML'den okuma/slot çağrısı), `test_container` (kurulum, kapanış) (Faz 3). Ortak kurulum `tests/support.py` (sahte saat, sabit saat dilimi UTC+3, İstanbul 26 Ekim bilinen değerleri) ve `conftest.py` (`qapp`, veri yalıtımı).

Ayırt edicilik mutasyonla denendi (hepsi kırmızı oldu, sonra geri alındı): bugün/kaza kuralı, 04:00 sınırı, upsert cemaat alanı (Faz 2); tetik penceresi 60→600 sn, hatırlatmada işaret kontrolü, "sıradaki" vurgusunda tarih karşılaştırması, gelecek gün sınırı, ilk tikin gün değişimi sayılması (Faz 3). QML sayfaları ve bildirimin ekranda gösterimi henüz yok (Faz 4 ve sonrası).

**QML test yöntemi (Faz 4):** `tests/qml_support.py` — `load_ui(qapp)` gerçek `Main.qml`'i bellek içi veritabanı ve sahte saatle yükler; `find(ui, objectName)` önce QObject ağacında, bulunamazsa görsel (`Item`) ağacında arar (Repeater temsilcileri QObject ağacında görünmez); `js(ui, nesne, "kod")` `QQmlExpression` ile fonksiyon çağırır; `QmlMessages` Qt uyarılarını toplar ve `problems()` yalnızca QML/bağlama hatalarını (ReferenceError, "Unable to assign" vb.) süzer. Dedektörün boş dönüp sahte yeşil vermediği, bilerek bozuk bir QML ile ayrı testlenir. Gerçek pencerede görsel kontrol için `QQuickWindow.grabWindow()` ile PNG alınır (ekransız modda yazı tipleri ve gölgeler gerçekçi çıkmaz).

**Ekran görüntüsünün yakaladığı hata (Faz 4):** `HomeBridge.refresh()` `countdownChanged` yayınlamıyordu; ilk şehir seçiminden sonra sayaç bir sonraki tike kadar boş kalıyordu. Birim ve QML testleri bunu görmemişti (bağlama ilk değerle başladığı için). Regresyon testi (`test_ilk_sehir_secimi_sayaci_hemen_gosterir`) düzeltme geri alınınca kırmızı oluyor.

## Katmanlar

| Katman | Ne sınanır | Nasıl |
|---|---|---|
| Domain | `prayer_day`, `next_prayer`, tarih anahtarı, kaza/borç hesabı, `turkish_upper`, `fold_turkish` | Saf fonksiyon testleri; mobil `domain_test.dart` senaryoları port edilir |
| Vakit hesabı | Python çıktısı = mobil çıktısı | **Golden vektör** testi (aşağıda) |
| Repository | Upsert, kaza türetme, bozuk DB yedeği, ayarlar | Bellek içi / geçici dosyalı SQLite; mobil `prayer_repository_test.dart` senaryoları |
| Servis / bridge | Saat servisi tetikleme (60 sn kuralı, yinelenme), bridge sinyalleri | Sahte saat; bridge'ler Python'da canlı tutulur |
| Mimari (bekçi) | Kural ihlali CI'da kırmızı | AST ile (aşağıda) |
| QML | Yerleşim, erişilebilirlik adı, kontrast | `QT_QPA_PLATFORM=offscreen` |
| Elle (gerçek Windows) | Pencere, tepsi, bildirim, autostart, DPI | [[dagitim]] kontrol listesi |

## Mobilden taşınacak senaryolar

- **`prayer_day`:** 00:30 dünkü gün; 03:59 dünkü, 04:00 bugün; ay başı; yazın Sabah 03:24'te sınır Sabah'tır (03:30 bugündür); Sabah verilmezse 04:00 kuralı; kışın sınır 04:00; Sabah tam 04:00; gece yarısından sonra yazın da dünkü gün.
- **`next_prayer`:** öğleden sonra İkindi; Yatsı'dan sonra yarının Sabah'ı (yenileme gerekmeden); gece yarısından sonra aynı takvim gününün Sabah'ı. Yeni: gece 00:00–04:00 arasında vurgu doğru tarihe gider.
- **`date_key`:** ISO biçimi, geri çevirme, metin sıralaması = tarih sıralaması.
- **Vakit servisi:** İstanbul vakitleri sıralı ve makul; güneş doğuşu 90 sn öne çekilir ve dakikaya indirilir.
- **Repository:** aynı vakit tekrar işaretlenince tek kayıt; kılındı kazadan çıkarır, kılmadım geri alınabilir; bugünün bekleyen vakti kaza değil; işaretlenmeyen geçmiş günler otomatik kaza; 5 vakit kılınmışsa gün listeden çıkar; kaza edilen çıkar; rastgele baytlı bozuk dosya silinmeden yedeklenir ve temiz açılır.
- **Faz 5 senaryosu:** 2 gün × 5 vakit = 10 kaza.

Kaynaklar: [[mobil-referans]].

## Golden vektör (vakit doğruluğu)

**Durum:** `tests/data/golden_times.json` üretildi (1060 satır, 81 il, 6 yöntem, 10 tarih) ve `tests/test_prayer_times.py` hepsini saniye düzeyinde karşılaştırıyor; 0 fark. Yeniden üretmek için (Dart gerekir, `C:\src\flutter\bin` PATH'te):

```powershell
cd tools\golden_times
dart pub get
dart run bin\golden.dart C:\2UYGULAMALAR\P008-NamazTakip-Mobil\prayer-tracker\packages\namaz_backend\lib\src\data\turkish_cities.dart C:\2UYGULAMALAR\P008-NamazTakip-Desktop\tests\data\golden_times.json
```

Dosyayı elle düzenleme; mobil vakit mantığı değişirse yeniden üret ve farkı [[vakit-hesabi]]'na yaz. Genel yöntem:

Mobilin kullandığı `adhan_dart 2.0.1` ile 81 il × birkaç tarih (yaz, kış, saat dilimi/gün sınırı dönemleri) × 6 yöntem için vakit listesi üretilir ve `tests/data/golden_times.json` olarak saklanır. Python testi her satırı dakika bazında karşılaştırır. Üretim yöntemi denendi (2026-10-29): geçici saf Dart projesi (`dart pub add adhan_dart:^2.0.1`, `C:\src\flutter\bin\dart.bat`) ile `dart run` çalışıyor; ilk karşılaştırma [[vakit-hesabi]]'ndadır. Fark çıkarsa nedeni ve kabul edilen tolerans [[vakit-hesabi]]'na yazılır; sessizce gevşetilmez. Bu, rehberin "bağımsız oracle" ilkesidir: yeni mantık başka bir kod yoluyla karşılaştırılır, yalnızca kendi birim testine güvenilmez.

## Bekçi (mimari) testleri

| Test | Zorunlu kıldığı kural |
|---|---|
| `test_katman_yonu_ihlal_edilmez` (+ `test_domain_katmani_pyside_icerik_aktarmaz`, `test_sqlite_yalnizca_veri_katmaninda`) | AST ile: `core/domain` Qt, `sqlite3`, repository, servis ve bridge'i; `core/repositories` Qt, servis ve bridge'i; `services` bridge ve container'ı; `bridge` `sqlite3`, repository, veritabanı ve container'ı içe aktarmaz; SQL yalnızca veri katmanında |
| `test_no_silent_except` | Çıplak `except` yok; geniş `except` loglar veya yeniden fırlatır |
| `test_source_files_have_no_utf8_bom` | Kaynakta BOM yok |
| `test_wiki` | Kırık `[[link]]`, öksüz sayfa, indeks eksiği yok; `CLAUDE.md` giriş noktalarını gösterir |
| `test_strings` | QML dosyalarında sabit Türkçe metin ve sabit ikon yok (mobildeki merkezi sistem testinin karşılığı) |
| `test_contrast` | 5 temada kart/metin renkleri en az 4,5:1 (WCAG AA) |

## Yazma ilkeleri

- Her kural için en az bir olumlu ve bir olumsuz test.
- Gerçek senaryo: geçici gerçek SQLite dosyası; uygulama yollarını `conftest.py` yalıtır.
- Ağ yok; testler gerçek ağa çıkmaz.
- Test dosyası adı `test_` ile başlar.
- Test sayıları belgelerde geçerse koddan doğrulanır (eskir).

## QML test notları

- Yerleşim ekransız çizimle sınanır. **Görsel his, gerçek fare/klavye, gerçek pencere otomatik doğrulanamaz**; rapor "elle kontrol gerekir" der.
- `Accessible.name` gibi ekli özellikler `item.property(...)` ile okunamaz: `QAccessible.setActive(True)` + `queryAccessibleInterface(item).text(QAccessible.Text.Name)` kullanılır.
- Ekransız modda SVG simgeler boş çizilir ve stil uyarısı verir; görsel kontrol gerçek platformda (`QT_QPA_PLATFORM=windows`) yapılır. "Kaldı" çıkan her kontrol bağımsız kaynakla doğrulanmadan hata sayılmaz.
- Bridge'ler (ViewModel) Python'da referansla canlı tutulur; QML context property'leri zayıf referanstır.

## Doğrulama yöntemleri

1. Bağımsız oracle (golden vektör, gerekirse Aladhan karşılaştırması).
2. Refactor davranışı değiştirmez: eski ve yeni kod aynı girdiyle koşturulur, çıktılar karşılaştırılır.
3. Ölçmeden karar verme: öneriler gerçek veriyle ölçülür.
4. Gerçek kullanıcı denemesi: CI yeşil ≠ kullanıcıda çalışır; paketlenmiş exe gerçek makinede denenir.
