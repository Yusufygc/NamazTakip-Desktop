"""Kullanıcı ayarları ve küçük kalıcı durumlar (`settings` tablosu).

Ayarlar işaretlerle aynı SQLite dosyasındadır; kritik değerler (`install_date`, `qaza_backlog`)
tek dosyayla yedeklenir. Değerler metin saklanır; bozuk değer loglanır ve varsayılana düşülür.
Kaynak: mobil `settings_repository.dart` (2026-10-29). Anahtarlar: docs/wiki/veri-katmani.md.
"""

import json
from datetime import date

from app.core.database import AppDatabase
from app.core.domain.dates import date_key, parse_date_key
from app.core.domain.prayer import PrayerType
from app.core.domain.prayer_times import AppLocation, CalcMethod
from app.core.domain.qaza import (
    DAILY_TARGET_DEFAULT,
    clamp_backlog,
    clamp_daily_target,
    empty_backlog,
)
from app.core.logger import logger

KEY_THEME = "theme"
KEY_NOTIFICATIONS = "notifications_enabled"
KEY_REMINDER_MINUTES = "reminder_minutes"
KEY_CALC_METHOD = "calc_method"
KEY_MANUAL_LOCATION = "manual_location"
KEY_INSTALL_DATE = "install_date"
KEY_CORRUPTED_DB_BACKUP = "corrupted_db_backup"
KEY_QAZA_BACKLOG = "qaza_backlog"
KEY_QAZA_DAILY_TARGET = "qaza_daily_target"
KEY_AUTOSTART = "autostart"
KEY_CLOSE_TO_TRAY = "close_to_tray"
KEY_TRAY_HINT_SHOWN = "tray_hint_shown"

DEFAULT_THEME = "default"
DEFAULT_REMINDER_MINUTES = 15


