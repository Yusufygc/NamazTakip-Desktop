"""Ayar, vakit ve kaza servisleri (saat dilimi sabit UTC+3, bellek içi SQLite)."""

from datetime import date, timedelta

import pytest

from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.domain.prayer_times import CalcMethod, PrayerTimeService
from app.services.prayer_service import PrayerService
from app.services.settings_service import REMINDER_CHOICES, THEME_KEYS
from tests.support import ISTANBUL, OCT26, TZ, at, build_services


class TestSettingsService:
    def test_varsayilan_goruntu(self):
        s = build_services(at(2026, 10, 26, 12), with_location=False).settings
        view = s.settings
        assert view.theme_key == "default"
        assert view.notifications_enabled is True
        assert view.reminder_minutes == 15
        assert view.calc_method is CalcMethod.DIYANET
        assert view.location is None
        assert view.autostart is None
        assert view.close_to_tray is True
        assert view.tray_hint_shown is False

    def test_gecersiz_tema_ve_hatirlatma_reddedilir(self):
        s = build_services(at(2026, 10, 26, 12)).settings
        with pytest.raises(ValueError):
            s.set_theme("neon")
        with pytest.raises(ValueError):
            s.set_reminder_minutes(25)
        assert s.settings.theme_key == "default"
        assert s.settings.reminder_minutes == 15

    def test_gecerli_degerler_kalici(self):
        s = build_services(at(2026, 10, 26, 12)).settings
        for key in THEME_KEYS:
            s.set_theme(key)
            assert s.settings.theme_key == key
        for minutes in REMINDER_CHOICES:
            s.set_reminder_minutes(minutes)
            assert s.settings.reminder_minutes == minutes

    def test_sehir_arama_turkce_duyarsiz(self):
        s = build_services(at(2026, 10, 26, 12)).settings
        assert len(s.search_cities("")) == 81
        assert [c.city for c in s.search_cities("  istanbul ")] == ["İstanbul"]
        assert [c.city for c in s.search_cities("IĞDIR")] == ["Iğdır"]
        assert s.search_cities("zzz") == []
        assert "Şanlıurfa" in [c.city for c in s.search_cities("urfa")]

    def test_sehir_bulma_tam_ad(self):
        s = build_services(at(2026, 10, 26, 12)).settings
        assert s.find_city("istanbul").city == "İstanbul"
        assert s.find_city("Ist") is None  # tam eşleşme gerekir

    def test_autostart_sorusu_cevaplaninca_kalkar(self):
        s = build_services(at(2026, 10, 26, 12)).settings
        assert s.needs_autostart_prompt is True
        s.set_autostart(False)
        assert s.needs_autostart_prompt is False
        assert s.settings.autostart is False


class TestPrayerService:
    def test_konum_yokken_vakit_yok_ama_takip_gunu_0400_kuraliyla_calisir(self):
        p = build_services(at(2026, 10, 27, 0, 30), with_location=False).prayers
        assert p.times_for(date(2026, 10, 26)) is None
        assert p.upcoming_days() == []
        assert p.next_prayer() is None
        assert p.remaining_until_next() is None
        assert p.tracking_day() == date(2026, 10, 26)

    def test_vakitler_servisle_ayni(self):
        stack = build_services(at(2026, 10, 26, 12))
        got = stack.prayers.times_for(date(2026, 10, 26))
        expected = PrayerTimeService().compute(ISTANBUL, date(2026, 10, 26), CalcMethod.DIYANET, tz=TZ)
        assert got == expected
        assert [getattr(got, n).strftime("%H:%M") for n in OCT26] == list(OCT26.values())

    def test_onbellek_ayni_gunu_bir_kez_hesaplar_ayar_degisince_yeniler(self):
        stack = build_services(at(2026, 10, 26, 12))
        calls = []

        class Spy(PrayerTimeService):
            def compute(self, *args, **kwargs):
                calls.append(args)
                return super().compute(*args, **kwargs)

        service = PrayerService(stack.settings, stack.prayer_repo, now=stack.clock, time_service=Spy(), tz=TZ)
        day = date(2026, 10, 26)
        for _ in range(5):
            service.times_for(day)
        assert len(calls) == 1
        stack.settings.set_calc_method(CalcMethod.MWL)  # yöntem değişti
        service.times_for(day)
        assert len(calls) == 2
        stack.settings.use_manual_location(stack.settings.find_city("Kars"))  # şehir değişti
        service.times_for(day)
        assert len(calls) == 3

    @pytest.mark.parametrize(
        ("now", "expected"),
        [
            (at(2026, 6, 21, 3, 30), date(2026, 6, 21)),  # yaz: Sabah 03:24'te gün değişir
            (at(2026, 6, 21, 3, 10), date(2026, 6, 20)),
            (at(2026, 12, 21, 3, 59), date(2026, 12, 20)),  # kış: sınır 04:00
            (at(2026, 12, 21, 4, 0), date(2026, 12, 21)),
            (at(2026, 10, 26, 0, 30), date(2026, 10, 25)),
        ],
    )
    def test_takip_gunu_sabah_vaktiyle(self, now, expected):
        assert build_services(now).prayers.tracking_day(now) == expected

    def test_yatsidan_sonra_sirada_yarinin_sabahi(self):
        p = build_services(at(2026, 10, 26, 22)).prayers
        upcoming = p.next_prayer()
        assert upcoming.type is PrayerType.FAJR
        assert upcoming.time.date() == date(2026, 10, 27)
        assert p.remaining_until_next() > timedelta(hours=7)

    def test_tracking_start_install_date_yoksa_takip_gunu(self):
        stack = build_services(at(2026, 10, 26, 12))
        assert stack.prayers.tracking_start == date(2026, 10, 26)
        stack.settings.ensure_install_date(date(2026, 10, 20))
        assert stack.prayers.tracking_start == date(2026, 10, 20)

    def test_isaretleme_bugun_ve_gecmis_serbest_gelecek_yasak(self):
        stack = build_services(at(2026, 10, 26, 12))
        p = stack.prayers
        p.mark_performed(date(2026, 10, 26), PrayerType.FAJR, congregation=True)
        p.mark_missed(date(2026, 10, 25), PrayerType.ISHA)
        assert p.records_for_date(date(2026, 10, 26))[PrayerType.FAJR].is_congregation is True
        assert p.records_for_date(date(2026, 10, 25))[PrayerType.ISHA].status == PrayerStatus.MISSED
        with pytest.raises(ValueError):
            p.mark_performed(date(2026, 10, 27), PrayerType.FAJR)
        with pytest.raises(ValueError):
            p.mark_missed(date(2026, 10, 27), PrayerType.FAJR)
        assert p.records_for_date(date(2026, 10, 27)) == {}

    def test_gece_yarisindan_sonra_dunun_gunu_isaretlenir(self):
        # 00:30'da takip günü hâlâ 26 Ekim; 26 Ekim işaretlenebilir, 27 Ekim (takvim günü) işaretlenemez.
        p = build_services(at(2026, 10, 27, 0, 30)).prayers
        p.mark_performed(date(2026, 10, 26), PrayerType.ISHA)
        with pytest.raises(ValueError):
            p.mark_performed(date(2026, 10, 27), PrayerType.FAJR)


