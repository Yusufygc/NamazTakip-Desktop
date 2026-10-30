# Ekranlar

Üç ana ekran (Vakitler, Kaza, Ayarlar) ve bir şehir seçici. Telefon düzeni (alt çubuk, tek sütun) masaüstünde **soldaki sidebar + geniş içerik alanı** olur. Görsel dil (renkler, Selçuklu motifleri, kart biçimleri) mobille aynıdır; referans: [[mobil-referans]]. Katman: `ui/qml` ([[mimari]]).

## Kabuk (`Main.qml`)

- Sol: sidebar (~88 px, etiketler görünür): **Vakitler**, **Kaza**, **Ayarlar**. Üstte uygulama simgesi, altta sürüm.
- Sağ: seçili sayfa; içerik en çok 1000 px genişliğinde ortalanır.
- Klavye: `Ctrl+1/2/3` sayfa geçişi, `Esc` açık diyaloğu kapatır.
- Minimum pencere 900×600; dar ekran düzeni yazılmaz (gereksiz).

## Köprüler (QML'in kullanacağı yüzey; Faz 3'te yazıldı)

QML sayfaları (Faz 4–6) yalnızca bu üç nesneyi kullanır; hepsi `app/bridge/` altındadır ve testlerde QML'den okunup çağrıldığı doğrulandı.

| Nesne | Özellikler | İşlemler |
|---|---|---|
| `homeBridge` | `hasLocation`, `cityLabel`, `selectedDateKey`, `selectedDateLabel`, `isToday`, `canGoPrevious`, `canGoNext`, `prayers` (6 satır: `key`, `name`, `time`, `status`, `isCongregation`, `isNext`, `isSunrise`, `markable`), `nextPrayerName`, `nextPrayerTime`, `countdown` | `previousDay()`, `nextDay()`, `goToday()`, `openDay(dateKey)`, `markPerformed(prayerKey, congregation)`, `markMissed(prayerKey)`; sinyal `markRejected(mesaj)` |
| `qazaBridge` | `summary` (`autoCount`, `backlogTotal`, `grandTotal`, `dailyTarget`, `estimatedDays` (yoksa −1), `estimatedDateLabel`), `backlog` (5 vakit: `key`, `name`, `count`), `groups` (gün kartları: `dateKey`, `dateLabel`, `count`, `items`), `isEmpty` | `compensate(dateKey, prayerKey)`, `decrementBacklog(prayerKey)`, `previewDuration(yıl, ay, gün, sayılar)` (kaydetmez), `savePlan(sayılar, günlükHedef)` |
| `settingsBridge` | `themeKey`/`themeKeys`, `notificationsEnabled`, `reminderMinutes`/`reminderChoices`, `calcMethodKey`/`calcMethods` (anahtar + ad), `hasLocation`, `cityLabel`, `needsAutostartPrompt`, `autostartEnabled`, `closeToTray`, `trayHintShown` | `setThemeKey`, `setNotificationsEnabled`, `setReminderMinutes`, `setCalcMethod`, `searchCities(sorgu)`, `selectCity(ad)`, `setAutostart`, `setCloseToTray`, `markTrayHintShown` |

Davranışlar: geçersiz değer (`setThemeKey("neon")`, 25 dk hatırlatma, bilinmeyen şehir) `false` döner ve loglanır, ayar değişmez. İşaretleme `recordsChanged` yayınlayıp kaza ekranını, kaza etme `changed` yayınlayıp vakitler ekranını yeniler; şehir veya yöntem değişince (`timesInvalidated`) ikisi de yenilenir. Windows'ta autostart kaydı ve tepsi davranışı bu köprülerde yoktur; yalnızca ayar değeri saklanır (Faz 7).

## 1. Vakitler (ana ekran)

İki sütun: sol **geri sayım kartı** ("Sıradaki Namaz: X", `HH:mm:ss` sayaç, şehir adı, takip günü tarihi); sağ **bugünün namazları** (6 satır: Sabah, Güneş, Öğle, İkindi, Akşam, Yatsı; saat; durum simgesi).

