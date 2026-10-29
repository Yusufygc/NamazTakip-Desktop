"""Uygulama içi saat: her saniye takip gününü, sıradaki vakti ve bildirim kararını üretir.

`ClockLogic` saf Python'dur (Qt yok, sahte saatle test edilir). `ClockService` onu `QTimer` ile sürer.
Kurallar: docs/wiki/bildirim-ve-tepsi.md.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal

from app.core.domain.prayer import NextPrayer, PrayerStatus, PrayerType
from app.core.formatters import format_time
from app.core.logger import logger
from app.core.strings import NotificationStrings, PrayerStrings
from app.services.prayer_service import PrayerService
from app.services.settings_service import SettingsService

# Vakit girdikten sonra bildirimin tetiklenebileceği süre. Uyku/uyanma sonrası eski vakitlerin
# toplu bildirim yağdırmasını önler.
TRIGGER_WINDOW = timedelta(seconds=60)
_FIRED_KEEP_DAYS = 3


class NotificationKind(Enum):
    PRE = "pre"  # vakit girmeden önce haber
    ADHAN = "adhan"
    REMINDER = "reminder"


@dataclass(frozen=True)
class Notification:
    kind: NotificationKind
    prayer: PrayerType
    day: date  # vaktin takvim günü; bildirimden işaretleme diyaloğu bu tarihle açılır
    title: str
    body: str


@dataclass(frozen=True)
class Tick:
    now: datetime
    tracking_day: date
    day_changed: bool
    next_prayer: "NextPrayer | None"
    remaining: "timedelta | None"
    notifications: tuple[Notification, ...]


class ClockLogic:
    def __init__(self, prayer_service: PrayerService, settings: SettingsService):
        self._prayers = prayer_service
        self._settings = settings
        self._last_day: "date | None" = None
        self._fired: set[tuple[date, PrayerType, NotificationKind]] = set()

    def tick(self, now: datetime) -> Tick:
        day = self._prayers.tracking_day(now)
        day_changed = self._last_day is not None and day != self._last_day
        self._last_day = day

        upcoming = self._prayers.next_prayer(now)
        remaining = None if upcoming is None else upcoming.time - now
        return Tick(now, day, day_changed, upcoming, remaining, self._due_notifications(now))

    def _due_notifications(self, now: datetime) -> tuple[Notification, ...]:
        settings = self._settings.settings
        if not settings.notifications_enabled or settings.location is None:
            return ()

        reminder_after = timedelta(minutes=settings.reminder_minutes)
        pre_minutes = settings.pre_reminder_minutes
        pre_before = timedelta(minutes=pre_minutes)
        due: list[Notification] = []
        # Dünün vakitleri de bakılır: gece yarısına yakın Yatsı bildirimi gün sınırını geçebilir.
        for calendar_day in (now.date() - timedelta(days=1), now.date()):
            times = self._prayers.times_for(calendar_day)
            if times is None:
                continue
            records = None
            for prayer in PrayerType:
                moment = times.time_of(prayer)
                name = PrayerStrings.name(prayer)
                if (
                    pre_minutes > 0
                    and self._in_window(now, moment - pre_before)
                    and self._fire(calendar_day, prayer, NotificationKind.PRE)
                ):
                    due.append(
                        Notification(
                            NotificationKind.PRE,
                            prayer,
                            calendar_day,
                            NotificationStrings.pre_title(name, pre_minutes),
                            NotificationStrings.pre_body(format_time(moment)),
                        )
                    )
                if self._in_window(now, moment) and self._fire(calendar_day, prayer, NotificationKind.ADHAN):
                    due.append(
                        Notification(
                            NotificationKind.ADHAN,
                            prayer,
                            calendar_day,
                            NotificationStrings.adhan_title(name),
                            NotificationStrings.adhan_body(name),
                        )
                    )
                if self._in_window(now, moment + reminder_after):
                    if records is None:
                        records = self._prayers.records_for_date(calendar_day)
                    record = records.get(prayer)
                    answered = record is not None and record.status != PrayerStatus.PENDING
                    if not answered and self._fire(calendar_day, prayer, NotificationKind.REMINDER):
                        due.append(
                            Notification(
                                NotificationKind.REMINDER,
                                prayer,
                                calendar_day,
                                NotificationStrings.reminder_title(name),
                                NotificationStrings.REMINDER_BODY,
                            )
                        )
        self._prune(now.date())
        return tuple(due)

    @staticmethod
    def _in_window(now: datetime, moment: datetime) -> bool:
        return moment <= now < moment + TRIGGER_WINDOW

    def _fire(self, day: date, prayer: PrayerType, kind: NotificationKind) -> bool:
        """Bu (gün, vakit, tür) için bu oturumda ilk kez ise True. Yeniden başlatmada sıfırlanır."""
        key = (day, prayer, kind)
        if key in self._fired:
            return False
        self._fired.add(key)
        return True

    def _prune(self, today: date) -> None:
        limit = today - timedelta(days=_FIRED_KEEP_DAYS)
        self._fired = {key for key in self._fired if key[0] >= limit}


class ClockService(QObject):
    ticked = Signal(object)  # Tick
    notification = Signal(object)  # Notification

    def __init__(self, logic: ClockLogic, now_fn, parent: "QObject | None" = None):
        super().__init__(parent)
        self._logic = logic
        self._now = now_fn
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.tick_now)

    @property
    def is_active(self) -> bool:
        return self._timer.isActive()

    def start(self) -> None:
        self.tick_now()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def tick_now(self) -> None:
        """Bir tik işler. Hata saati durdurmasın diye loglanır ve yutulur (sonraki tik denenir)."""
        try:
            tick = self._logic.tick(self._now())
            self.ticked.emit(tick)
            for item in tick.notifications:
                self.notification.emit(item)
        except Exception:
            logger.exception("Saat tiki işlenemedi")
