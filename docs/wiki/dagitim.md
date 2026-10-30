# Derleme ve Dağıtım

Dağıtım biçimi **Inno Setup kurulum dosyası + kararlı exe** ([[kararlar]] 28). Kurulum dosyası `dist/installer/NamazTakip-Setup-X.Y.Z.exe`, içindeki exe her sürümde **bayt bayt aynıdır**; uygulama kodu exe'nin dışında (`_internal` altında `.pyc`) durur. Yöntemin gerekçesi, ölçümleri ve yapılmaması gerekenler genel rehberdedir: `C:\2UYGULAMALAR\D002-HazirPromptlar\Prod hazırlığı\exe-dagitim-rehberi.md` (bu sayfa onun Namaz Takip'e uyarlamasıdır). Altyapı kuralları: [[altyapi-kontrol-listesi]].

**Durum (2026-10-30):** Aşama 1 (kurulum + kararlı exe + kapı) ve Aşama 2 (`tools/release.py`, `ci.yml`, `release.yml`) yazıldı ve yerelde sınandı; **iş akışları GitHub'da henüz hiç koşmadı**. Aşama 3 (uygulama içi güncelleme) **yapılmadı** ([[yol-haritasi]]).

## Komutlar

```powershell
venv\Scripts\activate
pip install -r requirements-build.txt
python build_installer.py                      # exe + kapı + deneme + kurulum dosyası + .sha256
python build_exe.py                            # yalnızca kararlı exe (dist/NamazTakip/) ve kapı
python build_installer.py --update-launcher-hash   # exe'yi BİLEREK değiştirdiysen yeni özeti onayla
python tools/build_onefile.py                  # isteğe bağlı: taşınabilir tek dosya exe (dist/portable/)
```

Gereken: Python 3.10, `pyinstaller==6.22.3` (sabit), Inno Setup 6 (`ISCC.exe`; `ISCC` ortam değişkeni, PATH ve standart yollar aranır).

## Kararlı exe

Windows 11 Akıllı Uygulama Denetimi (SAC), imzasız her exe'yi **dosya özetine** göre bulut kararına bırakır; karar dosya başına ve öngörülemezdir. Her sürümde yeni exe özeti, kurulan yeni exe'nin engellenmesi demektir. Çözüm: exe'yi sürümler arasında değiştirmemek. Dört parça (biri eksikse özet değişir):

| Parça | Dosya / ayar |
|---|---|
| Sabit giriş betiği | `packaging/launcher.py` (`from main import main; raise SystemExit(main())`). **Değiştirme.** |
| Modüller exe dışında | `--debug=noarchive` (`.pyc` dosyaları `_internal` altında) |
| Sabit zaman damgası | `SOURCE_DATE_EPOCH = 1700000000` (`build_exe.LAUNCHER_EPOCH`) |
| Sabit PE sürüm kaynağı | `packaging/launcher_version_info.txt` (sabit `1.0.0.0`) |

Ürün sürümü başka yerde görünür: kurulum dosyası adı, "Uygulamalar ve özellikler" kaydı ve uygulama. **Bedel:** Gezgin'de exe → Özellikler hep `1.0.0.0` gösterir. Özet ayrıca PyInstaller ve Python sürümüne, simgeye ve ada bağlıdır; bu yüzden PyInstaller sabitlenmiştir. `.gitattributes` `eol=lf` içerir (giriş betiği her makinede aynı derlenmeli).

**Onay kapısı:** `packaging/launcher.sha256` Windows'ta denenmiş exe özetini tutar. `build_exe.py` derlemeden sonra özeti karşılaştırır; farklıysa **derleme ve yayın durur**. Bilerek değiştirmek için: exe'yi yerelde derle, `build_verify.launch_check` ile bu makinede aç, engellenirse **yalnızca** `LAUNCHER_EPOCH` değerini değiştirip yeniden dene, açılınca `--update-launcher-hash` ile onayla, testlerdeki sabit özetleri ve `LAUNCHER_EPOCH` değerini güncelle.

**Referans uygulama:** rehberlerin gerçekleştirmesi `C:UYGULAMALAR\P020-Zipper\gitclean-archiver-pro` (GitClean Archiver; `P012-focustracker` aynı kalıbın PySide6 ikizi). Buradaki betikler ikisinden uyarlandı; GitClean'den alınan ek: bildirim üreticisi ve depo tutarlılık testleri. Alınmayanlar: kurulum sihirbazı görselleri (`wizard_*.bmp`, yalnızca görünüm) ve `AppUserModelID` (görev çubuğu sabitlemesi; Qt tepsi balonu için gerekmediği düşünülüyor, **doğrulanmadı**).

