"""Bridge'ler: Python tarafında davranış + QML'den okuma/çağırma (ekransız)."""

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

from app.bridge.home_bridge import FUTURE_DAYS_LIMIT
from app.container import AppContainer
from app.core.database import AppDatabase
from app.services.clock_service import Tick
from tests.support import ISTANBUL, OCT26, FakeClock, at


@pytest.fixture
def clock():
    return FakeClock(at(2026, 10, 26, 12))


@pytest.fixture
def app(qapp, clock):
    container = AppContainer(AppDatabase.open_in_memory(), now=clock)
    container.settings_service.use_manual_location(ISTANBUL)
    # Köprüler konumdan önce kurulduğu için yenile.
    container.home_bridge.refresh()
    container.qaza_bridge.refresh()
    yield container
    container.shutdown()


def record(signal) -> list:
    received: list = []
    signal.connect(lambda *args: received.append(args))
    return received


class TestHomeBridge:
    def test_konum_yokken_bos_durum(self, qapp, clock):
        container = AppContainer(AppDatabase.open_in_memory(), now=clock)
        try:
            home = container.home_bridge
            assert home.hasLocation is False
            assert home.prayers == []
            assert home.cityLabel == "" and home.nextPrayerName == "" and home.countdown == ""
        finally:
            container.shutdown()

    def test_alti_satir_vakit_sirali_ve_siradaki_vurgulu(self, app):
        home = app.home_bridge
        rows = home.prayers
        assert [r["key"] for r in rows] == ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]
        assert [r["time"] for r in rows] == list(OCT26.values())
        assert [r["name"] for r in rows] == ["Sabah", "Güneş", "Öğle", "İkindi", "Akşam", "Yatsı"]
        assert [r["key"] for r in rows if r["isNext"]] == ["dhuhr"]
        assert rows[1]["isSunrise"] is True and rows[1]["markable"] is False
        assert all(r["markable"] for r in rows if not r["isSunrise"])
        assert home.hasLocation and home.cityLabel == "İstanbul, Türkiye"

    def test_diyalog_basligi_ve_gelecek_gun_bayragi(self, app):
        home = app.home_bridge
        titles = {r["key"]: r["dialogTitle"] for r in home.prayers}
        assert titles["asr"] == "İKİNDİ NAMAZINI" and titles["isha"] == "YATSI NAMAZINI"
        assert titles["sunrise"] == ""
        assert home.isFuture is False
        home.nextDay()
        assert home.isFuture is True
        home.goToday()
        assert home.isFuture is False

    def test_sayac_ve_tarih_etiketi(self, app):
        home = app.home_bridge
        assert (home.nextPrayerName, home.nextPrayerTime, home.countdown) == ("Öğle", "12:53", "00:53:00")
        assert home.selectedDateKey == "2026-10-26" and home.selectedDateLabel == "26 Ekim 2026"
        assert home.isToday and home.canGoNext and not home.canGoPrevious

    def test_isaretleme_satiri_ve_kaza_ekranini_gunceller(self, app):
        home = app.home_bridge
        records = record(home.recordsChanged)
        assert home.markPerformed("fajr", True) is True
        fajr = home.prayers[0]
        assert (fajr["status"], fajr["isCongregation"]) == ("performed", True)
        assert records, "recordsChanged yayınlanmadı"
        assert home.markMissed("asr") is True
        assert next(r for r in home.prayers if r["key"] == "asr")["status"] == "missed"

    def test_gecersiz_anahtar_reddedilir(self, app):
        home = app.home_bridge
        assert home.markPerformed("sunrise", False) is False
        assert home.markMissed("yok") is False

    def test_gelecek_gun_gorunur_ama_isaretlenmez(self, app):
        home = app.home_bridge
        rejected = record(home.markRejected)
        home.nextDay()
        assert home.selectedDateKey == "2026-10-27" and not home.isToday
        assert not any(r["markable"] for r in home.prayers)
        assert home.markPerformed("fajr", False) is False
        assert rejected and "Gelecek" in rejected[0][0]

    def test_gun_gezinme_sinirlari(self, app):
        home = app.home_bridge
        home.previousDay()  # takip başlangıcından önceye gidilmez
        assert home.selectedDateKey == "2026-10-26"
        for _ in range(FUTURE_DAYS_LIMIT + 3):
            home.nextDay()
        assert home.selectedDateKey == "2026-11-02" and home.canGoNext is False
        home.goToday()
        assert home.isToday

    def test_gecmis_gun_baslangictan_sonra_gezilir_ve_isaretlenir(self, app, clock):
        clock.set(at(2026, 10, 28, 12))
        home = app.home_bridge
        home.refresh()
        home.previousDay()
        assert home.selectedDateKey == "2026-10-27" and home.canGoPrevious
        assert home.markPerformed("isha", False) is True
        home.previousDay()
        assert home.selectedDateKey == "2026-10-26" and home.canGoPrevious is False

    def test_openday_aralik_icindeyse_gider(self, app, clock):
        clock.set(at(2026, 10, 28, 12))
        home = app.home_bridge
        home.openDay("2026-10-26")
        assert home.selectedDateKey == "2026-10-26"
        home.openDay("2026-10-01")  # takip başlangıcından önce: değişmez
        home.openDay("bozuk")
        assert home.selectedDateKey == "2026-10-26"

    def test_tik_sayaci_gunceller_ve_vakit_gecince_vurguyu_tasir(self, app, clock):
        home = app.home_bridge
        countdowns = record(home.countdownChanged)
        clock.set(at(2026, 10, 26, 12, 0, 1))
        app.clock_service.tick_now()
        assert home.countdown == "00:52:59" and countdowns
        clock.set(at(2026, 10, 26, 12, 53, 1))
        app.clock_service.tick_now()
        assert [r["key"] for r in home.prayers if r["isNext"]] == ["asr"]
        assert home.nextPrayerName == "İkindi"

    def test_gun_degisince_bugune_doner(self, app, clock):
        home = app.home_bridge
        home.nextDay()
        clock.set(at(2026, 10, 26, 23, 59))
        app.clock_service.tick_now()
        clock.set(at(2026, 10, 27, 4, 0))
        app.clock_service.tick_now()
        assert home.selectedDateKey == "2026-10-27" and home.isToday

    def test_gece_yarisindan_sonra_dunun_sabahi_vurgulanmaz(self, app, clock):
        # 00:30: takip günü 26 Ekim, sıradaki Sabah ise 27 Ekim'in Sabah'ı; 26 Ekim listesinde vurgu yok.
        clock.set(at(2026, 10, 27, 0, 30))
        home = app.home_bridge
        home.refresh()
        assert home.selectedDateKey == "2026-10-26"
        assert not any(r["isNext"] for r in home.prayers)
        assert home.nextPrayerName == "Sabah" and home.nextPrayerTime == "05:56"  # 27 Ekim Sabah'ı (26 Ekim: 05:55)

    def test_tik_nesnesi_dogrudan_verilebilir(self, app):
        tick = app.clock_service._logic.tick(at(2026, 10, 26, 12, 30, 0))
        assert isinstance(tick, Tick)
        app.home_bridge.on_tick(tick)
        assert app.home_bridge.countdown == "00:23:00"


