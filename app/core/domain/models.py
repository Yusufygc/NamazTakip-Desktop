"""İşaret kaydı, kaza satırı ve kaza borcu planı. Qt içe aktarmaz.

Kaynak: mobil `models.dart` (2026-10-29). Kurallar: docs/wiki/takip-gunu-ve-kaza.md.
"""

import math
from dataclasses import dataclass, field
from datetime import date

from app.core.domain.dates import add_days
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.domain.prayer_times import AppLocation, CalcMethod


@dataclass(frozen=True)
class PrayerRecord:
    """Bir vaktin, bir gün için kayıtlı durumu."""

    date: date
    prayer: PrayerType
    status: PrayerStatus
    is_congregation: bool = False


@dataclass(frozen=True)
class QazaItem:
    """Kaza listesindeki tek satır.

    `status`: PENDING = gün bitti ama işaretlenmedi, MISSED = kullanıcı "kılmadım" dedi.
    """

    date: date
    prayer: PrayerType
    status: PrayerStatus

    @property
    def is_auto_detected(self) -> bool:
        return self.status == PrayerStatus.PENDING


@dataclass(frozen=True)
class AppSettings:
    """Kullanıcı ayarlarının o anki görüntüsü."""

    theme_key: str
    notifications_enabled: bool
    reminder_minutes: int
    pre_reminder_minutes: int  # 0 = vakitten önce haber verme kapalı
    calc_method: CalcMethod
    location: "AppLocation | None"
    autostart: "bool | None"  # None: henüz sorulmadı
    close_to_tray: bool
    tray_hint_shown: bool
    update_check_enabled: bool = True


@dataclass(frozen=True)
class QazaDebtPlan:
    """Geçmiş yıllardan kalan toplu kaza borcu ve günlük kaza eritme hedefi."""

    backlog_by_prayer: dict[PrayerType, int] = field(default_factory=dict)
    daily_target: int = 2

    def count_for(self, prayer: PrayerType) -> int:
        return self.backlog_by_prayer.get(prayer, 0)

    @property
    def total_backlog(self) -> int:
        return sum(self.backlog_by_prayer.values())

    def grand_total(self, auto_tracked_count: int) -> int:
        return self.total_backlog + auto_tracked_count

    def estimated_days_to_finish(self, auto_tracked_count: int) -> "int | None":
        total = self.grand_total(auto_tracked_count)
        if total <= 0 or self.daily_target <= 0:
            return None
        return math.ceil(total / self.daily_target)

    def estimated_completion_date(self, auto_tracked_count: int, today: date) -> "date | None":
        days = self.estimated_days_to_finish(auto_tracked_count)
        return None if days is None else add_days(today, days)
