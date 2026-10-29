"""AppContainer: kurulum, bağlantılar ve kapanış."""

from datetime import date
from pathlib import Path

from app.container import AppContainer
from app.core.database import FILE_NAME, AppDatabase
from tests.support import FakeClock, at


def test_install_date_ilk_acilista_yazilir_ve_degismez(qapp, tmp_path):
    db_path = tmp_path / FILE_NAME
    first = AppContainer(AppDatabase.open(db_path), now=FakeClock(at(2026, 10, 24, 12)))
    assert first.settings_service.install_date == date(2026, 10, 24)
    first.shutdown()

    second = AppContainer(AppDatabase.open(db_path), now=FakeClock(at(2026, 11, 5, 12)))
    try:
        assert second.settings_service.install_date == date(2026, 10, 24)
    finally:
        second.shutdown()


def test_bozuk_veritabani_yedek_yolu_ayara_yazilir(qapp, tmp_path):
    db_path = tmp_path / FILE_NAME
    db_path.write_bytes(b"bozuk")
    database = AppDatabase.open(db_path)
    container = AppContainer(database, now=FakeClock(at(2026, 10, 26, 12)))
    try:
        backup = container.settings_service._repo.corrupted_db_backup
        assert backup is not None and Path(backup).is_file()
        assert backup == str(database.corrupted_backup_path)
    finally:
        container.shutdown()


def test_baslat_saati_calistirir_kapat_durdurur_ve_veritabanini_kapatir(qapp):
    container = AppContainer(AppDatabase.open_in_memory(), now=FakeClock(at(2026, 10, 26, 12)))
    container.start()
    assert container.clock_service.is_active
    container.shutdown()
    assert not container.clock_service.is_active
    try:
        container.database.connection.execute("SELECT 1")
        closed = False
    except Exception:  # sqlite3.ProgrammingError: kapalı bağlantı
        closed = True
    assert closed
