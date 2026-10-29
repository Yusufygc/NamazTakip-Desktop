"""Uygulama giriş noktası: veritabanını açar, container'ı kurar, QML motorunu başlatır."""

import os
import sys

# QML kontrollerinin özelleştirilebilmesi için Basic stil zorunlu.
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from app.container import AppContainer  # noqa: E402
from app.core.database import AppDatabase  # noqa: E402
from app.core.logger import logger, setup_logging  # noqa: E402
from app.version import APP_NAME, __version__  # noqa: E402

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

QML_DIR = os.path.join(BASE_DIR, "app", "ui", "qml")


def build_engine(container: AppContainer) -> QQmlApplicationEngine:
    """QML motorunu kurar, köprüleri bağlar ve ana pencereyi yükler."""
    engine = QQmlApplicationEngine()
    engine.addImportPath(QML_DIR)
    container.register_context_properties(engine)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Main.qml")))
    return engine


def main() -> int:
    setup_logging()
    logger.info("--- %s %s başlatılıyor ---", APP_NAME, __version__)

    app = QGuiApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)

    try:
        container = AppContainer(AppDatabase.open())
    except Exception:
        # Veritabanı açılamadı veya daha yeni sürümle yazılmış: ayrıntı log dosyasında.
        logger.exception("Uygulama başlatılamadı")
        return 1

    engine = build_engine(container)
    if not engine.rootObjects():
        logger.error("QML yüklenemedi.")
        container.shutdown()
        return 1

    app.aboutToQuit.connect(container.shutdown)
    container.start()

    exit_code = app.exec()
    logger.info("Uygulama %s koduyla kapanıyor.", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
