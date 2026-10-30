"""Sürüm yayınlama yardımcısı: sürüm numarasını tüm kaynaklarda yükseltir, commit atar ve etiket (tag) oluşturur.

Kullanım:
    python tools/release.py 0.2.0              # sürümü yükselt, "chore(release): v0.2.0" commit'i at, v0.2.0 etiketini oluştur
    python tools/release.py 0.2.0 --dry-run    # yalnızca ne yapılacağını göster
    python tools/release.py --check-tag v0.2.0 # etiket, app/version.py ile aynı mı (CI'da kullanılır)

Hiçbir şey GitHub'a gönderilmez. Sonra elle: `git push origin main` ve `git push origin v0.2.0`; etiket itilince
`.github/workflows/release.yml` testleri koşar, kurulum dosyasını derler ve GitHub Release olarak yayınlar.
Yapay zekâ asistanları kullanıcının AÇIK isteği olmadan etiket oluşturmaz ve itmez (docs/wiki/dagitim.md).
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
VERSION_FILE = Path("app") / "version.py"


def read_version(root: "Path | None" = None) -> str:
    match = re.search(r'__version__ = "([^"]+)"', ((root or ROOT) / VERSION_FILE).read_text(encoding="utf-8"))
    if not match:
        raise SystemExit("app/version.py içinde __version__ bulunamadı.")
    return match.group(1)


def as_tuple(version: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(version)
    if not match:
        raise SystemExit(f"Geçersiz sürüm: {version!r} (beklenen biçim: X.Y.Z)")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def _sub(path: Path, pattern: str, replacement: str, count_expected: int = 1) -> None:
    text = path.read_bytes().decode("utf-8")
    new_text, count = re.subn(pattern, replacement, text)
    if count != count_expected:
        raise SystemExit(f"{path.name}: {pattern!r} için {count_expected} eşleşme beklendi, {count} bulundu.")
    path.write_bytes(new_text.encode("utf-8"))  # satır sonlarını olduğu gibi korur


def bump_files(root: Path, version: str) -> None:
    """Sürümü tek kaynakta (`app/version.py`) ve README rozetinde yazar.

    exe'nin Windows sürüm kaynağı (`packaging/launcher_version_info.txt`) BİLEREK yükseltilmez: exe'nin SHA-256 özeti
    sürümler arasında sabit kalmalı (Akıllı Uygulama Denetimi onayı); ürün sürümü kurulum dosyasında ve uygulamada görünür.
    """
    as_tuple(version)  # biçimi doğrula
    _sub(root / VERSION_FILE, r'__version__ = "[^"]+"', f'__version__ = "{version}"')
    _sub(root / "README.md", r"badge/Version-[0-9.]+-orange", f"badge/Version-{version}-orange")


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False)
    if result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} başarısız:\n{result.stderr.strip()}")
    return result.stdout.strip()


def check_tag(tag: str) -> int:
    expected = "v" + read_version()
    if tag != expected:
        print(f"Etiket {tag!r}, app/version.py sürümüyle ({expected!r}) uyuşmuyor.")
        return 1
    print(f"Etiket {tag} sürümle uyumlu.")
    return 0


def release(version: str, dry_run: bool) -> int:
    current = read_version()
    if as_tuple(version) <= as_tuple(current):
        raise SystemExit(f"Yeni sürüm ({version}) mevcut sürümden ({current}) büyük olmalı.")
    tag = f"v{version}"
    if git("tag", "--list", tag):
        raise SystemExit(f"{tag} etiketi zaten var.")
    if git("status", "--porcelain"):
        raise SystemExit("Çalışma ağacı temiz değil; önce değişiklikleri commit'leyin.")
    branch = git("branch", "--show-current")
    if branch != "main":
        raise SystemExit(f"Yayın yalnızca main dalından yapılır (şu an: {branch}).")
    print(f"{current} -> {version}  (etiket: {tag})")
    if dry_run:
        print("Deneme çalıştırması: hiçbir dosya değişmedi.")
        return 0
    bump_files(ROOT, version)
    git("add", "app/version.py", "README.md")
    git("commit", "-m", f"chore(release): v{version}")
    git("tag", "-a", tag, "-m", f"Namaz Takip {version}")
    print(f"Hazır. GitHub'a göndermek için:\n  git push origin main\n  git push origin {tag}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "--check-tag":
        return check_tag(argv[1])
    versions = [arg for arg in argv if not arg.startswith("--")]
    if len(versions) != 1:
        print(__doc__)
        return 2
    return release(versions[0].lstrip("v"), dry_run="--dry-run" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
