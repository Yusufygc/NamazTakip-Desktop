"""Güncelleme köprüsü: sessiz açılış denetimi, "Yeni sürüm var" penceresi ve Ayarlar kartı.

Bridge iş kuralı içermez: denetim, indirme ve kurulum `update_service`'tedir; burada yalnızca arka plan iş parçacığı,
bekleme/yeniden deneme ve QML'e açılan durum vardır. "Güncelle": kurulum dosyası indirilir, SHA-256 doğrulanır, kurulum başlatılır
ve uygulama kapanır (`quitRequested`). Kurallar: docs/wiki/guncelleme.md
"""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Property, QObject, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from app.core.logger import logger
from app.core.strings import UpdateStrings
from app.services import update_service
from app.services.settings_service import SettingsService
from app.services.update_service import InstallerBlockedError, UpdateCheckError, UpdateInfo
from app.version import RELEASE_REPO, __version__

RETRY_INTERVAL_MS = 15_000  # Windows engeli bir süre sonra kalkabiliyor (gözlem): 15 sn'de bir yeniden dene
RETRY_LIMIT = 40  # 40 x 15 sn = 10 dk; sonra dosya Gezgin'de gösterilir


def reveal_in_explorer(path: Path) -> None:
    """Dosyayı Gezgin'de seçili gösterir (kabuk yok: tek komut dizesi, adres tırnaklı)."""
    subprocess.Popen(f'explorer.exe /select,"{path}"')


class UpdateWorker(QThread):
    """Arka planda tek bir güncelleme denetimi (ağ beklerken arayüz donmaz)."""

    finished_check = Signal(object)  # UpdateInfo | None
    failed = Signal(str)

    def __init__(self, check: Callable[[], "UpdateInfo | None"]):
        super().__init__()
        self._check = check

    def run(self) -> None:
        try:
            self.finished_check.emit(self._check())
        except UpdateCheckError as error:
            self.failed.emit(str(error))
        except Exception:  # noqa: BLE001 - beklenmeyen hata arayüzü düşürmemeli; ayrıntı log'da
            logger.exception("Güncelleme denetimi beklenmedik şekilde başarısız")
            self.failed.emit(UpdateStrings.CHECK_FAILED)


class DownloadWorker(QThread):
    """Arka planda kurulum dosyasını indirir ve doğrular; ilerleme yüzdesini bildirir."""

    progress = Signal(int)
    downloaded = Signal(str)  # indirilen kurulum dosyasının yolu
    failed = Signal(str)

    def __init__(self, download: Callable[[UpdateInfo, Callable[[int], None]], Path], info: UpdateInfo):
        super().__init__()
        self._download = download
        self._info = info

    def run(self) -> None:
        try:
            self.downloaded.emit(str(self._download(self._info, self.progress.emit)))
        except UpdateCheckError as error:
            self.failed.emit(str(error))
        except Exception:  # noqa: BLE001 - beklenmeyen hata arayüzü düşürmemeli; ayrıntı log'da
            logger.exception("Güncelleme indirilemedi")
            self.failed.emit(UpdateStrings.DOWNLOAD_FAILED)


