"""Kaza türetme ve borç planlayıcı hesapları."""

from datetime import date

from app.core.domain.models import PrayerRecord, QazaDebtPlan, QazaItem
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.domain.qaza import (
    BACKLOG_MAX,
    add_duration_to_backlog,
    clamp_backlog,
    clamp_daily_target,
    decrement_backlog,
    derive_qaza_items,
    empty_backlog,
)

TODAY = date(2026, 1, 10)


def rec(day: date, prayer: PrayerType, status: PrayerStatus) -> PrayerRecord:
    return PrayerRecord(day, prayer, status)


class TestDeriveQazaItems:
    def test_bugun_bekleyen_vakit_kaza_degil(self):
        assert derive_qaza_items([], TODAY, TODAY) == []

    def test_bugun_kilmadim_denen_kaza_olur(self):
        items = derive_qaza_items([rec(TODAY, PrayerType.DHUHR, PrayerStatus.MISSED)], TODAY, TODAY)
        assert items == [QazaItem(TODAY, PrayerType.DHUHR, PrayerStatus.MISSED)]
        assert not items[0].is_auto_detected

    def test_isaretlenmeyen_gecmis_gunler_otomatik_kaza(self):
        items = derive_qaza_items([], date(2026, 1, 8), TODAY)
        assert len(items) == 10  # 8 ve 9 Ocak: 2 gün x 5 vakit
        assert all(i.is_auto_detected for i in items)
        assert items[0].date == date(2026, 1, 9)  # en yeni önce

    def test_bes_vakit_kilinmissa_gun_listeden_cikar(self):
        first = date(2026, 1, 9)
        records = [rec(first, p, PrayerStatus.PERFORMED) for p in PrayerType]
        assert derive_qaza_items(records, first, TODAY) == []

    def test_kaza_edilen_vakit_listeden_cikar(self):
        first = date(2026, 1, 9)
        items = derive_qaza_items([rec(first, PrayerType.FAJR, PrayerStatus.COMPENSATED)], first, TODAY)
        assert len(items) == 4
        assert all(i.prayer != PrayerType.FAJR for i in items)

    def test_gecmis_gunde_kilmadim_pending_gibi_kazadir_ama_durumu_korunur(self):
        first = date(2026, 1, 9)
        items = derive_qaza_items([rec(first, PrayerType.ASR, PrayerStatus.MISSED)], first, TODAY)
        asr = next(i for i in items if i.prayer == PrayerType.ASR)
        assert asr.status == PrayerStatus.MISSED
        assert not asr.is_auto_detected

    def test_siralama_tarih_azalan_vakit_artan(self):
        items = derive_qaza_items([], date(2026, 1, 8), date(2026, 1, 10))
        keys = [(i.date, i.prayer.index) for i in items]
        assert keys == sorted(keys, key=lambda k: (-k[0].toordinal(), k[1]))

    def test_baslangic_bugunden_sonra_ise_bos(self):
        assert derive_qaza_items([], date(2026, 1, 11), TODAY) == []


class TestQazaDebtPlan:
    def plan(self, counts: dict | None = None, target: int = 2) -> QazaDebtPlan:
        backlog = empty_backlog()
        backlog.update(counts or {})
        return QazaDebtPlan(backlog, target)

    def test_toplam_ve_genel_toplam(self):
        plan = self.plan({PrayerType.FAJR: 10, PrayerType.ISHA: 5})
        assert plan.total_backlog == 15
        assert plan.grand_total(3) == 18
        assert plan.count_for(PrayerType.FAJR) == 10
        assert plan.count_for(PrayerType.ASR) == 0

    def test_tahmini_bitis_yukari_yuvarlar(self):
        plan = self.plan({PrayerType.FAJR: 10}, target=3)
        assert plan.estimated_days_to_finish(0) == 4  # ceil(10/3)
        assert plan.estimated_days_to_finish(2) == 4  # ceil(12/3)
        assert plan.estimated_completion_date(0, TODAY) == date(2026, 1, 14)

    def test_borc_yoksa_tahmin_yok(self):
        plan = self.plan()
        assert plan.estimated_days_to_finish(0) is None
        assert plan.estimated_completion_date(0, TODAY) is None

    def test_otomatik_kaza_tek_basina_tahmin_uretir(self):
        assert self.plan(target=2).estimated_days_to_finish(5) == 3

    def test_hedef_sifirsa_tahmin_yok(self):
        assert self.plan({PrayerType.FAJR: 4}, target=0).estimated_days_to_finish(0) is None


class TestBacklogOperations:
    def test_sure_bes_vaktin_her_birine_eklenir(self):
        result = add_duration_to_backlog(empty_backlog(), years=1, months=2, days=3)
        assert set(result.values()) == {365 + 60 + 3}
        assert set(result) == set(PrayerType)

    def test_sure_mevcut_degerlere_eklenir(self):
        start = empty_backlog()
        start[PrayerType.FAJR] = 10
        result = add_duration_to_backlog(start, days=5)
        assert result[PrayerType.FAJR] == 15
        assert result[PrayerType.ISHA] == 5

    def test_sifir_veya_negatif_sure_degistirmez(self):
        start = empty_backlog()
        start[PrayerType.ASR] = 7
        assert add_duration_to_backlog(start) == start
        assert add_duration_to_backlog(start, days=-4) == start
        assert add_duration_to_backlog(start) is not start  # kopya döner

    def test_ekleme_ust_siniri_asmaz(self):
        start = empty_backlog()
        start[PrayerType.FAJR] = BACKLOG_MAX - 1
        assert add_duration_to_backlog(start, years=10)[PrayerType.FAJR] == BACKLOG_MAX

    def test_kaza_dus_sifirin_altina_inmez(self):
        start = empty_backlog()
        start[PrayerType.MAGHRIB] = 1
        once = decrement_backlog(start, PrayerType.MAGHRIB)
        assert once[PrayerType.MAGHRIB] == 0
        assert decrement_backlog(once, PrayerType.MAGHRIB)[PrayerType.MAGHRIB] == 0
        assert start[PrayerType.MAGHRIB] == 1  # giriş değişmez

    def test_sinirlar(self):
        assert clamp_backlog(-5) == 0
        assert clamp_backlog(2_000_000) == BACKLOG_MAX
        assert clamp_daily_target(0) == 1
        assert clamp_daily_target(99) == 50
        assert clamp_daily_target(7) == 7
