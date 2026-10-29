"""Bağımlılık kökü (composition root): veritabanından bridge'lere her şeyi kurar ve bağlar.

Katman kuralına tabi değildir; yalnızca burada tüm katmanlar bir araya gelir.
"""

from PySide6.QtQml import QQmlApplicationEngine

from app.bridge.home_bridge import HomeBridge
from app.bridge.qaza_bridge import QazaBridge
from app.bridge.settings_bridge import SettingsBridge
from app.core.clock import Clock, system_now
from app.core.database import AppDatabase
from app.core.repositories.prayer_repository import PrayerRepository
from app.core.repositories.settings_repository import SettingsRepository
from app.core.strings import ui_strings
from app.services.clock_service import ClockLogic, ClockService
from app.services.prayer_service import PrayerService
from app.services.qaza_service import QazaService
from app.services.settings_service import SettingsService


class AppContainer:
    def __init__(self, database: AppDatabase, now: Clock = system_now):
        self.database = database
        settings_repo = SettingsRepository(database)
        prayer_repo = PrayerRepository(database)

        self.settings_service = SettingsService(settings_repo)
        self.prayer_service = PrayerService(self.settings_service, prayer_repo, now=now)
        self.qaza_service = QazaService(prayer_repo, self.settings_service, self.prayer_service)

        # Takip başlangıcı ilk açılışta yazılır ve bir daha değişmez (kaza bu günden başlar).
        self.settings_service.ensure_install_date(self.prayer_service.tracking_day())
        if database.corrupted_backup_path is not None:
            self.settings_service.set_corrupted_db_backup(str(database.corrupted_backup_path))

        self.clock_service = ClockService(ClockLogic(self.prayer_service, self.settings_service), now)
        self.home_bridge = HomeBridge(self.prayer_service, self.settings_service)
        self.qaza_bridge = QazaBridge(self.qaza_service)
        self.settings_bridge = SettingsBridge(self.settings_service)
        self._wire()

    def _wire(self) -> None:
        self.clock_service.ticked.connect(self.home_bridge.on_tick)
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
        context.setContextProperty("strings", ui_strings())

    def start(self) -> None:
        self.clock_service.start()

    def shutdown(self) -> None:
        self.clock_service.stop()
        self.database.close()
