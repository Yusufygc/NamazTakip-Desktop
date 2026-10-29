# Vakit Hesabı

Ezan vakitleri cihazda hesaplanır; internet gerekmez. Mobil uygulama `adhan_dart 2.0.1` kullanır; masaüstü **`adhanpy 1.0.5`** kullanır ([[kararlar]] 9) ve mobille aynı sonucu üretmelidir. Katman: `core/domain` ([[mimari]]). Takip günü ve sıradaki vakit: [[takip-gunu-ve-kaza]].

## Mobilin yaptığı (referans)

Kaynak: `PrayerTimeService.compute` ([[mobil-referans]]). Girdi: konum, gün, yöntem. Çıktı: `DayTimes` (Sabah, Güneş, Öğle, İkindi, Akşam, Yatsı; sistem saat diliminde).

1. Sabah, Öğle, İkindi, Akşam, Yatsı: dakikaya yuvarlı (`precision: false`) hesaptan alınır, yerel saate çevrilir.
2. **Güneş doğuşu ayrıdır:** saniye hassasiyetli (`precision: true`) hesaptan alınır (yöntem düzeltmesi dahil), yerel saate çevrilir, **90 saniye çıkarılır** (`kSunriseCautionOffset`, Sabah namazının kerahet vaktine kalmaması için ihtiyat payı) ve saniye atılarak dakikaya indirilir (yuvarlanmaz, kesilir).

## Yöntem parametreleri (adhan_dart 2.0.1 kaynağından)

| Anahtar (ayarlarda) | Görünen ad | Fajr açısı | Isha | Dakika düzeltmeleri |
|---|---|---|---|---|
| `diyanet` | Diyanet (Türkiye) | 18° | 17° | Güneş −7, Öğle +5, İkindi +4, Akşam +7 |
| `mwl` | Müslüman Dünya Birliği | 18° | 17° | Öğle +1 |
| `egyptian` | Mısır Genel Otoritesi | 19,5° | 17,5° | Öğle +1 |
| `karachi` | Karaçi İslam Bilimleri Üniv. | 18° | 18° | Öğle +1 |
| `ummalqura` | Ümmü'l-Kura (Mekke) | 18,5° | Akşamdan 90 dk sonra | yok |
| `isna` | Kuzey Amerika (ISNA) | 15° | 15° | Öğle +1 |

İkindi için gölge uzunluğu varsayılandır (Şafii, 1). Diyanet düzeltmesi güneş doğuşuna da uygulanır.

## Python karşılığı: `adhanpy`

`adhanpy` (PyPI 1.0.5, MIT, saf Python, `adhan-java` portu) `requirements.txt` içinde sabitlidir. Diyanet için ön ayarı yoktur; özel parametreyle tanımlanır:

```python
CalculationParameters(
    fajr_angle=18.0, isha_angle=17.0,
    method_adjustments=PrayerAdjustments(sunrise=-7, dhuhr=5, asr=4, maghrib=7),
)
PrayerTimes((enlem, boylam), datetime(y, m, d, tzinfo=timezone.utc), calculation_parameters=params)
```

Kurallar:

