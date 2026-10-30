"""Ortak test ayarları.

Testler gerçek kullanıcı klasörüne (%APPDATA%\\NamazTakip) yazmaz: her test kendi geçici
veri klasörünü kullanır. Yeni bir kalıcılık noktası eklenince yalıtım burada da sağlanmalı.
"""

import os

# Ekransız QML. Yazı tipi klasörü yoksa metin genişlikleri gerçekçi olmaz.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.path.isdir("C:/Windows/Fonts"):
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

import pytest  # noqa: E402

from app.core import paths  # noqa: E402
from app.core.logger import shutdown_logging  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtGui import QGuiApplication

    from app.version import APP_NAME

    app = QGuiApplication.instance() or QGuiApplication([])
    app.setApplicationName(APP_NAME)
    return app


@pytest.fixture(autouse=True)
def fixed_timezone(monkeypatch):
    """Testler makinenin saat diliminden bağımsız çalışır: vakitler UTC+3 (Türkiye) olarak hesaplanır.

    Üretimde `PrayerService` saat dilimi verilmezse sistem saat dilimini kullanır; CI (UTC) ve geliştirme makinesi (UTC+3)
    aynı beklentiyle sınanabilsin diye, `tz` açıkça verilmeyen her `PrayerService` UTC+3 ile kurulur.
    """
    from tests.support import TZ
    from app.services.prayer_service import PrayerService

    original = PrayerService.__init__

    def init(self, *args, **kwargs):
        if "tz" not in kwargs and len(args) < 5:  # settings, prayers, now, time_service, tz
            kwargs["tz"] = TZ
        original(self, *args, **kwargs)

    monkeypatch.setattr(PrayerService, "__init__", init)


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path_factory, monkeypatch):
    folder = tmp_path_factory.mktemp("namaz_takip_data")
    monkeypatch.setenv(paths.DATA_DIR_ENV, str(folder))
    yield folder
    # Log dosyasını kapat: Windows'ta açık dosya geçici klasörün silinmesini engeller.
    shutdown_logging()
