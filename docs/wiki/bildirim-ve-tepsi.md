# Bildirim, Tepsi ve Arka Plan

Mobilde bildirimler işletim sistemine önceden planlanır. Masaüstünde buna gerek yoktur: uygulama bilgisayar açıkken **tepside çalışır** ve vakit girince kendisi bildirim gösterir. Uygulama kapalıysa bildirim gelmez; bu bilinçli bir sınırdır ([[kararlar]] 4). Katman: `services` ([[mimari]]).

## Doğrulama durumu (Faz 7, 2026-10-30)

Bu makinede (Windows 11, gerçek ekran ve gerçek sistem tepsisi) denendi:

| Davranış | Sonuç |
|---|---|
| Sistem tepsisi var mı (`SystemTrayIcon.available`) | **Evet** |
| Pencereyi kapatınca gizlenir, süreç yaşar, ilk kapatmada bilgi bir kez gösterilir | **Doğrulandı** (süreç içi, gerçek tepsiyle) |
| Tepsiden/ikinci örnekten "göster" isteği pencereyi geri getirir | **Doğrulandı** |
| Saat servisinin bildirimi tepsi `showMessage` çağrısına ulaşır, QML hatası yok | **Doğrulandı** |
| `--autostart` ile açılınca pencere görünmez (tepside), normal açılışta tam bir pencere var | **Doğrulandı** (iki gerçek süreç, görünür pencere sayımı) |
| İkinci örnek 0,4 sn'de çıkar, çalışan örnek "göster" isteğini alır; `--autostart` ile açılan ikinci örnek bildirmez; ilk örnek ölünce yeni örnek açılabilir | **Doğrulandı** (gerçek süreçler) |
| `HKCU\...\Run` kaydı yazma ve silme (kısa süreli, geri alındı) | **Doğrulandı** (gerçek kayıt defteri) |
| Toast'ın **ekranda göründüğü**, Odaklanma Yardımı/Rahatsız Etmeyin davranışı, **bildirime tıklama** (`messageClicked`) | **Doğrulanmadı**: `showMessage` hatasız çağrıldı ama toast gözle görülmedi, tıklama elle denenmedi |
| Gizli başlatmada kaçırılan vakit bildirimi tepsiye gider, pencere gelince "kıldınız mı" diyaloğu açılır | **Doğrulandı** (gerçek tepsi, süreç içi; bildirim başlığı tepsiye iletildi) |
| "Vakitten önce haber" ve "işaretlenmemiş vakitler var" toast'ının ekranda görünmesi ve tıklanması | **Doğrulanmadı** (diğer toast'larla aynı yol: `showMessage`) |
| Paketlenmiş exe ile autostart (donmuş exe yolu) | **Doğrulandı** (Faz 8, [[dagitim]]) |
| Uykudan dönüş, saat dilimi değişimi, birden çok monitör | **Doğrulanmadı** |

## Saat servisi (`ClockService`)

`ClockLogic` saf Python'dur: sahte saatle `tick(now)` çağrılır ve `Tick` (takip günü, gün değişti mi, sıradaki vakit, kalan süre, bildirimler) döner. `ClockService` onu 1 sn'lik `QTimer` ile sürer ve `ticked` / `notification` sinyallerini yayınlar; mantık hatası olursa loglar ve zamanlayıcı düşmez. `notification` sinyali `AppContainer` tarafından `ShellBridge.on_notification`'a bağlanır, oradan QML'deki tepsi simgesine gider.

Her tikte:

1. `tracking_day(şimdi)` hesaplanır; gün değiştiyse bridge'ler yenilenir ([[takip-gunu-ve-kaza]]).
2. Sıradaki vakit ve geri sayım güncellenir. **Vakitler (tarih, konum, yöntem) anahtarıyla önbelleğe alınır**; her saniye yeniden hesaplanmaz.
3. **Vakitten önce haber (`PRE`):** `pre_reminder_minutes` > 0 ise `t - pre_reminder_minutes` anında "<Vakit> vaktine 40 dk kaldı" / "Vakit girişi: 18:15". Beş farz vakit için gelir, Güneş için gelmez. Varsayılan **40 dk**; seçenekler 0 (kapalı), 10, 15, 20, 30, 40, 45, 60 ([[kararlar]] 25). Aynı 60 sn penceresi geçerlidir: uygulama haber anından sonra açılırsa eski haber verilmez. Bildirime tıklayınca yalnızca pencere öne gelir; henüz girmemiş vakit işaretlenemeyeceği için diyalog açılmaz.
4. **Tetikleme:** beş farz vakit `t` için `now >= t` ve `now < t + 60 sn` ve bu `(tarih, vakit)` için bu oturumda bildirim gösterilmemişse bildirim gösterilir (bellekte `set`). 60 sn penceresi, uyku/uyanma sonrası eski vakitlerin toplu bildirim yağdırmasını önler.
5. **Hatırlatma:** `t + reminder_minutes` anında, o vakit hâlâ işaretlenmemişse ("kıldın mı?") ikinci bildirim. İşaretlenmişse gösterilmez. Aynı 60 sn kuralı ve yinelenme koruması geçerlidir.

