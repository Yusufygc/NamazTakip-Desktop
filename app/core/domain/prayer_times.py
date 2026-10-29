"""Vakit hesabı: `adhanpy` ile, mobildeki `PrayerTimeService` davranışıyla. Qt içe aktarmaz.

Kaynak ve kurallar: docs/wiki/vakit-hesabi.md. Mobil referansı: `prayer_time_service.dart`.

`adhanpy` her vakti dakikaya yuvarlar ve yarım dakikayı aşağı yuvarlar; mobildeki `adhan_dart` ise
yarım dakikada yukarı yuvarlar ve güneş doğuşunu saniye hassasiyetiyle verir. Bu yüzden `adhanpy`'nin
yuvarlama adımı kapatılır (`_UnroundedPrayerTimes`), yuvarlama burada mobil kuralıyla yapılır.
Davranışı golden testi korur (tests/test_prayer_times.py, tests/data/golden_times.json).
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone, tzinfo
from enum import Enum

from adhanpy.calculation.CalculationParameters import CalculationParameters
from adhanpy.calculation.PrayerAdjustments import PrayerAdjustments
from adhanpy.PrayerTimes import PrayerTimes

from app.core.domain.prayer import DayTimes

# Sabah namazının kerahet vaktine kalmaması için güneş doğuşundan düşülen ihtiyat payı.
SUNRISE_CAUTION_OFFSET = timedelta(seconds=90)


@dataclass(frozen=True)
class AppLocation:
    """Elle seçilmiş konum."""

    latitude: float
    longitude: float
    city: str
    country: str = ""

    @property
    def label(self) -> str:
        return self.city if not self.country else f"{self.city}, {self.country}"

    def to_json(self) -> dict:
        return {"lat": self.latitude, "lon": self.longitude, "city": self.city, "country": self.country}

    @staticmethod
    def from_json(data: "dict | None") -> "AppLocation | None":
        """Eksik veya bozuk veri için None döner (sessizce varsayılana düşülür)."""
        if not isinstance(data, dict):
            return None
        lat, lon = data.get("lat"), data.get("lon")
        if isinstance(lat, bool) or isinstance(lon, bool):
            return None
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            return None
        city, country = data.get("city"), data.get("country")
        return AppLocation(
            float(lat),
            float(lon),
            city if isinstance(city, str) else "",
            country if isinstance(country, str) else "",
        )


@dataclass(frozen=True)
class _MethodSpec:
    fajr_angle: float
    isha_angle: float = 0.0
    isha_interval: int = 0
    sunrise: int = 0
    dhuhr: int = 0
    asr: int = 0
    maghrib: int = 0

    def parameters(self) -> CalculationParameters:
        return CalculationParameters(
            fajr_angle=self.fajr_angle,
            isha_angle=self.isha_angle,
            isha_interval=self.isha_interval,
            method_adjustments=PrayerAdjustments(
                sunrise=self.sunrise, dhuhr=self.dhuhr, asr=self.asr, maghrib=self.maghrib
            ),
        )


class CalcMethod(Enum):
    """Seçilebilir hesaplama yöntemleri. Değer, ayarlarda saklanan kararlı anahtardır."""

    DIYANET = "diyanet"
    MWL = "mwl"
    EGYPTIAN = "egyptian"
    KARACHI = "karachi"
    UMM_AL_QURA = "ummalqura"
    NORTH_AMERICA = "isna"

    @property
    def key(self) -> str:
        return self.value

    @classmethod
    def from_key(cls, key: "str | None") -> "CalcMethod":
        for method in cls:
            if method.value == key:
                return method
        return cls.DIYANET


# Parametreler adhan_dart 2.0.1 `CalculationMethodParameters` ile aynıdır (docs/wiki/vakit-hesabi.md).
_SPECS: dict[CalcMethod, _MethodSpec] = {
    CalcMethod.DIYANET: _MethodSpec(18.0, 17.0, sunrise=-7, dhuhr=5, asr=4, maghrib=7),
    CalcMethod.MWL: _MethodSpec(18.0, 17.0, dhuhr=1),
    CalcMethod.EGYPTIAN: _MethodSpec(19.5, 17.5, dhuhr=1),
    CalcMethod.KARACHI: _MethodSpec(18.0, 18.0, dhuhr=1),
    CalcMethod.UMM_AL_QURA: _MethodSpec(18.5, isha_interval=90),
    CalcMethod.NORTH_AMERICA: _MethodSpec(15.0, 15.0, dhuhr=1),
}


class _UnroundedPrayerTimes(PrayerTimes):
    """`adhanpy` vakitleri; yuvarlama yapmadan yalnızca düzeltmeleri uygular."""

    def _rounded_minute(self, adjustments, method_adjustments, prayer_name, temp_prayer):
        extra = getattr(adjustments, prayer_name) + getattr(method_adjustments, prayer_name)
        return temp_prayer + timedelta(minutes=extra)


def _round_half_up_minute(moment: datetime) -> datetime:
    """En yakın dakikaya yuvarlar; 30 sn ve üstü yukarı (mobildeki adhan_dart kuralı)."""
    seconds = moment.second
    offset = 60 - seconds if seconds >= 30 else -seconds
    return (moment + timedelta(seconds=offset)).replace(microsecond=0)


def _cautious_sunrise(sunrise: datetime) -> datetime:
    """Güneş doğuşundan 90 sn düşer ve saniyeyi keser (yuvarlamaz)."""
    return (sunrise - SUNRISE_CAUTION_OFFSET).replace(second=0, microsecond=0)


class PrayerTimeService:
    """Vakitleri cihazda hesaplar; internet gerekmez."""

    def compute(
        self,
        location: AppLocation,
        day: date,
        method: CalcMethod,
        tz: "tzinfo | None" = None,
    ) -> DayTimes:
        """`day` gününün vakitlerini verir. `tz` verilmezse sistem saat dilimi kullanılır."""
        params = _SPECS[method].parameters()
        times = _UnroundedPrayerTimes(
            (location.latitude, location.longitude),
            datetime(day.year, day.month, day.day, tzinfo=timezone.utc),
            calculation_parameters=params,
        )

        def local(moment: datetime) -> datetime:
            return moment.astimezone(tz)

        return DayTimes(
            date=day,
            fajr=local(_round_half_up_minute(times.fajr)),
            sunrise=local(_cautious_sunrise(times.sunrise)),
            dhuhr=local(_round_half_up_minute(times.dhuhr)),
            asr=local(_round_half_up_minute(times.asr)),
            maghrib=local(_round_half_up_minute(times.maghrib)),
            isha=local(_round_half_up_minute(times.isha)),
        )
