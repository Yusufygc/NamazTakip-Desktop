# Altyapı Kontrol Listesi

Yeni projenin ilk günü kurulacak altyapı önlemleri. Kaynak: `C:\2UYGULAMALAR\D002-HazirPromptlar\proje-altyapi-rehberi.md` (GitClean Archiver deneyimlerinden; her madde yaşanmış bir sorundan gelir). Bu sayfa o rehberin bu projeye uyarlanmış özetidir; rehberin güncel hali esastır. Test ayrıntısı: [[test-stratejisi]]; çalışma düzeni: [[calisma-duzeni]]; plan: [[yol-haritasi]] Faz 0.

Rehberdeki araç sürümleri (`pytest 9.1.1`, `ruff 0.17.0`, `pyinstaller 6.22.3`, `pip-audit 2.10.1`) örnektir; **Faz 0'da güncel/uyumlu sürümle yeniden doğrulanır**.

## Depo hijyeni

| Dosya | İçerik | Neden |
|---|---|---|
| `.gitattributes` | `* text=auto eol=lf`; `.bat .cmd .ps1` için `eol=crlf`; `*.png *.ico *.exe *.zip` `binary` | Satır sonu farkı diff gürültüsü ve derleme farkı üretir |
| `.editorconfig` | `charset = utf-8`, `end_of_line = lf`, son satırda yeni satır, boşluk temizliği, py için 4 boşluk | Editörler aynı biçimi yazsın |
| `.gitignore` | `venv/ .venv/ dist/ build/ *.spec .pytest_cache/ .ruff_cache/ htmlcov/` | Çıktı ve önbellek commit'e kaçmasın |
| Kaynak dosyalar | UTF-8, **BOM'suz** (testle zorunlu) | BOM bazı araçlarda ilk satırı bozar |

**Kodlama kuralı:** `open()`, `read_text()`, `write_text()` çağrılarında her zaman `encoding="utf-8"`. Türkçe Windows'ta varsayılan cp1254, CI runner'ında cp1252'dir; `ı`, `ş` runner'da hata verdi (rehberdeki ilk CI koşusunda 2 test kırıldı). Bu proje Türkçe metinle dolu olduğu için özellikle önemli.

## Bağımlılıklar

- Üç dosya, hepsi tam sürüm sabit: `requirements.txt` (çalışma zamanı), `requirements-dev.txt` (`-r requirements.txt` + pytest + ruff), `requirements-build.txt` (`-r requirements.txt` + pyinstaller). Neden: CI ile yerel aynı sonucu versin; derleme aracı sürümü exe özetini de etkiler.
- Kullanılmayan bağımlılığı çıkar; test/derleme aracı çalışma zamanı dosyasına girmesin.
- CI'da `pip-audit -r requirements.txt` (sürümü sabit).
- **Büyük kütüphane yükseltmesi** (PySide6 gibi): önce temiz geçici ortamda tam test; yerinde `pip install -U` venv'i bozdu (shiboken başlamadı). Önce kaldır, temiz kur.

## Lint (`ruff.toml`)

```toml
target-version = "py310"
line-length = 120
extend-exclude = ["venv", "build", "dist"]

[lint]
select = ["E9", "F"]     # yalnızca kesin hatalar
```

Bilinçli olarak yalnızca `E9` ve `F`; biçim kuralları gürültü üretir. İlk günden kurulur (geç kurmak toplu temizlik demek). Her değişiklikten sonra `py_compile` + `pytest` + `ruff`.

## Test altyapısı

`pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
filterwarnings =
    error::EncodingWarning
```