Onaylı özet: `ed66570c689362cf…` (bkz. `packaging/launcher.sha256`).

### Bu makinede doğrulananlar (2026-10-30)

| Denenen | Sonuç |
|---|---|
| Aynı kaynaktan yeniden derleme | Aynı özet |
| Uygulama koduna satır ekleyip yeniden derleme (`app/version.py`) | **Aynı özet** (kararlı exe çalışıyor) |
| `build_verify.launch_check`: exe yalıtılmış veri klasörüyle 8 sn çalıştı, kapatıldı | Geçti |
| `build_installer.py` tam akış: derle → kapı → exe denemesi → Inno → sessiz kurulum → kurulan exe denemesi → kaldırıcı | Geçti; kurulum dosyası **36,7 MB**; gerçek kayıt ve Başlat kısayolu etkilenmedi (deneme sonrası ikisi de yok/aynı) |
| Satır sonları | Giriş betiği ve sürüm kaynağı LF (`tests/test_release_packaging.py` özetlerini sabitler) |

### Doğrulanmadı

- **İş akışları GitHub'da hiç koşmadı** (yalnızca YAML sözdizimi ayrıştırıldı ve metin testleri geçti). `windows-latest` üzerinde kurulumlar, offscreen QML testleri, `choco install innosetup`, `pip-audit` sonucu ve `gh release create` bilinmiyor. İlk push'ta `ci.yml` koşacak; `release.yml` yalnızca etiketle.
- **SAC bu makinede kapalı** (`VerifiedAndReputablePolicyState` = 0). Bu yüzden "exe engellenmedi" denemesi SAC açısından bir şey kanıtlamaz; yalnızca exe'nin açıldığını gösterir. SAC'ın gerçek etkisi SAC'lı bir makinede denenmeli.
- Farklı kök klasörde derleme (CI'a benzetmek için) ve **CI'da derlenen exe'nin yerel özetle aynı çıkması** (Aşama 2'de kapıyla sınanır).
- İndirilmiş (MOTW'li) kurulum dosyasının başka bir bilgisayarda açılması.
- Kurulu uygulamanın Başlat menüsünden açılışı (kurulum dosyası sessiz kurulup kaldırılarak denendi, elle kullanıcı akışı değil).

## Sürüm numarası ve yayın (Aşama 2)

- Biçim `MAJOR.MINOR.PATCH`, etiket `vX.Y.Z`. **Tek kaynak:** `app/version.py` (`__version__`, `RELEASE_REPO`); README sürüm rozeti `tools/release.py` ile aynı değere çekilir, elle düzenlenmez (test tutarlılığı denetler). Güncelleyici (Aşama 3) yalnızca üç sayılı biçimi tanıyacak ve sayısal karşılaştıracak (`0.10.0 > 0.9.0`); `-rc1` gibi ön sürümler yok sayılır. Artış: hata düzeltme → PATCH, yeni özellik → MINOR, geriye dönük uyumsuz veri/ayar değişikliği → MAJOR. exe'nin Windows sürüm kaynağı **bilerek yükseltilmez** (kararlı exe).
- `python tools/release.py X.Y.Z`: sürümü yükseltir, `chore(release): vX.Y.Z` commit'i atar, ek açıklamalı `vX.Y.Z` etiketi oluşturur. **Hiçbir şey göndermez.** Önkoşullar: temiz çalışma ağacı, dal `main`, yeni sürüm mevcuttan büyük, etiket yok. `--dry-run` yalnızca gösterir; `--check-tag vX.Y.Z` etiketin sürümle uyumunu denetler (CI).
- Gönderme **elle ve yalnızca açık istekle**: `git push origin main` sonra `git push origin vX.Y.Z` (`--follow-tags` kullanma: hafif etiketi göndermez). Yapay zekâ asistanları kullanıcının açık isteği olmadan etiket oluşturmaz ve itmez; yayın tüm kurulu kullanıcılara güncelleme penceresi çıkarır.
- `.github/workflows/ci.yml` (her push ve PR): Windows, Python **3.10.11** (yerel venv ile aynı; exe özeti Python sürümüne bağlı), ruff, pytest (`QT_QPA_PLATFORM=offscreen`, `PYTHONWARNDEFAULTENCODING=1`), `pip-audit` (sürüm sabit). Ek iş **`exe-ozeti`** (PR hariç): `python build_exe.py` ile kararlı exe'yi CI'da derler ve özeti `packaging/launcher.sha256` ile karşılaştırır; farklıysa kırmızı. Etiket itmeden CI exe'sinin yerelle aynı olup olmadığını görmenin yolu budur.
- `.github/workflows/release.yml` (`v*` etiketi itilince): sırayla etiket↔sürüm denetimi (etiket adı `env: TAG` ile geçer, kabuk koduna gömülmez), bağımlılıklar, ruff, pytest, Inno Setup (yoksa `choco`), `python build_installer.py` (CI'da deneme atlanır, kapı çalışır), `gh release create … --generate-notes --verify-tag` (`-` içeren etiket `--prerelease`; kurulum dosyası ve `.sha256` yüklenir). İzin: yalnızca `contents: write`. Sürüm notları commit mesajlarından üretilir; bu yüzden commit mesajları anlaşılır ve Türkçe yazılır.
- Yayın kontrol listesi: CI yeşil ve `exe-ozeti` yeşil; `python tools/release.py X.Y.Z`; `git push origin main`; `git push origin vX.Y.Z`; Release iş akışı yeşil, günlükte "Kararlı exe özeti onaylananla aynı"; Release'te `NamazTakip-Setup-X.Y.Z.exe` ve `.sha256` var; **indirilen (MOTW'li) kurulum dosyası SAC'lı bir makinede denenir**.
- Hata ve geri alma: etiket↔sürüm farklı, iş akışı durdu (yayın yok) → düzelt, commit et, etiketi taşı (`git tag -f`, `git push -f origin vX.Y.Z`). Yayın oluştu ama sürüm hatalı → **yayınlanmış etiketi taşıma**, yeni PATCH çıkar; acilse `gh release delete vX.Y.Z --cleanup-tag`.

## Kurulum sihirbazı (Inno Setup 6)

`packaging/NamazTakip.iss`. Önemli ayarlar:

- `AppId` **sabit** (`{6E2B7C1D-8A44-4F3E-9B05-3D7C5A1E94F2}`): değişirse sonraki sürüm üstüne yazmaz, ikinci kurulum olur. `build_verify.UNINSTALL_KEY` aynı GUID'i taşır (testle bağlı).
- `PrivilegesRequired=lowest` (+ `OverridesAllowed=dialog`): UAC sormaz, varsayılan `%LOCALAPPDATA%\Programs\Namaz Takip`; güncelleme ve derleme sonrası deneme sessiz çalışır.
- `CloseApplications=yes`, `RestartApplications=no`; yeniden açmayı `[Run]` yapar: `/SILENT` (uygulama içi güncelleme) kurulumdan sonra uygulamayı açar, `/VERYSILENT` (deneme) açmaz (`Check: RelaunchAfterUpdate`).
- Türkçe ve İngilizce sihirbaz; masaüstü kısayolu isteğe bağlı (varsayılan kapalı); Başlat menüsü kısayolu.
- `LICENSE` ve `THIRD_PARTY_NOTICES.md` kurulumla birlikte dağıtılır. Kullanıcı verisi (`%APPDATA%\NamazTakip\`) kaldırıcı tarafından **silinmez**.
- Çıktı: `NamazTakip-Setup-X.Y.Z.exe`; `build_installer.py` yanına `.sha256` yazar (güncelleyici bu desene ve özete bakacak, Aşama 3).

## Derleme sonrası deneme (`build_verify.py`)

- `launch_check(exe)`: exe başlatılır, süre sonunda çalışıyorsa `taskkill /T /F` ile kapatılır; `WinError 4551/1260` engel sayılır. Deneme uygulaması **yalıtılmış veri klasörüyle** (`NAMAZ_TAKIP_DATA_DIR`) açılır: gerçek veritabanına, yedeklere, tek örnek kilidine ve açılış kaydına dokunmaz; deneme verisi silinir.
- `installer_check(kurulum)`: geçici klasöre sessizce kurar, kurulan exe'yi dener, **kaldırıcıyı da çalıştırır** (kaldırıcı da imzasız exe'dir).
- **Gerçek kurulumu koruma:** deneme kurulumu gerçek kurulumla aynı `AppId`'yi yazar; deneme öncesi "Uygulamalar ve özellikler" kaydı ve Başlat kısayolu yedeklenir, `try/finally` ile her durumda geri yazılır (`save_registration` / `restore_registration`; testler geçici HKCU alt anahtarı kullanır).
- CI'da (`CI` ortam değişkeni) ve `--no-verify` ile deneme atlanır.

## Boyut

PyInstaller'ın Qt kancası `PySide6/qml` klasörünü ve bağlı DLL'leri bütün toplar (ilk denemede klasör **388 MB**, yalnızca `Qt6WebEngineCore.dll` ~200 MB). `build_exe.prune` kullanılmayan QML modül klasörlerini, DLL'leri, `translations` ve `resources` klasörlerini derlemeden sonra siler (**148 MB** klasör, **36,7 MB** kurulum dosyası). Bu **exe dosyasını değiştirmez** (özet yalnızca exe'dendir). Silinen listesi `tools/build_onefile.py` içindeki `is_unused`/`EXCLUDED_MODULES`; QML'in kullandığı modüller (Quick, Controls, Layouts, Shapes, `Qt.labs.platform`) ve `Qt6Network` korunur, testle sabitlendi ([[kararlar]] 26).

## Taşınabilir tek dosya (isteğe bağlı)

`python tools/build_onefile.py` → `dist/portable/NamazTakip.exe` (56 MB). Kullanıcı isteğiyle eklendi ([[kararlar]] 27), ama **kararlı exe değildir**: kod exe'nin içine gömülür, her derlemede özet değişir, SAC her derlemeyi yeniden değerlendirir; onay kapısından geçmez. Her açılışta `%TEMP%`'e açılır (pencere ~3,4 sn). `Popen.kill()` yalnızca başlatıcıyı öldürür, uygulama yaşar. Dağıtım için kullanılmaz; kurulum dosyası esastır.

## Kimlik ve simge

`app/ui/assets/app.ico` (16–256 px) ve `tray.png` `tools/make_icons.py` ile üretilir ve depoda tutulur. Autostart kaydı yalnızca donmuş exe'de yazılır ([[bildirim-ve-tepsi]]): kurulu yola işaret eder; uygulama içi güncelleme exe yolunu değiştirmez, bu yüzden kayıt bozulmaz.

## Lisans ve bildirimler

`THIRD_PARTY_NOTICES.md` elle yazılmaz: `python tools/third_party_notices.py` üretir (kurulu paketlerin `dist-info` lisans metinlerinden; tüm bileşenlerde lisans adı, sürüm ve kaynak adresi yazılır; **MIT metni (adhanpy) kullanıcı kararıyla gömülmez**, bir daha eklenmez) ve `tests/test_release_packaging.py` dosyanın üretimle birebir aynı olduğunu ve her bağımlılığın kurulu sürümle `requirements*.txt` pininin eşleştiğini denetler.

`LICENSE`: **tüm hakları saklı** (kullanıcı kararı; depo public olduğundan GitHub'ın izin verdiği görüntüleme ve çatallama dışında kullanım hakkı vermez). `THIRD_PARTY_NOTICES.md`: PySide6/Qt (LGPL-3.0), adhanpy (MIT), PyInstaller (GPL-2.0-or-later, önyükleyici istisnasıyla), Python (PSF). Qt DLL olarak dinamik bağlanır (`--onedir`), LGPL açısından değiştirilebilir.

SmartScreen / Akıllı Uygulama Denetimi imzasız dosyayı engelleyebilir. Kod imzalama yok; kişisel kullanım için bilinçli karar.

## Elle kontrol (her yeni derlemede, gerçek Windows)

İlk açılışta şehir seçici gelir; şehir seçilince vakitler mobille aynıdır ([[vakit-hesabi]]); işaretleme kaza listesini günceller; kapat düğmesi tepsiye küçültür; tepsiden "Çıkış" gerçekten kapatır; bildirim vakitte gelir ve tıklanınca pencere açılır; yeniden açılışta işaretler ve ayarlar durur; autostart açıkken yeniden başlatmada uygulama tepside açılır; DPI %100/%150/%200; uykudan dönüş. Ayrıntı: [[test-stratejisi]].

Önceki tek dosya denemesinin sonuçları (Faz 8): pencere, şehirli Vakitler görünümü, tek örnek, `--autostart` gizli başlatma ve donmuş exe için `Run` kaydı doğrulandı; Kaza/Ayarlar sayfalarının görsel kontrolü, toast görünümü ve tıklama, SmartScreen ve DPI **doğrulanmadı**. Aynı denemeler kurulu (kararlı) exe ile tekrarlanmadı.

## Kullanıcı verisi

Veri `%APPDATA%\NamazTakip\` altındadır; uygulamayı kaldırmak veriyi silmez ([[veri-katmani]]).
