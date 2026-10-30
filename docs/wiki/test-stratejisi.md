# Test Stratejisi

Araç: `pytest`. Kurulum ve yalıtım: [[altyapi-kontrol-listesi]]. Kural kaynakları: [[takip-gunu-ve-kaza]], [[vakit-hesabi]]. Plan: [[yol-haritasi]].

## Durum (2026-10-30)

**CI dersleri (2026-10-30):** `ci.yml` windows-latest üzerinde 602 test yeşil. Yerelde görünmeyen üç sınıf hata: (1) `PYTHONWARNDEFAULTENCODING=1` yerelde de ayarlanmadıkça kodlamasız `write_text`/`open` testlerde fark edilmez; (2) saat dilimi: CI UTC'dir, geliştirme makinesi UTC+3; `fixed_timezone` autouse fixture'ı tz verilmeyen `PrayerService`'e UTC+3 verir, `TZ=UTC0` ile yerelde UTC simüle edilebilir; (3) aynı süreçte art arda Qt yerel sunucuları: bir test sunucusunun ertelenmiş silmesi sonraki testin `processEvents`'inde süreci çökertebiliyor (`Aborted`, yalnızca CI): sunucuyu test sonunda `DeferredDelete` ile tamamla. Süreç çökerse pytest özet yazmaz; CI `-v` kullanır, tek tek sonuç görünsün.

**Aşama 3 sonrası: 602 test**, `ruff` temiz. Yeni dosyalar: `test_update_service` (GitClean testleri uyarlandı: sürüm karşılaştırma, kayıt doğrulama, güvenilmez adresler, ağ hataları, indirme/özet/boyut, kurulumu başlatma, Windows engeli, artık temizliği), `test_update_bridge` (açılış/elle denetim, atlama, kapalı denetim, indirme, engel ve yeniden deneme, paketlenmemiş çalışma), `test_ui_update` (pencere, indirme kilidi, hata, öncelik sırası, gizliyken bildirim, Ayarlar kartı; arayüz kurulurken ağ isteği olsaydı test kırılır). Hiçbir test gerçek ağa çıkmaz ve gerçek kurulumu başlatmaz. On bir mutasyon yakalandı. QML enum özellikleri (`textFormat`, `closePolicy`) Python'dan okunamaz; `js(...)[0]` ile QML ifadesi olarak sınanır (`js` `(değer, tanımsız_mı)` döndürür).

**Aşama 2 sonrası: 503 test**, `ruff` temiz. `test_release_tool`: yükseltme (her kaynak, exe sürüm kaynağına dokunmama, eşleşme sayısı), geçersiz sürümler, etiket denetimi ve **gerçek yayın akışı geçici bir git deposunda** (`ROOT` o depoya yönlendirilir: kuru çalıştırma, commit + ek açıklamalı etiket, var olan etiket / kirli ağaç / `main` dışı dal reddi, aracın hiçbir şey itmemesi) ve iş akışı metin testleri (etiket tetikleyici, `env: TAG`, adım sırası, kapıyı atlamama, Python 3.10.11, izinler, pip-audit). Sekiz mutasyon yakalandı (biri eşdeğer mutant: `git tag -m` zaten ek açıklamalı etiket yapar). Not: `test_ucuncu_taraf_bildirimi_guncel`, kullanıcının `THIRD_PARTY_NOTICES.md`'den adhanpy MIT metnini bilerek silmesini (üretici hâlâ gömüyordu) yakaladı; üretici kullanıcı kararına uydurulup (metin gömülmez) testler düzeltildi. YAML sözdizimi PyYAML ile (geçici hedef klasöre kurulup) ayrıştırıldı; testler PyYAML'a bağlı değildir.

**Prod hazırlığı Aşama 1 sonrası: 469 test**, `ruff` temiz. Yeni dosyalar: `test_release_packaging` (giriş betiği ve sürüm kaynağı özetleri sabit, LF satır sonu, PyInstaller bayrakları ve `SOURCE_DATE_EPOCH`, onay kapısı: aynı/farklı/yok/güncelle, Qt ayıklama, Inno betiği ayarları ve `AppId` ↔ deneme kaydı eşleşmesi, sürüm biçimi ve kodda ikinci yazımın olmaması, lisans, bildirim dosyasının üreticiyle birebir aynı olması ve kurulu sürüm ↔ `requirements*.txt` pini, MIT metninin gömülü olması, `.gitignore` çıktıları), `test_build_verify` (gerçek kaydın ve kısayolun deneme sonrası aynen geri gelmesi, hata olsa bile geri yükleme, engel algılama, yalıtılmış veri klasörü). Testler **gerçek** `Uninstall` anahtarına değil, teste ait geçici HKCU alt anahtarına yazar ve siler. Yedi mutasyon (kısayol/kayıt geri yazma, yalıtım, kapı, `noarchive`, epoch, yetki düzeyi) yakalandı. `test_build_exe` → `test_build_onefile` olarak yeniden adlandırıldı. Derleme betikleri testlerde içe aktarılır (kök dizin `pythonpath`te). Gerçek derleme ve kurulum denemesi elle çalışır ([[dagitim]]).

