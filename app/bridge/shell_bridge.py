"""Pencere kabuğu köprüsü: tepsi bildirimi, bildirime tıklama, gösterme ve çıkış istekleri.

Bridge iş kuralı içermez. Bildirim *kararı* `ClockService`'te verilir; burada yalnızca QML'in tepsi
simgesine iletilir. Kurallar: docs/wiki/bildirim-ve-tepsi.md.
"""

from PySide6.QtCore import Property, QObject, Signal, Slot

from app.services.clock_service import Notification, NotificationKind


class ShellBridge(QObject):
    notificationRequested = Signal(str, str)  # başlık, gövde -> tepsi `showMessage`
    promptRequested = Signal(str, str)  # gün anahtarı, vakit anahtarı -> işaretleme diyaloğu
    showWindowRequested = Signal()  # tek örnek veya tepsi: pencereyi öne getir
    quitRequested = Signal()  # tepsi "Çıkış" veya tepsisiz kapatma

    def __init__(self, start_hidden: bool = False, tray_icon_url: str = "", parent: "QObject | None" = None):
        super().__init__(parent)
        self._start_hidden = start_hidden
        self._tray_icon_url = tray_icon_url
        self._last: "Notification | None" = None

    @Property(bool, constant=True)
    def startHidden(self) -> bool:
        """`--autostart` ile açıldıysa pencere gizli başlar (yalnızca tepsi)."""
        return self._start_hidden

    @Property(str, constant=True)
    def trayIconUrl(self) -> str:
        return self._tray_icon_url

    @Slot(object)
    def on_notification(self, notification: Notification) -> None:
        """Saat servisinden gelir. Tıklama için son bildirim hatırlanır (Qt bildirim tıklamasında yük taşımaz)."""
        self._last = notification
        self.notificationRequested.emit(notification.title, notification.body)

    @Slot()
    def activateLastNotification(self) -> None:
        """Bildirime tıklandı: o vaktin işaretleme diyaloğu ilgili gün için açılır."""
        # Vakitten önceki haberde işaretlenecek bir şey yok: yalnızca pencere öne gelir.
        if self._last is not None and self._last.kind is not NotificationKind.PRE:
            self.promptRequested.emit(self._last.day.isoformat(), self._last.prayer.key)

    @Slot()
    def forgetLastNotification(self) -> None:
        """Tepsiden saat servisi dışı bir bildirim gösterilecek: tıklama eski bildirimin diyaloğunu açmasın."""
        self._last = None

    @Slot()
    def requestQuit(self) -> None:
        self.quitRequested.emit()
