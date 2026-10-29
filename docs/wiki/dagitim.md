# Derleme ve Dağıtım

Dağıtım biçimi **PyInstaller** (`--onedir`). Uygulamayı yalnızca geliştirici kendi bilgisayarında kullanır; GitHub'a yüklenmez, kurulum dosyası, CI, yayın ve otomatik güncelleme yoktur ([[kararlar]] 10). Altyapı kuralları: [[altyapi-kontrol-listesi]].

## Derleme

`venv` içinde `requirements-build.txt` ile PyInstaller 6.22.3 kurulu ve çalışıyor (doğrulandı). Derleme betiği (`build_exe.py` veya basit bir `pyinstaller` komutu) Faz 8'de yazılır; çıktı `dist/` altında klasör olur:

- `--onedir`: Qt'nin yeniden bağlanabilirliği (LGPL) için de tercih edilir ([[altyapi-kontrol-listesi]]).
- Pencereli (konsolsuz) exe: `--windowed`. Konsol olmadığı için dosyaya loglama şarttır.
- QML dosyaları ve simgeler pakete veri olarak eklenir; `main.py` frozen durumda `sys._MEIPASS` kullanır (P012 `main.py` deseni).
- Sürüm tek kaynaktan: `app/version.py`.

Boyut: Qt yüzünden yüzlerce MB olur (P012'nin `dist` klasörü, kurulum dosyası dahil, yaklaşık 490 MB). Kullanım: `dist\...\NamazTakip.exe` doğrudan çalıştırılır veya kısayol oluşturulur. Windows açılışında başlatma kullanılırsa kayıt, klasör taşınınca bozulur ([[bildirim-ve-tepsi]]); exe'yi kalıcı bir klasöre koyun.

## Kimlik ve simge

`app/ui/assets/app.ico` (16–256 px, çok boyutlu) ve `tray.png` `tools/make_icons.py` ile üretilir ve depoda tutulur; PyInstaller'a `--icon app/ui/assets/app.ico` ve `app/ui/assets` veri klasörü olarak verilir (Faz 8). Autostart kaydı yalnızca donmuş exe'de yazılır; bu yüzden exe'yi kalıcı bir klasöre koyun ve ilk çalıştırmada "Evet, başlasın" deyin (kayıt her açılışta yeniden eşitlenir).


Uygulama simgesi çok boyutlu `.ico` (16–256); tepsi simgesi ayrı küçük `.ico`. Kod imzalama yok; kişisel kullanım için bilinçli karar. Windows 11'de Akıllı Uygulama Denetimi (SAC) veya SmartScreen imzasız exe'yi engelleyebilir; bu proje için henüz denenmedi (**doğrulanmadı**). Engelleme çıkarsa P012'deki "kararlı exe" yöntemi referanstır: `C:\2UYGULAMALAR\P012-focustracker\docs\wiki\exe-dagitim-rehberi.md`.

## İleride gerekirse

Kurulum dosyası (Inno Setup: `P012-focustracker\installer.iss`), GitHub yayını ve güncelleme sistemi bu projede **yoktur**; ihtiyaç doğarsa P012 hattı örnek alınır, karar [[kararlar]]'a yazılır.

## Elle kontrol (her yeni derlemede, gerçek Windows)

İlk açılışta şehir seçici gelir; şehir seçilince vakitler mobille aynıdır ([[vakit-hesabi]] doğrulama tablosu); işaretleme kaza listesini günceller; kapat düğmesi tepsiye küçültür; tepsiden "Çıkış" gerçekten kapatır; bildirim vakitte gelir ve tıklanınca pencere açılır; yeniden açılışta işaretler ve ayarlar durur; autostart açıkken yeniden başlatmada uygulama tepside açılır; DPI %100/%150/%200; uykudan dönüş. Ayrıntı: [[test-stratejisi]].

## Kullanıcı verisi

Veri `%APPDATA%\NamazTakip\` altındadır; exe klasörünü silmek veriyi silmez ([[veri-katmani]]).
