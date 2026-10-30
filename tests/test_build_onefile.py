"""Derleme betiği: spec üretimi, PyInstaller komutu ve Qt süzme kuralları.

Gerçek derleme ve exe denemesi elle yapılır (docs/wiki/dagitim.md).
"""

import ast
from pathlib import Path

import pytest

from tools import build_onefile as build_exe

# QML'in ve çekirdeğin kullandığı Qt parçaları: hiçbir koşulda süzülmemeli/dışlanmamalı.
NEEDED_MODULES = ("QtCore", "QtGui", "QtQml", "QtQuick", "QtNetwork", "QtWidgets")
NEEDED_PATHS = (
    "PySide6/qml/QtQuick/qmldir",
    "PySide6/qml/QtQuick/Controls/Basic/Button.qml",
    "PySide6/qml/QtQuick/Shapes/qmldir",
    "PySide6/qml/QtQuick/Layouts/qmldir",
    "PySide6/qml/QtQml/qmldir",
    "PySide6/qml/Qt/labs/platform/qmldir",
    "PySide6/Qt6Core.dll",
    "PySide6/Qt6Gui.dll",
    "PySide6/Qt6Quick.dll",
    "PySide6/Qt6Qml.dll",
    "PySide6/Qt6Network.dll",
    "PySide6/Qt6QuickShapes.dll",
    "PySide6/Qt6QuickControls2.dll",
    "PySide6/Qt6LabsPlatform.dll",
    "PySide6/Qt6Widgets.dll",
    "PySide6/QtCore.pyd",
    "PySide6/plugins/platforms/qwindows.dll",
    "app/ui/qml/Main.qml",
    "base_library.zip",
)


def test_komut_spec_dosyasini_derler(tmp_path, monkeypatch):
    monkeypatch.setattr(build_exe, "WORK", tmp_path / "build")
    spec = build_exe.write_spec()
    command = build_exe.build_command(spec)
    for flag in ("--noconfirm", "--clean"):
        assert flag in command
    assert Path(command[-1]) == spec and spec.is_file()
    assert "--onedir" not in command  # spec içindeki EXE tek dosya üretir


def test_spec_gecerli_python_ve_tek_dosya_exe_tanimlar(tmp_path, monkeypatch):
    monkeypatch.setattr(build_exe, "WORK", tmp_path / "build")
    text = build_exe.write_spec().read_text(encoding="utf-8")
    tree = ast.parse(text)  # sözdizimi geçerli
    assert tree is not None
    # Tek dosya: EXE'ye ikili ve veri listeleri verilir, COLLECT yoktur (klasör çıktısı üretmez).
    assert "analysis.binaries,\n    analysis.datas," in text
    assert "COLLECT" not in text
    assert "console=False" in text  # pencereli, konsolsuz
    assert "name='NamazTakip'" in text
    assert "app.ico" in text
    assert "is_unused" in text  # süzme uygulanır
    for target in ("app/ui/qml", "app/ui/assets"):
        assert f'"{target}"' in text  # main.py frozen'da sys._MEIPASS/app/ui/... arar


def test_spec_yollari_mevcut(tmp_path, monkeypatch):
    monkeypatch.setattr(build_exe, "WORK", tmp_path / "build")
    text = build_exe.write_spec().read_text(encoding="utf-8")
    for relative in ("main.py", "app/ui/assets/app.ico", "app/ui/qml", "app/ui/assets"):
        path = build_exe.ROOT / relative
        assert path.exists()
        assert repr(str(path)) in text  # spec'e yazılan mutlak yol gerçek bir yoldur


def test_kullanilan_qt_modulleri_dislanmaz():
    excluded = {name.removeprefix("PySide6.") for name in build_exe.EXCLUDED_MODULES}
    assert not excluded & set(NEEDED_MODULES)


@pytest.mark.parametrize("dest", NEEDED_PATHS)
def test_kullanilan_parcalar_suzulmez(dest):
    assert build_exe.is_unused(dest) is False


@pytest.mark.parametrize(
    "dest",
    [
        "PySide6/Qt6WebEngineCore.dll",
        "PySide6/QtWebEngineProcess.exe",
        "PySide6/Qt6Pdf.dll",
        "PySide6/Qt63DCore.dll",
        "PySide6/Qt6Quick3DRuntimeRender.dll",
        "PySide6/qml/QtWebEngine/qmldir",
        "PySide6/qml/Qt3D/Core/qmldir",
        "PySide6/qml/QtMultimedia/qmldir",
        "PySide6/qml/QtNetwork/qmldir",
        "PySide6/translations/qt_tr.qm",
        "PySide6/resources/qtwebengine_resources.pak",
        "PySide6\\Qt6Charts.dll",  # ters eğik çizgili yol da süzülür
    ],
)
def test_kullanilmayan_parcalar_suzulur(dest):
    assert build_exe.is_unused(dest) is True


def test_pyside_disindaki_yollar_suzulmez():
    assert build_exe.is_unused("shiboken6/Shiboken.pyd") is False
    assert build_exe.is_unused("adhanpy/__init__.py") is False
    assert build_exe.is_unused("qml/QtWebEngine/x") is False  # yalnızca PySide6/ altı
