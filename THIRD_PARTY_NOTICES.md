# Üçüncü taraf bileşenler ve lisansları

Namaz Takip'in kendi lisansı [LICENSE](LICENSE) dosyasındadır (tüm hakları saklıdır); aşağıdaki bileşenler kendi lisansları
altındadır ve bu lisanslar Namaz Takip'in lisansını değiştirmez. Dağıtılan uygulama (PyInstaller paketi) bu bileşenleri içerir.
Bu dosya `python tools/third_party_notices.py` ile üretilir.

## Qt (PySide6 / shiboken6): LGPL-3.0

Arayüz Qt 6 ile (Qt for Python) çizilir; Qt, **GNU LGPL sürüm 3** koşulları altında kullanılır
([metin](https://www.gnu.org/licenses/lgpl-3.0.html)). Uygulama klasör olarak dağıtılır (`--onedir`): Qt kütüphaneleri `_internal`
klasöründe ayrı dosyalardır ve değiştirilmiş bir Qt sürümüyle değiştirilebilir (yeniden bağlama hakkı). Uygulamanın kullanmadığı Qt
modülleri (WebEngine, Qt3D, Charts, Multimedia vb.) paketten çıkarılır; kalanlar değiştirilmez. Qt ve PySide6 kaynak kodu:
<https://code.qt.io> ve <https://pyside.org>. Qt'nin ticari lisansı kullanılmaz.

## Python ve PyInstaller

- **Python** ([PSF License](https://docs.python.org/3/license.html)): paketlenmiş yorumlayıcı ve standart kitaplık.
- **PyInstaller** ([GPL-2.0-or-later, derlenen uygulamanın dağıtımına izin veren özel istisnayla](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt)):
  yalnızca paketleme aracı ve açılış yükleyicisi; paketlenen uygulamaya GPL bulaşmaz.

## Python paketleri

### PySide6 6.11.0

- Lisans: LGPL-3.0-only (Qt for Python)
- Kaynak: <https://pyside.org>

### PySide6-Essentials 6.11.0

- Lisans: LGPL-3.0-only (Qt for Python)
- Kaynak: <https://pyside.org>

### PySide6-Addons 6.11.0

- Lisans: LGPL-3.0-only (Qt for Python)
- Kaynak: <https://pyside.org>

### shiboken6 6.11.0

- Lisans: LGPL-3.0-only (Qt for Python)
- Kaynak: <https://pyside.org>

### adhanpy 1.0.5

- Lisans: MIT
- Kaynak: <https://github.com/alphahm/adhanpy>

