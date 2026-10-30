"""Yayın aracı (tools/release.py) ve GitHub Actions iş akışları (docs/wiki/dagitim.md).

Gerçek depoya dokunulmaz: yayın akışı, dosyaları kopyalanmış geçici bir git deposunda koşar.
Hiçbir test etiket GitHub'a göndermez; araç zaten hiçbir şeyi itmez.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from app.version import RELEASE_REPO, __version__
from tools import release as release_tool

ROOT = Path(__file__).resolve().parent.parent


def read(relative: str) -> str:
    return (ROOT / relative).read_bytes().decode("utf-8")


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo, capture_output=True, text=True, encoding="utf-8", check=True,
    )  # fmt: skip
    return result.stdout.strip()


@pytest.fixture
def sandbox(tmp_path):
    for relative in ("app/version.py", "README.md"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return tmp_path


@pytest.fixture
def repo(sandbox, monkeypatch):
    """Aracın ROOT'u geçici bir git deposu (main dalı, temiz ağaç)."""
    run_git(sandbox, "init", "-q", "-b", "main")
    run_git(sandbox, "add", "-A")
    run_git(sandbox, "commit", "-q", "-m", "ilk")
    monkeypatch.setattr(release_tool, "ROOT", sandbox)
    # Aracın kendi `git` çağrısı kullanıcı kimliği ister; geçici depoya yerel kimlik yazılır.
    run_git(sandbox, "config", "user.name", "t")
    run_git(sandbox, "config", "user.email", "t@example.com")
    return sandbox


class TestSurumKaynaklari:
    def test_readme_rozeti_surumle_ayni(self):
        assert f"badge/Version-{__version__}-orange" in read("README.md")

    def test_depo_adi_readmede_geciyor(self):
        assert RELEASE_REPO in read("README.md")

    def test_surum_dosyasi_surumu_ve_depoyu_tanimlar(self):
        text = read("app/version.py").replace(chr(13) + chr(10), chr(10))
        assert re.search(r'^__version__ = "\d+\.\d+\.\d+"$', text, re.MULTILINE)
        assert re.search(r'^RELEASE_REPO = "[\w.-]+/[\w.-]+"', text, re.MULTILINE)


class TestSurumYukseltme:
    def test_her_kaynagi_yukseltir_baska_hicbir_seyi_degistirmez(self, sandbox):
        before = {name: (sandbox / name).read_bytes() for name in ("app/version.py", "README.md")}
        release_tool.bump_files(sandbox, "12.34.56")
        assert release_tool.read_version(sandbox) == "12.34.56"
        assert "badge/Version-12.34.56-orange" in (sandbox / "README.md").read_text(encoding="utf-8")
        for name, old in before.items():
            assert len((sandbox / name).read_bytes().splitlines()) == len(old.splitlines()), name
        release_tool.bump_files(sandbox, __version__)  # geri alınca aynı baytlar
        assert {name: (sandbox / name).read_bytes() for name in before} == before

    def test_exe_surum_kaynagina_dokunmaz(self, sandbox):
        info = sandbox / "packaging" / "launcher_version_info.txt"
        info.parent.mkdir()
        info.write_bytes(b"sabit")
        release_tool.bump_files(sandbox, "9.9.9")
        assert info.read_bytes() == b"sabit"  # kararlı exe: sürümle değişen kaynak yok

    @pytest.mark.parametrize("bad", ["2.1", "v2", "abc", "2.1.0-rc1", "1.2.3.4", ""])
    def test_gecersiz_surum_reddedilir(self, bad):
        with pytest.raises(SystemExit):
            release_tool.as_tuple(bad)

    def test_eslesme_sayisi_beklenenden_farkliysa_durur(self, sandbox):
        (sandbox / "README.md").write_text("rozet yok\n", encoding="utf-8")
        with pytest.raises(SystemExit, match="eşleşme"):
            release_tool.bump_files(sandbox, "9.9.9")

    def test_sayisal_karsilastirma(self):
        assert release_tool.as_tuple("2.10.0") > release_tool.as_tuple("2.9.0")


class TestEtiketDenetimi:
    def test_uyumlu_etiket(self):
        assert release_tool.check_tag("v" + __version__) == 0

    def test_uyumsuz_etiket(self, capsys):
        assert release_tool.check_tag("v99.0.0") == 1
        assert "uyuşmuyor" in capsys.readouterr().out
        assert release_tool.check_tag(__version__) == 1  # v öneki şart


