"""Tarih yardımcıları, takip günü ve sıradaki vakit. Qt içe aktarmaz.

Takvim günleri `datetime.date`, anlar saat dilimli (aware) `datetime`'dır; ikisi karıştırılmaz.
Kaynak: mobil `dates.dart` (2026-10-29). Kurallar: docs/wiki/takip-gunu-ve-kaza.md.
"""

from collections.abc import Iterator
from datetime import date, datetime, timedelta

from app.core.domain.prayer import DayTimes, NextPrayer, PrayerType

# Gece yarısından sonra bu saate kadar (Sabah vakti bu saatten önce girmediyse)
# "dünün" namazları geçerlidir.
LATE_NIGHT_CUTOFF_HOUR = 4


def date_key(day: date) -> str:
    """Veritabanı anahtarı: `2026-01-25`. Metin sıralaması tarih sıralamasıyla aynıdır."""
    return f"{day.year:04d}-{day.month:02d}-{day.day:02d}"


def parse_date_key(key: str) -> date:
    return date.fromisoformat(key)


def add_days(day: date, days: int) -> date:
    """Gün ekler; yaz/kış saatinden etkilenmez (takvim günü aritmetiği)."""
    return day + timedelta(days=days)


def days_diff(a: date, b: date) -> int:
    """`a - b` takvim günü farkı."""
    return (a - b).days


def days_between(first: date, last: date) -> Iterator[date]:
    """`first` ile `last` arasındaki (ikisi dahil) takvim günleri."""
    current = first
    while current <= last:
        yield current
        current = add_days(current, 1)


def prayer_day(now: datetime, fajr_today: "datetime | None" = None) -> date:
    """Takip açısından "bugün". Gün sınırı `min(04:00, bugünkü Sabah vakti)`'dir.

    Sınırdan önce hâlâ dünkü gündür. Sabah vakti 04:00'ten önce girdiğinde (ör. yazın İstanbul'da 03:24)
    gün o anda değişir; böylece Sabah namazı doğru güne yazılır. `fajr_today` verilmezse (konum yok)
    yalnızca 04:00 kuralı uygulanır.
    """
    boundary = now.replace(hour=LATE_NIGHT_CUTOFF_HOUR, minute=0, second=0, microsecond=0)
    if fajr_today is not None and fajr_today < boundary:
        boundary = fajr_today
    today = now.date()
    return add_days(today, -1) if now < boundary else today


def next_prayer(now: datetime, days: list[DayTimes]) -> "NextPrayer | None":
    """`now` anından sonraki ilk farz vakit. Güneş sayılmaz.

    `days` bugün ve yarının vakitlerini içermelidir; böylece Yatsı'dan sonra yarının Sabah'ı
    sayfa yenilenmeden bulunur.
    """
    best: "NextPrayer | None" = None
    for day in days:
        for prayer in PrayerType:
            moment = day.time_of(prayer)
            if moment > now and (best is None or moment < best.time):
                best = NextPrayer(prayer, moment)
    return best
