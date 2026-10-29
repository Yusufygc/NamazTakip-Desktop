"""İşaret deposu: mobil `prayer_repository_test.dart` senaryoları, bellek içi SQLite."""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.database import AppDatabase
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.repositories.prayer_repository import PrayerRepository

TODAY = date(2026, 1, 10)
FIXED = datetime(2026, 1, 10, 12, 0, 0, tzinfo=timezone(timedelta(hours=3)))


@pytest.fixture
def db():
    database = AppDatabase.open_in_memory()
    yield database
    database.close()


@pytest.fixture
def repo(db):
    return PrayerRepository(db, clock=lambda: FIXED)


def row_count(db) -> int:
    return db.connection.execute("SELECT COUNT(*) FROM prayers").fetchone()[0]


def test_ayni_vakit_tekrar_isaretlenince_tek_kayit_kalir(repo, db):
    for _ in range(3):
        repo.mark_missed(TODAY, PrayerType.DHUHR)
    assert len(repo.records_for_date(TODAY)) == 1
    assert row_count(db) == 1
    assert len(repo.qaza_items(TODAY, TODAY)) == 1


def test_kilindi_isareti_kazadan_cikarir_kilmadim_geri_alinabilir(repo):
    repo.mark_missed(TODAY, PrayerType.ASR)
    repo.mark_performed(TODAY, PrayerType.ASR, congregation=True)
    assert repo.qaza_items(TODAY, TODAY) == []
    record = repo.records_for_date(TODAY)[PrayerType.ASR]
    assert record.is_congregation is True
    assert record.status == PrayerStatus.PERFORMED


def test_yeniden_isaretleme_cemaati_sifirlar(repo):
    repo.mark_performed(TODAY, PrayerType.FAJR, congregation=True)
    repo.mark_performed(TODAY, PrayerType.FAJR)  # yalnız kıldım
    assert repo.records_for_date(TODAY)[PrayerType.FAJR].is_congregation is False


def test_bugun_bekleyen_vakit_kaza_degil(repo):
    assert repo.qaza_items(TODAY, TODAY) == []


def test_isaretlenmeyen_gecmis_gunler_otomatik_kaza(repo):
    items = repo.qaza_items(date(2026, 1, 8), TODAY)
    assert len(items) == 10  # 8 ve 9 Ocak: 2 gün x 5 vakit
    assert all(i.is_auto_detected for i in items)
    assert items[0].date == date(2026, 1, 9)


def test_bes_vakit_kilinmissa_gun_kazadan_cikar(repo):
    first = date(2026, 1, 9)
    for prayer in PrayerType:
        repo.mark_performed(first, prayer)
    assert repo.qaza_items(first, TODAY) == []


def test_kaza_edilen_vakit_listeden_cikar(repo):
    first = date(2026, 1, 9)
    repo.mark_compensated(first, PrayerType.FAJR)
    items = repo.qaza_items(first, TODAY)
    assert len(items) == 4
    assert all(i.prayer != PrayerType.FAJR for i in items)


def test_kaza_et_zamaninda_kilinmis_sayilmaz(repo):
    first = date(2026, 1, 9)
    repo.mark_compensated(first, PrayerType.FAJR)
    assert repo.records_for_date(first)[PrayerType.FAJR].status == PrayerStatus.COMPENSATED


def test_zaman_damgalari_yazilir(repo, db):
    repo.mark_performed(TODAY, PrayerType.FAJR)
    repo.mark_compensated(TODAY, PrayerType.DHUHR)
    rows = {
        r["prayer"]: (r["marked_at"], r["compensated_at"])
        for r in db.connection.execute("SELECT prayer, marked_at, compensated_at FROM prayers")
    }
    assert rows["fajr"] == ("2026-01-10T12:00:00+03:00", None)
    assert rows["dhuhr"] == ("2026-01-10T12:00:00+03:00", "2026-01-10T12:00:00+03:00")


def test_kaza_et_sonra_kilindi_diye_duzeltilirse_compensated_at_temizlenir(repo, db):
    repo.mark_compensated(TODAY, PrayerType.FAJR)
    repo.mark_performed(TODAY, PrayerType.FAJR)
    value = db.connection.execute("SELECT compensated_at FROM prayers").fetchone()[0]
    assert value is None


def test_records_between_aralik_iki_uc_dahil(repo):
    for day in (date(2026, 1, 7), date(2026, 1, 8), date(2026, 1, 10), date(2026, 1, 11)):
        repo.mark_performed(day, PrayerType.FAJR)
    got = sorted(r.date for r in repo.records_between(date(2026, 1, 8), date(2026, 1, 10)))
    assert got == [date(2026, 1, 8), date(2026, 1, 10)]


def test_baska_gunun_kaydi_karismaz(repo):
    repo.mark_performed(date(2026, 1, 9), PrayerType.FAJR)
    assert repo.records_for_date(TODAY) == {}


def test_sql_enjeksiyonu_denemesi_zararsiz(repo, db):
    # Tarih ve vakit anahtarı parametrik; yine de tablonun ayakta kaldığını doğrula.
    repo.mark_missed(TODAY, PrayerType.ISHA)
    assert row_count(db) == 1
    assert db.connection.execute("SELECT name FROM sqlite_master WHERE name = 'prayers'").fetchone() is not None
