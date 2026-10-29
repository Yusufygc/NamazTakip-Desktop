# Wiki İndeksi

Namaz Takip Masaüstü (Windows, Python + PySide6/QML + SQLite) için bilgi tabanı. Her oturumda önce bu sayfa okunur. Kurallar: `CLAUDE.md` (proje kökü). Kronoloji: [[log]].

## Başlangıç

- [[proje-ozeti]] — Ne yapılıyor, kapsam içi ve dışı.
- [[kararlar]] — Alınan kararlar, reddedilen seçenekler ve açık sorular.
- [[yol-haritasi]] — Fazlar, "bitti sayılır" ölçütleri ve riskler.

## Mimari ve alan mantığı

- [[mimari]] — Yığın, katman kuralları, klasör yapısı, masaüstüne özgü notlar.
- [[vakit-hesabi]] — Vakit hesabı, Diyanet parametreleri, 90 sn güneş payı, Python kütüphane seçenekleri, golden test.
- [[takip-gunu-ve-kaza]] — `prayer_day`, `next_prayer`, işaretleme, kaza türetme, borç planlayıcı.
- [[veri-katmani]] — SQLite şeması, ayarlar tablosu, bozulma ve yedek.

## Arayüz ve platform

- [[ekranlar]] — Vakitler, Kaza, Ayarlar, şehir seçici, temalar, metinler.
- [[bildirim-ve-tepsi]] — Saat servisi, bildirim, tepsi, pencere, autostart, tek örnek.
- [[dagitim]] — PyInstaller tek dosya exe ile yerel paketleme, elle kontrol.

## Kalite ve süreç

- [[altyapi-kontrol-listesi]] — İlk gün kurulacak altyapı: hijyen, bağımlılık, ruff, pytest, CI, loglama, lisans.
- [[test-stratejisi]] — Test katmanları, mobilden taşınacak senaryolar, golden vektör, bekçi testleri.
- [[calisma-duzeni]] — Plan/rapor, commit ve etiket kuralları, dürüst raporlama.

## Kaynaklar

- [[mobil-referans]] — Mobil proje ve P012 iskeletinin dosya haritası.
