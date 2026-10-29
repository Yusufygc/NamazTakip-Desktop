"""Açılışta "uygulama kapalıyken giren vakitleri kıldınız mı?" sorusu için aday vakitler. Qt içe aktarmaz.

Uygulama çalışırken en son anı dakikada bir yazar (`touch`). Açılışta o andan sonra girmiş, hâlâ
işaretlenmemiş farz vakitler aday olur. Uygulama açıkken giren vakitler hatırlatma bildirimiyle
sorulduğu için burada tekrar sorulmaz. Kurallar: docs/wiki/takip-gunu-ve-kaza.md.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.core.domain.dates import add_days
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.services.prayer_service import PrayerService
from app.services.settings_service import SettingsService

# En çok bu kadar takip gününe geri bakılır (bugün dahil). Daha eski işaretsiz vakitler zaten otomatik kazadır.
LOOKBACK_DAYS = 3
# Son çalışma anı en çok bu kadar sıklıkla yazılır.
TOUCH_INTERVAL = timedelta(seconds=55)


@dataclass(frozen=True)
class MissedPrayer:
    day: date  # vaktin takvim günü (işaret kaydı bu tarihle yazılır)
    prayer: PrayerType
    moment: datetime


class MissedPrayerService:
    def __init__(self, settings: SettingsService, prayers: PrayerService):
        self._settings = settings
        self._prayers = prayers
        self._last_touch: "datetime | None" = None

    def find(self, now: datetime) -> list[MissedPrayer]:
        """`son çalışma anı < vakit <= şimdi` olan, işaretlenmemiş farz vakitler (eskiden yeniye)."""
        last = self._settings.last_active_at
        if last is None or self._settings.location is None:
            return []
        first_day = max(
            self._prayers.tracking_start,
            last.astimezone(now.tzinfo).date(),
            add_days(self._prayers.tracking_day(now), -(LOOKBACK_DAYS - 1)),
        )
        found: list[MissedPrayer] = []
        day = first_day
        while day <= now.date():
            times = self._prayers.times_for(day)
            if times is not None:
                records = self._prayers.records_for_date(day)
                for prayer in PrayerType:
                    moment = times.time_of(prayer)
                    record = records.get(prayer)
                    pending = record is None or record.status == PrayerStatus.PENDING
                    if pending and last < moment <= now:
                        found.append(MissedPrayer(day, prayer, moment))
            day = add_days(day, 1)
        return sorted(found, key=lambda item: item.moment)

    def touch(self, now: datetime, force: bool = False) -> None:
        """Son çalışma anını yazar; `force` olmadıkça dakikada bir kez."""
        if not force and self._last_touch is not None and now - self._last_touch < TOUCH_INTERVAL:
            return
        self._settings.set_last_active_at(now)
        self._last_touch = now

    def answer(self, day: date, prayer: PrayerType, performed: bool) -> None:
        if performed:
            self._prayers.mark_performed(day, prayer)
        else:
            self._prayers.mark_missed(day, prayer)
