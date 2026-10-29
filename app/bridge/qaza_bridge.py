"""Kaza ekranı köprüsü: özet, geçmiş borç ve gün kartları. İş kuralı `QazaService`'tedir."""

from datetime import date

from PySide6.QtCore import Property, QObject, Signal, Slot

from app.core.domain.models import QazaItem
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.logger import logger
from app.core.strings import DateStrings, PrayerStrings
from app.services.qaza_service import QazaService

NO_ESTIMATE = -1


class QazaBridge(QObject):
    stateChanged = Signal()
    changed = Signal()  # kaza etme veya plan değişti; diğer ekranlar yenilenmeli

    def __init__(self, qaza: QazaService, parent: "QObject | None" = None):
        super().__init__(parent)
        self._qaza = qaza
        self._summary: dict = {}
        self._backlog: list[dict] = []
        self._groups: list[dict] = []
        self._is_empty = True
        self.refresh()

    @Slot()
    def refresh(self) -> None:
        items = self._qaza.items()
        summary = self._qaza.summary()
        plan = self._qaza.plan

        self._summary = {
            "autoCount": summary.auto_count,
            "backlogTotal": summary.backlog_total,
            "grandTotal": summary.grand_total,
            "dailyTarget": summary.daily_target,
            "estimatedDays": NO_ESTIMATE if summary.estimated_days is None else summary.estimated_days,
            "estimatedDateKey": "" if summary.estimated_date is None else summary.estimated_date.isoformat(),
            "estimatedDateLabel": "" if summary.estimated_date is None else DateStrings.long(summary.estimated_date),
        }
        self._backlog = [
            {"key": prayer.key, "name": PrayerStrings.name(prayer), "count": plan.count_for(prayer)}
            for prayer in PrayerType
        ]
        self._groups = self._group(items)
        self._is_empty = not items and plan.total_backlog == 0
        self.stateChanged.emit()

    @staticmethod
    def _group(items: list[QazaItem]) -> list[dict]:
        groups: dict[date, list[QazaItem]] = {}
        for item in items:  # sıra korunur: tarih azalan, vakit artan
            groups.setdefault(item.date, []).append(item)
        return [
            {
                "dateKey": day.isoformat(),
                "dateLabel": DateStrings.long(day),
                "count": len(day_items),
                "items": [
                    {
                        "prayerKey": item.prayer.key,
                        "prayerName": PrayerStrings.name(item.prayer),
                        "autoDetected": item.status == PrayerStatus.PENDING,
                    }
                    for item in day_items
                ],
            }
            for day, day_items in groups.items()
        ]

    # ---- QML'e açılan özellikler -------------------------------------------------------

    @Property("QVariantMap", notify=stateChanged)
    def summary(self) -> dict:
        return self._summary

    @Property("QVariantList", notify=stateChanged)
    def backlog(self) -> list:
        return self._backlog

    @Property("QVariantList", notify=stateChanged)
    def groups(self) -> list:
        return self._groups

    @Property(bool, notify=stateChanged)
    def isEmpty(self) -> bool:
        return self._is_empty

    # ---- İşlemler -------------------------------------------------------------------------

    @Slot(str, str, result=bool)
    def compensate(self, date_key: str, prayer_key: str) -> bool:
        try:
            item = QazaItem(date.fromisoformat(date_key), PrayerType.from_key(prayer_key), PrayerStatus.PENDING)
        except ValueError:
            logger.warning("Geçersiz kaza anahtarı: %r %r", date_key, prayer_key)
            return False
        self._qaza.compensate(item)
        self.refresh()
        self.changed.emit()
        return True

    @Slot(str, result=bool)
    def decrementBacklog(self, prayer_key: str) -> bool:
        try:
            prayer = PrayerType.from_key(prayer_key)
        except ValueError:
            logger.warning("Geçersiz vakit anahtarı: %r", prayer_key)
            return False
        self._qaza.decrement_backlog(prayer)
        self.refresh()
        self.changed.emit()
        return True

    @Slot(int, int, int, "QVariantMap", result="QVariantMap")
    def previewDuration(self, years: int, months: int, days: int, counts: dict) -> dict:
        """Süreyi elle girilen sayılara ekler; kaydetmez. `counts`: vakit anahtarı → sayı."""
        base = {prayer: _to_count(counts.get(prayer.key)) for prayer in PrayerType}
        result = QazaService.preview_duration(base, years, months, days)
        return {prayer.key: count for prayer, count in result.items()}

    @Slot("QVariantMap", int)
    def savePlan(self, counts: dict, daily_target: int) -> None:
        backlog = {prayer: _to_count(counts.get(prayer.key)) for prayer in PrayerType}
        self._qaza.save_plan(backlog, daily_target)
        self.refresh()
        self.changed.emit()


def _to_count(value) -> int:
    """QML'den gelen sayı veya metni int'e çevirir; çevrilemezse 0."""
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
