"""Namaz Takip çalıştırılabilir dosya (EXE) derleyicisi: KARARLI EXE.

Exe'nin SHA-256 özeti sürümler arasında DEĞİŞMEZ. Windows Akıllı Uygulama Denetimi (SAC), imzasız her yeni exe
özetini yeniden değerlendirir ve engelleyebilir. Bir kez onaylanan exe sabit kalırsa güncellemeler yeni bir
çalıştırılabilir dosya getirmez; yalnızca `_internal` altındaki `.pyc` ve veri dosyaları değişir.

Gereken dört parça:
1. Sabit giriş betiği: `packaging/launcher.py`
2. Sabit derleme zaman damgası: `SOURCE_DATE_EPOCH = 1700000000`
3. Sabit PE sürüm kaynağı: `packaging/launcher_version_info.txt` (sabit 1.0.0.0)
4. Modüller exe dışında: `--debug=noarchive` (modüller .pyc olarak _internal altında)

Onay kapısı: `packaging/launcher.sha256`. Ayrıntı: docs/wiki/dagitim.md

Derlemeden sonra kullanılmayan Qt parçaları (WebEngine, Qt3D vb.) `_internal` altından silinir: bu exe'yi
değiştirmez (özet yalnızca exe dosyasındandır), kurulum dosyasını küçültür.
"""

import hashlib
import importlib.util
import os
import shutil
import sys
from pathlib import Path

from tools.build_onefile import EXCLUDED_MODULES, is_unused

LAUNCHER_EPOCH = 1700000000  # DEĞİŞTİRME (bilerek yeni özet denemek için tek yol; bkz. docs/wiki/dagitim.md)
APP_EXE_NAME = "NamazTakip"
LAUNCHER_ENTRY = Path("packaging") / "launcher.py"
LAUNCHER_VERSION_INFO = Path("packaging") / "launcher_version_info.txt"
LAUNCHER_HASH_FILE = Path("packaging") / "launcher.sha256"
ICON = Path("app") / "ui" / "assets" / "app.ico"

# (kaynak klasör, paket içi hedef): main.py donmuş durumda `sys._MEIPASS/app/ui/...` yolunu arar.
DATA_DIRS = (
    (Path("app") / "ui" / "qml", "app/ui/qml"),
    (Path("app") / "ui" / "assets", "app/ui/assets"),
)


def ensure_pyinstaller() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        sys.exit("[X] PyInstaller yok. `pip install -r requirements-build.txt` çalıştırın.")
    print("[OK] PyInstaller hazır.")


def clean_build_artifacts(root_dir: Path) -> None:
    print("\n[*] Eski derleme klasörleri temizleniyor...")
    for name in ("build", "dist"):
        path = root_dir / name
        if path.exists():
            shutil.rmtree(path)
            print(f"  - Temizlendi: {name}")


def pyinstaller_arguments(root_dir: Path) -> list[str]:
    arguments = [
        str(root_dir / LAUNCHER_ENTRY),
        f"--paths={root_dir}",
        f"--name={APP_EXE_NAME}",
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--noupx",  # UPX DLL imzalarını bozar, antivirüs yanlış pozitifini artırır
        "--debug=noarchive",  # modüller .pyc olarak _internal altında
        f"--version-file={root_dir / LAUNCHER_VERSION_INFO}",
        f"--icon={root_dir / ICON}",
    ]
    for module in EXCLUDED_MODULES:
        arguments.append(f"--exclude-module={module}")
    for source, destination in DATA_DIRS:
        source_path = root_dir / source
        if not source_path.is_dir():
            raise FileNotFoundError(f"Pakete eklenecek klasör yok: {source_path}")
        arguments.extend(["--add-data", f"{source_path}{os.pathsep}{destination}"])
    return arguments


def run_pyinstaller(arguments: list[str]) -> None:
    print("\n[*] Namaz Takip derleniyor, lütfen bekleyin...")
    os.environ["SOURCE_DATE_EPOCH"] = str(LAUNCHER_EPOCH)  # PyInstaller'ı çalıştırmadan hemen önce
    import PyInstaller.__main__

    PyInstaller.__main__.run(arguments)


def prune(app_dir: Path) -> None:
    """Kullanılmayan Qt parçalarını `_internal/PySide6` altından siler (exe etkilenmez)."""
    internal = app_dir / "_internal"
    package = internal / "PySide6"
    candidates = [*package.iterdir(), *(package / "qml").iterdir()]
    for path in candidates:
        relative = path.relative_to(internal).as_posix()
        if not is_unused(relative):
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def exe_sha256(exe: Path) -> str:
    return hashlib.sha256(exe.read_bytes()).hexdigest()


def check_launcher_hash(root_dir: Path, exe: Path, update: bool = False) -> None:
    """Derlenen exe, Windows'ta denenip onaylanan özetle aynı mı? Değilse derleme ve yayın durur."""
    actual = exe_sha256(exe)
    hash_file = root_dir / LAUNCHER_HASH_FILE
    if update:
        hash_file.write_text(f"{actual} *{APP_EXE_NAME}.exe\n", encoding="utf-8")
        print(f"[OK] Onaylanan exe özeti yazıldı: {actual}")
        return
    approved = hash_file.read_text(encoding="utf-8").split()[0].lower() if hash_file.is_file() else ""
    if approved == actual:
        print(f"[OK] Kararlı exe özeti onaylananla aynı: {actual[:16]}...")
        return
    print(f"[X] Kararlı exe özeti DEĞİŞTİ.\n    onaylanan: {approved or '(yok)'}\n    derlenen : {actual}")
    print(
        "    Beklenmeyen bir değişiklikse (farklı PyInstaller / Python / ortam) yayınlama. "
        "Bilerek yaptıysan: yeni exe'yi Windows'ta dene (build_verify.launch_check) ve "
        "`python build_installer.py --update-launcher-hash` ile onayla."
    )
    sys.exit(1)


def build_executable(update_launcher_hash: bool = False) -> Path:
    print("=" * 60)
    print("      Namaz Takip - EXE Derleme (kararlı exe)      ")
    print("=" * 60)
    root_dir = Path(__file__).parent.resolve()
    ensure_pyinstaller()
    clean_build_artifacts(root_dir)
    run_pyinstaller(pyinstaller_arguments(root_dir))
    app_dir = root_dir / "dist" / APP_EXE_NAME
    prune(app_dir)
    exe = app_dir / f"{APP_EXE_NAME}.exe"
    print(f"\n[OK] Derleme tamamlandı: {exe}")
    check_launcher_hash(root_dir, exe, update=update_launcher_hash)
    return exe


if __name__ == "__main__":
    build_executable(update_launcher_hash="--update-launcher-hash" in sys.argv[1:])