- Konum yoksa vakit ve sayaç yerine "Şehir seçin" kartı ve düğme gösterilir.
- Beş farz vakit kartına tıklayınca **işaretleme diyaloğu**: başlık "X NAMAZINI KILDINIZ MI?", "Cemaatle kıldım" kutusu, **Kıldım**, **Kılmadım**, **Vazgeç**. Güneş satırı tıklanamaz.
- Kart durumları: bekliyor (boş daire), sıradaki (vurgulu, kum saati), kılındı / kaza edildi (açık yeşil, tik), kılınmadı (açık kırmızı, çarpı). Güneş: sarı kenarlık, güneş simgesi. Renkler kartın üstüne harmanlanır; kontrast en az 4,5:1 ([[altyapi-kontrol-listesi]]).
- Üstte önceki/sonraki gün okları: geçmiş günün vakitleri görüntülenir ve işaretlenebilir. Gelecek gün yalnızca vakit gösterir, işaretlenemez. **Sınırlar (bu projede seçildi, mobilde bilinmiyor):** geri en çok takip başlangıcına (`install_date`), ileri en çok 7 güne kadar gidilir (`FUTURE_DAYS_LIMIT`). Gün gezinme takip gününe göre sayılır; gün değişince seçim bugüne döner.
- Sayaç `HH:mm:ss` biçimindedir, saniye yukarı yuvarlanır (kalan 59,4 sn → `00:01:00`); saniyede bir değişir.
- "Sıradaki" vurgusu vaktin **tarihini de** karşılaştırır: gece 00:00–04:00 arasında takip günü dünkü olduğundan dünün Sabah kartı vurgulanmaz (mobildeki bilinen tutarsızlık burada yok; testle doğrulandı).
- Gece yarısından sonra takip günü kendiliğinden değişir ([[bildirim-ve-tepsi]] saat servisi).
- Bildirimden gelen "kıldın mı?" aynı diyaloğu ilgili tarihle açar.

## Vakitler sayfası: uygulama durumu (Faz 4, 2026-10-30)

Yazıldı ve testlerle ekransız doğrulandı; ekran görüntüleriyle (gerçek Windows penceresi, `grabWindow`) 5 temada ve diyalog, şehir seçici, gelecek gün durumlarında kontrol edildi.

| Dosya (`app/ui/qml/`) | İş |
|---|---|
| `Main.qml` | Pencere (900×600 asgari), `Binding` ile tema, `Ctrl+1/2/3` kısayolları, `SideBar` + `StackLayout`, konum yoksa şehir seçiciyi kendiliğinden açar |
| `components/SideBar.qml` | Soldaki 88 px gezinme çubuğu: Vakitler, Kaza, Ayarlar, sürüm; `Tab` ile odak, odak halkası |
| `components/CountdownCard.qml` | Hero kartı: sıradaki vakit adı, `HH:mm:ss` sayaç (Consolas), şehir, yıldız motifi |
| `components/PrayerRow.qml` | Zaman çizelgeli vakit satırı (düğüm simgesi, durum, Cemaatle/Sıradaki etiketi, saat); Enter/Boşluk/tık ile işaretleme diyaloğu |
| `components/PrayerDialog.qml` | "X NAMAZINI KILDINIZ MI?": cemaat kutusu, Kıldım, Kılmadım, Vazgeç; Esc kapatır |
| `components/CityPickerDialog.qml` | Arama kutusu + 81 il listesi; Yukarı/Aşağı + Enter ile seçim |
| `components/DayNavigator.qml` | Önceki/sonraki gün, "Bugüne dön" |
| `components/AppButton.qml`, `IconButton.qml`, `Card.qml`, `AppIcon.qml` | Ortak bileşenler (odak halkası, erişilebilirlik adı) |
| `components/AppTrayIcon.qml` | Sistem tepsisi: ipucu, menü (Göster/Gizle, sıradaki vakit, Bildirimler Açık/Kapalı, Çıkış), bildirim (`showMessage`), ilk kapatma bilgisi, bildirime tıklama |
| `components/MissedPrayersDialog.qml` | Açılışta "Bu vakitleri kıldınız mı?": uygulama kapalıyken giren işaretsiz vakitler, satır başına Kıldım / Kılmadım, altta Sonra ([[bildirim-ve-tepsi]]) |
| `components/UpdateDialog.qml` | "Yeni sürüm var": sürüm notları (düz metin), kurulum dosyası bilgisi, Güncelle / Sonra / Bu Sürümü Atla, indirme ilerlemesi, Windows bekleme durumu ([[guncelleme]]) |
| `components/AutostartPromptDialog.qml` | İlk açılışta "Windows açılınca başlasın mı?" (Evet, başlasın / Hayır) |
| `pages/HomePage.qml` | Vakitler sayfası (Kaza ve Ayarlar sayfaları aşağıda; geçici sayfa kaldırıldı) |
| `theme/Theme.qml`, `theme/Icons.qml` (+ `qmldir`) | Tema singleton'ı ve merkezi ikon yolları |

