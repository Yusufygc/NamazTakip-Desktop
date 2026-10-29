"""Windows açılışında başlatma: kayıt mantığı (sahte kayıt defteri) ve gerçek HKCU gidiş-dönüşü."""

import contextlib
import sys
import uuid
from datetime import date

import pytest

from app.core.database import AppDatabase
from app.core.repositories.settings_repository import SettingsRepository
from app.services.autostart_service import (
    AUTOSTART_ARG,
    VALUE_NAME,
    AutostartService,
    WinRegistry,
    frozen_executable,
)
from app.services.settings_service import SettingsService
from tests.support import FAKE_EXE, FakeRegistry

COMMAND = f'"{FAKE_EXE}" {AUTOSTART_ARG}'


def make(initial=None, exe=FAKE_EXE):
    registry = FakeRegistry(initial)
    return registry, AutostartService(registry, lambda: exe)


def test_komut_tirnakli_yol_ve_autostart_argumani():
    _, service = make()
    assert service.command() == COMMAND
    assert service.command().endswith(" --autostart")


def test_etkinlestirme_yazar_ve_tekrarinda_yeniden_yazmaz():
    registry, service = make()
    assert service.apply(True) is True
    assert registry.values == {VALUE_NAME: COMMAND}
    assert service.apply(True) is True
    assert registry.writes == 1  # aynı komut: ikinci yazma yok
    assert service.is_registered() is True


def test_devre_disi_birakma_siler_ve_yoksa_hata_vermez():
    registry, service = make({VALUE_NAME: COMMAND})
    assert service.apply(False) is True
    assert registry.values == {}
    assert service.apply(False) is True  # zaten yok
    assert service.is_registered() is False


def test_baska_uygulamanin_degerlerine_dokunulmaz():
    registry, service = make({"BaskaUygulama": "x.exe", VALUE_NAME: COMMAND})
    service.apply(False)
    assert registry.values == {"BaskaUygulama": "x.exe"}


def test_gelistirme_ortaminda_kayit_degistirilmez():
    """Donmuş exe yokken ne yazılır ne silinir: kurulu uygulamanın kaydı geliştirmede bozulmasın."""
    registry, service = make({VALUE_NAME: COMMAND}, exe=None)
    assert service.command() is None
    assert service.apply(True) is False
    assert service.apply(False) is False
    assert service.sync(False) is False
    assert registry.values == {VALUE_NAME: COMMAND}
    assert registry.writes == 0


def test_sync_tasinmis_klasoru_yeniler_kapaliysa_siler_sorulmadiysa_dokunmaz():
    registry, service = make({VALUE_NAME: '"D:\\Eski\\NamazTakip.exe" --autostart'})
    service.sync(True)
    assert registry.values[VALUE_NAME] == COMMAND  # yol güncellendi
    service.sync(False)
    assert registry.values == {}
    registry.values[VALUE_NAME] = "elle-yazilmis"
    assert service.sync(None) is False  # henüz sorulmadı
    assert registry.values[VALUE_NAME] == "elle-yazilmis"


def test_frozen_executable_gelistirmede_none(monkeypatch):
    assert frozen_executable() is None
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert frozen_executable() == sys.executable


class TestAyarServisiEntegrasyonu:
    @pytest.fixture
    def parts(self):
        database = AppDatabase.open_in_memory()
        registry, autostart = make()
        service = SettingsService(SettingsRepository(database), autostart)
        yield service, registry
        database.close()

    def test_ayar_saklanir_ve_kayit_yazilir(self, parts):
        service, registry = parts
        service.set_autostart(True)
        assert service.settings.autostart is True
        assert registry.values == {VALUE_NAME: COMMAND}
        service.set_autostart(False)
        assert service.settings.autostart is False
        assert registry.values == {}

    def test_kayit_hatasi_ayari_geri_almaz_ve_firlatmaz(self):
        class Broken(FakeRegistry):
            def set(self, name, value):
                raise PermissionError("kayıt defteri yazılamıyor")

        database = AppDatabase.open_in_memory()
        try:
            service = SettingsService(SettingsRepository(database), AutostartService(Broken(), lambda: FAKE_EXE))
            service.set_autostart(True)  # istisna dışarı çıkmaz
            assert service.settings.autostart is True
        finally:
            database.close()

    def test_acilista_esitleme_ayara_gore(self, parts):
        service, registry = parts
        service.sync_autostart()  # sorulmadı: dokunulmaz
        assert registry.values == {}
        service._repo.set_autostart(True)  # ayar var, kayıt yok (ör. kayıt silinmiş)
        service.sync_autostart()
        assert registry.values == {VALUE_NAME: COMMAND}

    def test_autostart_servisi_yoksa_yalniz_ayar(self):
        database = AppDatabase.open_in_memory()
        try:
            service = SettingsService(SettingsRepository(database))
            service.set_autostart(True)
            service.sync_autostart()
            assert service.settings.autostart is True
        finally:
            database.close()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows kayıt defteri")
def test_gercek_hkcu_gidis_donus():
    """Gerçek `HKCU` üzerinde, yalnızca bu teste ait geçici alt anahtarda yazma/okuma/silme."""
    import winreg

    key_path = rf"Software\NamazTakipTest\{uuid.uuid4().hex}"
    registry = WinRegistry(key_path)
    try:
        assert registry.get("Deneme") is None
        registry.set("Deneme", COMMAND)
        assert registry.get("Deneme") == COMMAND
        service = AutostartService(registry, lambda: FAKE_EXE)
        assert service.apply(True) is True
        assert registry.get(VALUE_NAME) == COMMAND
        assert service.apply(False) is True
        assert registry.get(VALUE_NAME) is None
        assert registry.delete("Deneme") is True
        assert registry.delete("Deneme") is False  # artık yok
    finally:
        # Anahtar hiç oluşmamışsa silinecek bir şey yoktur.
        with contextlib.suppress(FileNotFoundError):
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        with contextlib.suppress(FileNotFoundError, OSError):
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\NamazTakipTest")


def test_gercek_run_anahtarina_dokunulmadi():
    """Bu test dosyası gerçek Run kaydını değiştirmemeli (geliştirme ortamı kaydı korunur)."""
    if sys.platform != "win32":
        pytest.skip("Windows kayıt defteri")
    before = WinRegistry().get(VALUE_NAME)
    service = AutostartService(WinRegistry())  # varsayılan: donmuş exe yok
    service.apply(True)
    service.apply(False)
    service.sync(False)
    assert WinRegistry().get(VALUE_NAME) == before
    assert date.today()  # gürültü yok: testin bağımlılığı yok
