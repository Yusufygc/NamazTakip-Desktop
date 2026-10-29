"""Kaza türetme ve geçmiş borç hesapları. Qt ve SQL içermez.

Kaynak: mobil `PrayerRepository.qazaItems`, `QazaDebtNotifier` ve `qaza_debt_sheet.dart` (2026-10-29).
Kurallar: docs/wiki/takip-gunu-ve-kaza.md.
"""

from collections.abc import Iterable
from datetime import date

from app.core.domain.dates import days_between
from app.core.domain.models import PrayerRecord, QazaItem
from app.core.domain.prayer import PrayerStatus, PrayerType

BACKLOG_MIN = 0
BACKLOG_MAX = 1_000_000
DAILY_TARGET_MIN = 1
DAILY_TARGET_MAX = 50
DAILY_TARGET_DEFAULT = 2

DAYS_PER_YEAR = 365
DAYS_PER_MONTH = 30


def clamp_backlog(count: int) -> int:
    return max(BACKLOG_MIN, min(BACKLOG_MAX, count))


def clamp_daily_target(target: int) -> int:
    return max(DAILY_TARGET_MIN, min(DAILY_TARGET_MAX, target))


def empty_backlog() -> dict[PrayerType, int]:
    return {prayer: 0 for prayer in PrayerType}


def derive_qaza_items(records: Iterable[PrayerRecord], first_day: date, today: date) -> list[QazaItem]:
    """`first_day..today` aralığında kılınmamış / kaza edilmemiş her vakit.

    Önceki günlerde işaretlenmemiş (pending) ve "kılmadım" (missed) vakitler kaza olur; takip gününde
    (`today`) yalnızca "kılmadım" denenler girer, bekleyenler henüz kaza değildir. Sıralama: tarih
    azalan, aynı gün içinde vakit sırası artan.
    """
    statuses = {(record.date, record.prayer): record.status for record in records}
    items: list[QazaItem] = []
    for day in days_between(first_day, today):
        is_today = day >= today
        for prayer in PrayerType:
            status = statuses.get((day, prayer), PrayerStatus.PENDING)
            if status in (PrayerStatus.PERFORMED, PrayerStatus.COMPENSATED):
                continue
            if is_today and status != PrayerStatus.MISSED:
                continue
            items.append(QazaItem(day, prayer, status))
    items.sort(key=lambda item: (-item.date.toordinal(), item.prayer.index))
    return items


def add_duration_to_backlog(
    backlog: dict[PrayerType, int], years: int = 0, months: int = 0, days: int = 0
) -> dict[PrayerType, int]:
    """Süreyi (`yıl*365 + ay*30 + gün`) beş vaktin her birine ekler. Süre 0 veya negatifse değişmez."""
    added = years * DAYS_PER_YEAR + months * DAYS_PER_MONTH + days
    if added <= 0:
        return dict(backlog)
    return {prayer: clamp_backlog(backlog.get(prayer, 0) + added) for prayer in PrayerType}


def decrement_backlog(backlog: dict[PrayerType, int], prayer: PrayerType, step: int = 1) -> dict[PrayerType, int]:
    """İlgili vaktin borcunu `step` kadar azaltır; 0'ın altına inmez."""
    result = dict(backlog)
    result[prayer] = clamp_backlog(backlog.get(prayer, 0) - step)
    return result