- `time_zone` verilmez. Çıktı UTC gelir, `astimezone()` ile sistem saatine çevrilir. (`ZoneInfo` Windows'ta `tzdata` paketi ister; kullanılmaz.) Servis çıktısı saat dilimli (aware) datetime'dır; testlerde `tz=` ile sabit saat dilimi verilebilir.
- **`adhanpy`'nin yuvarlaması kapatılır.** `adhanpy` her vakti kendi yuvarlar ve bu yuvarlama mobilden farklıdır: yarım dakikayı aşağı atar (`adhan_dart` yukarı yuvarlar) ve 59:30–59:59 gibi değerleri saate taşımadan keser. Bu yüzden `PrayerTimes` alt sınıflanır (`_UnroundedPrayerTimes`): yalnızca özel `_rounded_minute` adımı, yuvarlamadan düzeltmeleri uygulayacak şekilde ezilir. Yuvarlama `prayer_times.py` içinde mobil kuralıyla yapılır: en yakın dakika, 30 sn ve üstü yukarı. Ölçüm: stok `adhanpy` yuvarlamasıyla 1060 golden satırının 154'ü (%14,5) mobilden farklı çıktı; bu yüzden ezme gereklidir.
- **Güneş doğuşu:** düzeltme (−7 dk) uygulanmış, yuvarlanmamış değerden 90 sn düşülür, saniye kesilir (yuvarlanmaz). `_rounded_minute` özel bir yöntemdir: sürüm sabit (`adhanpy==1.0.5`) ve davranışı golden test korur.
- `ummalqura` için `isha_interval=90` verilir (`adhanpy` yerleşik `UMM_AL_QURA` ayarı da aynıdır).
- `prayer-times-calculator` (Aladhan API'si, internet ister) uygun değil; `praytimes` ve `adhan` (PyPI) kullanılmadı.

## Doğrulama (2026-10-29)

**Golden test sonucu:** `tests/data/golden_times.json` içindeki **1060 satırın hepsi saniye düzeyinde eşit, tolerans yok** (0 farklı satır). Kapsam: 81 ilin tamamı için Diyanet, beş ilde (İstanbul, Ankara, Antalya, Kars, Hakkâri) diğer beş yöntem; her biri 10 tarihte (kış, ilkbahar, yaz, sonbahar, 29 Şubat 2028 dahil). Dosya `tools/golden_times` içindeki Dart betiğiyle üretilir ([[test-stratejisi]]). Testin ayırt edici olduğu mutasyonla doğrulandı: 90 sn payı 60 sn yapılınca 1060 satırın 557'si kırmızı oldu.

Sınırlar: yalnızca Türkiye koordinatları ve bu 10 tarih denendi; Türkiye dışı yüksek enlemler, kutup bölgeleri ve diğer tarihler kapsam dışıdır. Golden dosyası hem `adhan_dart`'a hem Python tarafına aynı soruyu sorar; Diyanet'in resmî tablosunu doğrulamaz.

İlk keşif karşılaştırması (aynı gün, elle; golden testten önce):

| Tarih | Sabah | Güneş: yuvarlak / saniyeli → mobil kuralı | Öğle | İkindi | Akşam | Yatsı |
|---|---|---|---|---|---|---|
| 26 Ekim | 05:55 | 07:21 / 07:20:41 → **07:19** | 12:53 | 15:46 | 18:15 | 19:35 |
| 21 Haziran | 03:24 | 05:25 / 05:25:01 → **05:23** | 13:11 | 17:11 | 20:47 | 22:38 |
| 21 Aralık | 06:46 | 08:18 / 08:18:25 → **08:16** | 13:07 | 15:25 | 17:46 | 19:13 |

- 26 Ekim'de `adhanpy` beş vakti de aynı verdi; güneş doğuşu ham değeri iki kütüphanede de 07:20:41 (Diyanet −7 dk düzeltmesinden sonra). Bu tarih `tests/test_prayer_times.py` içinde bilinen değer testidir.
- **Mobil belgesindeki tablo bayat:** mobil `namaz-vakitleri.md` "İstanbul 26 Eki … 07:21" der; bu değer 90 sn payı uygulanmamış yuvarlak güneş doğuşudur. Mobilin kod kuralı aynı gün **07:19** üretir. Masaüstü kabul ölçütü mobil kodun çıktısıdır, belge tablosu değil.

Resmî Diyanet tablosuyla birebir karşılaştırma yapılmamıştır; mobil belgesine göre Aladhan Diyanet (method 13) ile fark en çok 2 dk (çoğunlukla İkindi). Aynı sınır masaüstü için de geçerlidir.

## Şehir listesi

81 il merkezi, yaklaşık koordinat, `country: 'Türkiye'` (mobil `turkish_cities.dart`). Python karşılığı `app/core/domain/cities.py` (`CITIES`, mobildeki sırayla); golden testi liste adlarını ve koordinatlarını mobil dosyayla karşılaştırır. Şehir araması Türkçe harf ve büyük/küçük farkını yok sayar ([[ekranlar]]).
