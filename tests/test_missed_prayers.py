"""Açılışta "uygulama kapalıyken giren vakitleri kıldınız mı?": aday bulma, köprü, container ve diyalog."""

from datetime import date, timedelta

import pytest

from app.bridge.missed_bridge import MissedBridge
from app.container import AppContainer
from app.core.database import AppDatabase
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.services.autostart_service import AutostartService
from app.services.missed_prayer_service import LOOKBACK_DAYS, MissedPrayerService
from tests.qml_support import close_ui, find, js, load_ui
from tests.support import FAKE_EXE, ISTANBUL, FakeClock, FakeRegistry, at, build_services

# İstanbul 26 Ekim 2026: Sabah 05:55, Öğle 12:53, İkindi 15:46, Akşam 18:15, Yatsı 19:35.
DAY = date(2026, 10, 26)


@pytest.fixture
def stack():
    built = build_services(at(2026, 10, 26, 20))
    built.settings.ensure_install_date(date(2026, 10, 1))
    built.missed = MissedPrayerService(built.settings, built.prayers)
    return built


def found(stack, now) -> list[tuple[date, PrayerType]]:
    return [(item.day, item.prayer) for item in stack.missed.find(now)]


class TestAdayBulma:
    def test_son_calisma_yoksa_sormaz(self, stack):
        assert found(stack, at(2026, 10, 26, 20)) == []

    def test_kapaliyken_giren_vakitler_sirayla_bulunur(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 26, 17))
        assert found(stack, at(2026, 10, 26, 20)) == [(DAY, PrayerType.MAGHRIB), (DAY, PrayerType.ISHA)]

    def test_henuz_girmemis_vakit_sorulmaz(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 26, 17))
        assert found(stack, at(2026, 10, 26, 18)) == []
        assert found(stack, at(2026, 10, 26, 18, 15, 0)) == [(DAY, PrayerType.MAGHRIB)]  # tam vakit anı dahil

    def test_son_calismadan_once_giren_vakit_sorulmaz(self, stack):
        """Uygulama açıkken giren vakit hatırlatma bildirimiyle sorulur, açılışta tekrar sorulmaz."""
        stack.settings.set_last_active_at(at(2026, 10, 26, 18, 15, 0))
        assert found(stack, at(2026, 10, 26, 20)) == [(DAY, PrayerType.ISHA)]

    def test_isaretlenmis_vakit_sorulmaz(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 26, 12))
        stack.prayers.mark_performed(DAY, PrayerType.ASR)
        stack.prayers.mark_missed(DAY, PrayerType.MAGHRIB)
        assert found(stack, at(2026, 10, 26, 20)) == [(DAY, PrayerType.DHUHR), (DAY, PrayerType.ISHA)]

    def test_gunes_sorulmaz(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 26, 5))
        assert (DAY, PrayerType.FAJR) in found(stack, at(2026, 10, 26, 8))
        assert len(found(stack, at(2026, 10, 26, 8))) == 1  # Güneş 07:19 sayılmadı

    def test_gece_yarisini_asan_kapanis(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 25, 22))
        assert found(stack, at(2026, 10, 26, 13)) == [(DAY, PrayerType.FAJR), (DAY, PrayerType.DHUHR)]

    def test_uzun_aradan_sonra_yalniz_son_uc_gun(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 15, 12))
        items = found(stack, at(2026, 10, 26, 13))
        assert {day for day, _ in items} == {date(2026, 10, 24), date(2026, 10, 25), date(2026, 10, 26)}
        assert len(items) == 5 + 5 + 2
        assert LOOKBACK_DAYS == 3

    def test_takip_baslangicindan_onceki_gunler_sorulmaz(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 25, 22))
        built = build_services(at(2026, 10, 26, 13))
        built.settings.ensure_install_date(DAY)
        built.settings.set_last_active_at(at(2026, 10, 25, 22))
        service = MissedPrayerService(built.settings, built.prayers)
        assert [(i.day, i.prayer) for i in service.find(at(2026, 10, 26, 13))] == [
            (DAY, PrayerType.FAJR),
            (DAY, PrayerType.DHUHR),
        ]

    def test_sehir_yokken_sormaz(self):
        built = build_services(at(2026, 10, 26, 20), with_location=False)
        built.settings.set_last_active_at(at(2026, 10, 26, 10))
        assert MissedPrayerService(built.settings, built.prayers).find(at(2026, 10, 26, 20)) == []

    def test_bozuk_son_calisma_degeri_yok_sayilir(self, stack):
        stack.database.connection.execute(
            "INSERT INTO settings (key, value) VALUES ('last_active_at', '2026-10-26T17:00:00')"  # saat dilimi yok
        )
        assert stack.settings.last_active_at is None
        stack.database.connection.execute("UPDATE settings SET value = 'bozuk' WHERE key = 'last_active_at'")
        assert stack.settings.last_active_at is None
        assert found(stack, at(2026, 10, 26, 20)) == []