Kurallar: renk yalnızca `Theme`'den, metin yalnızca `strings`'ten (Python `ui_strings()` → QML `strings` bağlam özelliği; yer tutucu `%1` için `"metin %1".arg(değer)`), ikon yalnızca `Icons`'tan (`AppIcon name:`). Sabit kullanıcı metni `tests/test_architecture.py::test_qml_sabit_metin_yok` ile yasaktır (`theme/` hariç). Her vakit satırının erişilebilirlik adı "<Vakit> vakti saat <HH:mm>, <durum>"; sayaç kartının adı "<Vakit> vaktine <süre> kaldı".

**Doğrulanmadı / eksik:** gerçek fareyle tıklama ve klavyeyle `Tab` gezinmesi insan eliyle denenmedi (testler satır ve düğme işlevlerini doğrudan çağırır); ekran okuyucu denenmedi; DPI %125–%200 ve çoklu monitör denenmedi; Segoe UI ve Consolas yazı tipleri bu makinede var, başka makinede yedek yazı tipine düşer.

## 2. Kaza

- **Boş durum:** kaza ve borç yoksa "Kaza namazınız yok / Allah kabul etsin." ve "Geçmiş Borç Hesapla / Hedef Belirle" düğmesi.
- **Özet kartı:** "Kaza Borcu Özeti": iki metrik ("Kaza Vakti" = toplam, "Günlük Hedef"), varsa "Hedefinize uyarsanız tahmini bitiş: <tarih> (<N> gün)", planlayıcıyı açan düğme. Mihrap motifli zemin.
- **Geçmiş yıllar kaza borcu** (borç > 0 ise): vakit satırları, her birinde "N vakit kaldı" ve **1 Kaza Düş**.
- **Günlük takipten düşen kazalar:** gün kartları (açılır liste), başlıkta tarih ve "N Kaza" rozeti; açılınca vakit satırları, alt başlık "Otomatik tespit" veya "Kılınmadı olarak işaretlendi", **Kaza Et**. İlk gün açık gelir. Kaza Et → onay: "<tarih> tarihli <vakit> namazını kaza ettiniz mi?" (Evet, Kıldım / İptal).
- **Planlayıcı** (ortalanmış diyalog): Yıl / Ay / Gün alanları, "Süreden Hesapla ve Vakitlere Ekle", vakit bazlı elle sayılar, "Günlük Kaza Kılma Hedefi" (1–50), "Kaza Planını Kaydet". Formül: [[takip-gunu-ve-kaza]].
- Liste uzun olabilir: `ListView` ile gecikmeli çizim; sayfalama yok.

### Kaza sayfası: uygulama durumu (Faz 5, 2026-10-30)

Yazıldı; ekransız testlerle (`tests/test_ui_kaza.py`, 15 test) ve gerçek pencerede ekran görüntüleriyle (boş durum, dolu durum, onay, planlayıcı, koyu ve altın tema, 900×600 asgari boyut) doğrulandı.

