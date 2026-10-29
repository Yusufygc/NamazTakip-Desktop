"""Vakit ve işaretleme modelleri. Qt içe aktarmaz.

Kaynak: mobil `prayer.dart` (2026-10-29). Durum kodları veritabanına yazılır, değişmez.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, IntEnum


class PrayerType(Enum):
    """Günlük takip edilen beş farz vakit. Sıra tanımlandığı gibidir."""

    FAJR = "fajr"
    DHUHR = "dhuhr"
    ASR = "asr"
    MAGHRIB = "maghrib"
    ISHA = "isha"

    @property
    def key(self) -> str:
        """Veritabanında saklanan kararlı anahtar."""
        return self.value

    @property
    def index(self) -> int:
        return list(PrayerType).index(self)

    @property
    def previous(self) -> "PrayerType | None":
        order = list(PrayerType)
        return None if self.index == 0 else order[self.index - 1]

    @classmethod
    def from_key(cls, key: str) -> "PrayerType":
        for prayer in cls:
            if prayer.value == key:
                return prayer
        raise ValueError(f"Bilinmeyen vakit anahtarı: {key!r}")


class PrayerStatus(IntEnum):
    """Bir vaktin işaretlenme durumu. Yalnızca PERFORMED "zamanında kılındı" sayılır."""

    PENDING = 0
    PERFORMED = 1
    MISSED = 2
    COMPENSATED = 3

    @property
    def code(self) -> int:
        return int(self)

    @classmethod
    def from_code(cls, code: int) -> "PrayerStatus":
        try:
            return cls(code)
        except ValueError:
            return cls.PENDING


@dataclass(frozen=True)
class DayTimes:
    """Bir güne ait hesaplanmış vakitler. Anlar saat dilimli (aware) datetime'dır."""

    date: date
    fajr: datetime
    sunrise: datetime
    dhuhr: datetime
    asr: datetime
    maghrib: datetime
    isha: datetime

    def time_of(self, prayer: PrayerType) -> datetime:
        return {
            PrayerType.FAJR: self.fajr,
            PrayerType.DHUHR: self.dhuhr,
            PrayerType.ASR: self.asr,
            PrayerType.MAGHRIB: self.maghrib,
            PrayerType.ISHA: self.isha,
        }[prayer]


@dataclass(frozen=True)
class NextPrayer:
    """Sıradaki farz vakit ve zamanı."""

    type: PrayerType
    time: datetime