class TestSonCalismaAni:
    def test_dakikada_bir_yazilir(self, stack):
        stack.missed.touch(at(2026, 10, 26, 20, 0, 0))
        assert stack.settings.last_active_at == at(2026, 10, 26, 20, 0, 0)
        stack.missed.touch(at(2026, 10, 26, 20, 0, 30))  # çok erken: yazılmaz
        assert stack.settings.last_active_at == at(2026, 10, 26, 20, 0, 0)
        stack.missed.touch(at(2026, 10, 26, 20, 1, 0))
        assert stack.settings.last_active_at == at(2026, 10, 26, 20, 1, 0)

    def test_zorla_her_zaman_yazar(self, stack):
        stack.missed.touch(at(2026, 10, 26, 20, 0, 0))
        stack.missed.touch(at(2026, 10, 26, 20, 0, 5), force=True)
        assert stack.settings.last_active_at == at(2026, 10, 26, 20, 0, 5)

    def test_saat_dilimiyle_gidis_donus(self, stack):
        stack.settings.set_last_active_at(at(2026, 10, 26, 17, 30, 15))
        assert stack.settings.last_active_at == at(2026, 10, 26, 17, 30, 15)
        assert stack.settings.last_active_at.utcoffset() == timedelta(hours=3)


class TestCevap:
    def test_kildim_ve_kilmadim_yazilir(self, stack):
        stack.missed.answer(DAY, PrayerType.MAGHRIB, True)
        stack.missed.answer(DAY, PrayerType.ISHA, False)
        records = stack.prayers.records_for_date(DAY)
        assert records[PrayerType.MAGHRIB].status == PrayerStatus.PERFORMED
        assert records[PrayerType.ISHA].status == PrayerStatus.MISSED


class TestKopru:
    @pytest.fixture
    def bridge(self, qapp, stack):
        stack.settings.set_last_active_at(at(2026, 10, 26, 17))
        return MissedBridge(stack.missed, stack.clock)

    def test_yukleme_listeyi_ve_satirlari_verir(self, bridge):
        bridge.load()
        assert bridge.count == 2
        assert bridge.items == [
            {"dayKey": "2026-10-26", "prayerKey": "maghrib", "name": "Akşam", "dateLabel": "26 Ekim 2026", "timeLabel": "18:15"},
            {"dayKey": "2026-10-26", "prayerKey": "isha", "name": "Yatsı", "dateLabel": "26 Ekim 2026", "timeLabel": "19:35"},
        ]

    def test_ayni_vakitler_ikinci_acilista_sorulmaz(self, bridge):
        bridge.load()
        bridge.load()  # ilk yükleme son çalışma anını şimdiye aldı
        assert bridge.count == 0

    def test_cevap_satiri_kaldirir_ve_yenileme_ister(self, bridge, stack):
        bridge.load()
        refreshed: list = []
        bridge.recordsChanged.connect(lambda: refreshed.append(True))
        assert bridge.answer("2026-10-26", "maghrib", True) is True
        assert bridge.count == 1 and bridge.items[0]["prayerKey"] == "isha"
        assert refreshed == [True]
        assert stack.prayers.records_for_date(DAY)[PrayerType.MAGHRIB].status == PrayerStatus.PERFORMED

    def test_bilinmeyen_satir_reddedilir(self, bridge):
        bridge.load()
        assert bridge.answer("2026-10-26", "asr", True) is False
        assert bridge.answer("2026-10-26", "xyz", True) is False
        assert bridge.count == 2

    def test_sonra_listeyi_bosaltir_ve_kayit_yazmaz(self, bridge, stack):
        bridge.load()
        bridge.dismiss()
        assert bridge.count == 0
        assert stack.prayers.records_for_date(DAY) == {}


