# Namaz Takip Masaüstü

![Sürüm](https://img.shields.io/badge/Version-0.1.0-orange) ![Platform](https://img.shields.io/badge/Platform-Windows-blue)

Ezan vakitlerini gösteren, kıldığınız namazları işaretlemenizi sağlayan ve kaza borcunuzu takip eden sade bir **Windows masaüstü uygulaması**. Bilgisayarınız açıkken sistem tepsisinde sessizce çalışır; vakit girmeden haber verir, vakit girince bildirim gösterir.

Python + PySide6 (QML) + SQLite ile yazıldı. Verileriniz yalnızca kendi bilgisayarınızda durur; hesap, internet bağlantısı ya da sunucu gerekmez.

<p align="center">
  <img src="docs/screenshots/vakitler.png" alt="Vakitler ekranı" width="820">
</p>

## Özellikler

- **Vakitler ve geri sayım.** Sabah, Güneş, Öğle, İkindi, Akşam ve Yatsı saatleri; sıradaki vakte kalan süre saniye saniye akar. Önceki ve sonraki günlere göz atabilirsiniz.
- **Namaz işaretleme.** Her vakit için *Kıldım* (isterseniz *cemaatle*) veya *Kılmadım*. Geçmiş günleri de düzeltebilirsiniz.
- **Kaza takibi.** İşaretlemediğiniz ya da "kılmadım" dediğiniz vakitler otomatik olarak kaza listesine düşer. Geçmiş yıllardan kalan borcu yıl/ay/gün olarak hesaplatabilir, günlük hedef belirleyip tahmini bitiş tarihini görebilirsiniz.
- **Akıllı bildirimler.** Vakitten önce haber (varsayılan 40 dk), vakit girince ezan bildirimi, işaretlemediyseniz "kıldınız mı?" hatırlatması. Bildirime tıklayınca ilgili vaktin işaretleme penceresi açılır.
- **Kapalıyken kaçan vakitler.** Bilgisayar kapalıyken giren vakitler için bir sonraki açılışta tek seferlik "bu vakitleri kıldınız mı?" sorusu çıkar.
- **Tepside çalışır.** Pencereyi kapatınca uygulama tepsiye iner; Windows açılışında kendiliğinden başlayabilir (isteğe bağlı).
- **81 il, 6 hesaplama yöntemi.** Varsayılan Diyanet; Müslüman Dünya Birliği, Mısır, Karaçi, Ümmü'l-Kura ve ISNA da seçilebilir.
- **5 tema.** Selçuklu Zümrüdü, Koyu, Okyanus, Gül Kurusu ve Altın.
- **Günlük yedek.** Veritabanı her gün otomatik yedeklenir (son 7 yedek tutulur).
- **Kendini güncelleyebilir.** Açılışta yeni sürüm olup olmadığına bakar; varsa sorar. Güncelleme indirilir, bütünlüğü (SHA-256) doğrulanır ve verileriniz korunarak kurulur.

## Ekran görüntüleri

| | |
|---|---|
| ![Namaz işaretleme](docs/screenshots/isaretleme.png) | ![Kaza takibi](docs/screenshots/kaza.png) |
| **İşaretleme:** vakte tıklayın, *Kıldım* / *Kılmadım* deyin. | **Kaza:** otomatik tespit edilen vakitler ve geçmiş borç planı. |
| ![Açılış sorusu](docs/screenshots/acilis-sorusu.png) | ![Ayarlar](docs/screenshots/ayarlar.png) |
| **Açılış sorusu:** bilgisayar kapalıyken giren vakitler. | **Ayarlar:** bildirimler, konum, hesaplama yöntemi, tema. |

<p align="center">
  <img src="docs/screenshots/vakitler-koyu.png" alt="Koyu tema" width="640"><br>
  <sub>Koyu tema</sub>
</p>

## Kullanım

### İlk açılış

1. Uygulamayı açın; **şehrinizi** seçin (arama kutusu Türkçe karakterlerden bağımsız çalışır).
2. Windows açılınca başlasın mı sorusuna cevap verin (sonradan Ayarlar'dan değiştirilebilir).
3. Vakitler ekranı hazır: sıradaki vakit ve geri sayım en üstte görünür.

### Günlük kullanım

- Bir vakte tıklayın → **Kıldım** (cemaatle kıldıysanız kutuyu işaretleyin) veya **Kılmadım**. Yanlış işaretlerseniz aynı vakte yeniden tıklayıp düzeltin.
- Kaza ekranında bir vakti kaza ettiğinizde **Kaza Et**'e basın; listeden çıkar.
- Geçmiş yıllardan kalan borcunuz için **Geçmiş Borç Hesapla / Hedef Belirle**'yi kullanın; kıldıkça **1 Kaza Düş** ile sayacı azaltın.
- Klavye kısayolları: `Ctrl+1` Vakitler, `Ctrl+2` Kaza, `Ctrl+3` Ayarlar.

### Gün sınırı

Gece yarısından sonra kıldığınız Yatsı "dünün" namazı sayılır. Takip günü, Sabah vaktinde (en geç 04:00'te) değişir.

### Bildirimler ve tepsi

Uygulama **çalışırken** bildirim verir. Pencereyi kapatmak uygulamayı kapatmaz, tepsiye indirir; tamamen kapatmak için tepsi simgesine sağ tıklayıp **Çıkış**'ı seçin. Tepsi menüsünden pencereyi gösterebilir, bildirimleri açıp kapatabilirsiniz.

Uygulama kapalıyken ya da bilgisayar uykudayken bildirim gelmez. Bildirimleri güvenilir almak için *Windows açılışında başlat* seçeneğini açık tutun.

### Verileriniz

Her şey `%APPDATA%\NamazTakip\` klasöründedir:

| Dosya | İçerik |
|---|---|
| `namaz_takip.db` | İşaretleriniz ve ayarlarınız (SQLite) |
| `backups\` | Günlük yedekler (son 7) |
| `logs\` | Günlük dosyaları |

Uygulamayı silmek verilerinizi silmez. Yedeği geri yüklemek için uygulamayı kapatıp yedek dosyasını `namaz_takip.db` adıyla kopyalamanız yeterlidir.

## Kurulum

Henüz GitHub'da hazır bir kurulum dosyası yayınlanmıyor; uygulamayı kaynaktan çalıştırabilir veya kurulum dosyasını kendiniz üretebilirsiniz. Gereken: **Windows** ve **Python 3.10**.

```powershell
git clone https://github.com/Yusufygc/NamazTakip-Desktop.git
cd NamazTakip-Desktop
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
python main.py
```

### Kurulum dosyası üretme

Gereken: [Inno Setup 6](https://jrsoftware.org/isdl.php).

```powershell
pip install -r requirements-build.txt
python build_installer.py
```

Çıktı `dist\installer\NamazTakip-Setup-X.Y.Z.exe` olur (yaklaşık 37 MB). Çalıştırınca uygulama kullanıcıya özel kurulur (yönetici izni gerekmez), Başlat menüsüne eklenir; kaldırınca verileriniz silinmez. İçindeki `NamazTakip.exe` her sürümde bayt bayt aynıdır ("kararlı exe"): imzasız dosyaları sürüm sürüm yeniden değerlendiren Windows Akıllı Uygulama Denetimi'ne takılma riskini azaltır. Ayrıntı: [`docs/wiki/dagitim.md`](docs/wiki/dagitim.md).

İsteğe bağlı taşınabilir tek dosya exe: `python tools/build_onefile.py` → `dist\portable\NamazTakip.exe` (her açılışta geçici klasöre açılır, pencere birkaç saniyede görünür; kararlı exe değildir).

> İmzasız bir exe olduğundan Windows SmartScreen / Akıllı Uygulama Denetimi uyarı verebilir.

## Nasıl çalışıyor?

- **Vakit hesabı** [`adhanpy`](https://pypi.org/project/adhanpy/) ile yapılır, Diyanet kurallarına göre (yuvarlama ve Güneş için güvenlik payı dahil). Çıktılar, mobil uygulamanın ürettiği 1060 satırlık bir referans tabloyla saniyesine kadar karşılaştırılır (`tests/data/golden_times.json`).
- **Kaza listesi saklanmaz, türetilir.** Her gün için beş vakit incelenir; kılınmamış veya işaretlenmemiş geçmiş vakitler kaza olur. İşaretlenmeyen bir günü sonradan düzeltmek listeyi kendiliğinden günceller.
- **Katmanlı mimari.** `ui/qml → bridge → services → core/repositories → core/domain`; ters yön yasak ve testle denetlenir. İş kuralları Qt'den bağımsız saf Python'dur.
- **Test.** 460'ı aşkın test: iş kuralları, SQLite, servisler, gerçek QML arayüzü (ekransız), kontrast (WCAG AA) ve mimari kuralları.

Ayrıntılı proje bilgisi [`docs/wiki/`](docs/wiki/index.md) altındadır: mimari, vakit hesabı, kaza kuralları, veri katmanı, bildirim/tepsi, dağıtım ve alınan kararlar.

## Geliştirme

```powershell
venv\Scripts\activate
python main.py                # çalıştır
python -m pytest              # testler
python -m ruff check .        # lint
python build_installer.py     # kurulum dosyası üret
```

| Klasör | İçerik |
|---|---|
| `app/core/domain/` | Saf iş kuralları: vakit hesabı, takip günü, kaza |
| `app/core/` | SQLite, ayar ve işaret depoları, yedek, günlük, metinler |
| `app/services/` | Ayar, vakit, kaza, saat, autostart, tek örnek servisleri |
| `app/bridge/` | Python ↔ QML köprüleri |
| `app/ui/qml/` | Arayüz (sayfalar, bileşenler, temalar) |
| `tests/` | Testler |
| `packaging/` | Kurulum betiği (Inno), sabit giriş betiği, onaylı exe özeti |
| `tools/` | Simge üretimi, taşınabilir exe betiği |
| `docs/wiki/` | Proje bilgi tabanı |

## Gizlilik

Uygulama hesap istemez ve verilerinizi hiçbir yere göndermez. **Tek ağ isteği** güncelleme denetimidir: açılışta GitHub'a "en son sürüm hangisi?" diye sorulur (`api.github.com/repos/Yusufygc/NamazTakip-Desktop/releases/latest`). Bu istekte işaretleriniz, şehriniz ya da herhangi bir kimlik/kullanım bilgisi gönderilmez; GitHub her web isteğinde olduğu gibi yalnızca isteğin geldiği IP adresini görür. Kapatmak için Ayarlar → Güncellemeler → "Açılışta güncellemeyi denetle" anahtarını kapatın ya da `NAMAZ_TAKIP_NO_UPDATE_CHECK=1` ortam değişkenini ayarlayın. Kurulum dosyası yalnızca siz "Güncelle" derseniz indirilir.

## Sınırlar

- Yalnızca Windows (Windows 11'de geliştirildi ve denendi).
- Uygulama kapalıyken ya da bilgisayar uykudayken bildirim gelmez.
- Vakitler seçili şehre göre hesaplanır; seyahatte şehri kendiniz değiştirmelisiniz. Konum otomatik bulunmaz.
- Veriler eşitlenmez; mobil uygulamayla bağlantı yoktur.

## Kullanılan kütüphaneler

[PySide6](https://doc.qt.io/qtforpython-6/) (Qt, LGPL), [adhanpy](https://pypi.org/project/adhanpy/), [PyInstaller](https://pyinstaller.org/), Inno Setup, pytest ve ruff. Üçüncü taraf lisanslar: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Lisans

Tüm hakları saklıdır ([`LICENSE`](LICENSE)). Kod görüntülenebilir, ancak yazılı izin olmadan kullanılamaz ve dağıtılamaz.
