"""Ayarlar ekranı köprüsü. Doğrulama `SettingsService`'tedir.

Windows açılışında başlatma kaydı (registry) ve tepsi davranışı Faz 7'de bağlanır; burada yalnızca
ayar değeri saklanır. Kurallar: docs/wiki/ekranlar.md (Ayarlar), docs/wiki/veri-katmani.md.
"""

from PySide6.QtCore import Property, QObject, Signal, Slot

from app.core.domain.prayer_times import CalcMethod
from app.core.logger import logger
from app.core.strings import CalcMethodStrings
from app.services.settings_service import REMINDER_CHOICES, THEME_KEYS, SettingsService


class SettingsBridge(QObject):
    settingsChanged = Signal()
    # Şehir veya hesaplama yöntemi değişti: vakitler yeniden hesaplanmalı.
    timesInvalidated = Signal()

    def __init__(self, settings: SettingsService, parent: "QObject | None" = None):
        super().__init__(parent)
        self._settings = settings

    # ---- Okunan özellikler -------------------------------------------------------------

    @Property(str, notify=settingsChanged)
    def themeKey(self) -> str:
        return self._settings.settings.theme_key

    @Property("QVariantList", constant=True)
    def themeKeys(self) -> list:
        return list(THEME_KEYS)

    @Property(bool, notify=settingsChanged)
    def notificationsEnabled(self) -> bool:
        return self._settings.settings.notifications_enabled

    @Property(int, notify=settingsChanged)
    def reminderMinutes(self) -> int:
        return self._settings.settings.reminder_minutes

    @Property("QVariantList", constant=True)
    def reminderChoices(self) -> list:
        return list(REMINDER_CHOICES)

    @Property(str, notify=settingsChanged)
    def calcMethodKey(self) -> str:
        return self._settings.settings.calc_method.key

    @Property("QVariantList", constant=True)
    def calcMethods(self) -> list:
        return [{"key": method.key, "name": CalcMethodStrings.name(method)} for method in CalcMethod]

    @Property(bool, notify=settingsChanged)
    def hasLocation(self) -> bool:
        return self._settings.location is not None

    @Property(str, notify=settingsChanged)
    def cityLabel(self) -> str:
        location = self._settings.location
        return "" if location is None else location.label

    @Property(bool, notify=settingsChanged)
    def needsAutostartPrompt(self) -> bool:
        return self._settings.needs_autostart_prompt

    @Property(bool, notify=settingsChanged)
    def autostartEnabled(self) -> bool:
        return self._settings.settings.autostart is True

    @Property(bool, notify=settingsChanged)
    def closeToTray(self) -> bool:
        return self._settings.settings.close_to_tray

    @Property(bool, notify=settingsChanged)
    def trayHintShown(self) -> bool:
        return self._settings.settings.tray_hint_shown

    # ---- Değiştirme --------------------------------------------------------------------------

    @Slot(str, result=bool)
    def setThemeKey(self, key: str) -> bool:
        return self._apply(lambda: self._settings.set_theme(key))

    @Slot(bool)
    def setNotificationsEnabled(self, enabled: bool) -> None:
        self._apply(lambda: self._settings.set_notifications_enabled(enabled))

    @Slot(int, result=bool)
    def setReminderMinutes(self, minutes: int) -> bool:
        return self._apply(lambda: self._settings.set_reminder_minutes(minutes))

    @Slot(str, result=bool)
    def setCalcMethod(self, key: str) -> bool:
        method = next((m for m in CalcMethod if m.key == key), None)
        if method is None:
            logger.warning("Bilinmeyen hesaplama yöntemi: %r", key)
            return False
        ok = self._apply(lambda: self._settings.set_calc_method(method))
        self.timesInvalidated.emit()
        return ok

    @Slot(str, result="QVariantList")
    def searchCities(self, query: str) -> list:
        return [{"city": city.city, "label": city.label} for city in self._settings.search_cities(query)]

    @Slot(str, result=bool)
    def selectCity(self, city_name: str) -> bool:
        city = self._settings.find_city(city_name)
        if city is None:
            logger.warning("Bilinmeyen şehir: %r", city_name)
            return False
        ok = self._apply(lambda: self._settings.use_manual_location(city))
        self.timesInvalidated.emit()
        return ok

    @Slot(bool)
    def setAutostart(self, enabled: bool) -> None:
        self._apply(lambda: self._settings.set_autostart(enabled))

    @Slot(bool)
    def setCloseToTray(self, enabled: bool) -> None:
        self._apply(lambda: self._settings.set_close_to_tray(enabled))

    @Slot()
    def markTrayHintShown(self) -> None:
        self._apply(self._settings.mark_tray_hint_shown)

    def _apply(self, action) -> bool:
        try:
            action()
        except ValueError as error:
            logger.warning("Ayar reddedildi: %s", error)
            return False
        self.settingsChanged.emit()
        return True