class TestQazaService:
    def stack(self):
        stack = build_services(at(2026, 10, 26, 12))
        stack.settings.ensure_install_date(date(2026, 10, 24))
        return stack

    def test_liste_baslangictan_dune_kadar_otomatik_kaza(self):
        items = self.stack().qaza.items()
        assert len(items) == 10  # 24 ve 25 Ekim: 2 gün x 5 vakit
        assert all(i.is_auto_detected for i in items)
        assert items[0].date == date(2026, 10, 25)

    def test_kaza_et_listeden_cikarir(self):
        stack = self.stack()
        item = stack.qaza.items()[0]
        stack.qaza.compensate(item)
        assert len(stack.qaza.items()) == 9
        assert stack.prayers.records_for_date(item.date)[item.prayer].status == PrayerStatus.COMPENSATED

    def test_bugun_kilmadim_denen_listeye_girer(self):
        stack = self.stack()
        stack.prayers.mark_missed(date(2026, 10, 26), PrayerType.FAJR)
        assert len(stack.qaza.items()) == 11

    def test_ozet_ve_tahmini_bitis(self):
        stack = self.stack()
        stack.qaza.save_plan({PrayerType.FAJR: 10, PrayerType.ISHA: 7}, daily_target=3)
        summary = stack.qaza.summary()
        assert summary.auto_count == 10
        assert summary.backlog_total == 17
        assert summary.grand_total == 27
        assert summary.daily_target == 3
        assert summary.estimated_days == 9  # ceil(27/3)
        assert summary.estimated_date == date(2026, 10, 26) + timedelta(days=9)

    def test_borc_yoksa_tahmin_yok(self):
        stack = build_services(at(2026, 10, 26, 12))
        summary = stack.qaza.summary()
        assert summary.grand_total == 0
        assert summary.estimated_days is None and summary.estimated_date is None

    def test_plan_kaydi_sinirlari_kirpar(self):
        stack = self.stack()
        stack.qaza.save_plan({PrayerType.FAJR: 5_000_000, PrayerType.ASR: -4}, daily_target=99)
        plan = stack.qaza.plan
        assert plan.count_for(PrayerType.FAJR) == 1_000_000
        assert plan.count_for(PrayerType.ASR) == 0
        assert plan.daily_target == 50

    def test_kaza_dus_ve_onizleme(self):
        stack = self.stack()
        stack.qaza.save_plan({PrayerType.MAGHRIB: 1}, daily_target=2)
        stack.qaza.decrement_backlog(PrayerType.MAGHRIB)
        stack.qaza.decrement_backlog(PrayerType.MAGHRIB)
        assert stack.qaza.plan.count_for(PrayerType.MAGHRIB) == 0
        preview = stack.qaza.preview_duration({p: 1 for p in PrayerType}, years=1, days=5)
        assert set(preview.values()) == {1 + 365 + 5}
        assert stack.qaza.plan.total_backlog == 0  # önizleme kaydetmez