class SettingsRepository:
    def __init__(self, database: AppDatabase):
        self._db = database

    # ---- Ham erişim ---------------------------------------------------------------

    def _get(self, key: str) -> "str | None":
        row = self._db.connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return None if row is None else row["value"]

    def _set(self, key: str, value: str) -> None:
        self._db.connection.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def _remove(self, key: str) -> None:
        self._db.connection.execute("DELETE FROM settings WHERE key = ?", (key,))

    def _get_bool(self, key: str, default: "bool | None") -> "bool | None":
        raw = self._get(key)
        if raw is None:
            return default
        if raw in ("0", "1"):
            return raw == "1"
        logger.warning("Ayar %s için geçersiz mantıksal değer %r; varsayılan kullanılıyor.", key, raw)
        return default

    def _set_bool(self, key: str, value: bool) -> None:
        self._set(key, "1" if value else "0")

    def _get_int(self, key: str, default: int) -> int:
        raw = self._get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError:
            logger.warning("Ayar %s için geçersiz sayı %r; varsayılan kullanılıyor.", key, raw)
            return default

    # ---- Görünüm ve bildirim ----------------------------------------------------

    @property
    def theme_key(self) -> str:
        return self._get(KEY_THEME) or DEFAULT_THEME

    def set_theme_key(self, value: str) -> None:
        self._set(KEY_THEME, value)

    @property
    def notifications_enabled(self) -> bool:
        return bool(self._get_bool(KEY_NOTIFICATIONS, True))

    def set_notifications_enabled(self, value: bool) -> None:
        self._set_bool(KEY_NOTIFICATIONS, value)

    @property
    def reminder_minutes(self) -> int:
        """Vakitten kaç dakika sonra "kıldın mı" hatırlatması gelsin."""
        return self._get_int(KEY_REMINDER_MINUTES, DEFAULT_REMINDER_MINUTES)

    def set_reminder_minutes(self, value: int) -> None:
        self._set(KEY_REMINDER_MINUTES, str(value))

    # ---- Konum ve yöntem ----------------------------------------------------------

    @property
    def calc_method(self) -> CalcMethod:
        return CalcMethod.from_key(self._get(KEY_CALC_METHOD))

    def set_calc_method(self, method: CalcMethod) -> None:
        self._set(KEY_CALC_METHOD, method.key)

    @property
    def manual_location(self) -> "AppLocation | None":
        raw = self._get(KEY_MANUAL_LOCATION)
        if raw is None:
            return None
        try:
            location = AppLocation.from_json(json.loads(raw))
        except json.JSONDecodeError:
            location = None
        if location is None:
            logger.warning("Ayar %s okunamadı; konum yok sayılıyor.", KEY_MANUAL_LOCATION)
        return location

    def set_manual_location(self, location: AppLocation) -> None:
        self._set(KEY_MANUAL_LOCATION, json.dumps(location.to_json(), ensure_ascii=False))

    # ---- Takip başlangıcı ---------------------------------------------------------

    @property
    def install_date(self) -> "date | None":
        raw = self._get(KEY_INSTALL_DATE)
        if raw is None:
            return None
        try:
            return parse_date_key(raw)
        except ValueError:
            logger.warning("Ayar %s okunamadı: %r", KEY_INSTALL_DATE, raw)
            return None

    def ensure_install_date(self, day: date) -> None:
        """İlk kullanım gününü yazar ve bir daha değiştirmez; kaza hesabı bu günden başlar."""
        if self._get(KEY_INSTALL_DATE) is None:
            self._set(KEY_INSTALL_DATE, date_key(day))

    # ---- Bozuk veritabanı uyarısı -------------------------------------------------

    @property
    def corrupted_db_backup(self) -> "str | None":
        return self._get(KEY_CORRUPTED_DB_BACKUP)

    def set_corrupted_db_backup(self, path: "str | None") -> None:
        if path is None:
            self._remove(KEY_CORRUPTED_DB_BACKUP)
        else:
            self._set(KEY_CORRUPTED_DB_BACKUP, path)

    # ---- Kaza planı ---------------------------------------------------------------

    @property
    def qaza_backlog(self) -> dict[PrayerType, int]:
        """Geçmiş yıllardan kalan vakit bazlı toplu borç."""
        raw = self._get(KEY_QAZA_BACKLOG)
        if not raw:
            return empty_backlog()
        try:
            decoded = json.loads(raw)
            if not isinstance(decoded, dict):
                raise ValueError("JSON nesnesi bekleniyordu")
            return {prayer: clamp_backlog(_to_int(decoded.get(prayer.key))) for prayer in PrayerType}
        except (json.JSONDecodeError, ValueError):
            logger.warning("Ayar %s okunamadı; borç sıfır kabul ediliyor.", KEY_QAZA_BACKLOG)
            return empty_backlog()

    def set_qaza_backlog(self, counts: dict[PrayerType, int]) -> None:
        data = {prayer.key: clamp_backlog(counts.get(prayer, 0)) for prayer in PrayerType}
        self._set(KEY_QAZA_BACKLOG, json.dumps(data))

    @property
    def qaza_daily_target(self) -> int:
        return clamp_daily_target(self._get_int(KEY_QAZA_DAILY_TARGET, DAILY_TARGET_DEFAULT))

    def set_qaza_daily_target(self, target: int) -> None:
        self._set(KEY_QAZA_DAILY_TARGET, str(clamp_daily_target(target)))

    # ---- Masaüstü -----------------------------------------------------------------

    @property
    def autostart(self) -> "bool | None":
        """Windows açılışında başlat. Ayar yoksa None: ilk açılışta kullanıcıya sorulur."""
        return self._get_bool(KEY_AUTOSTART, None)

    def set_autostart(self, value: bool) -> None:
        self._set_bool(KEY_AUTOSTART, value)

    @property
    def close_to_tray(self) -> bool:
        return bool(self._get_bool(KEY_CLOSE_TO_TRAY, True))

    def set_close_to_tray(self, value: bool) -> None:
        self._set_bool(KEY_CLOSE_TO_TRAY, value)

    @property
    def tray_hint_shown(self) -> bool:
        return bool(self._get_bool(KEY_TRAY_HINT_SHOWN, False))

    def set_tray_hint_shown(self, value: bool) -> None:
        self._set_bool(KEY_TRAY_HINT_SHOWN, value)


def _to_int(value: object) -> int:
    """JSON'daki sayıyı int'e çevirir; sayı değilse 0."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(value)