class TestContainer:
    def test_acilis_isleri_kacirilanlari_yukler_ve_kapanista_zamani_yazar(self, qapp):
        clock = FakeClock(at(2026, 10, 26, 17))
        container = AppContainer(
            AppDatabase.open_in_memory(), now=clock, autostart=AutostartService(FakeRegistry(), lambda: FAKE_EXE)
        )
        container.settings_service.use_manual_location(ISTANBUL)
        container.settings_service.set_last_active_at(at(2026, 10, 26, 12))
        clock.set(at(2026, 10, 26, 20))
        container.run_startup_tasks()
        assert container.missed_bridge.count == 4  # Öğle, İkindi, Akşam, Yatsı (12:00'den sonra)
        assert container.settings_service.last_active_at == at(2026, 10, 26, 20)
        clock.set(at(2026, 10, 26, 20, 30))
        container.shutdown()
        # Veritabanı kapandı; zaman yazılmış olmalı (yeniden açılamayan bellek içi DB'de kapanıştan önce doğrulanamaz)

    def test_saat_tiki_son_calisma_anini_gunceller(self, qapp):
        clock = FakeClock(at(2026, 10, 26, 20))
        container = AppContainer(AppDatabase.open_in_memory(), now=clock)
        try:
            container.settings_service.use_manual_location(ISTANBUL)
            container.run_startup_tasks()
            clock.set(at(2026, 10, 26, 20, 5))
            container.clock_service.tick_now()
            assert container.settings_service.last_active_at == at(2026, 10, 26, 20, 5)
        finally:
            container.shutdown()


class TestDiyalog:
    @pytest.fixture
    def ui(self, qapp):
        handle = load_ui(qapp, now=at(2026, 10, 26, 20), installed=at(2026, 10, 26, 8), last_active=at(2026, 10, 26, 17))
        # Autostart sorusu önce gelir; cevaplanınca açılış sorusu açılır.
        js(handle, find(handle, "autostartPromptDialog"), "answer(false)")
        yield handle
        close_ui(handle)

    def dialog(self, ui):
        return find(ui, "missedPrayersDialog")

    def test_autostart_sorusundan_sonra_acilir(self, ui):
        assert self.dialog(ui).property("opened") is True
        assert find(ui, "missedRow_2026-10-26_maghrib") is not None
        assert find(ui, "missedRow_2026-10-26_isha") is not None
        assert ui.messages.problems() == []

    def test_autostart_sorusu_aciksa_acilmaz(self, qapp):
        handle = load_ui(qapp, now=at(2026, 10, 26, 20), installed=at(2026, 10, 26, 8), last_active=at(2026, 10, 26, 17))
        try:
            assert find(handle, "autostartPromptDialog").property("opened") is True
            assert find(handle, "missedPrayersDialog").property("opened") is False
        finally:
            close_ui(handle)

    def test_kildim_isaretler_ve_diyalog_acik_kalir(self, ui):
        js(ui, find(ui, "missedPerformed_2026-10-26_maghrib"), "clicked()")
        records = ui.container.prayer_service.records_for_date(DAY)
        assert records[PrayerType.MAGHRIB].status == PrayerStatus.PERFORMED
        assert self.dialog(ui).property("opened") is True
        assert ui.container.missed_bridge.count == 1

    def test_hepsi_cevaplaninca_kapanir_ve_ekranlar_yenilenir(self, ui):
        js(ui, find(ui, "missedPerformed_2026-10-26_maghrib"), "clicked()")
        js(ui, find(ui, "missedMissed_2026-10-26_isha"), "clicked()")
        assert self.dialog(ui).property("opened") is False
        statuses = {row["key"]: row["status"] for row in ui.container.home_bridge.prayers if not row["isSunrise"]}
        assert statuses["maghrib"] == "performed" and statuses["isha"] == "missed"
        qaza = [(item.date, item.prayer) for item in ui.container.qaza_service.items()]
        assert qaza == [(DAY, PrayerType.ISHA)]  # "kılmadım" kazaya düşer, "kıldım" düşmez
        assert ui.container.qaza_bridge.isEmpty is False  # Kaza ekranı da yenilendi

    def test_sonra_hicbir_sey_yazmaz_ve_tekrar_acilmaz(self, ui):
        js(ui, find(ui, "missedLater"), "clicked()")
        assert self.dialog(ui).property("opened") is False
        assert ui.container.prayer_service.records_for_date(DAY) == {}
        ui.root.hide()
        ui.root.show()
        ui.qapp.processEvents()
        assert self.dialog(ui).property("opened") is False

    def test_kapatma_kalanlari_sormaz(self, ui):
        js(ui, self.dialog(ui), "close()")
        assert ui.container.missed_bridge.count == 0

    def test_aday_yoksa_acilmaz(self, qapp):
        handle = load_ui(qapp, now=at(2026, 10, 26, 20), installed=at(2026, 10, 26, 8))
        try:
            js(handle, find(handle, "autostartPromptDialog"), "answer(false)")
            assert find(handle, "missedPrayersDialog").property("opened") is False
        finally:
            close_ui(handle)
