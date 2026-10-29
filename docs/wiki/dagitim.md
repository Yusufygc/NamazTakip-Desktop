# Derleme ve Dağıtım

Dağıtım biçimi **PyInstaller tek dosya** (`--onefile`): tek `NamazTakip.exe`, yanında `_internal` klasörü yok, istenen klasöre kopyalanıp oradan çalıştırılır ([[kararlar]] 27). Uygulamayı yalnızca geliştirici kendi bilgisayarında kullanır; GitHub'a yüklenmez, kurulum dosyası, CI, yayın ve otomatik güncelleme yoktur ([[kararlar]] 10). Altyapı kuralları: [[altyapi-kontrol-listesi]].

## Derleme

```powershell
venv\Scripts\activate
pip install -r requirements-build.txt
python tools/build_exe.py            # --keep-build: build/ ara klasörünü silme
```

`tools/build_exe.py` bir `build/NamazTakip.spec` üretir ve PyInstaller 6.22.3'ü onunla çağırır. Spec: `EXE` doğrudan ikili ve veri listelerini alır (`COLLECT` yok, bu yüzden tek dosya), pencereli (`console=False`), simge `app/ui/assets/app.ico`, `app/ui/qml` ve `app/ui/assets` veri olarak `app/ui/...` yoluna eklenir, kullanılmayan Qt modülleri dışlanır, kullanılmayan Qt parçaları `is_unused` ile süzülür. Çıktı: `dist/NamazTakip.exe` (`dist/` ve `build/` Git'e girmez). Süre yaklaşık 50 sn.

**Boyut:** PyInstaller'ın Qt kancası `PySide6/qml` klasörünü ve bağlı DLL'leri bütün olarak toplar; ilk derleme **388 MB** çıktı (yalnızca `Qt6WebEngineCore.dll` ~200 MB). Betik kullanılmayan QML modül klasörlerini (Qt3D, Charts, WebEngine, Multimedia vb.), ilgili DLL'leri, `translations` ve `resources` klasörlerini pakete girmeden süzer: klasör çıktısında 141 MB, **tek dosyada 56 MB** (sıkıştırılmış). Silinenlerin hiçbiri uygulamada içe aktarılmaz; QML'in kullandığı modüller (Quick, Controls, Layouts, Shapes, `Qt.labs.platform`) ve `Qt6Network` korunur (testle sabitlendi: `tests/test_build_exe.py`). Çalışan exe QML'i yüklediği sürece eksik modül yoktur: `StackLayout` üç sayfayı da açılışta kurar.

**Tek dosyanın bedeli:** her açılışta paket `%TEMP%\_MEI…` altına açılır. Bu makinede pencere ~3,4 sn'de görünür (soğuk ve sıcak aynı), ikinci başlatmanın "göster" isteği için çıkışı ~3 sn sürer. Windows açılışında başlatmada da aynı açılma süresi vardır. `kill` ile ölen sürecin geçici klasörünün kalıp kalmadığı **doğrulanmadı**. Tek dosyada exe, çalışırken iki süreç görünür (başlatıcı + uygulama); `Popen.kill()` yalnızca başlatıcıyı öldürüp uygulamayı yaşattı (Görev Yöneticisi'nde "Görevi sonlandır" için **doğrulanmadı**); tepsiden **Çıkış** ikisini de kapatır. Bu sorunlar ve antivirüs/SmartScreen'in tek dosyaya daha şüpheli bakması sakıncalı olursa `--onedir`'e dönülür ([[kararlar]] 27).

Notlar:

- Tek dosya: kullanıcı isteği (klasör değil, tek exe). Qt'nin yeniden bağlanabilirliği (LGPL) için `--onedir` daha uygundu; kişisel kullanımda dağıtım olmadığından bu kaygı şimdilik geçerli değil, dağıtılırsa yeniden değerlendirilir ([[altyapi-kontrol-listesi]]).
- Pencereli (konsolsuz) exe: `--windowed`. Konsol olmadığı için dosyaya loglama şarttır.
- QML dosyaları ve simgeler pakete veri olarak eklenir; `main.py` frozen durumda `sys._MEIPASS` kullanır (P012 `main.py` deseni).
- Sürüm tek kaynaktan: `app/version.py`.

