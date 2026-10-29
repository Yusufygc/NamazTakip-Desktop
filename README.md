# Namaz Takip Masaüstü

Mobil Namaz Takip uygulamasının basit Windows sürümü: ezan vakitleri ve geri sayım, namaz işaretleme, kaza takibi, ayarlar. Yığın: Python 3.10 + PySide6/QML + SQLite. Vakit hesabı: `adhanpy`. Dağıtım: PyInstaller (yalnızca kişisel kullanım).

Durum: planlama ve altyapı kurulumu; uygulama kodu henüz yok. Proje bilgisi `docs/wiki/` altındadır, giriş noktası [`docs/wiki/index.md`](docs/wiki/index.md). Çalışma kuralları [`CLAUDE.md`](CLAUDE.md) dosyasındadır.

## Kurulum

```powershell
python -m venv venv                       # Python 3.10.11
venv\Scripts\activate
pip install -r requirements-dev.txt
```
