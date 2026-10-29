"""Vakit hesabı: mobil (adhan_dart 2.0.1) ile aynı sonuç ve temel davranışlar."""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.domain.cities import CITIES
from app.core.domain.prayer import DayTimes, PrayerType
from app.core.domain.prayer_times import (
    SUNRISE_CAUTION_OFFSET,
    AppLocation,
    CalcMethod,
    PrayerTimeService,
    _round_half_up_minute,
)

GOLDEN = Path(__file__).parent / "data" / "golden_times.json"
UTC = timezone.utc
UTC3 = timezone(timedelta(hours=3))
ISTANBUL = AppLocation(41.0082, 28.9784, "İstanbul", "Türkiye")
FIELDS = ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha")


@pytest.fixture(scope="module")
def golden():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def test_golden_vektor_mobille_ayni(golden):
    """Tüm satırlar saniye düzeyinde eşit olmalı; tolerans yok."""
    service = PrayerTimeService()
    mismatches = []
    for row in golden["rows"]:
        city = golden["cities"][row["c"]]
        location = AppLocation(city["lat"], city["lon"], city["city"], "Türkiye")
        day = date.fromisoformat(row["d"])
        times = service.compute(location, day, CalcMethod.from_key(row["m"]), tz=UTC)
        got = [int(getattr(times, name).timestamp()) for name in FIELDS]
        if got != row["t"]:
            diff = [f"{n}:{(g - e) // 1}s" for n, g, e in zip(FIELDS, got, row["t"]) if g != e]
            mismatches.append(f"{city['city']} {row['d']} {row['m']} {diff}")
    assert len(golden["rows"]) >= 1000
    assert not mismatches, f"{len(mismatches)} farklı satır, ilk 15: {mismatches[:15]}"


def test_il_listesi_mobille_ayni(golden):
    assert len(CITIES) == 81
    assert [(c.city, c.latitude, c.longitude) for c in CITIES] == [
        (c["city"], c["lat"], c["lon"]) for c in golden["cities"]
    ]
    assert {c.country for c in CITIES} == {"Türkiye"}


def test_istanbul_26_ekim_bilinen_degerler():
    t = PrayerTimeService().compute(ISTANBUL, date(2026, 10, 26), CalcMethod.DIYANET, tz=UTC3)
    got = [getattr(t, name).strftime("%H:%M") for name in FIELDS]
    # Güneş 07:19: ham 07:20:41 − 90 sn, saniye kesilir (mobil kod kuralı; mobil belgesindeki 07:21 yuvarlak değerdir).
    assert got == ["05:55", "07:19", "12:53", "15:46", "18:15", "19:35"]


def test_vakitler_sirali_ve_saniyesiz():
    t = PrayerTimeService().compute(ISTANBUL, date(2026, 6, 21), CalcMethod.DIYANET, tz=UTC3)
    ordered = [getattr(t, name) for name in FIELDS]
    assert ordered == sorted(ordered)
    assert all(m.second == 0 and m.microsecond == 0 for m in ordered)


def test_gunes_dogusu_ihtiyat_payi_90_sn():
    assert SUNRISE_CAUTION_OFFSET == timedelta(seconds=90)


def test_sistem_saat_dilimi_aware_doner():
    t = PrayerTimeService().compute(ISTANBUL, date(2026, 10, 26), CalcMethod.DIYANET)
    assert t.fajr.tzinfo is not None
    assert t.date == date(2026, 10, 26)


def test_time_of_bes_farz_vakti_verir():
    t = PrayerTimeService().compute(ISTANBUL, date(2026, 10, 26), CalcMethod.DIYANET, tz=UTC3)
    assert isinstance(t, DayTimes)
    assert t.time_of(PrayerType.FAJR) == t.fajr
    assert t.time_of(PrayerType.ISHA) == t.isha
    assert [t.time_of(p) for p in PrayerType] == [t.fajr, t.dhuhr, t.asr, t.maghrib, t.isha]


@pytest.mark.parametrize(
    ("second", "expected_minute"),
    [(0, 10), (29, 10), (30, 11), (59, 11)],
)
def test_yarim_dakika_yukari_yuvarlanir(second, expected_minute):
    assert _round_half_up_minute(datetime(2026, 1, 1, 5, 10, second, tzinfo=UTC)).minute == expected_minute


def test_saat_basina_tasan_yuvarlama():
    # adhanpy kendi yuvarlayıcısında 59:40 gibi değerleri aşağı atar; burada saate taşmalı.
    assert _round_half_up_minute(datetime(2026, 1, 1, 5, 59, 40, tzinfo=UTC)) == datetime(2026, 1, 1, 6, 0, tzinfo=UTC)


def test_yontem_anahtarlari_ve_varsayilan():
    assert [m.key for m in CalcMethod] == ["diyanet", "mwl", "egyptian", "karachi", "ummalqura", "isna"]
    assert CalcMethod.from_key("mwl") is CalcMethod.MWL
    assert CalcMethod.from_key("bilinmeyen") is CalcMethod.DIYANET
    assert CalcMethod.from_key(None) is CalcMethod.DIYANET


def test_yontemler_farkli_vakit_uretir():
    service = PrayerTimeService()
    day = date(2026, 10, 26)
    fajrs = {m: service.compute(ISTANBUL, day, m, tz=UTC3).fajr for m in CalcMethod}
    assert fajrs[CalcMethod.DIYANET] == fajrs[CalcMethod.MWL]  # ikisi de 18°
    assert fajrs[CalcMethod.EGYPTIAN] < fajrs[CalcMethod.DIYANET]  # 19,5° daha erken
    assert fajrs[CalcMethod.NORTH_AMERICA] > fajrs[CalcMethod.DIYANET]  # 15° daha geç


def test_konum_etiketi_ve_json():
    assert ISTANBUL.label == "İstanbul, Türkiye"
    assert AppLocation(1.0, 2.0, "X").label == "X"
    assert AppLocation.from_json(ISTANBUL.to_json()) == ISTANBUL


@pytest.mark.parametrize(
    "bozuk",
    [None, {}, {"lat": "41", "lon": 29}, {"lat": 41, "lon": None}, {"lat": True, "lon": 1}, "metin", []],
)
def test_bozuk_konum_json_none_verir(bozuk):
    assert AppLocation.from_json(bozuk) is None


def test_eksik_sehir_ulke_bos_metin_olur():
    loc = AppLocation.from_json({"lat": 41, "lon": 29})
    assert loc == AppLocation(41.0, 29.0, "", "")