Boyut: Qt yüzünden yüzlerce MB olur (P012'nin `dist` klasörü, kurulum dosyası dahil, yaklaşık 490 MB). Kullanım: `dist\...\NamazTakip.exe` doğrudan çalıştırılır veya kısayol oluşturulur. Windows açılışında başlatma kullanılırsa kayıt, klasör taşınınca bozulur ([[bildirim-ve-tepsi]]); exe'yi kalıcı bir klasöre koyun.

## Doğrulama (Faz 8, 2026-10-30, gerçek Windows)

Paketlenmiş tek dosya `NamazTakip.exe` (**proje dışında, başka bir klasöre kopyalanıp** oradan çalıştırıldı), izole veri klasörüyle. İlk tur klasör (`--onedir`) çıktısıyla, ikinci tur tek dosyayla yapıldı; aşağıdaki sonuçlar tek dosya içindir:

| Denenen | Sonuç |
|---|---|
| Exe açılır, tek görünür pencere, ilk açılışta şehir seçici | **Doğrulandı** (ekran görüntüsü) |
| Şehir seçili veriyle Vakitler sayfası (geri sayım, vakitler, kenar çubuğu, simgeler) | **Doğrulandı** (ekran görüntüsü) |
| Log'da `ERROR`/`Traceback` yok; veritabanı ve günlük yedek oluşur | **Doğrulandı** |
| İkinci exe çıkar (tek dosyada ~3 sn, paketin açılması dahil), çalışan örnek "göster" isteğini alır | **Doğrulandı** |
| `--autostart` ile açılınca pencere görünmez (tepside) | **Doğrulandı** |
| Ayar açıkken açılışta `HKCU\...\Run` değeri `"<exe>" --autostart` yazılır (donmuş exe yolu) | **Doğrulandı** (değer sonra silindi, kayıt öncesi haline döndü) |
| Kaza ve Ayarlar sayfalarının exe içinde görsel kontrolü | **Doğrulanmadı** (sayfalar açılışta yüklenir ve QML hatası yok, ama klavye kısayoluyla gezinti ekran görüntüsünde çalışmadı) |
| Toast'ın ekranda görünmesi ve tıklanması | **Doğrulanmadı** |
| SmartScreen / Akıllı Uygulama Denetimi, başka bir klasöre veya bilgisayara taşıma, DPI %150/%200, uykudan dönüş | **Doğrulanmadı** |

Test notu: venv başlatıcısı (`python.exe`) ve tek dosyalı exe'nin başlatıcısı alt süreç açtığından `Popen.kill()` yalnızca başlatıcıyı öldürür (tek dosyada `taskkill /F /T` gerekir); alt süreç tek örnek adlı borusunu tutmaya devam eder ve sonraki denemelerde "ikinci örnek" yanlışlıkla eski sürece bağlanır (yanlış alarm: tek örnek bozuk görünür). Denemeler arasında kalan `main.py` süreçleri temizlenir. Boru adı sabittir ([[bildirim-ve-tepsi]]), gerçek kullanımda tek veri klasörü olduğundan sorun değildir.

## Kimlik ve simge

`app/ui/assets/app.ico` (16–256 px, çok boyutlu) ve `tray.png` `tools/make_icons.py` ile üretilir ve depoda tutulur; PyInstaller'a `--icon app/ui/assets/app.ico` ve `app/ui/assets` veri klasörü olarak verilir (`tools/build_exe.py`). Autostart kaydı yalnızca donmuş exe'de yazılır; bu yüzden exe'yi kalıcı bir klasöre koyun ve ilk çalıştırmada "Evet, başlasın" deyin (kayıt her açılışta yeniden eşitlenir).


Uygulama simgesi çok boyutlu `.ico` (16–256); tepsi simgesi ayrı küçük `.ico`. Kod imzalama yok; kişisel kullanım için bilinçli karar. Windows 11'de Akıllı Uygulama Denetimi (SAC) veya SmartScreen imzasız exe'yi engelleyebilir; bu proje için henüz denenmedi (**doğrulanmadı**). Engelleme çıkarsa P012'deki "kararlı exe" yöntemi referanstır: `C:\2UYGULAMALAR\P012-focustracker\docs\wiki\exe-dagitim-rehberi.md`.

## İleride gerekirse

Kurulum dosyası (Inno Setup: `P012-focustracker\installer.iss`), GitHub yayını ve güncelleme sistemi bu projede **yoktur**; ihtiyaç doğarsa P012 hattı örnek alınır, karar [[kararlar]]'a yazılır.

## Elle kontrol (her yeni derlemede, gerçek Windows)

İlk açılışta şehir seçici gelir; şehir seçilince vakitler mobille aynıdır ([[vakit-hesabi]] doğrulama tablosu); işaretleme kaza listesini günceller; kapat düğmesi tepsiye küçültür; tepsiden "Çıkış" gerçekten kapatır; bildirim vakitte gelir ve tıklanınca pencere açılır; yeniden açılışta işaretler ve ayarlar durur; autostart açıkken yeniden başlatmada uygulama tepside açılır; DPI %100/%150/%200; uykudan dönüş. Ayrıntı: [[test-stratejisi]].

## Kullanıcı verisi

Veri `%APPDATA%\NamazTakip\` altındadır; exe klasörünü silmek veriyi silmez ([[veri-katmani]]).
