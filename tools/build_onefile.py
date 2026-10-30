"""Namaz Takip'i PyInstaller ile TAŞINABİLİR tek dosyalı exe olarak paketler (`--onefile`).

Bu, kurulum dosyasının (build_installer.py) yanında isteğe bağlı bir seçenektir: kararlı exe DEĞİLDİR
(kod exe'nin içine gömülür, her sürümde özet değişir; Windows Akıllı Uygulama Denetimi her sürümü yeniden
değerlendirir) ve onay kapısından geçmez. Dağıtım yolu `python build_installer.py`'dir (docs/wiki/dagitim.md).

Kullanım (proje kökünden, venv içinde):  python tools/build_onefile.py [--keep-build]
Çıktı: dist/portable/NamazTakip.exe (tek dosya; istenen klasöre kopyalanıp oradan çalıştırılır).
`is_unused` ve `EXCLUDED_MODULES` kararlı derleme tarafından da kullanılır (build_exe.py).
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.version import APP_NAME, __version__  # noqa: E402

EXE_NAME = "NamazTakip"
DIST = ROOT / "dist" / "portable"
WORK = ROOT / "build"

# Uygulamanın kullanmadığı büyük Qt modülleri paketten çıkarılır (boyut). QML'in kullandığı modüller
# (Quick, Controls, Layouts, Shapes, Qt.labs.platform) çıkarılmaz.
EXCLUDED_MODULES = (
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtQuick3D",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtGraphs",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtLocation",
    "PySide6.QtPositioning",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSerialBus",
    "PySide6.QtTest",
    "PySide6.QtSql",
    "PySide6.QtTextToSpeech",
    "PySide6.QtRemoteObjects",
    "PySide6.QtSpatialAudio",
    "PySide6.QtVirtualKeyboard",
    "tkinter",
    "pytest",
)

# PyInstaller'ın Qt kancası `PySide6/qml` klasörünün tamamını ve bağlı DLL'leri toplar (WebEngine tek başına
# yaklaşık 200 MB). Uygulamanın kullanmadığı QML modül klasörleri ve DLL'ler pakete girmeden süzülür.
UNUSED_QML_DIRS = (
    "Qt3D", "Qt5Compat", "QtCharts", "QtDataVisualization", "QtGraphs", "QtLocation", "QtMultimedia",
    "QtPositioning", "QtQuick3D", "QtRemoteObjects", "QtScxml", "QtSensors", "QtTest", "QtTextToSpeech",
    "QtWebChannel", "QtWebEngine", "QtWebSockets", "QtWebView", "QtNetwork",
)  # fmt: skip
UNUSED_DLL_PREFIXES = (
    "Qt6WebEngine", "Qt6Pdf", "Qt63D", "Qt6Quick3D", "Qt6Charts", "Qt6DataVisualization", "Qt6Graphs",
    "Qt6Location", "Qt6Multimedia", "Qt6Positioning", "Qt6RemoteObjects", "Qt6Scxml", "Qt6Sensors",
    "Qt6TextToSpeech", "Qt6WebChannel", "Qt6WebSockets", "Qt6WebView", "Qt6SpatialAudio", "Qt6Test",
    "Qt6Designer", "Qt6Help", "Qt6Bluetooth", "Qt6Nfc", "Qt6SerialPort", "Qt6SerialBus", "Qt6Sql",
    "QtWebEngineProcess",
)  # fmt: skip
UNUSED_PACKAGE_DIRS = ("translations", "resources")  # QML'de standart diyalog yok; WebEngine kaynakları


def is_unused(dest: str) -> bool:
    """Paket içi hedef yolu (`PySide6/...`) kullanılmayan bir Qt parçasına mı ait."""
    parts = dest.replace("\\", "/").split("/")
    if len(parts) < 2 or parts[0] != "PySide6":
        return False
    if parts[1] in UNUSED_PACKAGE_DIRS:
        return True
    if parts[1] == "qml":
        return len(parts) > 2 and parts[2] in UNUSED_QML_DIRS
    return len(parts) == 2 and parts[1].startswith(UNUSED_DLL_PREFIXES)


SPEC_TEMPLATE = '''\
import sys

sys.path.insert(0, {root!r})
from tools.build_onefile import is_unused

analysis = Analysis(
    [{main!r}],
    pathex=[{root!r}],
    datas=[({qml!r}, "app/ui/qml"), ({assets!r}, "app/ui/assets")],
    excludes={excludes!r},
)
analysis.binaries = [item for item in analysis.binaries if not is_unused(item[0])]
analysis.datas = [item for item in analysis.datas if not is_unused(item[0])]
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name={name!r},
    icon={icon!r},
    console=False,
    upx=False,
)
'''


def write_spec() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    spec = WORK / f"{EXE_NAME}.spec"
    spec.write_text(
        SPEC_TEMPLATE.format(
            root=str(ROOT),
            main=str(ROOT / "main.py"),
            qml=str(ROOT / "app" / "ui" / "qml"),
            assets=str(ROOT / "app" / "ui" / "assets"),
            excludes=list(EXCLUDED_MODULES),
            name=EXE_NAME,
            icon=str(ROOT / "app" / "ui" / "assets" / "app.ico"),
        ),
        encoding="utf-8",
    )
    return spec


def build_command(spec: Path) -> list[str]:
    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        str(spec),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} {__version__} exe derlemesi")
    parser.add_argument("--keep-build", action="store_true", help="build/ ara klasörünü silme")
    args = parser.parse_args()

    result = subprocess.run(build_command(write_spec()), cwd=str(ROOT), check=False)
    if result.returncode != 0:
        print("PyInstaller başarısız oldu.", file=sys.stderr)
        return result.returncode

    exe = DIST / f"{EXE_NAME}.exe"
    if not exe.is_file():
        print(f"Beklenen çıktı yok: {exe}", file=sys.stderr)
        return 1
    if not args.keep_build:
        shutil.rmtree(WORK, ignore_errors=True)
    print(f"Hazır: {exe} ({exe.stat().st_size / (1024 * 1024):.0f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
