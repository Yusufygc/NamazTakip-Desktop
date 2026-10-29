"""Kabuk köprüsü, container bağlantıları ve komut satırı argümanları."""

from datetime import date

import pytest

from app.bridge.shell_bridge import ShellBridge
from app.container import AppContainer
from app.core.backup import backup_path
from app.core.database import FILE_NAME, AppDatabase
from app.core.domain.prayer import PrayerType
from app.services.autostart_service import VALUE_NAME, AutostartService
from app.services.clock_service import Notification, NotificationKind
from main import parse_args
from tests.support import FAKE_EXE, FakeClock, FakeRegistry, at


def notification(prayer=PrayerType.ASR, day=date(2026, 10, 26)) -> Notification:
    return Notification(NotificationKind.ADHAN, prayer, day, "İkindi Vakti", "İkindi vakti girdi.")


def record(signal) -> list:
    received: list = []
    signal.connect(lambda *args: received.append(args))
    return received


class TestShellBridge:
    def test_bildirim_tepsiye_iletilir(self, qapp):
        shell = ShellBridge()
        shown = record(shell.notificationRequested)
        shell.on_notification(notification())
        assert shown == [("İkindi Vakti", "İkindi vakti girdi.")]

    def test_tiklama_son_bildirimin_gun_ve_vaktini_verir(self, qapp):
        shell = ShellBridge()
        prompts = record(shell.promptRequested)
        shell.activateLastNotification()  # henüz bildirim yok: hiçbir şey olmaz
        assert prompts == []
        shell.on_notification(notification(PrayerType.DHUHR, date(2026, 10, 25)))
        shell.on_notification(notification(PrayerType.ASR, date(2026, 10, 26)))
        shell.activateLastNotification()
        assert prompts == [("2026-10-26", "asr")]  # en son bildirim

    def test_cikis_istegi(self, qapp):
        shell = ShellBridge()
        quits = record(shell.quitRequested)
        shell.requestQuit()
        assert quits == [()]

    def test_sabit_ozellikler(self, qapp):
        shell = ShellBridge(start_hidden=True, tray_icon_url="file:///C:/x/tray.png")
        assert shell.startHidden is True
        assert shell.trayIconUrl == "file:///C:/x/tray.png"
        assert ShellBridge().startHidden is False


class TestContainerKurulumu:
    def test_saat_servisi_bildirimi_kabuk_koprusune_iletir(self, qapp):
        container = AppContainer(AppDatabase.open_in_memory(), now=FakeClock(at(2026, 10, 26, 12)))
        try:
            shown = record(container.shell_bridge.notificationRequested)
            container.clock_service.notification.emit(notification())
            assert shown == [("İkindi Vakti", "İkindi vakti girdi.")]
        finally:
            container.shutdown()

    def test_tepsi_simgesi_adresi_gercek_dosyaya_gider(self, qapp):
        container = AppContainer(AppDatabase.open_in_memory(), now=FakeClock(at(2026, 10, 26, 12)))
        try:
            url = container.shell_bridge.trayIconUrl
            assert url.startswith("file:///") and url.endswith("/app/ui/assets/tray.png")
            from pathlib import Path

            from PySide6.QtCore import QUrl

            assert Path(QUrl(url).toLocalFile()).is_file()
        finally:
            container.shutdown()

    def test_acilis_isleri_yedek_alir_ve_autostart_esitler(self, qapp, tmp_path, isolated_data_dir):
        registry = FakeRegistry()
        autostart = AutostartService(registry, lambda: FAKE_EXE)
        container = AppContainer(
            AppDatabase.open(tmp_path / FILE_NAME), now=FakeClock(at(2026, 10, 26, 12)), autostart=autostart
        )
        try:
            container.run_startup_tasks()
            assert registry.values == {}  # henüz sorulmadı: kayıt yok
            assert backup_path(isolated_data_dir / "backups", date(2026, 10, 26)).is_file()
            container.settings_service.set_autostart(True)
            registry.values.clear()  # kayıt dışarıdan silinmiş gibi
            container.run_startup_tasks()
            assert VALUE_NAME in registry.values  # açılışta yeniden yazıldı
        finally:
            container.shutdown()

    def test_acilis_isleri_bellek_ici_veritabaninda_yedek_almaz(self, qapp, isolated_data_dir):
        container = AppContainer(AppDatabase.open_in_memory(), now=FakeClock(at(2026, 10, 26, 12)))
        try:
            container.run_startup_tasks()
            assert not (isolated_data_dir / "backups").exists()
        finally:
            container.shutdown()


class TestKomutSatiri:
    @pytest.mark.parametrize(
        ("argv", "expected"),
        [([], False), (["--autostart"], True), (["--autostart", "-platform", "offscreen"], True), (["-style", "x"], False)],
    )
    def test_autostart_bayragi(self, argv, expected):
        assert parse_args(argv).autostart is expected
