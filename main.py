"""Uygulama giriş noktası: tek örnek denetimi, veritabanı, container ve QML motoru."""

import argparse
import os
import sys
from pathlib import Path

# QML kontrollerinin özelleştirilebilmesi için Basic stil zorunlu.
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication, QIcon  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402

from app.container import AppContainer  # noqa: E402
from app.core.database import AppDatabase  # noqa: E402
from app.core.logger import logger, setup_logging  # noqa: E402
from app.services.single_instance import SingleInstance  # noqa: E402
from app.version import APP_NAME, __version__  # noqa: E402

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

QML_DIR = os.path.join(BASE_DIR, "app", "ui", "qml")
ASSETS_DIR = Path(BASE_DIR) / "app" / "ui" / "assets"
UPDATE_CHECK_DELAY_MS = 3000


def parse_args(argv: list[str]) -> argparse.Namespace:
    """`--autostart`: Windows açılışında başlatıldı; pencere gizli, yalnızca tepside çalışır."""
    parser = argparse.ArgumentParser(prog=APP_NAME, add_help=False)
    parser.add_argument("--autostart", action="store_true")
    args, _unknown = parser.parse_known_args(argv)  # Qt'nin kendi argümanları yok sayılır
    return args


def build_engine(container: AppContainer) -> QQmlApplicationEngine:
    """QML motorunu kurar, köprüleri bağlar ve ana pencereyi yükler."""
    engine = QQmlApplicationEngine()
    engine.addImportPath(QML_DIR)
    container.register_context_properties(engine)
    engine.load(QUrl.fromLocalFile(os.path.join(QML_DIR, "Main.qml")))
    return engine


def main() -> int:
    setup_logging()
    args = parse_args(sys.argv[1:])
    logger.info("--- %s %s başlatılıyor%s ---", APP_NAME, __version__, " (autostart)" if args.autostart else "")

    app = QGuiApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    # Pencere kapatılınca süreç sürer (tepsi); gerçek çıkış `shellBridge.requestQuit` ile olur.
    app.setQuitOnLastWindowClosed(False)
    app.setWindowIcon(QIcon(str(ASSETS_DIR / "app.ico")))

    single = SingleInstance()
    if not single.try_acquire():
        # Windows açılışındaki otomatik başlatma çalışan örneği öne getirmemeli; elle başlatma getirmeli.
        logger.info("Başka bir örnek çalışıyor; %s.", "çıkılıyor" if args.autostart else "gösterme isteği gönderiliyor")
        if not args.autostart:
            single.notify_existing()
        return 0

    try:
        container = AppContainer(AppDatabase.open(), start_hidden=args.autostart, assets_dir=ASSETS_DIR)
    except Exception:
        # Veritabanı açılamadı veya daha yeni sürümle yazılmış: ayrıntı log dosyasında.
        logger.exception("Uygulama başlatılamadı")
        single.release()
        return 1

    single.showRequested.connect(container.shell_bridge.showWindowRequested)
    container.shell_bridge.quitRequested.connect(app.quit)
    container.run_startup_tasks()

    engine = build_engine(container)
    if not engine.rootObjects():
        logger.error("QML yüklenemedi.")
        container.shutdown()
        single.release()
        return 1

    def cleanup() -> None:
        container.shutdown()
        single.release()

    app.aboutToQuit.connect(cleanup)
    container.start()
    # Güncelleme denetimi pencere çizildikten sonra (testler ve `build_engine` ağa çıkmasın diye burada).
    QTimer.singleShot(UPDATE_CHECK_DELAY_MS, container.update_bridge.startupCheck)

    exit_code = app.exec()
    logger.info("Uygulama %s koduyla kapanıyor.", exit_code)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
