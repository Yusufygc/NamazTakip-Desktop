"""Açılış sorusu köprüsü: uygulama kapalıyken giren, işaretlenmemiş vakitler.

Bridge iş kuralı içermez; aday bulma `MissedPrayerService`'tedir. Kurallar: docs/wiki/bildirim-ve-tepsi.md.
"""

from PySide6.QtCore import Property, QObject, Signal, Slot

from app.core.clock import Clock
from app.core.domain.prayer import PrayerType
from app.core.formatters import format_time
from app.core.logger import logger
from app.core.strings import DateStrings, PrayerStrings
from app.services.missed_prayer_service import MissedPrayer, MissedPrayerService


class MissedBridge(QObject):
    changed = Signal()
    recordsChanged = Signal()  # bir cevap yazıldı; Vakitler ve Kaza ekranları yenilenmeli

    def __init__(self, service: MissedPrayerService, now: Clock, parent: "QObject | None" = None):
        super().__init__(parent)
        self._service = service
        self._now = now
        self._items: list[MissedPrayer] = []

    @Slot()
    def load(self) -> None:
        """Adayları bulur ve son çalışma anını şimdiye alır (aynı vakitler bir daha sorulmaz)."""
        now = self._now()
        self._items = self._service.find(now)
        self._service.touch(now, force=True)
        self.changed.emit()

    @Property(int, notify=changed)
    def count(self) -> int:
        return len(self._items)

    @Property("QVariantList", notify=changed)
    def items(self) -> list:
        return [
            {
                "dayKey": item.day.isoformat(),
                "prayerKey": item.prayer.key,
                "name": PrayerStrings.name(item.prayer),
                "dateLabel": DateStrings.long(item.day),
                "timeLabel": format_time(item.moment),
            }
            for item in self._items
        ]

    @Slot(str, str, bool, result=bool)
    def answer(self, day_key: str, prayer_key: str, performed: bool) -> bool:
        target = next(
            (item for item in self._items if item.day.isoformat() == day_key and item.prayer.key == prayer_key), None
        )
        if target is None:
            logger.warning("Bilinmeyen işaretlenmemiş vakit: %r %r", day_key, prayer_key)
            return False
        try:
            PrayerType.from_key(prayer_key)
            self._service.answer(target.day, target.prayer, performed)
        except ValueError as error:
            logger.warning("İşaretlenmemiş vakit yazılamadı: %s", error)
            return False
        self._items = [item for item in self._items if item is not target]
        self.changed.emit()
        self.recordsChanged.emit()
        return True

    @Slot()
    def dismiss(self) -> None:
        """"Sonra": kalanlar sorulmaz, işaretlenmezse zamanla kaza olur."""
        if self._items:
            self._items = []
            self.changed.emit()
