"""Vakitten önce haber ("Akşam vaktine 40 dk kaldı"): ayar, saat kararı, bildirime tıklama ve Ayarlar sayfası."""

from datetime import date

import pytest

from app.bridge.settings_bridge import SettingsBridge
from app.bridge.shell_bridge import ShellBridge
from app.core.domain.prayer import PrayerType
from app.services.clock_service import ClockLogic, NotificationKind, Tick
from app.services.settings_service import PRE_REMINDER_CHOICES
from tests.qml_support import close_ui, find, js, load_ui
from tests.support import at, build_services

# İstanbul 26 Ekim 2026: Öğle 12:53, İkindi 15:46, Akşam 18:15, Yatsı 19:35 (varsayılan: 40 dk önce).


@pytest.fixture
def stack():
    return build_services(at(2026, 10, 26, 10))


def logic_for(stack) -> ClockLogic:
    return ClockLogic(stack.prayers, stack.settings)


def kinds(tick: Tick) -> list[tuple[NotificationKind, PrayerType]]:
    return [(n.kind, n.prayer) for n in tick.notifications]


class TestAyar:
    def test_varsayilan_40_dakika(self, stack):
        assert stack.settings.settings.pre_reminder_minutes == 40

    def test_secenekler_kapaliyi_ve_40i_icerir(self):
        assert 0 in PRE_REMINDER_CHOICES and 40 in PRE_REMINDER_CHOICES

    def test_kaydedilir(self, stack):
        stack.settings.set_pre_reminder_minutes(20)
        assert stack.settings.settings.pre_reminder_minutes == 20
        stack.settings.set_pre_reminder_minutes(0)
        assert stack.settings.settings.pre_reminder_minutes == 0

    def test_gecersiz_deger_reddedilir_ve_yazilmaz(self, stack):
        with pytest.raises(ValueError):
            stack.settings.set_pre_reminder_minutes(7)
        assert stack.settings.settings.pre_reminder_minutes == 40

    def test_kopru_gecersizi_false_doner(self, qapp, stack):
        bridge = SettingsBridge(stack.settings)
        assert bridge.setPreReminderMinutes(7) is False
        assert bridge.preReminderMinutes == 40
        assert bridge.setPreReminderMinutes(30) is True
        assert bridge.preReminderMinutes == 30
        assert bridge.preReminderChoices == list(PRE_REMINDER_CHOICES)


class TestSaatKarari:
    def test_vakitten_40_dk_once_bir_kez_gelir(self, stack):
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 12, 12, 59)).notifications == ()
        tick = logic.tick(at(2026, 10, 26, 12, 13, 0))
        assert kinds(tick) == [(NotificationKind.PRE, PrayerType.DHUHR)]
        note = tick.notifications[0]
        assert (note.title, note.body) == ("Öğle vaktine 40 dk kaldı", "Vakit girişi: 12:53")
        assert note.day == date(2026, 10, 26)
        assert logic.tick(at(2026, 10, 26, 12, 13, 30)).notifications == ()  # aynı pencerede tekrar yok
        assert logic.tick(at(2026, 10, 26, 12, 14, 0)).notifications == ()  # pencere kapandı

    def test_bes_farz_vaktin_hepsi_icin_gelir(self, stack):
        logic = logic_for(stack)
        # İstanbul 26 Ekim: 05:55, 12:53, 15:46, 18:15, 19:35 -> 40 dk önce.
        for hour, minute, prayer in [
            (5, 15, PrayerType.FAJR),
            (12, 13, PrayerType.DHUHR),
            (15, 6, PrayerType.ASR),
            (17, 35, PrayerType.MAGHRIB),
            (18, 55, PrayerType.ISHA),
        ]:
            assert kinds(logic.tick(at(2026, 10, 26, hour, minute, 0))) == [(NotificationKind.PRE, prayer)]

    def test_gunes_icin_gelmez(self, stack):
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 6, 39, 0)).notifications == ()  # Güneş 07:19 - 40 dk

    def test_sure_ayardan_gelir(self, stack):
        stack.settings.set_pre_reminder_minutes(20)
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 12, 13, 0)).notifications == ()
        tick = logic.tick(at(2026, 10, 26, 12, 33, 0))
        assert [n.title for n in tick.notifications] == ["Öğle vaktine 20 dk kaldı"]

    def test_sifir_kapali_demektir(self, stack):
        stack.settings.set_pre_reminder_minutes(0)
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 12, 13, 0)).notifications == ()
        # 0 dk "vakit anında haber" değildir: ezan anında yalnızca ezan bildirimi gelir.
        assert kinds(logic.tick(at(2026, 10, 26, 12, 53, 0))) == [(NotificationKind.ADHAN, PrayerType.DHUHR)]

    def test_bildirimler_kapaliyken_gelmez(self, stack):
        stack.settings.set_notifications_enabled(False)
        assert logic_for(stack).tick(at(2026, 10, 26, 12, 13, 0)).notifications == ()

    def test_gec_acilista_gecmis_haber_yagmaz(self, stack):
        """Uygulama 12:30'da açılırsa 12:13'teki haber verilmez (60 sn penceresi)."""
        assert logic_for(stack).tick(at(2026, 10, 26, 12, 30, 0)).notifications == ()

    def test_haber_ezan_ve_hatirlatma_ayri_anlarda_gelir(self, stack):
        logic = logic_for(stack)
        seen = []
        for minute in (13, 53):  # 12:13 haber, 12:53 ezan
            seen += kinds(logic.tick(at(2026, 10, 26, 12, minute, 0)))
        seen += kinds(logic.tick(at(2026, 10, 26, 13, 8, 0)))  # 12:53 + 15 dk hatırlatma
        assert seen == [
            (NotificationKind.PRE, PrayerType.DHUHR),
            (NotificationKind.ADHAN, PrayerType.DHUHR),
            (NotificationKind.REMINDER, PrayerType.DHUHR),
        ]