| Dosya (`app/ui/qml/`) | İş |
|---|---|
| `pages/QazaPage.qml` | Boş durum kartı veya özet kartı (mihrap motifli degrade), geçmiş borç kartı, gün kartları; gün kartlarının açık/kapalı durumu sayfada tutulur ve veri yenilense de korunur |
| `components/DayCard.qml` | Açılır gün kartı: tarih, "N Kaza" rozeti, vakit satırları ("Otomatik tespit" / "Kılınmadı olarak işaretlendi"), **Kaza Et** |
| `components/QazaConfirmDialog.qml` | "<tarih> tarihli <vakit> namazını kaza ettiniz mi?" (Evet, Kıldım / İptal) |
| `components/QazaPlannerDialog.qml` | Yıl/Ay/Gün + "Süreden Hesapla ve Vakitlere Ekle", 5 vakit sayısı, günlük hedef (1–50), "Kaza Planını Kaydet". Form kaydırılır, Kaydet/İptal altta sabittir (900×600'de de görünür) |
| `components/NumberField.qml` | Yalnızca rakam kabul eden alan; boş alan 0 sayılır |

Davranış kararları: özet kartında yalnızca iki metrik vardır (**Kaza Vakti** = otomatik + geçmiş borç toplamı, **Günlük Hedef**); mobil metin dosyasındaki "Eksik Gün" ve "Geçmiş Borç" etiketleri kullanılmadı. Geçmiş borç kartında yalnızca borcu olan vakitler görünür ("1 Kaza Düş" 0'ın altına inmez). Planlayıcı kaydedilene kadar hiçbir şey yazmaz; açılışta mevcut plan alanlara yüklenir; "Süreden Hesapla" süreyi mevcut sayılara ekler ve süre alanlarını sıfırlar. Mihrap motifi `Icons.paths.mihrab` ile çizilir.

**Doğrulanmadı / eksik:** gerçek fareyle tıklama ve `Tab` ile alan gezinmesi insan eliyle denenmedi (özellikle planlayıcıda ve gün kartı başlıklarında); ekran okuyucu ve "kart açık/kapalı" durumunun duyurulması yok; çok uzun kaza listesinde (yüzlerce gün) performans ölçülmedi, mobildeki gibi sayfalama yoktur.

## 3. Ayarlar

Kart gruplarıyla tek sütun, en çok 720 px, ortalı.

| Bölüm | Öğeler |
|---|---|
| Bildirimler | "Bildirimler" anahtarı (alt başlık: Vakitten önce haber, ezan vakti ve "kıldın mı" hatırlatmaları); "Vakitten önce haber ver" listesi: Kapalı, 10, 15, 20, 30, **40**, 45, 60 dk; "Hatırlatma süresi" listesi: 5, 10, 15, 20, 30, 45, 60 dk (ikisi de bildirim kapalıyken pasif) |
| Konum ve Vakitler | Seçili şehir ("Vakit hesabında kullanılan konum"), **Şehir seç**; "Hesaplama yöntemi" listesi (6 yöntem, adlar: [[vakit-hesabi]]) |
| Masaüstü | "Windows açılışında başlat" anahtarı; "Pencereyi kapatınca tepsiye küçült" anahtarı |
| Güncellemeler | "Açılışta güncellemeyi denetle" anahtarı; "Kurulu sürüm: vX" ve durum satırı; **Şimdi Denetle** ([[guncelleme]]) |
| Tema | 5 tema kartı: simge, ad, alt başlık, 4 renk örneği, seçili kenarlığı |
| Alt bilgi | Sürüm ve alt metin |

### Ayarlar sayfası: uygulama durumu (Faz 6, 2026-10-30)

Yazıldı; `tests/test_ui_settings.py` (18 test) ve gerçek pencerede ekran görüntüleriyle (5 tema, bildirim kapalı durumu, 900×600, tema bölümü) doğrulandı.

| Dosya (`app/ui/qml/`) | İş |
|---|---|
| `pages/SettingsPage.qml` | Tek sütun, en çok 720 px, ortalı: Bildirimler, Konum ve Vakitler, Masaüstü, Tema, alt bilgi |
| `components/SettingsSection.qml` | Başlıklı kart grubu (alt öğeler karta eklenir) |
| `components/SwitchRow.qml` | Başlık + açıklama + anahtar (`Switch` tabanlı: klavye, odak halkası, erişilebilirlik adı) |
| `components/ChoiceChips.qml` | Tek seçimli düğme grubu (hatırlatma süresi: 5, 10, 15, 20, 30, 45, 60 dk); bildirim kapalıyken pasif |
| `components/RadioRow.qml` | Liste biçiminde tek seçim (6 hesaplama yöntemi) |
| `components/ThemeCard.qml` | Ad, alt başlık, 4 renk örneği (`Theme.palettes`'ten, kartın kendi teması), seçili kenarlık + onay simgesi |

Spesifikasyondan sapmalar: hatırlatma süresi ve hesaplama yöntemi "açılır liste" yerine düğme grubu / radyo listesi olarak yapıldı (masaüstünde tek tıkla seçim, açılır menü gerektirmez; [[kararlar]] 21). Tema kartında tema başına simge yok, renk örnekleri kimliği taşır. Alt bilgi: "Sürüm 0.1.0 • Günlük namazlarınızı kolayca takip edin" (mobildeki geliştirici adı alınmadı).

**Masaüstü anahtarlarının etkisi (Faz 7'de bağlandı):** "Windows açılışında başlat" Run kaydını yazar/siler (yalnızca paketlenmiş exe'de, [[kararlar]] 23); "Pencereyi kapatınca tepsiye küçült" kapat düğmesinin davranışını belirler (tepsi varsa); "Bildirimler" ve hatırlatma süresi saat servisinin kararını belirler. Ayrıntı ve doğrulama durumu: [[bildirim-ve-tepsi]].

**Şehir seçici:** arama kutusu (otomatik odak), 81 ilin listesi, Türkçe duyarsız arama (`fold_turkish`: "istanbul", "Şanlıurfa", "igdir" eşleşir). Seçince vakitler yeniden hesaplanır. İlk açılışta zorunlu gösterilir; varsayılan öneri İstanbul.

## Temalar

`Theme.qml` singleton'ı seçili paleti tutar; ekranlar renklere buradan bağlanır. Tema sistem açık/koyu ayarını izlemez, yalnızca kullanıcı seçimi geçerlidir. Beş tema (ana renk / vurgu / arka plan):

| Anahtar | Ad | Ana | Vurgu | Arka plan |
|---|---|---|---|---|
| `default` | Selçuklu Zümrüdü | `#1B5E43` | `#C89D3C` | `#F8F5EE` |
| `dark` | Gece Kubbesi | `#38B281` | `#E2B553` | `#0C1411` |
| `ocean` | İznik Çinisi | `#175D85` | `#2EA3B8` | `#F3F8FB` |
| `rose` | Gül Kurusu | `#8C3747` | `#C87A82` | `#FCF6F7` |
| `gold` | Altın | `#8E6918` | `#D1A234` | `#FAF6EC` |

Palet tek kaynaktan, `app/ui/qml/theme/Theme.qml` singleton'ından okunur (değerler mobil `app_theme.dart` ile aynı, [[mobil-referans]]); seçili tema `Main.qml`'deki `Binding` ile `settingsBridge.themeKey`'den gelir. **Küçük yazı için ek belirteçler:** ham `secondary` (altın/turkuaz) kart üzerinde 2,1–3,2:1 verdiği için yalnızca çizgi ve dolguda kullanılır; yazıda `Theme.secondaryText` (kart ve vurgulu satır üstünde) ve `Theme.heroAccent` (sayaç kartı üstünde) kullanılır. Bunlar her temada en az 4,5:1'dir (`tests/test_contrast.py`).

**Motifler:** Selçuklu yıldızı (8 köşeli) QML `Shape` ile çizilir (`Icons.paths.star8`), sayaç kartında süs olarak yer alır. Mihrap kemerli zemin Kaza ekranı (Faz 5) ile gelecek.

## Metinler ve ikonlar

Kullanıcıya görünen Türkçe metin `app/core/strings.py`'da toplanır ve QML'e `Strings` nesnesi olarak açılır (P012 deseni); ekranlarda sabit metin yok. İkonlar tek yerde (P012'de `AppIcon.qml`). Masaüstüne özgü metinler (tepsi menüsü, açılışta başlat, tepsiye küçült) ayrı bölümdedir.

**Türkçe harf tuzağı:** Python `"ikindi".upper()` sonucu `"IKINDI"` verir, `"İKİNDİ"` değil; `"İ".lower()` birleşik nokta üretir. Başlıkları büyütmek ve şehir aramak için `turkish_upper` ve `fold_turkish` (`İ→i`, `I→ı`, aksan duyarsız) `app/core/text_utils.py` içinde yazıldı ve test edildi (81 ilin hepsinde arama kimseyi çakıştırmıyor) ([[test-stratejisi]]). QML'deki JS `toUpperCase` da aynı sorunu taşır: büyük harf başlıkları Python tarafında üretilir.

## Erişilebilirlik

Sayaç için erişilebilirlik adı; tema kartlarında seçili durumu; tüm düğmeler `Tab` ile odaklanır, Enter/Boşluk çalıştırır, odak halkası görünür. Kart renkleri beş temada en az 4,5:1 kontrast ([[altyapi-kontrol-listesi]]).
