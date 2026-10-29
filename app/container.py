"""Bağımlılık kökü (composition root): veritabanından bridge'lere her şeyi kurar ve bağlar.

Katman kuralına tabi değildir; yalnızca burada tüm katmanlar bir araya gelir.
"""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine

from app.bridge.home_bridge import HomeBridge
from app.bridge.missed_bridge import MissedBridge
from app.bridge.qaza_bridge import QazaBridge
from app.bridge.settings_bridge import SettingsBridge
from app.bridge.shell_bridge import ShellBridge
from app.core.backup import run_daily_backup
from app.core.clock import Clock, system_now
from app.core.database import AppDatabase
from app.core.repositories.prayer_repository import PrayerRepository
from app.core.repositories.settings_repository import SettingsRepository
from app.core.strings import ui_strings
from app.services.autostart_service import AutostartService
from app.services.clock_service import ClockLogic, ClockService
from app.services.missed_prayer_service import MissedPrayerService
from app.services.prayer_service import PrayerService
from app.services.qaza_service import QazaService
from app.services.settings_service import SettingsService


class AppContainer:
    def __init__(
        self,
        database: AppDatabase,
        now: Clock = system_now,
        start_hidden: bool = False,
        assets_dir: "Path | None" = None,
        autostart: "AutostartService | None" = None,
    ):
        self.database = database
        self._now = now
        settings_repo = SettingsRepository(database)
        prayer_repo = PrayerRepository(database)

        self.autostart_service = autostart if autostart is not None else AutostartService()
        self.settings_service = SettingsService(settings_repo, self.autostart_service)
        self.prayer_service = PrayerService(self.settings_service, prayer_repo, now=now)
        self.qaza_service = QazaService(prayer_repo, self.settings_service, self.prayer_service)

        # Takip başlangıcı ilk açılışta yazılır ve bir daha değişmez (kaza bu günden başlar).
        self.settings_service.ensure_install_date(self.prayer_service.tracking_day())
        if database.corrupted_backup_path is not None:
            self.settings_service.set_corrupted_db_backup(str(database.corrupted_backup_path))

        self.missed_service = MissedPrayerService(self.settings_service, self.prayer_service)
        self.clock_service = ClockService(ClockLogic(self.prayer_service, self.settings_service), now)
        self.home_bridge = HomeBridge(self.prayer_service, self.settings_service)
        self.qaza_bridge = QazaBridge(self.qaza_service)
        self.settings_bridge = SettingsBridge(self.settings_service)
        self.missed_bridge = MissedBridge(self.missed_service, now)
        assets = assets_dir if assets_dir is not None else Path(__file__).resolve().parent / "ui" / "assets"
        tray_icon_url = QUrl.fromLocalFile(str(assets / "tray.png")).toString()
        self.shell_bridge = ShellBridge(start_hidden, tray_icon_url)
        self._wire()

    def _wire(self) -> None:
        self.clock_service.ticked.connect(self.home_bridge.on_tick)
        self.clock_service.notification.connect(self.shell_bridge.on_notification)
        self.clock_service.ticked.connect(self._touch_last_active)
        # Açılış sorusuna verilen cevap Vakitler ve Kaza ekranlarını yeniler.
        self.missed_bridge.recordsChanged.connect(self.home_bridge.refresh)
        self.missed_bridge.recordsChanged.connect(self.qaza_bridge.refresh)
        # İşaret yazılınca kaza listesi, kaza edilince vakitler ekranı yenilenir.
        self.home_bridge.recordsChanged.connect(self.qaza_bridge.refresh)
        self.qaza_bridge.changed.connect(self.home_bridge.refresh)
        # Şehir veya yöntem değişince vakitler, sıradaki vakit ve kaza (takip günü) yenilenir.
        self.settings_bridge.timesInvalidated.connect(self.home_bridge.refresh)
        self.settings_bridge.timesInvalidated.connect(self.qaza_bridge.refresh)

    def register_context_properties(self, engine: QQmlApplicationEngine) -> None:
        context = engine.rootContext()
        context.setContextProperty("homeBridge", self.home_bridge)
        context.setContextProperty("qazaBridge", self.qaza_bridge)
        context.setContextProperty("settingsBridge", self.settings_bridge)
        context.setContextProperty("shellBridge", self.shell_bridge)
        context.setContextProperty("missedBridge", self.missed_bridge)
        context.setContextProperty("strings", ui_strings())

    def _touch_last_active(self, tick) -> None:
        self.missed_service.touch(tick.now)

    def run_startup_tasks(self) -> None:
        """Açılış işleri: autostart kaydını eşitle, günlük yedeği al, kapalıyken kaçan vakitleri bul."""
        self.settings_service.sync_autostart()
        run_daily_backup(self.database, self._now().date())
        # QML yüklenmeden önce çalışır; diyalog liste doluysa pencere görününce açılır.
        self.missed_bridge.load()

    def start(self) -> None:
        self.clock_service.start()

    def shutdown(self) -> None:
        self.clock_service.stop()
        self.missed_service.touch(self._now(), force=True)
        self.database.close()