class TestYayinAkisi:
    def test_ayni_veya_kucuk_surum_reddedilir(self, repo):
        with pytest.raises(SystemExit, match="büyük olmalı"):
            release_tool.release(__version__, dry_run=True)
        with pytest.raises(SystemExit, match="büyük olmalı"):
            release_tool.release("0.0.1", dry_run=True)

    def test_kuru_calistirma_hicbir_seyi_degistirmez(self, repo):
        before = release_tool.read_version(repo)
        release_tool.release("0.2.0", dry_run=True)
        assert release_tool.read_version(repo) == before
        assert run_git(repo, "tag", "--list") == ""
        assert run_git(repo, "status", "--porcelain") == ""

    def test_gercek_yayin_commit_ve_ek_aciklamali_etiket_olusturur(self, repo):
        assert release_tool.release("0.2.0", dry_run=False) == 0
        assert release_tool.read_version(repo) == "0.2.0"
        assert run_git(repo, "log", "-1", "--format=%s") == "chore(release): v0.2.0"
        assert run_git(repo, "tag", "--list") == "v0.2.0"
        assert run_git(repo, "cat-file", "-t", "v0.2.0") == "tag"  # ek açıklamalı (hafif değil)
        assert run_git(repo, "status", "--porcelain") == ""
        assert "badge/Version-0.2.0-orange" in (repo / "README.md").read_text(encoding="utf-8")

    def test_arac_hicbir_seyi_gondermez(self, repo):
        assert run_git(repo, "remote") == ""  # uzak yok; araç itmeye de çalışmaz
        release_tool.release("0.2.0", dry_run=False)
        source = read("tools/release.py")
        assert '"push"' not in source and "git push" not in source.replace("git push origin", "")

    def test_var_olan_etiket_reddedilir(self, repo):
        run_git(repo, "tag", "v0.2.0")
        with pytest.raises(SystemExit, match="zaten var"):
            release_tool.release("0.2.0", dry_run=True)

    def test_kirli_agac_reddedilir(self, repo):
        (repo / "README.md").write_text("degisti\n", encoding="utf-8")
        with pytest.raises(SystemExit, match="temiz değil"):
            release_tool.release("0.2.0", dry_run=True)

    def test_main_disindaki_dal_reddedilir(self, repo):
        run_git(repo, "checkout", "-q", "-b", "gelistirme")
        with pytest.raises(SystemExit, match="yalnızca main"):
            release_tool.release("0.2.0", dry_run=True)

    def test_komut_satiri(self, capsys):
        assert release_tool.main(["--check-tag", "v" + __version__]) == 0
        assert release_tool.main([]) == 2
        assert release_tool.main(["1.0.0", "2.0.0"]) == 2


class TestIsAkislari:
    release_yml = read(".github/workflows/release.yml")
    ci_yml = read(".github/workflows/ci.yml")

    def test_yayin_yalniz_surum_etiketinde_tetiklenir(self):
        assert re.search(r'tags:\s*\n\s*- "v\*"', self.release_yml)
        assert "branches:" not in self.release_yml.split("jobs:")[0]  # dal itmesi yayın başlatmaz

    def test_etiket_kabuk_koduna_gomulmez_yalniz_ortam_degiskeniyle(self):
        offenders = [
            line for line in self.release_yml.splitlines()
            if "${{ github.ref_name }}" in line and not line.strip().startswith(("TAG:", "#"))
        ]  # fmt: skip
        assert offenders == []
        assert '--check-tag "$env:TAG"' in self.release_yml

    def test_yayin_adimlari_sirasi_etiket_lint_test_derleme_release(self):
        text = self.release_yml
        order = [text.index(marker) for marker in ("--check-tag", "ruff check", "pytest -q", "build_installer.py", "gh release create")]
        assert order == sorted(order)

    def test_yayin_kapiyi_atlamaz_ve_kurulum_dosyasini_yukler(self):
        assert "build_installer.py" in self.release_yml
        assert "--no-verify" not in self.release_yml and "--update-launcher-hash" not in self.release_yml
        assert "dist/installer/*" in self.release_yml  # kurulum dosyası + .sha256
        assert "--verify-tag" in self.release_yml and "--generate-notes" in self.release_yml
        assert '"Namaz Takip $($tag.TrimStart(\'v\'))"' in self.release_yml

    def test_on_surum_etiketi_prerelease_olur(self):
        assert 'Contains("-")' in self.release_yml and "--prerelease" in self.release_yml

    def test_yazma_izni_yalniz_yayin_isinde(self):
        assert "contents: write" in self.release_yml
        assert "contents: read" in self.ci_yml and "write" not in self.ci_yml.split("jobs:")[0]

    def test_python_surumu_yerel_venv_ile_ayni(self):
        for text in (self.release_yml, self.ci_yml):
            versions = set(re.findall(r'python-version: "([^"]+)"', text))
            assert versions == {"3.10.11"}  # exe özeti Python sürümüne bağlı

    def test_ci_lint_test_ve_guvenlik_taramasi(self):
        for expected in ("ruff check", "pytest -q", "pip_audit -r requirements.txt", "QT_QPA_PLATFORM: offscreen", "PYTHONWARNDEFAULTENCODING"):
            assert expected in self.ci_yml, expected
        assert re.search(r"pip-audit==\d+\.\d+\.\d+", self.ci_yml)  # sürüm sabit

    def test_ci_exe_ozetini_etiket_itmeden_sinar(self):
        assert "python build_exe.py" in self.ci_yml  # kapı: farklı özet = kırmızı
        assert "github.event_name != 'pull_request'" in self.ci_yml  # PR'larda ağır exe derlemesi koşmaz

    def test_bagimlilik_dosyalari_iki_akista_da_kullanilir(self):
        assert "requirements-dev.txt" in self.release_yml and "requirements-build.txt" in self.release_yml
        assert "requirements-build.txt" in self.ci_yml

    def test_satir_sonlari_lf(self):
        for relative in (".github/workflows/ci.yml", ".github/workflows/release.yml"):
            assert b"\r" not in (ROOT / relative).read_bytes(), relative
