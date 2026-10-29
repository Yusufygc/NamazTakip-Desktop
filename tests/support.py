"""Servis, saat ve bridge testleri için ortak kurulum."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.core.database import AppDatabase
from app.core.domain.prayer_times import AppLocation
from app.core.repositories.prayer_repository import PrayerRepository
from app.core.repositories.settings_repository import SettingsRepository
from app.services.prayer_service import PrayerService
from app.services.qaza_service import QazaService
from app.services.settings_service import SettingsService

TZ = timezone(timedelta(hours=3))
ISTANBUL = AppLocation(41.0082, 28.9784, "İstanbul", "Türkiye")

# İstanbul, 26 Ekim 2026, Diyanet (golden testle doğrulanmış; tests/test_prayer_times.py).
OCT26 = {"fajr": "05:55", "sunrise": "07:19", "dhuhr": "12:53", "asr": "15:46", "maghrib": "18:15", "isha": "19:35"}


class FakeRegistry:
    """Windows kayıt defteri yerine sözlük: testler gerçek `Run` anahtarına dokunmaz."""

    def __init__(self, initial: "dict[str, str] | None" = None):
        self.values: dict[str, str] = dict(initial or {})
        self.writes = 0

    def get(self, name: str) -> "str | None":
        return self.values.get(name)

    def set(self, name: str, value: str) -> None:
        self.writes += 1
        self.values[name] = value

    def delete(self, name: str) -> bool:
        return self.values.pop(name, None) is not None


FAKE_EXE = r"C:\Apps\NamazTakip\NamazTakip.exe"


def at(year, month, day, hour=0, minute=0, second=0) -> datetime:
    return datetime(year, month, day, hour, minute, second, tzinfo=TZ)


class FakeClock:
    def __init__(self, now: datetime):
        self.current = now

    def __call__(self) -> datetime:
        return self.current

    def set(self, now: datetime) -> None:
        self.current = now


def build_services(now: datetime, with_location: bool = True) -> SimpleNamespace:
    """Bellek içi veritabanıyla ayar, vakit ve kaza servislerini kurar (saat dilimi UTC+3 sabit)."""
    database = AppDatabase.open_in_memory()
    clock = FakeClock(now)
    prayer_repo = PrayerRepository(database)
    settings = SettingsService(SettingsRepository(database))
    if with_location:
        settings.use_manual_location(ISTANBUL)
    prayers = PrayerService(settings, prayer_repo, now=clock, tz=TZ)
    qaza = QazaService(prayer_repo, settings, prayers)
    return SimpleNamespace(
        database=database, clock=clock, prayer_repo=prayer_repo, settings=settings, prayers=prayers, qaza=qaza
    )