class TestTiklama:
    def test_haber_tiklaninca_isaretleme_diyalogu_acilmaz(self, qapp, stack):
        """Henüz girmemiş vakit işaretlenemez: tıklama yalnızca pencereyi öne getirir."""
        shell = ShellBridge()
        prompts: list = []
        shell.promptRequested.connect(lambda *args: prompts.append(args))
        tick = logic_for(stack).tick(at(2026, 10, 26, 12, 13, 0))
        shell.on_notification(tick.notifications[0])
        shell.activateLastNotification()
        assert prompts == []

    def test_ezan_bildirimi_tiklaninca_diyalog_acilir(self, qapp, stack):
        shell = ShellBridge()
        prompts: list = []
        shell.promptRequested.connect(lambda *args: prompts.append(args))
        tick = logic_for(stack).tick(at(2026, 10, 26, 12, 53, 0))
        shell.on_notification(tick.notifications[0])
        shell.activateLastNotification()
        assert prompts == [("2026-10-26", "dhuhr")]

    def test_son_bildirim_unutulabilir(self, qapp, stack):
        shell = ShellBridge()
        prompts: list = []
        shell.promptRequested.connect(lambda *args: prompts.append(args))
        shell.on_notification(logic_for(stack).tick(at(2026, 10, 26, 12, 53, 0)).notifications[0])
        shell.forgetLastNotification()
        shell.activateLastNotification()
        assert prompts == []


class TestAyarlarSayfasi:
    @pytest.fixture
    def ui(self, qapp):
        handle = load_ui(qapp)
        handle.root.setProperty("pageIndex", 2)
        handle.qapp.processEvents()
        yield handle
        close_ui(handle)

    def test_secenekler_ve_varsayilan(self, ui):
        for minutes in PRE_REMINDER_CHOICES:
            assert find(ui, f"preReminderChip_{minutes}").property("selected") is (minutes == 40)

    def test_kapali_secenegi_kapali_yazar(self, ui):
        js(ui, find(ui, "preReminderChip_0"), "clicked()")
        assert ui.container.settings_service.settings.pre_reminder_minutes == 0
        assert find(ui, "preReminderChip_0").property("selected") is True
        assert find(ui, "preReminderChip_40").property("selected") is False

    def test_secilen_sure_saat_servisine_yansir(self, ui):
        js(ui, find(ui, "preReminderChip_20"), "clicked()")
        logic = ui.container.clock_service._logic
        assert logic.tick(at(2026, 10, 26, 12, 13, 0)).notifications == ()
        assert [n.kind for n in logic.tick(at(2026, 10, 26, 12, 33, 0)).notifications] == [NotificationKind.PRE]

    def test_bildirim_kapaliyken_pasif(self, ui):
        js(ui, find(ui, "notificationsSwitch"), "click()")
        assert find(ui, "preReminderChip_40").property("enabled") is False
        assert ui.messages.problems() == []