class TestQazaBridge:
    @pytest.fixture
    def qaza_app(self, qapp):
        clock = FakeClock(at(2026, 10, 24, 12))
        container = AppContainer(AppDatabase.open_in_memory(), now=clock)  # install_date = 24 Ekim
        container.settings_service.use_manual_location(ISTANBUL)
        clock.set(at(2026, 10, 26, 12))
        container.home_bridge.refresh()
        container.qaza_bridge.refresh()
        yield container
        container.shutdown()

    def test_bos_baslangic(self, app):
        qaza = app.qaza_bridge
        assert qaza.isEmpty is True and qaza.groups == []
        assert qaza.summary["estimatedDays"] == -1 and qaza.summary["estimatedDateLabel"] == ""

    def test_gun_kartlari_ve_ozet(self, qaza_app):
        qaza = qaza_app.qaza_bridge
        groups = qaza.groups
        assert [g["dateKey"] for g in groups] == ["2026-10-25", "2026-10-24"]
        assert groups[0]["dateLabel"] == "25 Ekim 2026" and groups[0]["count"] == 5
        assert groups[0]["items"][0] == {"prayerKey": "fajr", "prayerName": "Sabah", "autoDetected": True}
        assert qaza.summary["autoCount"] == 10 and qaza.summary["grandTotal"] == 10
        assert qaza.isEmpty is False

    def test_kaza_et_listeyi_ve_vakitler_ekranini_yeniler(self, qaza_app):
        qaza, home = qaza_app.qaza_bridge, qaza_app.home_bridge
        changed = record(qaza.changed)
        assert qaza.compensate("2026-10-25", "fajr") is True
        assert qaza.groups[0]["count"] == 4 and qaza.summary["autoCount"] == 9 and changed
        home.openDay("2026-10-25")
        assert next(r for r in home.prayers if r["key"] == "fajr")["status"] == "compensated"

    def test_vakitler_ekranindan_isaretleme_kazayi_yeniler(self, qaza_app):
        qaza_app.home_bridge.markMissed("fajr")  # bugün (26 Ekim) kılmadım
        assert qaza_app.qaza_bridge.summary["autoCount"] == 11

    def test_gecersiz_anahtarlar_reddedilir(self, qaza_app):
        qaza = qaza_app.qaza_bridge
        assert qaza.compensate("bozuk", "fajr") is False
        assert qaza.compensate("2026-10-25", "yok") is False
        assert qaza.decrementBacklog("yok") is False

    def test_plan_kaydi_tahmin_ve_borc_dusme(self, qaza_app):
        qaza = qaza_app.qaza_bridge
        qaza.savePlan({"fajr": 10, "isha": "7", "asr": "abc"}, 3)  # QML'den metin de gelebilir
        backlog = {b["key"]: b["count"] for b in qaza.backlog}
        assert backlog == {"fajr": 10, "dhuhr": 0, "asr": 0, "maghrib": 0, "isha": 7}
        assert qaza.summary["grandTotal"] == 27 and qaza.summary["estimatedDays"] == 9
        assert qaza.summary["estimatedDateLabel"] == "4 Kasım 2026"
        assert qaza.decrementBacklog("fajr") is True
        assert qaza.backlog[0]["count"] == 9

    def test_sure_onizleme_kaydetmez(self, qaza_app):
        qaza = qaza_app.qaza_bridge
        preview = qaza.previewDuration(1, 0, 5, {"fajr": 3, "isha": "x"})
        assert preview == {"fajr": 3 + 370, "dhuhr": 370, "asr": 370, "maghrib": 370, "isha": 370}
        assert all(b["count"] == 0 for b in qaza.backlog)


