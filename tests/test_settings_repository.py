"""Ayarlar deposu: varsayılanlar, kalıcılık, bozuk değerler."""

from datetime import date

import pytest

from app.core.database import FILE_NAME, AppDatabase
from app.core.domain.prayer import PrayerType
from app.core.domain.prayer_times import AppLocation, CalcMethod
from app.core.repositories.settings_repository import (
    KEY_AUTOSTART,
    KEY_INSTALL_DATE,
    KEY_MANUAL_LOCATION,
    KEY_QAZA_BACKLOG,
    KEY_REMINDER_MINUTES,
    SettingsRepository,
)


@pytest.fixture
def db():
    database = AppDatabase.open_in_memory()
    yield database
    database.close()


@pytest.fixture
def settings(db):
    return SettingsRepository(db)


def put_raw(db, key: str, value: str) -> None:
    db.connection.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))


def test_varsayilanlar(settings):
    assert settings.theme_key == "default"
    assert settings.notifications_enabled is True
    assert settings.reminder_minutes == 15
    assert settings.calc_method is CalcMethod.DIYANET
    assert settings.manual_location is None
    assert settings.install_date is None
    assert settings.qaza_daily_target == 2
    assert settings.qaza_backlog == {p: 0 for p in PrayerType}
    assert settings.close_to_tray is True
    assert settings.tray_hint_shown is False
    assert settings.corrupted_db_backup is None


def test_autostart_ayari_yokken_none_sonra_cevap_kalici(settings):
    assert settings.autostart is None  # ilk açılışta kullanıcıya sorulur
    settings.set_autostart(False)
    assert settings.autostart is False  # "hayır" cevabı da cevaptır, tekrar sorulmaz
    settings.set_autostart(True)
    assert settings.autostart is True


def test_degerler_yazilip_okunur(settings):
    settings.set_theme_key("dark")
    settings.set_notifications_enabled(False)
    settings.set_reminder_minutes(30)
    settings.set_calc_method(CalcMethod.MWL)
    settings.set_close_to_tray(False)
    settings.set_tray_hint_shown(True)
    assert settings.theme_key == "dark"
    assert settings.notifications_enabled is False
    assert settings.reminder_minutes == 30
    assert settings.calc_method is CalcMethod.MWL
    assert settings.close_to_tray is False
    assert settings.tray_hint_shown is True


def test_konum_turkce_karakterle_kalici(settings):
    location = AppLocation(38.42, 27.14, "İzmir", "Türkiye")
    settings.set_manual_location(location)
    assert settings.manual_location == location


def test_bozuk_konum_json_none_verir(db, settings):
    put_raw(db, KEY_MANUAL_LOCATION, "{bozuk json")
    assert settings.manual_location is None
    put_raw(db, KEY_MANUAL_LOCATION, '{"lat": "x", "lon": 1}')
    assert settings.manual_location is None


def test_install_date_yalnizca_bir_kez_yazilir(settings):
    settings.ensure_install_date(date(2026, 1, 5))
    settings.ensure_install_date(date(2026, 3, 9))
    assert settings.install_date == date(2026, 1, 5)


def test_bozuk_install_date_none(db, settings):
    put_raw(db, KEY_INSTALL_DATE, "dün")
    assert settings.install_date is None


def test_qaza_borcu_yazilip_okunur_ve_kirpilir(settings):
    settings.set_qaza_backlog({PrayerType.FAJR: 10, PrayerType.ISHA: 5_000_000, PrayerType.ASR: -3})
    backlog = settings.qaza_backlog
    assert backlog[PrayerType.FAJR] == 10
    assert backlog[PrayerType.ISHA] == 1_000_000
    assert backlog[PrayerType.ASR] == 0
    assert backlog[PrayerType.DHUHR] == 0  # verilmeyen vakit 0


@pytest.mark.parametrize("bozuk", ["", "bozuk", "[1,2]", "null", '{"fajr": "x", "isha": true, "asr": 4.9}'])
def test_bozuk_qaza_borcu_sifira_duser(db, settings, bozuk):
    put_raw(db, KEY_QAZA_BACKLOG, bozuk)
    backlog = settings.qaza_backlog
    assert set(backlog) == set(PrayerType)
    assert backlog[PrayerType.FAJR] == 0
    assert backlog[PrayerType.ISHA] == 0
    assert backlog[PrayerType.ASR] == (4 if "4.9" in bozuk else 0)


def test_gunluk_hedef_1_ile_50_arasina_kirpilir(settings):
    settings.set_qaza_daily_target(0)
    assert settings.qaza_daily_target == 1
    settings.set_qaza_daily_target(99)
    assert settings.qaza_daily_target == 50
    settings.set_qaza_daily_target(7)
    assert settings.qaza_daily_target == 7


def test_bozuk_sayi_ve_bool_varsayilana_duser(db, settings):
    put_raw(db, KEY_REMINDER_MINUTES, "çok")
    put_raw(db, KEY_AUTOSTART, "belki")
    assert settings.reminder_minutes == 15
    assert settings.autostart is None


def test_bozuk_veritabani_yedek_yolu_yazilip_silinir(settings):
    settings.set_corrupted_db_backup("C:/x/namaz_takip.db.bozuk-1")
    assert settings.corrupted_db_backup == "C:/x/namaz_takip.db.bozuk-1"
    settings.set_corrupted_db_backup(None)
    assert settings.corrupted_db_backup is None


def test_ayarlar_dosyaya_yazilinca_yeniden_acilista_korunur(tmp_path):
    db_path = tmp_path / FILE_NAME
    first = AppDatabase.open(db_path)
    store = SettingsRepository(first)
    store.ensure_install_date(date(2026, 1, 5))
    store.set_qaza_backlog({PrayerType.FAJR: 123})
    store.set_autostart(True)
    first.close()

    second = AppDatabase.open(db_path)
    try:
        again = SettingsRepository(second)
        assert again.install_date == date(2026, 1, 5)
        assert again.qaza_backlog[PrayerType.FAJR] == 123
        assert again.autostart is True
    finally:
        second.close()