Bildirim yalnızca `notifications_enabled` açıksa ve konum varsa çalışır. Zaman karşılaştırması her tikte gerçek saatle yapılır; saat dilimi/saat değişimi ve uykudan dönüş kendiliğinden düzelir.

Metinler `app/core/strings.py` (`NotificationStrings`) içindedir ve mobille aynıdır: ezan başlığı "<Vakit> Vakti", gövde "<Vakit> vakti girdi."; hatırlatma başlığı "<Vakit> Namazını Kıldınız mı?", gövde "Namazınızı işaretlemek için dokunun.". Her bildirim vaktin takvim gününü (`day`) ve vakti taşır.

Ayrıntılar (testle doğrulanmış): ilk tik de pencere içindeyse tetikler; `(gün, vakit, tür)` kayıtları 3 günden sonra temizlenir; yeniden başlatmada aynı dakika için bildirim bir kez daha gösterilebilir; "kıldım" veya "kılmadım" denmiş vakit için hatırlatma gitmez; hatırlatma süresi ayardan (5–60 dk) gelir; bir önceki takvim gününün vakitleri de taranır (gece yarısına yakın Yatsı).

## Bildirim gösterimi ve tıklama

`AppTrayIcon.qml` içinde `Qt.labs.platform.SystemTrayIcon.showMessage(başlık, metin)` çağrılır. Qt'nin `messageClicked` sinyali hangi bildirime ait olduğunu taşımaz: `ShellBridge` son bildirimin `(gün, vakit)` bilgisini tutar; tıklanınca pencere öne gelir, Vakitler sayfası bildirimin gününe geçer (`HomeBridge.openDay`) ve o vaktin işaretleme diyaloğu açılır (`HomePage.promptPrayer`). Testlerde `activateLastNotification()` doğrudan çağrılır; gerçek tıklama denenmedi (yukarıdaki tablo).

Eylem düğmesi ("Kıldım" / "Kılmadım" doğrudan bildirimden) bu yolla yoktur. İstenirse ayrı bir Windows toast paketi (örn. `windows-toasts`) denenir; v1 için şart değil.

## Açılışta kaçırılan vakitler

Bilgisayar kapalıyken giren vakitler için bildirim gelmez (60 sn kuralı). Bunun yerine açılışta **bir kez** sorulur ([[kararlar]] 24):

- `MissedPrayerService` uygulama çalışırken en son anı `last_active_at` ayarına **dakikada bir** yazar (saat tikinden, kapanışta zorla) ([[veri-katmani]]).
- Açılışta (`AppContainer.run_startup_tasks`, QML yüklenmeden önce) `son çalışma < vakit <= şimdi` olan, **işaretlenmemiş** (kayıt yok veya `pending`) beş farz vakit aday olur. Takip başlangıcından önceki günler ve son 3 takip gününden eskiler alınmaz (eskiler zaten otomatik kazadır, [[takip-gunu-ve-kaza]]). Sonra son çalışma anı şimdiye alınır: aynı vakitler bir daha sorulmaz.
- Uygulama açıkken giren vakitler sorulmaz; onları hatırlatma bildirimi sorar.
- Pencere görünürken diyalog açılır (`MissedPrayersDialog`): her satırda **Kıldım** / **Kılmadım**, altta **Sonra**. Cevap hemen yazılır ve Vakitler ile Kaza ekranları yenilenir. "Sonra" veya Esc kalanları sormaz; işaretlenmeyenler gün bitince kaza listesine düşer. İlk açılışta autostart sorusu açıksa o cevaplanınca açılır.
- `--autostart` ile gizli açılışta (Windows açılışı) diyalog açılmaz; tepside "İşaretlenmemiş vakitler var" bildirimi çıkar, tıklayınca pencere gelir ve diyalog açılır. `ShellBridge.forgetLastNotification` bu bildirimin tıklamasının eski bir bildirimin diyaloğunu açmasını önler.
- İlk kurulumda `last_active_at` yoktur: hiçbir şey sorulmaz.

## Sistem tepsisi

