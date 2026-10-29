"""Takip günü, tarih yardımcıları ve sıradaki vakit (mobil `domain_test.dart` senaryoları)."""

from datetime import date, datetime, timedelta, timezone

from app.core.domain.dates import (
    add_days,
    date_key,
    days_between,
    days_diff,
    next_prayer,
    parse_date_key,
    prayer_day,
)
from app.core.domain.prayer import DayTimes, PrayerType

TZ = timezone(timedelta(hours=3))


def at(year, month, day, hour=0, minute=0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=TZ)


class TestPrayerDay:
    def test_gece_0030_hala_dunku_gun(self):
        assert prayer_day(at(2026, 1, 25, 0, 30)) == date(2026, 1, 24)

    def test_0359_dunku_0400_bugun(self):
        assert prayer_day(at(2026, 1, 25, 3, 59)) == date(2026, 1, 24)
        assert prayer_day(at(2026, 1, 25, 4, 0)) == date(2026, 1, 25)

    def test_ay_basinda_onceki_aya_duser(self):
        assert prayer_day(at(2026, 3, 1, 1, 0)) == date(2026, 2, 28)

    def test_yil_basinda_onceki_yila_duser(self):
        assert prayer_day(at(2026, 1, 1, 2, 0)) == date(2025, 12, 31)


class TestPrayerDayWithFajr:
    """Gün sınırı = min(04:00, Sabah vakti)."""

    summer_fajr = at(2026, 6, 21, 3, 24)  # İstanbul 21 Haziran
    winter_fajr = at(2026, 12, 21, 6, 46)  # İstanbul 21 Aralık

    def test_yazin_sabah_girince_gun_degisir(self):
        assert prayer_day(at(2026, 6, 21, 3, 30), self.summer_fajr) == date(2026, 6, 21)

    def test_yazin_sabahtan_once_hala_dunku_gun(self):
        assert prayer_day(at(2026, 6, 21, 3, 23), self.summer_fajr) == date(2026, 6, 20)
        assert prayer_day(at(2026, 6, 21, 3, 24), self.summer_fajr) == date(2026, 6, 21)

    def test_sabah_verilmezse_0400_kurali(self):
        assert prayer_day(at(2026, 6, 21, 3, 30)) == date(2026, 6, 20)

    def test_kisin_sinir_0400_kalir(self):
        assert prayer_day(at(2026, 12, 21, 3, 59), self.winter_fajr) == date(2026, 12, 20)
        assert prayer_day(at(2026, 12, 21, 4, 0), self.winter_fajr) == date(2026, 12, 21)
        assert prayer_day(at(2026, 12, 21, 5, 0), self.winter_fajr) == date(2026, 12, 21)

    def test_sabah_tam_0400(self):
        fajr = at(2026, 5, 1, 4, 0)
        assert prayer_day(at(2026, 5, 1, 3, 59), fajr) == date(2026, 4, 30)
        assert prayer_day(at(2026, 5, 1, 4, 0), fajr) == date(2026, 5, 1)

    def test_gece_yarisindan_sonra_yazin_da_dunku_gun(self):
        assert prayer_day(at(2026, 6, 21, 0, 30), self.summer_fajr) == date(2026, 6, 20)


class TestDateHelpers:
    def test_date_key_iso_ve_geri_cevirme(self):
        assert date_key(date(2026, 1, 5)) == "2026-01-05"
        assert parse_date_key("2026-01-05") == date(2026, 1, 5)

    def test_metin_siralamasi_tarih_siralamasidir(self):
        keys = ["2026-02-01", "2025-12-31", "2026-01-15"]
        assert sorted(keys) == ["2025-12-31", "2026-01-15", "2026-02-01"]

    def test_add_days_ay_ve_artik_yil(self):
        assert add_days(date(2026, 1, 31), 1) == date(2026, 2, 1)
        assert add_days(date(2028, 2, 28), 1) == date(2028, 2, 29)
        assert add_days(date(2026, 3, 1), -1) == date(2026, 2, 28)

    def test_days_between_iki_uc_dahil(self):
        assert list(days_between(date(2026, 1, 8), date(2026, 1, 10))) == [
            date(2026, 1, 8),
            date(2026, 1, 9),
            date(2026, 1, 10),
        ]
        assert list(days_between(date(2026, 1, 10), date(2026, 1, 10))) == [date(2026, 1, 10)]
        assert list(days_between(date(2026, 1, 11), date(2026, 1, 10))) == []

    def test_days_diff(self):
        assert days_diff(date(2026, 1, 10), date(2026, 1, 8)) == 2
        assert days_diff(date(2026, 1, 8), date(2026, 1, 10)) == -2


def make_day(d: date) -> DayTimes:
    def t(hour, minute=0):
        return datetime(d.year, d.month, d.day, hour, minute, tzinfo=TZ)

    return DayTimes(
        date=d, fajr=t(5), sunrise=t(6, 30), dhuhr=t(12), asr=t(15), maghrib=t(18), isha=t(19, 30)
    )


class TestNextPrayer:
    days = [make_day(date(2026, 1, 10)), make_day(date(2026, 1, 11))]

    def test_ogleden_sonra_ikindi(self):
        result = next_prayer(at(2026, 1, 10, 13), self.days)
        assert result is not None and result.type == PrayerType.ASR

    def test_yatsidan_sonra_yarinin_sabahi(self):
        result = next_prayer(at(2026, 1, 10, 22), self.days)
        assert result is not None
        assert result.type == PrayerType.FAJR
        assert result.time == at(2026, 1, 11, 5)

    def test_gece_yarisindan_sonra_ayni_takvim_gununun_sabahi(self):
        result = next_prayer(at(2026, 1, 11, 0, 30), self.days)
        assert result is not None and result.time == at(2026, 1, 11, 5)

    def test_gunes_siradaki_vakit_sayilmaz(self):
        # 05:30: Sabah geçti, Güneş (06:30) sıradaki sayılmaz, Öğle gelir.
        result = next_prayer(at(2026, 1, 10, 5, 30), self.days)
        assert result is not None and result.type == PrayerType.DHUHR

    def test_tam_vakit_aninda_sonraki_vakit(self):
        # 12:00 tam Öğle: o an geçmiş sayılır (strict), sıradaki İkindi.
        result = next_prayer(at(2026, 1, 10, 12, 0), self.days)
        assert result is not None and result.type == PrayerType.ASR

    def test_vakit_listesi_bos_none(self):
        assert next_prayer(at(2026, 1, 10, 13), []) is None
