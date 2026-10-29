# Bildirim, Tepsi ve Arka Plan

Mobilde bildirimler işletim sistemine önceden planlanır. Masaüstünde buna gerek yoktur: uygulama bilgisayar açıkken **tepside çalışır** ve vakit girince kendisi bildirim gösterir. Uygulama kapalıysa bildirim gelmez; bu bilinçli bir sınırdır ([[kararlar]] 4). Katman: `services` ([[mimari]]).

> **Doğrulanmadı:** Bu sayfadaki Windows davranışlarının hiçbiri gerçek makinede denenmedi (toast görünümü, tıklama, Rahatsız Etmeyin, autostart). Faz 0'daki kısa deneme ve Faz 7 bunları doğrular ([[yol-haritasi]]). Denenince bu sayfa güncellenir.

## Saat servisi (`ClockService`)

**Durum:** karar mantığı yazıldı ve test edildi (`app/services/clock_service.py`, Faz 3). `ClockLogic` saf Python'dur: sahte saatle `tick(now)` çağrılır ve `Tick` (takip günü, gün değişti mi, sıradaki vakit, kalan süre, bildirimler) döner. `ClockService` onu 1 sn'lik `QTimer` ile sürer ve `ticked` / `notification` sinyallerini yayınlar; mantık hatası olursa loglar ve zamanlayıcı düşmez. **Bildirimin ekranda gösterilmesi (tepsi `showMessage`) henüz yok** (Faz 7): `notification` sinyaline bağlanacak.

Tek `QTimer`, 1 saniye. Her tikte:

1. `tracking_day(şimdi)` hesaplanır; gün değiştiyse bridge'ler yenilenir ([[takip-gunu-ve-kaza]]).
2. Sıradaki vakit ve geri sayım güncellenir. **Vakitler (tarih, konum, yöntem) anahtarıyla önbelleğe alınır**; her saniye yeniden hesaplanmaz (hesap iki kez `precision` ile çalışır, pahalıdır).
3. **Tetikleme:** beş farz vakit `t` için `now >= t` ve `now < t + 60 sn` ve bu `(tarih, vakit)` için bu oturumda bildirim gösterilmemişse bildirim gösterilir ve kayıt altına alınır (bellekte `set`). 60 sn penceresi, uyku/uyanma sonrası eski vakitlerin toplu bildirim yağdırmasını önler.
4. **Hatırlatma:** `t + reminder_minutes` anında, o vakit hâlâ işaretlenmemişse ("kıldın mı?") ikinci bildirim. İşaretlenmişse gösterilmez. Aynı 60 sn kuralı ve yinelenme koruması geçerlidir.

Bildirim yalnızca `notifications_enabled` açıksa ve konum varsa çalışır. Zaman karşılaştırması her tikte gerçek saatle yapılır; bu yüzden saat dilimi/saat değişimi ve uykudan dönüş kendiliğinden düzelir. Sabah bildirimi dünkü Yatsı işaretlenmediyse onu da sorabilir (isteğe bağlı).

Metinler `app/core/strings.py` (`NotificationStrings`) içindedir ve mobille aynıdır: ezan başlığı "<Vakit> Vakti", gövde "<Vakit> vakti girdi."; hatırlatma başlığı "<Vakit> Namazını Kıldınız mı?", gövde "Namazınızı işaretlemek için dokunun.". Her bildirim, vaktin takvim gününü (`day`) ve vakti taşır; tıklanınca işaretleme diyaloğu bu gün için açılır (`HomeBridge.openDay`).

Ayrıntılar (testle doğrulanmış): ilk tik de pencere içindeyse tetikler (geç başlayan tik); `(gün, vakit, tür)` kayıtları bellekte tutulur ve 3 günden eskileri temizlenir; yeniden başlatmada aynı dakika için bildirim bir kez daha gösterilebilir; "kıldım" veya "kılmadım" denmiş vakit için hatırlatma gitmez; hatırlatma süresi ayardan (5–60 dk) gelir; bir önceki takvim gününün vakitleri de taranır (gece yarısına yakın Yatsı).

