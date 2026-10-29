"""Vakit servisi: önbellekli vakitler, takip günü, sıradaki vakit ve işaretleme. Qt içe aktarmaz."""

from datetime import date, datetime, timedelta, tzinfo

from app.core.clock import Clock, system_now
from app.core.domain.dates import add_days, next_prayer, prayer_day
from app.core.domain.models import PrayerRecord
from app.core.domain.prayer import DayTimes, NextPrayer, PrayerType
from app.core.domain.prayer_times import PrayerTimeService
from app.core.repositories.prayer_repository import PrayerRepository
from app.services.settings_service import SettingsService

_CACHE_LIMIT = 64


class PrayerService:
    def __init__(
        self,
        settings: SettingsService,
        prayers: PrayerRepository,
        now: Clock = system_now,
        time_service: "PrayerTimeService | None" = None,
        tz: "tzinfo | None" = None,
    ):
        self._settings = settings
        self._prayers = prayers
        self._now = now
        self._time_service = time_service or PrayerTimeService()
        self._tz = tz
        self._cache: dict[tuple, DayTimes] = {}

    def now(self) -> datetime:
        return self._now()

    # ---- Vakitler -----------------------------------------------------------------

    def times_for(self, day: date) -> "DayTimes | None":
        """`day` gününün vakitleri; konum seçilmemişse None. Sonuç (gün, konum, yöntem) ile önbelleğe alınır."""
        location = self._settings.location
        if location is None:
            return None
        method = self._settings.calc_method
        key = (day, location.latitude, location.longitude, method)
        cached = self._cache.get(key)
        if cached is None:
            if len(self._cache) >= _CACHE_LIMIT:
                self._cache.clear()
            cached = self._time_service.compute(location, day, method, tz=self._tz)
            self._cache[key] = cached
        return cached

    def upcoming_days(self, now: "datetime | None" = None) -> list[DayTimes]:
        """Takvim olarak bugün ve yarının vakitleri; konum yoksa boş."""
        today = (now or self._now()).date()
        days = [self.times_for(today), self.times_for(add_days(today, 1))]
        return [day for day in days if day is not None]

    def next_prayer(self, now: "datetime | None" = None) -> "NextPrayer | None":
        current = now or self._now()
        return next_prayer(current, self.upcoming_days(current))

    def remaining_until_next(self, now: "datetime | None" = None) -> "timedelta | None":
        current = now or self._now()
        upcoming = self.next_prayer(current)
        return None if upcoming is None else upcoming.time - current

    # ---- Takip günü -------------------------------------------------------------------

    def tracking_day(self, now: "datetime | None" = None) -> date:
        current = now or self._now()
        times = self.times_for(current.date())
        return prayer_day(current, fajr_today=None if times is None else times.fajr)

    @property
    def tracking_start(self) -> date:
        """Kaza hesabının başlangıcı: `install_date`, yoksa takip günü."""
        return self._settings.install_date or self.tracking_day()

    # ---- İşaretleme -----------------------------------------------------------------

    def records_for_date(self, day: date) -> dict[PrayerType, PrayerRecord]:
        return self._prayers.records_for_date(day)

    def _check_markable(self, day: date) -> None:
        if day > self.tracking_day():
            raise ValueError("Gelecek günün namazı işaretlenemez.")

    def mark_performed(self, day: date, prayer: PrayerType, congregation: bool = False) -> None:
        self._check_markable(day)
        self._prayers.mark_performed(day, prayer, congregation)

    def mark_missed(self, day: date, prayer: PrayerType) -> None:
        self._check_markable(day)
        self._prayers.mark_missed(day, prayer)
