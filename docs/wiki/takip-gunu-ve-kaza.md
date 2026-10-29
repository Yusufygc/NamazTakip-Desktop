# Takip Günü, İşaretleme ve Kaza

Masaüstünde **aynen korunacak** iş kuralları. Hepsi `core/domain` içinde saf fonksiyon olarak yazılır ([[mimari]]) ve mobilin davranışıyla test edilir ([[test-stratejisi]]). Kaynaklar: [[mobil-referans]]. Vakitlerin kendisi: [[vakit-hesabi]]. Tablo ve ayarlar: [[veri-katmani]].

## Modeller

- `PrayerType`: `fajr, dhuhr, asr, maghrib, isha` (anahtar = ad; DB'de böyle saklanır).
- `PrayerStatus`: `pending=0, performed=1, missed=2, compensated=3`. Kodlar değişmez (DB'ye yazılır). Yalnızca `performed` "zamanında kılındı" sayılır; `compensated` sayılmaz.
- `DayTimes`: tarih + `fajr, sunrise, dhuhr, asr, maghrib, isha`; `time_of(PrayerType)`.
- `NextPrayer`: tür + zaman. `AppLocation`: enlem, boylam, şehir, ülke. `PrayerRecord`: tarih, vakit, durum, cemaat. `QazaItem`: tarih, vakit, durum (`is_auto_detected` = durum `pending`). `QazaDebtPlan` (aşağıda).

## Takip günü (`prayer_day`)

Gece yarısından sonra kılınan Yatsı "dünün" namazıdır. Gün sınırı **`min(04:00, o günün Sabah vakti)`**'dir; sınırdan önceki anlar bir önceki güne yazılır.

```python
def prayer_day(now, fajr_today=None):
    boundary = now.replace(hour=4, minute=0, second=0, microsecond=0)
    if fajr_today is not None and fajr_today < boundary:
        boundary = fajr_today
    return now.date() - timedelta(days=1) if now < boundary else now.date()
```

Yazın Sabah 04:00'ten önce girer (İstanbul 21 Haziran 03:24): sınır o zaman Sabah vaktidir. Kışın sınır 04:00 kalır. Konum yoksa yalnızca 04:00 kuralı uygulanır. Uygulama katmanında `tracking_day(now)` = `prayer_day(now, fajr_today=times_for(now.date()).fajr)`.

Test senaryoları mobil `domain_test.dart`'tan: 00:30 dünkü gün; 03:59 dünkü, 04:00 bugün; ay başında dünkü gün önceki aya düşer; yazın Sabah girince (03:30) gün değişir; yazın Sabah'tan önce dünkü gün; Sabah verilmezse 04:00 kuralı; kışın sınır 04:00; Sabah tam 04:00 ise sınır 04:00.

## Sıradaki vakit (`next_prayer`)

Bugün ve yarının vakitleri içinde, `now`'dan sonraki en erken **beş farz vakit**. Güneş sıradaki vakit sayılmaz. Yatsı'dan sonra sonuç yarının Sabah'ıdır, yenileme gerekmez.

Bilinen küçük tutarsızlık (mobilde de var): 00:00–04:00 arasında takip günü dünkü, takvim günü bugündür. "Sıradaki" vurgusu yalnızca vakit **türüne** bakarsa dünün listesindeki Sabah kartı vurgulanabilir. Masaüstünde `NextPrayer` **tarihi de** karşılaştırılarak başlangıçtan doğru yapılır.

## Tarih yardımcıları

Tarih anahtarı ISO biçimindedir (`yyyy-MM-dd`); metin sıralaması tarih sıralamasıdır, SQL `BETWEEN` ve `ORDER BY` doğru çalışır. `date_key`, `parse_date_key`, `days_between` (iki uç dahil), `days_diff`. Gün eklemek `timedelta(days=1)` ile yapılır.

## Namaz işaretleme

- `mark_performed(tarih, vakit, cemaat)` → durum 1; `mark_missed` → 2; `mark_compensated` → 3.
- Hepsi **upsert** (`UNIQUE(date, prayer)` + `INSERT OR REPLACE` veya `ON CONFLICT`). Aynı vakit tekrar işaretlenince tek kayıt kalır; yanlış işaretlemeyi düzeltmenin yolu yeniden işaretlemedir.
- Tarih parametresi vardır: normalde takip günü; geçmiş günler Vakitler ekranından veya Kaza ekranından düzeltilir. Gelecek gün işaretlenemez.

## Kaza listesi (türetilir, tabloda tutulmaz)

`qaza_items(first_day=takip_başlangıcı, today=takip_günü)`:

1. `first_day..today` arasındaki kayıtlar okunur.
2. Her gün × beş vakit için durum bulunur; kayıt yoksa `pending`.
3. `performed` veya `compensated` olanlar atlanır.
4. Takip günü (`today`) için yalnızca `missed` olanlar listeye girer; bugünün bekleyen vakitleri henüz kaza değildir.
5. Önceki günlerde hem `missed` hem `pending` (işaretlenmemiş) kaza olur.
6. Sıralama: tarih azalan, aynı gün içinde vakit sırası artan.

"Kaza Et" → onay → `mark_compensated` → vakit listeden çıkar ve zamanında kılınmış sayılmaz. Neden türetilir: işaretlenmeyi unutulan günler otomatik kaza olsun, ayrı tablo senkron bozmasın (mobil `kararlar/005-kaza-turetilir`).

## Kapalıyken kaçan vakitler ve açılış sorusu

PC kapalıyken giren vakitler için kayıt yazılmaz, yani `pending` kalır. Kural yukarıdaki gibi işler: takip günü içindeyken bekleyen sayılır, gün bitince **otomatik kaza** olur ("Otomatik tespit"). Buna ek olarak açılışta uygulama kapalıyken girmiş işaretsiz vakitler için "Kıldınız mı?" diye sorulur; cevap `mark_performed` / `mark_missed` olarak yazılır. Sorunun kuralları ve sınırları: [[bildirim-ve-tepsi]] (Açılışta kaçırılan vakitler), karar: [[kararlar]] 24.

## Geçmiş yıllar kaza borcu (planlayıcı)

Takip başlangıcından önceki borç ayrı bir sayaçtır ([[veri-katmani]] ayarları):

- `qaza_backlog`: `{fajr, dhuhr, asr, maghrib, isha}` → her biri 0..1.000.000.
- `qaza_daily_target`: günlük hedef 1..50, varsayılan 2.
- Süreden hesap: `toplam_gün = yıl*365 + ay*30 + gün`; **beş vaktin her birine** `toplam_gün` eklenir.
- "1 Kaza Düş": ilgili vaktin borcu 1 azalır, 0'ın altına inmez.
- `total_backlog = Σ vakit borçları`; `grand_total(otomatik_sayı) = total_backlog + otomatik_sayı`.
- `estimated_days_to_finish = ceil(grand_total / daily_target)`; toplam 0 veya hedef 0 ise `None`. `estimated_completion_date = bugün + gün`.

Kullanıcı arayüzü: [[ekranlar]].

## Kodda nerede

| Kural | Python |
|---|---|
| `prayer_day`, `next_prayer`, tarih yardımcıları | `app/core/domain/dates.py` |
| Modeller (`PrayerRecord`, `QazaItem`, `QazaDebtPlan`) | `app/core/domain/models.py` |
| Kaza türetme, süreden borç ekleme, "1 Kaza Düş", sınırlar | `app/core/domain/qaza.py` (`derive_qaza_items`, `add_duration_to_backlog`, `decrement_backlog`) |
| İşaretleme ve `qaza_items` (SQL) | `app/core/repositories/prayer_repository.py` |
| Borç ve hedef ayarları | `app/core/repositories/settings_repository.py` |

Ayrıntılar: "Süreden hesapla" mevcut sayılara **eklenir** (mobil `qaza_debt_sheet.dart` da öyle); süre 0 veya negatifse hiçbir şey değişmez. Geçmiş günde "kılmadım" denen vakit kazadır ve durumu `MISSED` olarak kalır (`is_auto_detected` yalnızca işaretlenmemişler için doğrudur). `tracking_day` ve `trackingStart` (yani `install_date` yoksa bugün) servis katmanındadır (Faz 3).