class UpdateBridge(QObject):
    stateChanged = Signal()
    popupRequested = Signal()  # yeni sürüm bulundu: pencere açılmalı
    quitRequested = Signal()  # kurulum başlatıldı: uygulama kapanmalı

    def __init__(
        self,
        settings: SettingsService,
        check: "Callable[[], UpdateInfo | None] | None" = None,
        download: "Callable[[UpdateInfo, Callable[[int], None]], Path] | None" = None,
        launcher: "Callable[[Path], None] | None" = None,
        revealer: "Callable[[Path], None] | None" = None,
        retry_interval_ms: int = RETRY_INTERVAL_MS,
        retry_limit: int = RETRY_LIMIT,
        installable: "bool | None" = None,
        parent: "QObject | None" = None,
    ):
        super().__init__(parent)
        self._settings = settings
        self._check = check or (lambda: update_service.check_for_update(__version__, RELEASE_REPO))
        self._download = download or update_service.download_installer
        self._launcher = launcher or update_service.launch_installer
        self._revealer = revealer or reveal_in_explorer
        # Geliştirme ortamında (`python main.py`) kurulum başlatılmaz; sürüm sayfası açılır.
        self._installable = bool(getattr(sys, "frozen", False)) if installable is None else installable
        self._retry_limit = retry_limit
        self._retries_left = 0
        self._waiting = False
        self._pending: "Path | None" = None
        self._retry_timer = QTimer(self)
        self._retry_timer.setInterval(retry_interval_ms)
        self._retry_timer.timeout.connect(self._try_launch)
        self._downloading = False
        self._progress = 0
        self._error = ""
        self._worker: "QThread | None" = None
        self._manual = False
        self._checking = False
        self._info: "UpdateInfo | None" = None
        self._status = ""

    # ---- Özellikler ----------------------------------------------------------------------

    @Property(str, constant=True)
    def currentVersion(self) -> str:
        return __version__

    @Property(bool, notify=stateChanged)
    def checking(self) -> bool:
        return self._checking

    @Property(bool, notify=stateChanged)
    def updateAvailable(self) -> bool:
        return self._info is not None

    @Property(str, notify=stateChanged)
    def latestVersion(self) -> str:
        return self._info.version if self._info else ""

    @Property(str, notify=stateChanged)
    def releaseNotes(self) -> str:
        return self._info.notes if self._info else ""

    @Property(str, notify=stateChanged)
    def publishedDate(self) -> str:
        return self._info.published if self._info else ""

    @Property(str, notify=stateChanged)
    def installerLabel(self) -> str:
        """Kurulum dosyasının adı ve boyutu; kurulamıyorsa sürüm sayfası açılacağı belirtilir."""
        if not self._info:
            return ""
        if not self.canInstall:
            return UpdateStrings.RELEASE_PAGE_HINT
        megabytes = f", {self._info.size / (1024 * 1024):.0f} MB" if self._info.size else ""
        return f"{self._info.asset_name}{megabytes}"

    @Property(str, notify=stateChanged)
    def statusText(self) -> str:
        return self._status

    @Property(bool, notify=stateChanged)
    def isDownloading(self) -> bool:
        return self._downloading

    @Property(int, notify=stateChanged)
    def downloadProgress(self) -> int:
        return self._progress

    @Property(str, notify=stateChanged)
    def errorMessage(self) -> str:
        return self._error

    @Property(bool, notify=stateChanged)
    def isWaitingForWindows(self) -> bool:
        """Windows kurulum dosyasını engelledi; engel kalkana dek otomatik yeniden deneniyor."""
        return self._waiting

    @Property(bool, notify=stateChanged)
    def canInstall(self) -> bool:
        """Kurulum burada başlatılabilir mi: Release'te kurulum dosyası var ve uygulama paketlenmiş çalışıyor."""
        return bool(self._info and self._info.download_url and self._installable)

    # ---- Denetim ---------------------------------------------------------------------------

    def _start(self, manual: bool) -> None:
        if self._checking:
            return
        self._manual = manual
        self._checking = True
        self._status = UpdateStrings.CHECKING if manual else ""
        self.stateChanged.emit()
        worker = UpdateWorker(self._check)
        worker.finished_check.connect(self._on_checked)
        worker.failed.connect(self._on_failed)
        self._worker = worker
        worker.start()

    @Slot()
    def startupCheck(self) -> None:
        """Açılışta sessiz denetim (kapalıysa hiç ağ isteği yapılmaz). Önceki güncellemenin artıklarını da temizler."""
        update_service.cleanup_update_directory()
        if self._settings.settings.update_check_enabled and not update_service.updates_disabled_by_environment():
            self._start(manual=False)

    @Slot()
    def checkNow(self) -> None:
        self._start(manual=True)

    def _on_checked(self, info: "UpdateInfo | None") -> None:
        self._checking = False
        self._info = info
        if info is None:
            self._status = UpdateStrings.up_to_date(__version__) if self._manual else ""
        else:
            self._status = UpdateStrings.new_version(info.version)
        self.stateChanged.emit()
        if info is not None and (self._manual or info.version != self._settings.update_skipped_version):
            self.popupRequested.emit()  # atlanan sürüm yalnızca açılışta sessiz kalır, elle denetimde gösterilir

    def _on_failed(self, message: str) -> None:
        self._checking = False
        self._status = message if self._manual else ""
        self.stateChanged.emit()

    # ---- Kullanıcı eylemleri ------------------------------------------------------------------

    @Slot()
    def skipVersion(self) -> None:
        if self._info:
            self._settings.set_update_skipped_version(self._info.version)

    @Slot()
    def startUpdate(self) -> None:
        """Kurulum dosyasını indirir ve doğrular; sonra kurulum başlar ve uygulama kapanır."""
        if self._info is None or self._downloading:
            return
        if not self.canInstall:
            self.openReleasePage()  # kurulum dosyası yok ya da paketlenmemiş çalışma: sürüm sayfası açılır
            return
        self._error = ""
        self._progress = 0
        self._downloading = True
        self.stateChanged.emit()
        worker = DownloadWorker(self._download, self._info)
        worker.progress.connect(self._on_progress)
        worker.downloaded.connect(self._on_downloaded)
        worker.failed.connect(self._on_download_failed)
        self._worker = worker
        worker.start()

    def _on_progress(self, percent: int) -> None:
        self._progress = percent
        self.stateChanged.emit()

    def _on_downloaded(self, path: str) -> None:
        self._pending = Path(path)
        self._retries_left = self._retry_limit
        self._try_launch()

    def _try_launch(self) -> None:
        """Kurulumu başlatır. Windows engellerse (Akıllı Uygulama Denetimi) dosya indirilmiş ve doğrulanmış kalır: engel
        kalkana dek aralıklarla yeniden denenir, süre dolarsa dosya Gezgin'de gösterilir (elle kurulum)."""
        if self._pending is None:
            return
        try:
            self._launcher(self._pending)
        except InstallerBlockedError as error:
            if self._retries_left > 0:
                self._waiting = True
                self._error = UpdateStrings.WAITING_FOR_WINDOWS
                self._retries_left -= 1
                self._retry_timer.start()
                self.stateChanged.emit()
                return
            self._give_up(error)
            return
        except (UpdateCheckError, OSError) as error:
            self._stop_waiting()
            self._on_download_failed(str(error) if isinstance(error, UpdateCheckError) else UpdateStrings.INSTALL_FAILED)
            return
        self._stop_waiting()
        self.quitRequested.emit()

    def _stop_waiting(self) -> None:
        self._retry_timer.stop()
        self._waiting = False

    def _give_up(self, error: InstallerBlockedError) -> None:
        self._stop_waiting()
        try:
            self._revealer(error.path)
        except OSError:
            logger.warning("Gezgin açılamadı", exc_info=True)
        self._on_download_failed(str(error))

    @Slot()
    def stopWaiting(self) -> None:
        """Beklemeyi bırakır: dosya Gezgin'de gösterilir, kullanıcı elle kurar."""
        if self._waiting and self._pending is not None:
            self._give_up(InstallerBlockedError(self._pending))

    def _on_download_failed(self, message: str) -> None:
        self._downloading = False
        self._error = message
        self.stateChanged.emit()

    @Slot()
    def openReleasePage(self) -> None:
        if self._info:
            QDesktopServices.openUrl(QUrl(self._info.page_url))