## Bildirim gösterimi

Plan: `Qt.labs.platform.SystemTrayIcon.showMessage(başlık, metin)` ve `messageClicked` sinyali (P012 zaten aynı bileşeni tepsi için kullanıyor). Ek paket ve uygulama kimliği ayarı gerektirmemesi artısıdır. Sınırlar / doğrulanacaklar:

- Tıklama sinyali hangi bildirime ait olduğunu taşımaz: gösterilen son bildirimin `(tarih, vakit)` bilgisi bridge'de tutulur, tıklanınca pencere öne gelir ve o vakit için işaretleme diyaloğu açılır.
- Eylem düğmesi ("Kıldım" / "Kılmadım" doğrudan bildirimden) bu yolla yoktur. İstenirse ayrı bir Windows toast paketi (örn. `windows-toasts`) denenir; v1 için şart değil.
- Windows 11'de toast'ın gerçekten görünmesi, Odaklanma Yardımı / Rahatsız Etmeyin açık ve kapalıyken davranışı, geliştirme ile paketlenmiş exe arasındaki fark: **doğrulanmadı**.

## Sistem tepsisi

- Simge: `.ico`; araç ipucu "Namaz Takip • Sıradaki: <vakit> <HH:mm>" (dakikada bir güncellenir).
- Menü: **Göster/Gizle**, "Sıradaki: <vakit> <HH:mm>" (pasif satır), **Bildirimler: Açık/Kapalı**, **Çıkış**.
- Çift tık (P012 deseni) veya sol tık: pencereyi göster / öne getir. Gerçek çıkış yalnızca menüdeki **Çıkış**'tır.

## Pencere davranışı

`ApplicationWindow.onClosing` içinde `close_to_tray` açıksa `close.accepted = false; hide()`; kapalıysa uygulama kapanır. `QGuiApplication.setQuitOnLastWindowClosed(False)` (P012'de var). İlk kapatmada tek seferlik "Namaz Takip tepside çalışmaya devam ediyor" bilgisi gösterilir; gösterildiği `tray_hint_shown` ayarına yazılır ([[kararlar]] 13).

**Tek örnek:** ikinci başlatma mevcut pencereyi öne getirir (`QLockFile` + `QLocalServer`; P012'de yok, eklenir).

## Windows açılışında başlatma

`winreg` ile `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` altına `--autostart` argümanlı komut yazılır / silinir (yönetici izni gerekmez). Kurallar:

- Yol yalnızca paketlenmiş (donmuş) exe için yazılır (`sys.executable`); geliştirme ortamının yolu kayda **yazılmaz**.
- Klasör taşınırsa kayıt bozulur: her açılışta kayıt açıksa yol kontrol edilip yeniden yazılır.
- `--autostart` ile açılınca pencere gizli başlar (yalnızca tepsi).
- Varsayılan yoktur: `autostart` ayarı yokken ilk açılışta soru gösterilir ve cevap kaydedilir ([[kararlar]] 12). İlk açılışta `--autostart` bağımsız değişkeni gelmez, pencere normal açılır.

## Uyku ve saat

Uyku sırasında bildirim gelmez; uyanınca yalnızca son 60 sn içinde girmiş vakit bildirilir. İsteğe bağlı iyileştirme: güç olayı (`WM_POWERBROADCAST`) için P012'deki yerel olay süzgeci (`GlobalHotkey`) deseniyle uyanınca anında yeniden eşitleme.

## Sınırlar

- Uygulama kapalıyken veya bilgisayar uykudayken ezan bildirimi gelmez.
- Şehir değiştirilmedikçe vakitler eski şehre göre kalır (seyahatte kullanıcı şehri değiştirmeli).
- Yinelenme koruması bellektedir; yeniden başlatmada aynı dakikaya denk gelen bildirim bir kez daha gösterilebilir (önemsiz).
- İmzasız exe için SmartScreen / Akıllı Uygulama Denetimi uyarıları: [[dagitim]].
