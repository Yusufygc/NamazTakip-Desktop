# Uygulama İçi Güncelleme

Kurulu uygulama açılışta GitHub Releases'te yeni sürüm arar; varsa "Yeni sürüm var" penceresi çıkar. **Güncelle** denince kurulum dosyası indirilir, SHA-256 özeti doğrulanır, uygulama kapanır ve kurulum dosyası sessiz kurulumla üstüne yazar; uygulama kendiliğinden yeniden açılır. Tasarım rehberi: `C:\2UYGULAMALAR\D002-HazirPromptlar\Prod hazırlığı\guncelleme-sistemi.md`; referans gerçekleştirme GitClean Archiver (`P020-Zipper\gitclean-archiver-pro`, `update_service.py`, `UpdateViewModel`, `UpdateDialog.qml`). Yayın hattı ve etiket: [[dagitim]]. Kararlar: [[kararlar]] 28–29.

**Durum (2026-10-30): yazıldı ve testlerle (sahte ağ, sahte kurulum) sınandı; gerçek bir Release'e karşı hiç denenmedi** (henüz yayın yok). Uçtan uca doğrulama için gerçek bir sürüm yayınlanıp önceki sürümden güncelleme denenmelidir ([[dagitim]] kontrol listesi).

## Akış

1. **Yayın:** `vX.Y.Z` etiketi itilince `release.yml` kurulum dosyası `NamazTakip-Setup-X.Y.Z.exe` ve `.sha256` dosyasını Release olarak yükler ([[dagitim]]).
2. **Denetim:** `main.py`, pencere kurulduktan 3 sn sonra `UpdateBridge.startupCheck()` çağırır (testlerde ve `build_engine` içinde değil: ağa çıkılmasın). Ağ yoksa ya da hata olursa sessiz geçer. Ayarlar → Güncellemeler'deki **Şimdi Denetle** her sonucu gösterir ("Güncelsiniz: vX en son sürüm." ya da hata mesajı). Kapatma: aynı kartta **Açılışta güncellemeyi denetle** anahtarı ya da `NAMAZ_TAKIP_NO_UPDATE_CHECK=1`.
3. **Karşılaştırma:** `releases/latest` etiketi `app/version.py` sürümüyle sayısal karşılaştırılır (`0.10.0 > 0.9.0`). Ön sürüm (`-rc1`) ve taslak yok sayılır.
4. **Pencere:** pencere görünürken açılır; gizliyken (tepside) tepsi bildirimi "Yeni sürüm var" gelir ve pencere görününce açılır. **Öncelik sırası:** ilk açılış autostart sorusu → "kıldınız mı" açılış sorusu → güncelleme penceresi (aynı anda iki modal açılmaz).
5. **İndirme:** **Güncelle** → arka plan iş parçacığı (`DownloadWorker`), ilerleme çubuğu; indirme sürerken pencere kapatılamaz. Boyut ve SHA-256 doğrulanır: özet GitHub'ın asset `digest` alanından, yoksa Release'teki `.sha256` dosyasından alınır; **ikisi de yoksa güncelleme reddedilir**. Uyuşmazlıkta dosya silinir. İndirme klasörü `%TEMP%\NamazTakipUpdate`; sonraki açılışta artık kurulum dosyaları ve `install.log` temizlenir.
6. **Kurulum:** `/SILENT /SUPPRESSMSGBOXES /CLOSEAPPLICATIONS /LOG=<klasör>\install.log` ile bağımsız süreç (kabuk yok), sonra `UpdateBridge.quitRequested → ShellBridge.quitRequested → app.quit`. `packaging/NamazTakip.iss` içindeki `Check: RelaunchAfterUpdate` kurulumdan sonra uygulamayı yeniden açar (`/VERYSILENT` derleme sonrası denemede açmaz). Verileriniz (`%APPDATA%\NamazTakip\`) ve Windows açılış kaydı bozulmaz.

### Windows başlatmayı engellerse

`launch_installer` önce doğrudan süreç oluşturur (`CreateProcess`); `WinError 4551/1260` (Akıllı Uygulama Denetimi) gelirse Gezgin'in çift tıklama yolunu (`ShellExecute`) dener; ikisi de engellenirse `InstallerBlockedError`. Köprü bu durumda **otomatik yeniden dener**: 15 sn aralıkla en çok 40 kez (10 dk), pencerede "Windows bekleniyor…" ve **Beklemeyi Bırak** düğmesi görünür; engel kalkınca kurulum kendiliğinden başlar. Süre dolarsa ya da kullanıcı beklemeyi bırakırsa dosya **Gezgin'de seçili gösterilir** ve pencere "çift tıklayarak kurabilirsiniz" der (**Sürüm Sayfası** düğmesi de çıkar). Kararlı exe sayesinde ([[dagitim]]) bu yola nadiren girilmesi beklenir; kurulum dosyası her sürümde yeni olduğundan emniyet ağı tutulur.

## Katmanlar ve dosyalar

| Katman | Dosya |
|---|---|
| Servis (Qt'siz) | `app/services/update_service.py`: sürüm karşılaştırma, kayıt doğrulama, ağ, indirme, kurulumu başlatma, artık temizliği |
| Köprü | `app/bridge/update_bridge.py` (`UpdateBridge`, `UpdateWorker`, `DownloadWorker`); tercihler `SettingsBridge.updateCheckEnabled` |
| Arayüz | `components/UpdateDialog.qml`, Ayarlar → Güncellemeler kartı (`SettingsPage.qml`), `Main.qml` (öncelik sırası, gizliyken bildirim) |
| Metinler | `UpdateStrings` (`app/core/strings.py`, `strings.update`) |
| Tercihler | SQLite `settings`: `update_check_enabled` (varsayılan açık), `update_skipped_version` ([[veri-katmani]]); GitClean'deki ayrı `updates.json` kullanılmaz |

## Güvenlik ve gizlilik

- Tek istek: `GET https://api.github.com/repos/Yusufygc/NamazTakip-Desktop/releases/latest`; `User-Agent: NamazTakip/<sürüm>`. Kimlik bilgisi, çerez, kullanıcı verisi (işaretler, şehir) **gönderilmez**. GitHub, isteğin geldiği IP adresini görür (her web isteği gibi). README'de gizlilik açıklaması ve kapatma yolu var.
- İndirme adresi yalnızca `https://github.com/Yusufygc/NamazTakip-Desktop/...` olabilir; yönlendirme yalnızca `github.com` / `*.githubusercontent.com` adreslerine kabul edilir. Sürüm kaydındaki sayfa adresi güvenilir değilse kayıt reddedilir.
- Kurulum dosyası adı sıkı desene uymalı (`NamazTakip-Setup-X.Y.Z.exe`); başka ad indirilmez ve başlatılmaz. Boyut sınırı 400 MB; yanıt boyutu ve süre sınırlıdır; sürüm notu düz metin gösterilir (`textFormat: Text.PlainText`, bağlantı/biçim çalıştırılmaz).
- Bu kontroller kaldırılmaz; özet yoksa "yine de kur" yoktur.
- **Sınır:** özet GitHub'dan gelir; GitHub hesabı ele geçirilirse sahte dosya + sahte özet yayınlanabilir (imza olmadığından fark yakalanamaz). İmzasız dağıtımın doğasıdır.
- Paketlenmemiş çalışmada (`python main.py`) **Güncelle** kurulum başlatmaz; sürüm sayfasını açar (geliştirme oturumu yanlışlıkla kapanmasın). Taşınabilir tek dosya exe de paketlenmiş sayılır ve **Güncelle** kurulum dosyasını çalıştırır (kurulu sürüm oluşur).

## GitClean ile farklar

| | GitClean Archiver | Namaz Takip |
|---|---|---|
| Tercih deposu | `~/.gitclean/updates.json` | SQLite `settings` tablosu |
| Kurulum dosyası | `GitCleanArchiver-Setup-X.Y.Z.exe` | `NamazTakip-Setup-X.Y.Z.exe` |
| Paketlenmemiş çalışma | kurulum başlatılabilir | sürüm sayfası açılır |
| Pencere sırası | tek diyalog | autostart sorusu ve açılış sorusuyla sıralı, gizliyken tepsi bildirimi |
| Metinler | QML içinde | merkezi `UpdateStrings` |

## Sınırlar

- Yalnızca Windows.
- İndirme sürerken pencere kapatılamaz; iptal düğmesi yok.
- Uygulama kapalıyken ya da uykudayken denetim yapılmaz; yalnızca açılışta denetlenir (uzun süre açık kalan uygulama yeni sürümü sonraki açılışta görür; elle denetim her zaman çalışır).
- **Doğrulanmadı:** gerçek Release'e karşı denetim, indirme ve sessiz kurulum; kurulumdan sonra uygulamanın yeniden açılması; Akıllı Uygulama Denetimi'nin kurulum dosyasına tepkisi (bu makinede SAC kapalı); kapanma sırasında tepside çalışan uygulamanın Inno `CloseApplications` ile sorunsuz kapanması (uygulama zaten kendi kapanıyor, ama sıra denenmedi).
