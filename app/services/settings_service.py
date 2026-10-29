"""Ayar servisi: doğrulama ve şehir arama. Qt içe aktarmaz."""

from datetime import date

from app.core.domain.cities import CITIES
from app.core.domain.models import AppSettings
from app.core.domain.prayer import PrayerType
from app.core.domain.prayer_times import AppLocation, CalcMethod
from app.core.repositories.settings_repository import SettingsRepository
from app.core.text_utils import fold_turkish

THEME_KEYS = ("default", "dark", "ocean", "rose", "gold")
REMINDER_CHOICES = (5, 10, 15, 20, 30, 45, 60)


class SettingsService:
    def __init__(self, repository: SettingsRepository):
        self._repo = repository

    @property
    def settings(self) -> AppSettings:
        return AppSettings(
            theme_key=self._repo.theme_key,
            notifications_enabled=self._repo.notifications_enabled,
            reminder_minutes=self._repo.reminder_minutes,
            calc_method=self._repo.calc_method,
            location=self._repo.manual_location,
            autostart=self._repo.autostart,
            close_to_tray=self._repo.close_to_tray,
            tray_hint_shown=self._repo.tray_hint_shown,
        )

    # ---- Konum ve yöntem ----------------------------------------------------------

    @property
    def location(self) -> "AppLocation | None":
        return self._repo.manual_location

    @property
    def calc_method(self) -> CalcMethod:
        return self._repo.calc_method

    def use_manual_location(self, location: AppLocation) -> None:
        self._repo.set_manual_location(location)

    def set_calc_method(self, method: CalcMethod) -> None:
        self._repo.set_calc_method(method)

    @property
    def cities(self) -> tuple[AppLocation, ...]:
        return CITIES

    def search_cities(self, query: str) -> list[AppLocation]:
        """Türkçe harf ve büyük/küçük farkını yok sayarak il arar; boş sorgu tüm illeri verir."""
        needle = fold_turkish(query.strip())
        return [city for city in CITIES if needle in fold_turkish(city.city)]

    def find_city(self, name: str) -> "AppLocation | None":
        """Tam ad eşleşmesiyle il bulur (Türkçe duyarsız)."""
        needle = fold_turkish(name.strip())
        return next((city for city in CITIES if fold_turkish(city.city) == needle), None)

    # ---- Görünüm ve bildirim ----------------------------------------------------

    def set_theme(self, key: str) -> None:
        if key not in THEME_KEYS:
            raise ValueError(f"Bilinmeyen tema: {key!r}")
        self._repo.set_theme_key(key)

    def set_notifications_enabled(self, enabled: bool) -> None:
        self._repo.set_notifications_enabled(enabled)

    def set_reminder_minutes(self, minutes: int) -> None:
        if minutes not in REMINDER_CHOICES:
            raise ValueError(f"Geçersiz hatırlatma süresi: {minutes!r} (izinli: {REMINDER_CHOICES})")
        self._repo.set_reminder_minutes(minutes)

    # ---- Masaüstü -----------------------------------------------------------------

    @property
    def needs_autostart_prompt(self) -> bool:
        """`autostart` ayarı yoksa ilk açılışta kullanıcıya sorulur."""
        return self._repo.autostart is None

    def set_autostart(self, enabled: bool) -> None:
        self._repo.set_autostart(enabled)

    def set_close_to_tray(self, enabled: bool) -> None:
        self._repo.set_close_to_tray(enabled)

    def mark_tray_hint_shown(self) -> None:
        self._repo.set_tray_hint_shown(True)

    # ---- Takip başlangıcı ve kaza planı ---------------------------------------

    @property
    def install_date(self) -> "date | None":
        return self._repo.install_date

    def ensure_install_date(self, day: date) -> None:
        self._repo.ensure_install_date(day)

    @property
    def qaza_backlog(self) -> dict[PrayerType, int]:
        return self._repo.qaza_backlog

    def set_qaza_backlog(self, counts: dict[PrayerType, int]) -> None:
        self._repo.set_qaza_backlog(counts)

    @property
    def qaza_daily_target(self) -> int:
        return self._repo.qaza_daily_target

    def set_qaza_daily_target(self, target: int) -> None:
        self._repo.set_qaza_daily_target(target)

    def set_corrupted_db_backup(self, path: "str | None") -> None:
        self._repo.set_corrupted_db_backup(path)
