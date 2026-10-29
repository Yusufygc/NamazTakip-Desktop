"""Günlük veritabanı yedeği: yeni dosya, günde bir, son 7, hata dayanıklılığı."""

from datetime import date, timedelta

import pytest

from app.core.backup import BACKUP_KEEP, backup_path, run_daily_backup
from app.core.database import FILE_NAME, AppDatabase
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.repositories.prayer_repository import PrayerRepository

TODAY = date(2026, 10, 30)


@pytest.fixture
def db(tmp_path):
    database = AppDatabase.open(tmp_path / FILE_NAME)
    PrayerRepository(database).mark_performed(date(2026, 10, 29), PrayerType.FAJR, congregation=True)
    yield database
    database.close()


def test_yedek_alinir_ve_veriyi_icerir(db, tmp_path):
    folder = tmp_path / "yedekler"
    created = run_daily_backup(db, TODAY, folder)
    assert created == backup_path(folder, TODAY)
    assert created.name == "namaz_takip-20261030.db"
    assert [p.name for p in folder.iterdir()] == ["namaz_takip-20261030.db"]  # .partial kalmaz
    restored = AppDatabase.open(created)
    try:
        record = PrayerRepository(restored).records_for_date(date(2026, 10, 29))[PrayerType.FAJR]
        assert (record.status, record.is_congregation) == (PrayerStatus.PERFORMED, True)
    finally:
        restored.close()


def test_ayni_gun_ikinci_kez_alinmaz(db, tmp_path):
    folder = tmp_path / "yedekler"
    assert run_daily_backup(db, TODAY, folder) is not None
    assert run_daily_backup(db, TODAY, folder) is None
    assert len(list(folder.iterdir())) == 1


def test_yedek_acik_veritabanindan_sonraki_yazimi_icermez_ama_tutarlidir(db, tmp_path):
    folder = tmp_path / "yedekler"
    first = run_daily_backup(db, TODAY, folder)
    PrayerRepository(db).mark_missed(date(2026, 10, 29), PrayerType.ISHA)
    second = run_daily_backup(db, TODAY + timedelta(days=1), folder)
    for path, expected in ((first, 1), (second, 2)):
        copy = AppDatabase.open(path)
        try:
            assert len(PrayerRepository(copy).records_for_date(date(2026, 10, 29))) == expected
        finally:
            copy.close()


def test_son_yedi_yedek_tutulur_eskiler_silinir(db, tmp_path):
    folder = tmp_path / "yedekler"
    for offset in range(10):
        run_daily_backup(db, TODAY + timedelta(days=offset), folder)
    names = sorted(p.name for p in folder.iterdir())
    assert len(names) == BACKUP_KEEP == 7
    assert names[0] == "namaz_takip-20261102.db"  # en eski 3 silindi (30, 31 Ekim, 1 Kasım)
    assert names[-1] == "namaz_takip-20261108.db"


def test_baska_dosyalar_silinmez(db, tmp_path):
    folder = tmp_path / "yedekler"
    folder.mkdir()
    (folder / "notlarim.txt").write_text("dokunma", encoding="utf-8")
    for offset in range(9):
        run_daily_backup(db, TODAY + timedelta(days=offset), folder)
    assert (folder / "notlarim.txt").read_text(encoding="utf-8") == "dokunma"


def test_bellek_ici_veritabaninda_atlanir(tmp_path):
    memory = AppDatabase.open_in_memory()
    try:
        assert run_daily_backup(memory, TODAY, tmp_path / "yedekler") is None
        assert not (tmp_path / "yedekler").exists()
    finally:
        memory.close()


def test_hata_uygulamayi_durdurmaz(db, tmp_path):
    blocked = tmp_path / "yedekler"
    blocked.write_text("klasör değil, dosya", encoding="utf-8")
    assert run_daily_backup(db, TODAY, blocked) is None  # istisna dışarı çıkmaz


def test_varsayilan_klasor_veri_klasorunun_icindeki_backups(db, isolated_data_dir):
    created = run_daily_backup(db, TODAY)
    assert created is not None
    assert created.parent == isolated_data_dir / "backups"
