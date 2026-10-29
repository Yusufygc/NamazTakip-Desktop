"""Saat servisi: tik kararları (60 sn kuralı, hatırlatma, gün değişimi) ve QTimer sarmalayıcısı."""

from datetime import date, timedelta

import pytest

from app.core import paths
from app.core.domain.prayer import PrayerType
from app.core.logger import LOG_FILE_NAME, setup_logging
from app.services.clock_service import ClockLogic, ClockService, NotificationKind, Tick
from tests.support import at, build_services

# İstanbul 26 Ekim 2026: Öğle 12:53, İkindi 15:46, Yatsı 19:35 (hatırlatma varsayılan 15 dk).


@pytest.fixture
def stack():
    return build_services(at(2026, 10, 26, 12))


def logic_for(stack) -> ClockLogic:
    return ClockLogic(stack.prayers, stack.settings)


def kinds(tick: Tick) -> list[tuple[NotificationKind, PrayerType]]:
    return [(n.kind, n.prayer) for n in tick.notifications]


class TestAdhanNotification:
    def test_vakit_aninda_bir_kez_tetiklenir(self, stack):
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 12, 52, 59)).notifications == ()
        tick = logic.tick(at(2026, 10, 26, 12, 53, 0))
        assert kinds(tick) == [(NotificationKind.ADHAN, PrayerType.DHUHR)]
        note = tick.notifications[0]
        assert (note.title, note.body) == ("Öğle Vakti", "Öğle vakti girdi.")
        assert note.day == date(2026, 10, 26)
        # Aynı pencerede tekrar gelmez.
        assert logic.tick(at(2026, 10, 26, 12, 53, 1)).notifications == ()
        assert logic.tick(at(2026, 10, 26, 12, 53, 59)).notifications == ()

    def test_pencere_60_sn_sonra_kapanir(self, stack):
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 12, 54, 0)).notifications == ()

    def test_gec_gelen_ilk_tik_pencere_icindeyse_tetikler(self, stack):
        logic = logic_for(stack)
        tick = logic.tick(at(2026, 10, 26, 12, 53, 30))
        assert kinds(tick) == [(NotificationKind.ADHAN, PrayerType.DHUHR)]

    def test_uykudan_donuste_eski_vakitler_yagmaz(self, stack):
        logic = logic_for(stack)
        logic.tick(at(2026, 10, 26, 10, 0))
        # 8 saat uyku: Öğle, İkindi, Akşam, Yatsı geçti; hiçbiri için bildirim yok.
        assert logic.tick(at(2026, 10, 26, 22, 0)).notifications == ()

    def test_yeniden_baslatmada_ayni_dakika_bir_kez_daha_gosterilebilir(self, stack):
        first = logic_for(stack).tick(at(2026, 10, 26, 12, 53, 10))
        second = logic_for(stack).tick(at(2026, 10, 26, 12, 53, 20))  # yeni oturum: bellek sıfır
        assert len(first.notifications) == len(second.notifications) == 1

    def test_bildirim_kapaliyken_veya_konum_yokken_yok(self, stack):
        stack.settings.set_notifications_enabled(False)
        assert logic_for(stack).tick(at(2026, 10, 26, 12, 53, 0)).notifications == ()
        bare = build_services(at(2026, 10, 26, 12), with_location=False)
        assert logic_for(bare).tick(at(2026, 10, 26, 12, 53, 0)).notifications == ()


class TestReminder:
    def test_isaretlenmemisse_hatirlatir(self, stack):
        logic = logic_for(stack)
        logic.tick(at(2026, 10, 26, 13, 7, 59))
        tick = logic.tick(at(2026, 10, 26, 13, 8, 0))  # 12:53 + 15 dk
        assert kinds(tick) == [(NotificationKind.REMINDER, PrayerType.DHUHR)]
        note = tick.notifications[0]
        assert note.title == "Öğle Namazını Kıldınız mı?"
        assert note.body == "Namazınızı işaretlemek için dokunun."
        assert logic.tick(at(2026, 10, 26, 13, 8, 1)).notifications == ()

    def test_kildim_denmisse_hatirlatmaz(self, stack):
        stack.prayers.mark_performed(date(2026, 10, 26), PrayerType.DHUHR)
        assert logic_for(stack).tick(at(2026, 10, 26, 13, 8, 0)).notifications == ()

    def test_kilmadim_denmisse_de_hatirlatmaz(self, stack):
        stack.prayers.mark_missed(date(2026, 10, 26), PrayerType.DHUHR)
        assert logic_for(stack).tick(at(2026, 10, 26, 13, 8, 0)).notifications == ()

    def test_hatirlatma_suresi_ayardan_gelir(self, stack):
        stack.settings.set_reminder_minutes(30)
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 13, 8, 0)).notifications == ()
        assert kinds(logic.tick(at(2026, 10, 26, 13, 23, 0))) == [(NotificationKind.REMINDER, PrayerType.DHUHR)]


class TestTickState:
    def test_siradaki_vakit_ve_kalan_sure(self, stack):
        tick = logic_for(stack).tick(at(2026, 10, 26, 12, 0, 0))
        assert tick.next_prayer.type is PrayerType.DHUHR
        assert tick.remaining == timedelta(minutes=53)
        assert tick.tracking_day == date(2026, 10, 26)

    def test_konum_yokken_sayac_yok(self):
        bare = build_services(at(2026, 10, 26, 12), with_location=False)
        tick = logic_for(bare).tick(at(2026, 10, 26, 12, 0, 0))
        assert tick.next_prayer is None and tick.remaining is None

    def test_gun_degisimi_yalnizca_gun_degisince_bildirilir(self, stack):
        logic = logic_for(stack)
        assert logic.tick(at(2026, 10, 26, 23, 59, 0)).day_changed is False  # ilk tik değişim sayılmaz
        assert logic.tick(at(2026, 10, 27, 0, 30, 0)).day_changed is False  # hâlâ 26 Ekim takip günü
        changed = logic.tick(at(2026, 10, 27, 4, 0, 0))
        assert changed.day_changed is True and changed.tracking_day == date(2026, 10, 27)
        assert logic.tick(at(2026, 10, 27, 4, 0, 1)).day_changed is False

    def test_eski_tetik_kayitlari_temizlenir(self, stack):
        logic = logic_for(stack)
        logic.tick(at(2026, 10, 26, 12, 53, 0))
        assert logic._fired
        logic.tick(at(2026, 10, 31, 12, 0, 0))
        assert not any(key[0] == date(2026, 10, 26) for key in logic._fired)


class TestClockService:
    def test_baslat_hemen_tik_atar_ve_zamanlayici_calisir(self, qapp, stack):
        ticks, notes = [], []
        service = ClockService(logic_for(stack), stack.clock)
        service.ticked.connect(ticks.append)
        service.notification.connect(notes.append)
        stack.clock.set(at(2026, 10, 26, 12, 53, 0))
        service.start()
        try:
            assert service.is_active
            assert len(ticks) == 1
            assert [n.kind for n in notes] == [NotificationKind.ADHAN]
        finally:
            service.stop()
        assert not service.is_active

    def test_mantik_hata_verirse_loglanir_zamanlayici_dusmez(self, qapp, stack):
        setup_logging()

        class Broken:
            def tick(self, now):
                raise RuntimeError("deneme")

        service = ClockService(Broken(), stack.clock)
        service.tick_now()  # istisna dışarı çıkmaz
        text = (paths.logs_dir() / LOG_FILE_NAME).read_text(encoding="utf-8")
        assert "Saat tiki işlenemedi" in text and "deneme" in text
