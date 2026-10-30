"""Derleme sonrası deneme: gerçek kurulumun kaydı ve kısayolu korunur, deneme uygulaması yalıtılır."""

import subprocess
import uuid
import winreg
from pathlib import Path

import pytest

import build_verify


@pytest.fixture
def isolated_registration(tmp_path, monkeypatch):
    """Gerçek kaydı değil, teste ait geçici bir HKCU alt anahtarını ve geçici bir kısayol yolunu kullanır."""
    key = rf"Software\NamazTakipTest\{uuid.uuid4()}_is1"
    shortcut = tmp_path / "Namaz Takip.lnk"
    monkeypatch.setattr(build_verify, "UNINSTALL_KEY", key)
    monkeypatch.setattr(build_verify, "SHORTCUT", shortcut)
    yield key, shortcut
    for path in (key, key.rsplit("\\", 1)[0]):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            continue
        except OSError:
            continue  # alt anahtarı olan üst anahtar silinemez; test anahtarları zaten tek tek silindi


def write_registration(key: str, values: dict) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key, 0, winreg.KEY_SET_VALUE) as handle:
        for name, (value, kind) in values.items():
            winreg.SetValueEx(handle, name, 0, kind, value)


def read_registration(key: str) -> "dict | None":
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            result, index = {}, 0
            while True:
                try:
                    name, value, kind = winreg.EnumValue(handle, index)
                except OSError:
                    return result
                result[name] = (value, kind)
                index += 1
    except FileNotFoundError:
        return None


REAL = {"DisplayName": ("Namaz Takip", winreg.REG_SZ), "InstallLocation": (r"C:\Gercek\Kurulum", winreg.REG_SZ), "EstimatedSize": (1234, winreg.REG_DWORD)}


class TestKayitKorumasi:
    def test_gercek_kayit_deneme_sonrasi_aynen_geri_gelir(self, isolated_registration):
        key, shortcut = isolated_registration
        write_registration(key, REAL)
        shortcut.write_bytes(b"gercek-kisayol")
        saved = build_verify.save_registration()

        # Deneme kurulumu aynı anahtarı başka değerlerle ezer ve kısayolu değiştirir.
        write_registration(key, {"DisplayName": ("DENEME", winreg.REG_SZ), "InstallLocation": (r"C:\Temp\deneme", winreg.REG_SZ), "Ekstra": ("x", winreg.REG_SZ)})
        shortcut.write_bytes(b"deneme-kisayolu")

        build_verify.restore_registration(saved)
        assert read_registration(key) == REAL
        assert shortcut.read_bytes() == b"gercek-kisayol"

    def test_gercek_kurulum_yoksa_deneme_kaydi_silinir(self, isolated_registration):
        key, shortcut = isolated_registration
        saved = build_verify.save_registration()
        assert saved == (None, None)
        write_registration(key, {"DisplayName": ("DENEME", winreg.REG_SZ)})
        shortcut.write_bytes(b"deneme-kisayolu")

        build_verify.restore_registration(saved)
        assert read_registration(key) is None
        assert not shortcut.exists()

    def test_hata_olsa_bile_geri_yuklenir(self, isolated_registration, monkeypatch, tmp_path):
        key, shortcut = isolated_registration
        write_registration(key, REAL)
        shortcut.write_bytes(b"gercek-kisayol")

        def broken(installer, seconds):
            write_registration(key, {"DisplayName": ("DENEME", winreg.REG_SZ)})
            shortcut.write_bytes(b"x")
            raise RuntimeError("deneme çöktü")

        monkeypatch.setattr(build_verify, "_installer_check", broken)
        with pytest.raises(RuntimeError):
            build_verify.installer_check(tmp_path / "Setup.exe")
        assert read_registration(key) == REAL
        assert shortcut.read_bytes() == b"gercek-kisayol"

    def test_app_id_gercek_kayit_anahtarini_gosterir(self):
        assert build_verify.UNINSTALL_KEY.endswith("_is1")
        assert "{6E2B7C1D-8A44-4F3E-9B05-3D7C5A1E94F2}" in build_verify.UNINSTALL_KEY


class TestEngelAlgilama:
    @pytest.mark.parametrize("code,blocked", [(4551, True), (1260, True), (5, False), (2, False)])
    def test_winerror(self, code, blocked):
        assert build_verify.is_blocked(OSError(0, "x", None, code)) is blocked

    def test_winerrorsuz_hata_engel_degil(self):
        assert build_verify.is_blocked(OSError("x")) is False


class FakeProcess:
    def __init__(self, exit_code=None):
        self.pid = 4242
        self._exit_code = exit_code
        self.returncode = exit_code

    def poll(self):
        return self._exit_code


class TestLaunchCheck:
    @pytest.fixture(autouse=True)
    def fast(self, monkeypatch):
        monkeypatch.setattr(build_verify.time, "sleep", lambda seconds: None)
        self.killed = []
        monkeypatch.setattr(build_verify, "_kill_tree", lambda pid: self.killed.append(pid))

    def test_calisan_exe_basarili_ve_kapatilir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: FakeProcess(None))
        assert build_verify.launch_check(tmp_path / "NamazTakip.exe") is True
        assert self.killed == [4242]

    def test_hemen_kapanan_exe_basarisiz(self, monkeypatch, tmp_path):
        monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: FakeProcess(1))
        assert build_verify.launch_check(tmp_path / "NamazTakip.exe") is False

    def test_engellenen_exe_basarisiz(self, monkeypatch, tmp_path):
        def blocked(*args, **kwargs):
            raise OSError(0, "Uygulama Denetimi ilkesi engelledi", None, 4551)

        monkeypatch.setattr(subprocess, "Popen", blocked)
        assert build_verify.launch_check(tmp_path / "NamazTakip.exe") is False

    def test_baska_hata_yukselir(self, monkeypatch, tmp_path):
        def missing(*args, **kwargs):
            raise OSError(0, "dosya yok", None, 2)

        monkeypatch.setattr(subprocess, "Popen", missing)
        with pytest.raises(OSError):
            build_verify.launch_check(tmp_path / "NamazTakip.exe")

    def test_deneme_yalitilmis_veri_klasoruyle_acilir_ve_temizlenir(self, monkeypatch, tmp_path):
        seen = {}

        def popen(command, cwd=None, env=None):
            seen["env"] = env
            seen["dir"] = Path(env["NAMAZ_TAKIP_DATA_DIR"])
            (seen["dir"] / "namaz_takip.db").write_text("x")
            return FakeProcess(None)

        monkeypatch.setattr(subprocess, "Popen", popen)
        build_verify.launch_check(tmp_path / "NamazTakip.exe")
        data_dir = seen["dir"]
        assert data_dir.name.startswith("nt_verify_data_")
        assert not data_dir.exists()  # deneme verisi silindi
        assert seen["env"]["NAMAZ_TAKIP_NO_UPDATE_CHECK"] == "1"
        assert "QT_QPA_PLATFORM" not in seen["env"]
