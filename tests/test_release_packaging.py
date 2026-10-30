"""Kararlı exe, onay kapısı, Inno betiği ve sürüm/lisans tutarlılığı (docs/wiki/dagitim.md).

Giriş betiği ve sürüm kaynağı özetleri BİLEREK sabittir: biri değişirse exe'nin SHA-256 özeti değişir ve Windows
Akıllı Uygulama Denetimi yeni exe'yi yeniden değerlendirir. Bilerek değiştiriyorsan bu testteki özeti güncelle ve
build_exe.py'deki "Exe'yi bilerek değiştirme" adımlarını izle.
"""

import ast
import hashlib
import importlib.metadata
import re
from pathlib import Path

import pytest

import build_exe
import build_verify
from app import version
from tools import third_party_notices

ROOT = Path(__file__).resolve().parent.parent

LAUNCHER_SHA256 = "ec12c6ce94cfb0c28a1be8c3d4c6df408ea2b34809d843d4394bdc07f9caad09"
VERSION_INFO_SHA256 = "eb6917e16d1c04a677fa21492438b92c3e5d3f3467cb057bb8165d3561fd6dd8"


def lf_sha256(path: Path) -> str:
    """Satır sonları LF'ye çevrilerek (Windows CRLF ile CI LF aynı sonucu versin)."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class TestSabitDosyalar:
    def test_giris_betigi_ozeti_sabit(self):
        assert lf_sha256(ROOT / "packaging" / "launcher.py") == LAUNCHER_SHA256, (
            "packaging/launcher.py değişti: exe özeti değişir (Akıllı Uygulama Denetimi yeniden değerlendirir)."
        )

    def test_surum_kaynagi_ozeti_sabit(self):
        assert lf_sha256(ROOT / "packaging" / "launcher_version_info.txt") == VERSION_INFO_SHA256, (
            "packaging/launcher_version_info.txt değişti: exe özeti değişir."
        )

    def test_exe_surum_kaynagi_urun_surumunu_icermez(self):
        text = (ROOT / "packaging" / "launcher_version_info.txt").read_text(encoding="utf-8")
        assert "1.0.0.0" in text
        assert version.__version__ not in text.replace("1.0.0.0", "")  # sürümle değişen kaynak exe'yi değiştirirdi

    def test_giris_betigi_yalniz_main_cagirir(self):
        tree = ast.parse((ROOT / "packaging" / "launcher.py").read_text(encoding="utf-8"))
        imports = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        assert len(imports) == 1 and imports[0].module == "main" and imports[0].names[0].name == "main"
        assert len(tree.body) <= 3  # docstring + import + çağrı

    def test_satir_sonlari_lf(self):
        for relative in ("packaging/launcher.py", "packaging/launcher_version_info.txt"):
            assert b"\r" not in (ROOT / relative).read_bytes(), f"{relative} LF olmalı (.gitattributes eol=lf)"
        assert "eol=lf" in (ROOT / ".gitattributes").read_text(encoding="utf-8")


class TestDerlemeBayraklari:
    def test_kararli_exe_bayraklari(self):
        args = build_exe.pyinstaller_arguments(ROOT)
        assert args[0] == str(ROOT / "packaging" / "launcher.py")
        for flag in ("--onedir", "--windowed", "--noupx", "--debug=noarchive", "--noconfirm", "--clean"):
            assert flag in args
        assert f"--version-file={ROOT / 'packaging' / 'launcher_version_info.txt'}" in args
        assert f"--paths={ROOT}" in args
        assert "--onefile" not in args

    def test_epoch_ve_ortam_degiskeni(self):
        assert build_exe.LAUNCHER_EPOCH == 1700000000
        source = (ROOT / "build_exe.py").read_text(encoding="utf-8")
        assert 'os.environ["SOURCE_DATE_EPOCH"] = str(LAUNCHER_EPOCH)' in source

    def test_qml_ve_varliklar_pakete_eklenir(self):
        args = build_exe.pyinstaller_arguments(ROOT)
        data = [args[i + 1] for i, part in enumerate(args) if part == "--add-data"]
        assert {item.split(";")[-1] if ";" in item else item for item in data} >= {"app/ui/qml", "app/ui/assets"}

    def test_pyinstaller_surumu_sabit(self):
        requirements = (ROOT / "requirements-build.txt").read_text(encoding="utf-8")
        assert re.search(r"^pyinstaller==\d+\.\d+\.\d+$", requirements, re.MULTILINE)


class TestOnayKapisi:
    def fake_exe(self, tmp_path: Path) -> Path:
        exe = tmp_path / "dist" / "NamazTakip.exe"
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b"MZ-sahte-exe")
        (tmp_path / "packaging").mkdir()
        return exe

    def test_ayni_ozet_gecer(self, tmp_path, capsys):
        exe = self.fake_exe(tmp_path)
        (tmp_path / "packaging" / "launcher.sha256").write_text(f"{build_exe.exe_sha256(exe)} *NamazTakip.exe\n")
        build_exe.check_launcher_hash(tmp_path, exe)
        assert "onaylananla aynı" in capsys.readouterr().out

    def test_farkli_ozet_durdurur(self, tmp_path):
        exe = self.fake_exe(tmp_path)
        (tmp_path / "packaging" / "launcher.sha256").write_text(f"{'0' * 64} *NamazTakip.exe\n")
        with pytest.raises(SystemExit):
            build_exe.check_launcher_hash(tmp_path, exe)

    def test_onay_dosyasi_yoksa_durdurur(self, tmp_path):
        exe = self.fake_exe(tmp_path)
        with pytest.raises(SystemExit):
            build_exe.check_launcher_hash(tmp_path, exe)

    def test_guncelleme_yazar_ve_sonra_gecer(self, tmp_path):
        exe = self.fake_exe(tmp_path)
        build_exe.check_launcher_hash(tmp_path, exe, update=True)
        written = (tmp_path / "packaging" / "launcher.sha256").read_text(encoding="utf-8")
        assert written == f"{build_exe.exe_sha256(exe)} *NamazTakip.exe\n"
        build_exe.check_launcher_hash(tmp_path, exe)  # artık geçer

    def test_depodaki_onay_dosyasi_gecerli_bicimde(self):
        line = (ROOT / "packaging" / "launcher.sha256").read_text(encoding="utf-8").strip()
        assert re.fullmatch(r"[0-9a-f]{64} \*NamazTakip\.exe", line)

    def test_yayin_betigi_kapiyi_atlamaz(self):
        source = (ROOT / "build_installer.py").read_text(encoding="utf-8")
        assert "build_exe.build_executable(update_launcher_hash=update_launcher_hash)" in source
        assert "launcher.sha256" in (ROOT / "build_exe.py").read_text(encoding="utf-8")


class TestAyiklama:
    def test_kullanilmayan_qt_parcalari_silinir_kullanilanlar_kalir(self, tmp_path):
        package = tmp_path / "_internal" / "PySide6"
        (package / "qml").mkdir(parents=True)
        keep = ["qml/QtQuick/qmldir", "qml/Qt/labs/platform/qmldir", "Qt6Core.dll", "Qt6Quick.dll", "Qt6Network.dll", "QtCore.pyd"]
        drop = ["qml/QtWebEngine/qmldir", "qml/Qt3D/qmldir", "translations/qt_tr.qm", "Qt6WebEngineCore.dll", "Qt6Pdf.dll"]
        for relative in (*keep, *drop):
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x")
        build_exe.prune(tmp_path)
        for relative in keep:
            assert (package / relative).exists(), relative
        for relative in drop:
            assert not (package / relative).exists(), relative


class TestInnoBetigi:
    iss = (ROOT / "packaging" / "NamazTakip.iss").read_text(encoding="utf-8")

    def test_sabit_app_id_dogrulama_kaydiyla_ayni(self):
        match = re.search(r"^AppId=\{\{([0-9A-F-]{36})\}", self.iss, re.MULTILINE)
        assert match, "AppId bulunamadı"
        assert match.group(1) in build_verify.UNINSTALL_KEY  # deneme kaydı gerçek kaydı yedekler

    def test_onemli_ayarlar(self):
        for line in (
            "PrivilegesRequired=lowest",
            "CloseApplications=yes",
            "RestartApplications=no",
            "OutputBaseFilename=NamazTakip-Setup-{#AppVersion}",
            "Check: RelaunchAfterUpdate",
            "WizardSilent and not HasParam('/VERYSILENT')",
        ):
            assert line in self.iss, line

    def test_betik_dosyalari_mevcut(self):
        for relative in ("LICENSE", "THIRD_PARTY_NOTICES.md", "app/ui/assets/app.ico"):
            assert (ROOT / relative).is_file()
        assert "LicenseFile=..\\LICENSE" in self.iss
        assert "THIRD_PARTY_NOTICES.md" in self.iss

    def test_cikti_adi_installer_betigiyle_uyumlu(self):
        import build_installer

        assert build_installer.SCRIPT.name == "NamazTakip.iss"
        assert build_installer.EXE == ROOT / "dist" / "NamazTakip" / "NamazTakip.exe"
        assert "NamazTakip-Setup-" in (ROOT / "build_installer.py").read_text(encoding="utf-8")


class TestSurumVeLisans:
    def test_surum_bicimi_ucayrisayi(self):
        assert re.fullmatch(r"\d+\.\d+\.\d+", version.__version__)

    def test_yayin_deposu_bicimi(self):
        assert re.fullmatch(r"[\w.-]+/[\w.-]+", version.RELEASE_REPO)

    def test_lisans_dosyasi_var(self):
        assert "Tüm hakları saklıdır" in (ROOT / "LICENSE").read_text(encoding="utf-8")

    def test_ucuncu_taraf_bildirimi_guncel(self):
        """Dosya `python tools/third_party_notices.py` çıktısıyla birebir aynı olmalı (bağımlılık değişince yeniden üret)."""
        on_disk = (ROOT / "THIRD_PARTY_NOTICES.md").read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        assert on_disk == third_party_notices.render()

    def test_bildirim_gerektiren_her_calisma_zamani_bagimliligi_kapsanir(self):
        pinned = third_party_notices.requirement_versions()
        runtime = {name for name in pinned if name not in ("pyinstaller",)}
        covered = {name.lower() for name in third_party_notices.COMPONENTS}
        assert runtime <= covered, f"bildirimde olmayan bağımlılık: {sorted(runtime - covered)}"
        for package in third_party_notices.COMPONENTS:
            installed = importlib.metadata.version(package)
            assert installed == pinned[package.lower()], f"{package}: kurulu {installed}, requirements {pinned[package.lower()]}"

    def test_mit_bilesenin_lisans_metni_gomulu(self):
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        assert "Permission is hereby granted, free of charge" in notices
        assert "Copyright (c) 2022 alphahm" in notices

    def test_surum_baska_yerde_sabit_yazilmamis(self):
        """Sürüm tek kaynaktan gelir (app/version.py); kodda ve arayüzde ikinci bir yazım olmamalı."""
        pattern = re.compile(rf"(?<![\w.]){re.escape(version.__version__)}(?![\w.])")
        offenders = []
        for path in [ROOT / "main.py", *(ROOT / "app").rglob("*.py"), *(ROOT / "app").rglob("*.qml")]:
            if path.name == "version.py":
                continue
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(ROOT)))
        assert offenders == []

    def test_kurulum_dosyasi_adi_guncelleyici_desenine_uyar(self):
        name = f"NamazTakip-Setup-{version.__version__}.exe"
        assert re.fullmatch(r"NamazTakip-Setup-[0-9.]+\.exe", name)

    def test_uretilen_ciktilar_depoya_girmez(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        for entry in ("dist/", "build/", "venv/"):
            assert entry in ignored