**Ekran görüntüsü notu:** `QQuickWindow.grabWindow()` aynı pencerede **ikinci** çağrıda `Shape` (CurveRenderer) ikonlarını çizmez; durum değişmese de ikon pikselleri kaybolur (ölçüldü: 92 → 0). Uygulama hatası değil, yakalama davranışıdır. Çoklu görüntü gerekirse her görüntü için yeni pencere kurulur. README görüntüleri `docs/screenshots/` altındadır ve bu yöntemle üretilir (gerçek QML, örnek veri).

**Tek dosya exe sonrası: 426 test** (`test_build_exe` spec üretimi, süzme kuralları ve kullanılan Qt yollarının süzülmediğini sınar). Gerçek derleme ve exe denemesi elle yapılır ([[dagitim]]).

**Faz 8 sonrası: 394 test**, `ruff` temiz. `test_build_exe` PyInstaller komutunu (bayraklar, simge, veri yolları) ve ayıklama kurallarını sınar; gerçek derleme ve exe denemesi elle yapılır ([[dagitim]]). Kenar çubuğu ortalaması için `test_ui_shell` içinde ölçüm testi var (içerik kutunun tam ortasında; eski sürümde kırılır). Exe denemesinde ekran görüntüsü `QScreen.grabWindow(hwnd)` ile alındı.

**Vakitten önce haber ve açılış sorusu sonrası: 389 test**, `ruff` temiz. Yeni dosyalar: `test_pre_reminder` (ayar, saat kararı, tıklama, Ayarlar sayfası), `test_missed_prayers` (aday bulma, son çalışma anı, köprü, container, diyalog). Ayırt edicilik: sekiz mutasyon (haber anı, 0 = kapalı, son çalışma sınırı, işaretli vakti atlama, geri bakış sınırı, haber tıklaması, `load` içindeki `touch`, kapatınca `dismiss`) testlerce yakalandı; `0 = kapalı` mutasyonu ilk testlerde kaçtı, ezan anı kontrolü eklenerek kapatıldı. Test altyapısı notu: `close_ui` ertelenmiş silmeyi (`DeferredDelete`) artık hemen işler; `processEvents` bunu yapmadığı için motor sonraki testin Qt mesajlarına karışıyordu (tam takımda sıraya bağlı kırılma). `load_ui(last_active=...)` uygulamayı o anda kapanmış gibi kurar.

**Faz 7 sonrası: 340 test**, `ruff` temiz. Faz 7 ile eklenenler: `test_autostart_service` (sahte kayıt defteri; geliştirmede kayıt değişmez; **gerçek `HKCU` gidiş-dönüşü** yalnızca teste ait geçici alt anahtarda, test sonunda silinir), `test_single_instance` (ikinci örnek **gerçek alt süreç**), `test_backup`, `test_shell_bridge` (köprü, container bağlantıları, `--autostart` argümanı), `test_ui_shell` (tepsi ipucu, bildirim iletimi, bildirime tıklama, kapatma davranışı, autostart sorusu, gizli başlatma). Ayırt edicilik: yedi mutasyon (geliştirmede kayıt koruması, yedek sayısı, günde bir yedek, kapatınca tepsi ayarı, tepsi yokken gizleme, ilk kapatma bilgisinin tek seferliği, son bildirimin hatırlanması) testlerce yakalandı.

Faz 7 notları: (1) Aynı süreçte `QLocalSocket` yazması sunucunun olay döngüsünü bekler (Windows adlandırılmış boru: `flush`/`waitForBytesWritten` False döner), bu yüzden tek örnek istemcisi alt süreç olarak sınanır. (2) Ekransız ortamda sistem tepsisi yoktur; tepsi gerektiren kapatma davranışı `Main.qml`'deki `trayAvailable` özelliği testte ayarlanarak sınanır, gerçek tepsiyle ayrıca elle doğrulanır (aşağıda). (3) Testler gerçek `Run` anahtarına dokunmaz: `load_ui` ve container testleri sahte kayıt defteri kullanır, geliştirme ortamında zaten kayıt değişmez; test sonrası gerçek kayıtta `NamazTakip` değeri ve geçici anahtar kalmadığı kontrol edildi.

**Gerçek Windows doğrulaması (elle, betikle):** ekranlı pencere ve gerçek sistem tepsisiyle süreç içi senaryo (kapat → gizlenir → göster → bildirim → gizli başlatma), iki gerçek `main.py` sürecinde tek örnek ve `--autostart` (görünür pencere `EnumWindows` ile başlığa göre sayıldı; venv başlatıcısı alt süreç açtığı için süreç kimliğiyle değil), gerçek `Run` anahtarında yazma/silme. Sonuçlar [[bildirim-ve-tepsi]] tablosunda.

Aşağıdaki özet Faz 6 sonundaki durumdur.

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
