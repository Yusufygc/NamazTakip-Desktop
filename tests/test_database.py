"""Veritabanı şeması, açılış ve bozuk dosya kurtarma (mobil `prayer_repository_test.dart`)."""

import sqlite3
from datetime import date, datetime

import pytest

from app.core import paths
from app.core.database import FILE_NAME, SCHEMA_VERSION, AppDatabase, DatabaseVersionError
from app.core.domain.prayer import PrayerStatus, PrayerType
from app.core.repositories.prayer_repository import PrayerRepository

TODAY = date(2026, 1, 10)


def test_sema_tablolar_indeksler_ve_surum():
    db = AppDatabase.open_in_memory()
    try:
        names = {r["name"] for r in db.connection.execute("SELECT name FROM sqlite_master")}
        assert {"prayers", "settings", "idx_prayers_date", "idx_prayers_status"} <= names
        assert db.connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION == 1
        columns = [r["name"] for r in db.connection.execute("PRAGMA table_info(prayers)")]
        assert columns == ["id", "date", "prayer", "status", "is_congregation", "marked_at", "compensated_at"]
    finally:
        db.close()


def test_date_prayer_cifti_benzersiz():
    db = AppDatabase.open_in_memory()
    try:
        insert = "INSERT INTO prayers (date, prayer) VALUES ('2026-01-10', 'fajr')"
        db.connection.execute(insert)
        with pytest.raises(sqlite3.IntegrityError):
            db.connection.execute(insert)
    finally:
        db.close()


def test_varsayilan_yol_veri_klasorune_yazar(isolated_data_dir):
    db = AppDatabase.open()
    db.close()
    assert (isolated_data_dir / FILE_NAME).is_file()
    assert paths.db_path() == isolated_data_dir / FILE_NAME


def test_saglam_veritabani_yeniden_acilinca_yedeklenmez_ve_veri_korunur(tmp_path):
    db_path = tmp_path / FILE_NAME
    first = AppDatabase.open(db_path)
    assert first.corrupted_backup_path is None
    PrayerRepository(first).mark_performed(TODAY, PrayerType.DHUHR)
    first.close()

    reopened = AppDatabase.open(db_path)
    try:
        assert reopened.corrupted_backup_path is None
        assert [p for p in tmp_path.iterdir() if ".bozuk-" in p.name] == []
        records = PrayerRepository(reopened).records_for_date(TODAY)
        assert records[PrayerType.DHUHR].status == PrayerStatus.PERFORMED
    finally:
        reopened.close()


def test_rastgele_baytli_bozuk_dosya_silinmeden_once_yedeklenir_ve_temiz_acilir(tmp_path):
    db_path = tmp_path / FILE_NAME
    corrupt = bytes((i * 73 + 19) & 0xFF for i in range(256))
    db_path.write_bytes(corrupt)
    # Yeni yedek alınırken önceki .bozuk-* yedeği silinir, yer kaplamaz.
    old_backup = tmp_path / f"{FILE_NAME}.bozuk-20260101-000000"
    old_backup.write_bytes(b"\x01\x02\x03")

    recovered = AppDatabase.open(db_path, now=datetime(2026, 10, 26, 21, 30, 45))
    try:
        expected = tmp_path / f"{FILE_NAME}.bozuk-20261026-213045"
        assert recovered.corrupted_backup_path == expected
        assert not old_backup.exists()
        assert expected.read_bytes() == corrupt

        repo = PrayerRepository(recovered)
        repo.mark_performed(TODAY, PrayerType.FAJR, congregation=True)
        assert repo.records_for_date(TODAY)[PrayerType.FAJR].status == PrayerStatus.PERFORMED
    finally:
        recovered.close()


def test_basligi_gecerli_ama_sayfalari_bozuk_dosya_da_yedeklenir(tmp_path):
    db_path = tmp_path / FILE_NAME
    garbage = b"SQLite format 3\x00" + bytes((i * 41 + 7) & 0xFF for i in range(200))
    db_path.write_bytes(garbage)

    recovered = AppDatabase.open(db_path, now=datetime(2026, 10, 26, 21, 31, 0))
    try:
        expected = tmp_path / f"{FILE_NAME}.bozuk-20261026-213100"
        assert recovered.corrupted_backup_path == expected
        assert expected.read_bytes() == garbage

        repo = PrayerRepository(recovered)
        repo.mark_missed(TODAY, PrayerType.ISHA)
        assert repo.records_for_date(TODAY)[PrayerType.ISHA].status == PrayerStatus.MISSED
    finally:
        recovered.close()


def test_bos_dosya_bozuk_sayilir_ve_yedeklenir(tmp_path):
    db_path = tmp_path / FILE_NAME
    db_path.write_bytes(b"")
    recovered = AppDatabase.open(db_path, now=datetime(2026, 10, 26, 22, 0, 0))
    try:
        assert recovered.corrupted_backup_path is not None
        assert recovered.corrupted_backup_path.is_file()
    finally:
        recovered.close()


def test_yeni_surumle_yazilmis_veritabani_bozuk_sayilmaz(tmp_path):
    db_path = tmp_path / FILE_NAME
    first = AppDatabase.open(db_path)
    first.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    first.close()

    with pytest.raises(DatabaseVersionError):
        AppDatabase.open(db_path)
    assert db_path.is_file()
    assert [p for p in tmp_path.iterdir() if ".bozuk-" in p.name] == []
    # Dosya kilitli kalmamalı: silinebilmeli (Windows'ta açık bağlantı engeller).
    db_path.unlink()