class TestSettingsBridge:
    def test_varsayilanlar_ve_listeler(self, qapp):
        container = AppContainer(AppDatabase.open_in_memory(), now=FakeClock(at(2026, 10, 26, 12)))
        try:
            s = container.settings_bridge
            assert (s.themeKey, s.notificationsEnabled, s.reminderMinutes) == ("default", True, 15)
            assert s.calcMethodKey == "diyanet" and s.closeToTray is True and s.trayHintShown is False
            assert s.hasLocation is False and s.cityLabel == ""
            assert s.themeKeys == ["default", "dark", "ocean", "rose", "gold"]
            assert s.reminderChoices == [5, 10, 15, 20, 30, 45, 60]
            assert [m["key"] for m in s.calcMethods] == ["diyanet", "mwl", "egyptian", "karachi", "ummalqura", "isna"]
            assert s.calcMethods[0]["name"] == "Diyanet (Türkiye)"
        finally:
            container.shutdown()

    def test_gecersiz_degerler_reddedilir_gecerliler_kaydedilir(self, app):
        s = app.settings_bridge
        changes = record(s.settingsChanged)
        assert s.setThemeKey("neon") is False and s.themeKey == "default"
        assert s.setReminderMinutes(25) is False and s.reminderMinutes == 15
        assert s.setCalcMethod("yok") is False
        assert not changes
        assert s.setThemeKey("dark") is True and s.themeKey == "dark"
        assert s.setReminderMinutes(30) is True and s.reminderMinutes == 30
        s.setNotificationsEnabled(False)
        assert s.notificationsEnabled is False and changes

    def test_sehir_arama_ve_secimi_vakitleri_yeniler(self, app):
        s, home = app.settings_bridge, app.home_bridge
        found = s.searchCities("urfa")
        assert any(item["city"] == "Şanlıurfa" for item in found)
        invalidated = record(s.timesInvalidated)
        assert s.selectCity("kars") is True
        assert s.cityLabel == "Kars, Türkiye" and invalidated
        assert home.cityLabel == "Kars, Türkiye"
        assert home.prayers[0]["time"] != OCT26["fajr"]  # Kars'ın vakitleri İstanbul'dan farklı
        assert s.selectCity("Atlantis") is False

    def test_yontem_degisince_vakitler_yenilenir(self, app):
        s, home = app.settings_bridge, app.home_bridge
        before = home.prayers[0]["time"]
        assert s.setCalcMethod("egyptian") is True
        assert home.prayers[0]["time"] != before  # 19,5° daha erken Sabah

    def test_autostart_sorusu_ve_masaustu_ayarlari(self, app):
        s = app.settings_bridge
        assert s.needsAutostartPrompt is True and s.autostartEnabled is False
        s.setAutostart(False)
        assert s.needsAutostartPrompt is False and s.autostartEnabled is False
        s.setAutostart(True)
        assert s.autostartEnabled is True
        s.setCloseToTray(False)
        s.markTrayHintShown()
        assert s.closeToTray is False and s.trayHintShown is True


