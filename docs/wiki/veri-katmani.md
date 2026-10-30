# Veri Katmanı

SQLite (stdlib `sqlite3`) tek veri deposudur: işaretler ve ayarlar aynı dosyadadır ([[kararlar]] 6). Katman: `core/repositories` ([[mimari]]). İş kuralları: [[takip-gunu-ve-kaza]].

## Konum ve dosya

`%APPDATA%\NamazTakip\namaz_takip.db`. Yol açıkça uygulama kodunda verilir (çalışma dizinine bağlı olmaz; autostart'ta çalışma dizini farklıdır). Testler gerçek klasöre yazmaz ([[test-stratejisi]]). Kullanıcı verisi kaldırıcıyla silinmez ([[dagitim]]).

## Şema (sürüm 1)

Sürüm `PRAGMA user_version` ile tutulur. Şema değişikliği: sürümü artır → migrasyon yaz → bellek içi DB'de test et → bu sayfayı güncelle.

```sql
CREATE TABLE prayers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,              -- 'yyyy-MM-dd'
  prayer TEXT NOT NULL,            -- 'fajr' | 'dhuhr' | 'asr' | 'maghrib' | 'isha'
  status INTEGER NOT NULL DEFAULT 0,
  is_congregation INTEGER NOT NULL DEFAULT 0,
  marked_at TEXT,                  -- ISO 8601
  compensated_at TEXT,             -- yalnızca status = 3
  UNIQUE(date, prayer)
);
CREATE INDEX idx_prayers_date ON prayers(date);
CREATE INDEX idx_prayers_status ON prayers(status);

CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

Şema mobildeki `prayers` tablosuyla aynıdır (mobilde bu tablo sürüm 2'de zikir tablosuyla birlikte; zikir masaüstünde yok). Kural: bir vaktin satırı **yalnızca kullanıcı işaretleyince** oluşur; işaretlenmemiş vakit için satır yoktur. Kaza listesinin türetilmesi buna dayanır. Tüm SQL parametriktir. Upsert `INSERT ... ON CONFLICT(date, prayer) DO UPDATE` ile yapılır: satırın `id`'si korunur (mobildeki `replace` satırı silip yeniden ekliyordu); yeniden işaretleme `status`, `is_congregation`, `marked_at` ve `compensated_at` alanlarının hepsini günceller, yani "kaza edildi"den "kıldım"a dönülürse `compensated_at` temizlenir. `marked_at` saat dilimli ISO 8601'dir (örn. `2026-01-10T12:00:00+03:00`).

## Repository işlemleri

`records_for_date`, `records_between`, `mark_performed`, `mark_missed`, `mark_compensated`, `qaza_items`. Ayar okuma/yazma ayrı `SettingsRepository`'de. İstatistik sorguları v1'de yok.

## Ayarlar (`settings` tablosu)

Değerler metin olarak saklanır (bool `"1"/"0"`, JSON metin). Bozuk veya eksik değer varsayılana döner (sessizce değil: loglanır).

| Anahtar | Tür | Varsayılan | Ne |
|---|---|---|---|
| `theme` | metin | `default` | `default`, `dark`, `ocean`, `rose`, `gold` ([[ekranlar]]) |
| `notifications_enabled` | bool | `1` | Ezan bildirimi açık mı |
| `reminder_minutes` | int | `15` | Vakitten kaç dk sonra "kıldın mı" hatırlatması |
| `pre_reminder_minutes` | int | `40` | Vakit girmeden kaç dk önce haber; `0` = kapalı (izinli: 0, 10, 15, 20, 30, 40, 45, 60) |
| `calc_method` | metin | `diyanet` | Anahtarlar: [[vakit-hesabi]] |
| `manual_location` | JSON | yok | `{lat, lon, city, country}`; yoksa ana ekran "şehir seç" kartı gösterir |
| `install_date` | metin | ilk açılış | Takip başlangıç günü; kaza bu günden başlar |
| `qaza_backlog` | JSON | hepsi 0 | Geçmiş yıllar borcu, vakit bazlı |
| `qaza_daily_target` | int | `2` | 1..50 |
| `autostart` | bool | yok (ilk açılışta sorulur, [[kararlar]] 12) | Windows açılışında başlat; anahtar yoksa soru gösterilir |
| `close_to_tray` | bool | `1` | Pencereyi kapatınca tepsiye küçült ([[kararlar]] 13) |
| `tray_hint_shown` | bool | `0` | İlk kapatmadaki "tepside çalışıyor" bilgisi gösterildi mi |
| `update_check_enabled` | bool | `1` | Açılışta GitHub'dan yeni sürüm sorulsun mu ([[guncelleme]]) |
| `update_skipped_version` | metin (`X.Y.Z`) | yok | "Bu sürümü atla" denen sürüm: yalnızca açılış denetiminde sessiz kalır |
| `last_active_at` | ISO tarih-saat (saat dilimli) | yok | Uygulamanın en son çalıştığı an (dakikada bir, kapanışta); açılışta kapalıyken kaçan vakitleri bulmak için. Saat dilimsiz veya bozuk değer yok sayılır |
| `window_bounds` | JSON | yok | İsteğe bağlı: son pencere boyutu/konumu |

Mobildeki konum modu (`auto`/`manual`) yoktur; konum her zaman `manual_location`'dır.

### Önemli noktalar

- **`install_date`** ilk açılışta `prayer_day(şimdi)` ile yazılır ve **bir daha değişmez**. Kaybolursa kaza geçmişi sessizce sıfırlanmış gibi görünür; bu yüzden ayarlar işaretlerle aynı dosyadadır.
- **Etkili konum** = `manual_location`; yoksa `None` ve vakit/sayaç gösterilmez.
- `qaza_backlog` okuyucusu bozuk JSON'da varsayılana (hepsi 0) döner; değerler 0..1.000.000 aralığına kırpılır.

## Açılış, bozulma ve yedek

- Açılışta: dosya varsa SQLite başlığını (`"SQLite format 3\0"`, en az 100 bayt) ve `PRAGMA integrity_check` ile `prayers` tablosunun varlığını denetle.
- Bozuksa: dosyayı `namaz_takip.db.bozuk-<yyyyMMdd-HHmmss>` olarak yedekle (eski bozuk yedekler silinir, yalnızca sonuncusu kalır), temiz DB aç, kullanıcıya basit bir uyarı göster. Açılamıyorsa hata ekranı.
- Boş (0 bayt) veya 100 bayttan kısa dosya da bozuk sayılır ve yedeklenir. Başlığı geçerli ama sayfaları bozuk dosya, `integrity_check` veya okuma hatasıyla yakalanır.
- Dosya bu uygulamadan **daha yeni** bir şema sürümüyle yazılmışsa (`user_version` > 1) bozuk sayılmaz: `DatabaseVersionError` fırlatılır ve dosyaya dokunulmaz.
- Bağlantı otomatik commit modundadır (`isolation_level=None`); çok adımlı yazma gerekirse açık `BEGIN`/`COMMIT` kullanılır. Açılışta hata olursa bağlantı kapatılır: Windows'ta açık bağlantı dosyanın yedeklenip silinmesini engeller.
- **Günlük yedek (yazıldı, Faz 7):** açılışta günde bir kez `sqlite3.Connection.backup` ile `%APPDATA%\NamazTakip\backups\namaz_takip-YYYYMMDD.db`; son 7 tutulur. Neden: yıllarca birikmiş kaza borcu ve işaretler tek dosyada; bozulma durumunda yalnızca "bozuk yedek" yetmez.
- JSON dışa/içe aktarma v1 sonrası ([[yol-haritasi]]).
- Bağlantı ana iş parçacığında kullanılır; başka iş parçacığından kullanım gerekirse ayrı bağlantı (P012 `test_database_threading_and_collation` desenine bak).
