"""Tek örnek: ikinci başlatma yeni pencere açmaz, çalışan örneğe "göster" isteği gönderip çıkar.

`QLockFile` ilk örneği belirler (çökmüş sürecin artık kilidi Qt tarafından eski sayılıp temizlenir);
`QLocalServer` ikinci örneğin mesajını alır. Kurallar: docs/wiki/bildirim-ve-tepsi.md.
"""

from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from app.core import paths
from app.core.logger import logger

SERVER_NAME = "NamazTakip-tek-ornek"
SHOW_MESSAGE = b"show"


class SingleInstance(QObject):
    showRequested = Signal()

    def __init__(self, name: str = SERVER_NAME, lock_dir: "Path | None" = None, parent: "QObject | None" = None):
        super().__init__(parent)
        self._name = name
        self._lock_path = (lock_dir or paths.app_data_dir()) / f"{name}.lock"
        self._lock: "QLockFile | None" = None
        self._server: "QLocalServer | None" = None

    def try_acquire(self) -> bool:
        """Bu süreç ilk örnekse kilidi alır ve sunucuyu dinlemeye başlar; değilse False."""
        lock = QLockFile(str(self._lock_path))
        if not lock.tryLock(0):
            return False
        self._lock = lock
        QLocalServer.removeServer(self._name)  # çökmüş sürecin artığı
        server = QLocalServer(self)
        if not server.listen(self._name):
            logger.error("Tek örnek sunucusu dinlemeye başlayamadı: %s", server.errorString())
        server.newConnection.connect(self._on_connection)
        self._server = server
        return True

    def notify_existing(self, timeout_ms: int = 1500) -> bool:
        """Çalışan örneğe "göster" gönderir. İletilebildiyse True."""
        socket = QLocalSocket(self)
        socket.connectToServer(self._name)
        if not socket.waitForConnected(timeout_ms):
            logger.warning("Çalışan örneğe bağlanılamadı: %s", socket.errorString())
            return False
        socket.write(SHOW_MESSAGE)
        socket.flush()
        # Veri `flush` ile hemen yazılmış olabilir; o durumda `waitForBytesWritten` False döner.
        delivered = socket.bytesToWrite() == 0 or socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        if socket.state() != QLocalSocket.LocalSocketState.UnconnectedState:
            socket.waitForDisconnected(timeout_ms)
        return delivered

    def release(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._lock is not None:
            self._lock.unlock()
            self._lock = None

    def _on_connection(self) -> None:
        while self._server is not None and self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            socket.readyRead.connect(lambda s=socket: self._on_ready(s))
            socket.disconnected.connect(socket.deleteLater)
            if socket.bytesAvailable():
                self._on_ready(socket)

    def _on_ready(self, socket: QLocalSocket) -> None:
        message = bytes(socket.readAll())
        if SHOW_MESSAGE in message:
            logger.info("Başka bir örnekten gösterme isteği alındı.")
            self.showRequested.emit()