CI'da `PYTHONWARNDEFAULTENCODING=1`; kodlamasız dosya açan kod hataya döner. `tests/conftest.py` autouse fixture'ı **kullanıcı verisini yalıtır**: veritabanı yolu, günlük yedek klasörü, log klasörü, ayar yolu `tmp_path_factory` altına yönlendirilir; testler gerçek `%APPDATA%\NamazTakip\` klasörüne yazmaz. Yeni bir kalıcılık noktası eklenince yalıtım fixture'ı aynı anda eklenir. Ekransız QML için `QT_QPA_PLATFORM=offscreen` ve `QT_QPA_FONTDIR=C:/Windows/Fonts` `conftest.py`'da `setdefault` ile ayarlanır. Bekçi testleri ve senaryolar: [[test-stratejisi]].

## CI (şimdilik yok)

GitHub kullanılmayacağı için ([[kararlar]] 10) CI şimdilik yok. Aynı kapı yerelde elle koşulur: `python -m ruff check .` → `python -m pytest -q` (`PYTHONWARNDEFAULTENCODING=1`) → isteğe bağlı `pip-audit -r requirements.txt`. GitHub'a geçilirse P012'deki `.github/workflows/tests.yml` başlangıç noktasıdır (hedef platform `windows-latest`, izin `contents: read`). Yerel git deposu kuruldu (`git init`, dal `main`); `venv/` `.gitignore`'da. Commit yalnızca kullanıcı "commit at" deyince ([[calisma-duzeni]]).

## Loglama ve hata

- Dosyaya loglama ilk günden: `RotatingFileHandler` (1 MB × 3, `%APPDATA%\NamazTakip\logs\`). Konsolsuz (windowed) exe'de stderr yoktur; log olmadan hata kaybolur. `sys.excepthook` ve `threading.excepthook` kurulur. Kurulum idempotent olmalı (çift handler eklemesin).
- **Sessiz hata yutma yok.** Gerekçeli ve yorumlu istisna yutma kabul edilir; gerekçesiz sayılır. Bozuk ayar/JSON varsayılana düşerken loglanır.

## Güvenlik ve gizlilik (bu proje için geçerli olanlar)

- Uygulama **ağ isteği yapmaz** (vakitler cihazda hesaplanır); README'de yazılır. Güncelleme sistemi eklenirse ağ minimizasyonu ilkeleri uygulanır (tek istek, kimlik/veri yok, kapatma yolu, zorunlu SHA-256).
- Kullanıcı verisi (`namaz_takip.db`) kaldırıcıyla silinmez ([[veri-katmani]]).
- Tek politika kaynağı: aynı kural (örn. vakit anahtarları, yöntem listesi) birden çok yerde tekrarlanmaz.
- Rehberdeki sır/junction/git maddeleri bu uygulama için geçerli değil (dosya sistemi taraması yok).

## Lisans ve üçüncü taraf

`LICENSE` ilk gün. Qt (LGPL) için `THIRD_PARTY_NOTICES.md` üretilir ve testle `requirements.txt` sürümlerine bağlanır; kurulumla dağıtılır. `--onedir` Qt'nin yeniden bağlanabilirliğini korur ([[dagitim]]).

## Arayüz ilkeleri

- Önce backend, UI sonra; çekirdek servis katmanından tüketilir, QML ince kalır ([[mimari]]).
- Ağır iş UI iş parçacığında koşmaz (bu uygulamada ağır iş yok; vakit hesabı önbelleğe alınır).
- **Erişilebilirlik ilk günden:** tıklanabilir her öğe Tab ile odaklanır, Enter/Boşluk çalıştırır, odak halkası ve erişilebilirlik adı; metin kontrastı en az 4,5:1, **5 temada** testle zorunlu.
- Arayüz metni açık ve okunaklı; en küçük yazı 12 px; iç terimler gösterilmez.
- Türkçe arama: `İ→i`, `I→ı`, aksan duyarsız ([[ekranlar]]).
- Bayat sonuç bırakma: işaretleme sonrası kaza ve özet kendiliğinden yenilenir.

## Bu kontrol listesini güncellemek

Başka bir projeden öğrenilen bir önlem, yalnızca **gerçekten yaşanmış veya ölçülmüş** bir şeye dayanıyorsa buraya (ve kaynak rehbere) eklenir; "iyi pratik" dolgusu eklenmez. Her maddede "ne yapılmalı" + "neden" bulunur.
