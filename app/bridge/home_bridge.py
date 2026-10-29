"""Vakitler ekranı köprüsü: seçili günün vakitleri, sıradaki vakit, sayaç ve işaretleme.

Bridge iş kuralı içermez; servisleri çağırır ve sonucu QML'in okuyacağı biçime çevirir.
Kurallar: docs/wiki/ekranlar.md (Vakitler), docs/wiki/takip-gunu-ve-kaza.md.
"""

from datetime import date

from PySide6.QtCore import Property, QObject, Signal, Slot

from app.core.domain.dates import add_days, days_diff
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.formatters import format_countdown, format_time
from app.core.logger import logger
from app.core.strings import DateStrings, PrayerDialogStrings, PrayerStrings
from app.services.clock_service import Tick
from app.services.prayer_service import PrayerService
from app.services.settings_service import SettingsService

# Gelecek günlere en çok bu kadar ileri bakılır (yalnızca vakit gösterir, işaretlenemez).
FUTURE_DAYS_LIMIT = 7
SUNRISE_KEY = "sunrise"


class HomeBridge(QObject):
    stateChanged = Signal()
    countdownChanged = Signal()
    recordsChanged = Signal()  # bir işaret yazıldı; kaza ekranı yenilenmeli
    markRejected = Signal(str)

    def __init__(self, prayers: PrayerService, settings: SettingsService, parent: "QObject | None" = None):
        super().__init__(parent)
        self._prayers = prayers
        self._settings = settings
        self._offset = 0  # takip gününe göre seçili gün farkı
        self._rows: list[dict] = []
        self._has_location = False
        self._city_label = ""
        self._selected: "date | None" = None
        self._date_label = ""
        self._can_previous = False
        self._can_next = False
        self._is_today = True
        self._next_name = ""
        self._next_time = ""
        self._countdown = ""
        self._next_instant = None
        self.refresh()

    # ---- Durum ----------------------------------------------------------------------

    @Slot()
    def refresh(self) -> None:
        now = self._prayers.now()
        today = self._prayers.tracking_day(now)
        selected = add_days(today, self._offset)
        location = self._settings.location
        times = self._prayers.times_for(selected)
        upcoming = self._prayers.next_prayer(now)
        records = self._prayers.records_for_date(selected)

        rows: list[dict] = []
        if times is not None:
            markable = selected <= today
            rows.append(self._row(PrayerType.FAJR, times, records, upcoming, markable))
            rows.append(
                {
                    "key": SUNRISE_KEY,
                    "name": PrayerStrings.SUNRISE,
                    "dialogTitle": "",
                    "time": format_time(times.sunrise),
                    "status": "",
                    "isCongregation": False,
                    "isNext": False,
                    "isSunrise": True,
                    "markable": False,
                }
            )
            for prayer in (PrayerType.DHUHR, PrayerType.ASR, PrayerType.MAGHRIB, PrayerType.ISHA):
                rows.append(self._row(prayer, times, records, upcoming, markable))

        self._rows = rows
        self._selected = selected
        self._has_location = location is not None
        self._city_label = "" if location is None else location.label
        self._date_label = DateStrings.long(selected)
        self._is_today = self._offset == 0
        self._can_previous = selected > self._prayers.tracking_start
        self._can_next = self._offset < FUTURE_DAYS_LIMIT
        self._apply_next(upcoming, now)
        self.stateChanged.emit()
        # Sayaç ayrı bildirim sinyaline bağlıdır; yenilemede de bildirilmeli (ör. ilk şehir seçimi).
        self.countdownChanged.emit()

    @staticmethod
    def _row(prayer, times, records, upcoming, markable) -> dict:
        record = records.get(prayer)
        moment = times.time_of(prayer)
        return {
            "key": prayer.key,
            "name": PrayerStrings.name(prayer),
            "dialogTitle": PrayerDialogStrings.title(PrayerStrings.name(prayer)),
            "time": format_time(moment),
            "status": (record.status if record else PrayerStatus.PENDING).name.lower(),
            "isCongregation": bool(record and record.is_congregation),
            # Tarih de karşılaştırılır: gece 00:00–04:00 arasında dünün Sabah kartı vurgulanmaz.
            "isNext": upcoming is not None and upcoming.time == moment,
            "isSunrise": False,
            "markable": markable,
        }

    def _apply_next(self, upcoming, now) -> None:
        if upcoming is None:
            self._next_name = self._next_time = self._countdown = ""
            self._next_instant = None
        else:
            self._next_name = PrayerStrings.name(upcoming.type)
            self._next_time = format_time(upcoming.time)
            self._countdown = format_countdown(upcoming.time - now)
            self._next_instant = upcoming.time

    @Slot(object)
    def on_tick(self, tick: Tick) -> None:
        """Saat servisinden gelir: sayacı günceller; gün veya sıradaki vakit değiştiyse yeniler."""
        if tick.day_changed:
            self._offset = 0
            self.refresh()
            return
        upcoming = tick.next_prayer
        instant = None if upcoming is None else upcoming.time
        if instant != self._next_instant:
            self.refresh()
            return
        countdown = "" if tick.remaining is None else format_countdown(tick.remaining)
        if countdown != self._countdown:
            self._countdown = countdown
            self.countdownChanged.emit()

    # ---- QML'e açılan özellikler -------------------------------------------------------

    @Property(bool, notify=stateChanged)
    def hasLocation(self) -> bool:
        return self._has_location

    @Property(str, notify=stateChanged)
    def cityLabel(self) -> str:
        return self._city_label

    @Property(str, notify=stateChanged)
    def selectedDateKey(self) -> str:
        return "" if self._selected is None else self._selected.isoformat()

    @Property(str, notify=stateChanged)
    def selectedDateLabel(self) -> str:
        return self._date_label

    @Property(bool, notify=stateChanged)
    def isToday(self) -> bool:
        return self._is_today

    @Property(bool, notify=stateChanged)
    def isFuture(self) -> bool:
        return self._offset > 0

    @Property(bool, notify=stateChanged)
    def canGoPrevious(self) -> bool:
        return self._can_previous

    @Property(bool, notify=stateChanged)
    def canGoNext(self) -> bool:
        return self._can_next

    @Property("QVariantList", notify=stateChanged)
    def prayers(self) -> list:
        return self._rows

    @Property(str, notify=stateChanged)
    def nextPrayerName(self) -> str:
        return self._next_name

    @Property(str, notify=stateChanged)
    def nextPrayerTime(self) -> str:
        return self._next_time

    @Property(str, notify=countdownChanged)
    def countdown(self) -> str:
        return self._countdown

    # ---- Gün gezinme ---------------------------------------------------------------------

    @Slot()
    def previousDay(self) -> None:
        if self._can_previous:
            self._offset -= 1
            self.refresh()

    @Slot()
    def nextDay(self) -> None:
        if self._can_next:
            self._offset += 1
            self.refresh()

    @Slot()
    def goToday(self) -> None:
        self._offset = 0
        self.refresh()

    @Slot(str)
    def openDay(self, date_key: str) -> None:
        """Bildirimden veya kaza ekranından belirli güne git. Aralık dışıysa bugünde kalır."""
        try:
            target = date.fromisoformat(date_key)
        except ValueError:
            logger.warning("Geçersiz gün anahtarı: %r", date_key)
            return
        offset = days_diff(target, self._prayers.tracking_day())
        if offset <= FUTURE_DAYS_LIMIT and target >= self._prayers.tracking_start:
            self._offset = offset
            self.refresh()

    # ---- İşaretleme -------------------------------------------------------------------------

    @Slot(str, bool, result=bool)
    def markPerformed(self, prayer_key: str, congregation: bool) -> bool:
        return self._mark(prayer_key, lambda day, prayer: self._prayers.mark_performed(day, prayer, congregation))

    @Slot(str, result=bool)
    def markMissed(self, prayer_key: str) -> bool:
        return self._mark(prayer_key, self._prayers.mark_missed)

    def _mark(self, prayer_key: str, action) -> bool:
        try:
            prayer = PrayerType.from_key(prayer_key)
        except ValueError:
            logger.warning("Geçersiz vakit anahtarı: %r", prayer_key)
            return False
        if self._selected is None:
            return False
        try:
            action(self._selected, prayer)
        except ValueError as error:
            self.markRejected.emit(str(error))
            return False
        self.refresh()
        self.recordsChanged.emit()
        return True