class TestQmlIntegration:
    def make_object(self, qapp, container, source: str):
        engine = QQmlApplicationEngine()
        container.register_context_properties(engine)
        component = QQmlComponent(engine)
        component.setData(source.encode("utf-8"), QUrl())
        obj = component.create()
        assert obj is not None, [e.toString() for e in component.errors()]
        return engine, component, obj  # bileşen yaşamalı: erken silinirse nesne de silinir

    def test_qmlden_okuma_ve_slot_cagrisi(self, app, qapp):
        engine, component, obj = self.make_object(
            qapp,
            app,
            """
            import QtQuick
            Item {
                property string city: homeBridge.cityLabel
                property int rows: homeBridge.prayers.length
                property string firstName: homeBridge.prayers[0].name
                property string next: homeBridge.nextPrayerName
                property string countdown: homeBridge.countdown
                property bool marked: homeBridge.markPerformed("fajr", true)
                property var preview: qazaBridge.previewDuration(0, 0, 5, ({fajr: 3}))
                property var methods: settingsBridge.calcMethods
                property bool prompt: settingsBridge.needsAutostartPrompt
            }
            """,
        )
        try:
            assert obj.property("city") == "İstanbul, Türkiye"
            assert obj.property("rows") == 6
            assert obj.property("firstName") == "Sabah"
            assert obj.property("next") == "Öğle"
            assert obj.property("countdown") == "00:53:00"
            assert obj.property("marked") is True
            assert obj.property("prompt") is True
            preview = obj.property("preview")
            preview = preview.toVariant() if hasattr(preview, "toVariant") else preview
            assert preview["fajr"] == 8 and preview["isha"] == 5
            methods = obj.property("methods")
            methods = methods.toVariant() if hasattr(methods, "toVariant") else methods
            assert len(methods) == 6
            assert app.home_bridge.prayers[0]["status"] == "performed"
        finally:
            obj.deleteLater()
            component.deleteLater()
            engine.deleteLater()
            qapp.processEvents()