- Simge: `app/ui/assets/tray.png` (zümrüt zemin, altın 8 köşeli yıldız); `tools/make_icons.py` bunu ve çok boyutlu `app.ico`'yu üretir.
- İpucu: "Namaz Takip  •  Sıradaki: <vakit> <HH:mm>" (sayaçla birlikte güncellenir); şehir yoksa yalnızca "Namaz Takip".
- Menü: **Göster/Gizle**, "Sıradaki: <vakit> <HH:mm>" (pasif satır), **Bildirimler: Açık/Kapalı** (tıklayınca ayarı değiştirir), **Çıkış** (`ShellBridge.requestQuit` → `app.quit`).
- Sol tık veya çift tık: pencereyi göster / öne getir.

## Pencere davranışı

`ApplicationWindow.onClosing`: `close_to_tray` açıksa **ve sistem tepsisi varsa** `close.accepted = false; hide()` ve ilk kapatmada tek seferlik "Namaz Takip tepside çalışıyor" bilgisi (`tray_hint_shown` ayarına yazılır, [[kararlar]] 13); aksi halde `ShellBridge.requestQuit()` ile uygulama kapanır. Tepsi yokken gizlemek uygulamayı erişilmez kılacağı için bu koruma vardır ([[kararlar]] 22). `QGuiApplication.setQuitOnLastWindowClosed(False)`; gerçek çıkış yalnızca `requestQuit` ile olur.

`ayar kapalıyken kapat` ve `tepsi yokken kapat` birim testle, `tepsi varken kapat` gerçek tepsiyle doğrulandı.

## Tek örnek

`app/services/single_instance.py`: `QLockFile` (`%APPDATA%\NamazTakip\NamazTakip-tek-ornek.lock`) ilk örneği belirler, `QLocalServer` (adlandırılmış boru) ikinci örneğin "show" mesajını alır. İkinci başlatma `notify_existing` ile "göster" gönderip 0 koduyla çıkar. **İstisna:** `--autostart` ile açılan ikinci örnek bildirim göndermeden çıkar (Windows açılışı çalışan örneği öne getirmemeli, [[kararlar]] 23). Çökmüş sürecin artık kilidi Qt tarafından eski sayılır ve temizlenir.

Test notu: aynı süreçte `QLocalSocket` yazması sunucunun olay döngüsünü bekler (Windows adlandırılmış boru), bu yüzden ikinci örnek testlerde gerçek alt süreçtir ([[test-stratejisi]]).

## Windows açılışında başlatma

`app/services/autostart_service.py`: `winreg` ile `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` altına `NamazTakip` değeri olarak `"<exe>" --autostart` yazılır / silinir (yönetici izni gerekmez). Kurallar:

- **Kayıt yalnızca paketlenmiş (donmuş) exe için değiştirilir** (`sys.frozen`). Geliştirme ortamında (`python main.py`, testler) ne yazılır ne silinir: kurulu uygulamanın kaydı geliştirmede bozulmasın ([[kararlar]] 23).
- Her açılışta (`AppContainer.run_startup_tasks`) ayar açıksa komut yeniden yazılır (klasör taşınmış olabilir), kapalıysa silinir; ayar yoksa dokunulmaz.
- `--autostart` ile açılınca ve tepsi varsa pencere gizli başlar; tepsi yoksa pencere yine görünür.
- **İlk açılışta soru** ([[kararlar]] 12): `autostart` ayarı yokken, şehir seçildikten sonra pencere görünürken "Windows açılınca başlasın mı?" diyaloğu çıkar. Evet/Hayır cevabı ayara yazılır ve bir daha sorulmaz; Esc cevap sayılmaz, bir sonraki açılışta yeniden sorulur. Gizli başlatmada soru çıkmaz. Ayarlar sayfasındaki anahtar da aynı kaydı değiştirir.
- Kayıt hatası (`OSError`) ayarı geri almaz, loglanır.

## Günlük veritabanı yedeği

Açılışta günde bir kez `%APPDATA%\NamazTakip\backups\namaz_takip-YYYYMMDD.db` ([[veri-katmani]]).

## Uyku ve saat

Uyku sırasında bildirim gelmez; uyanınca yalnızca son 60 sn içinde girmiş vakit bildirilir. İsteğe bağlı iyileştirme: güç olayı (`WM_POWERBROADCAST`) için P012'deki yerel olay süzgeci (`GlobalHotkey`) deseniyle uyanınca anında yeniden eşitleme.

## Sınırlar

- Uygulama kapalıyken veya bilgisayar uykudayken ezan bildirimi gelmez.
- Şehir değiştirilmedikçe vakitler eski şehre göre kalır (seyahatte kullanıcı şehri değiştirmeli).
- Yinelenme koruması bellektedir; yeniden başlatmada aynı dakikaya denk gelen bildirim bir kez daha gösterilebilir (önemsiz).
- İmzasız exe için SmartScreen / Akıllı Uygulama Denetimi uyarıları: [[dagitim]].
