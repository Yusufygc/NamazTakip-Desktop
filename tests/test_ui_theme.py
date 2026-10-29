"""Theme belirteçleri: QML'de gerçekten çözülüyor mu?

Geçersiz renk QML'de uyarı vermeden siyah çizilir (`onPrimary` adı sinyal işleyici adıyla çakıştığı için
düğme yazısı siyah çıktı; yalnızca ekran görüntüsünde fark edildi). Palet testi bunu görmez, çünkü Python
tarafında hesaplanır; bu yüzden değerler QML'den okunur ve kaynakta kullanılan her `Theme.x` tanımlıdır.
"""

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

QML_DIR = Path(__file__).resolve().parent.parent / "app" / "ui" / "qml"
THEME_KEYS = ["default", "dark", "ocean", "rose", "gold"]
COLOR_TOKENS = [
    "primary", "secondary", "accent", "dark", "background", "card", "text", "textLight", "danger",
    "secondaryText", "heroAccent", "textOnPrimary", "heroStart", "heroEnd", "textOnHero",
]  # fmt: skip


def _theme_members() -> set[str]:
    source = (QML_DIR / "theme" / "Theme.qml").read_text(encoding="utf-8")
    properties = set(re.findall(r"property\s+\w+\s+(\w+)\s*:", source))
    functions = set(re.findall(r"function\s+(\w+)\s*\(", source))
    return properties | functions


def test_kaynakta_kullanilan_her_theme_uyesi_tanimli():
    members = _theme_members()
    missing = []
    for path in QML_DIR.rglob("*.qml"):
        if path.parent.name == "theme":
            continue
        for name in set(re.findall(r"\bTheme\.(\w+)", path.read_text(encoding="utf-8"))):
            if name not in members:
                missing.append(f"{path.relative_to(QML_DIR).as_posix()}: Theme.{name}")
    assert not missing, missing


def test_sinyal_isleyici_adiyla_cakisan_ozellik_yok():
    """`onXxx` biçiminde (on + büyük harf) özellik adı QML'de sinyal işleyici gibi okunur."""
    bad = [name for name in _theme_members() if re.fullmatch(r"on[A-Z]\w*", name)]
    assert not bad, bad


@pytest.fixture
def engine(qapp):
    qml = QQmlEngine()
    qml.addImportPath(str(QML_DIR))
    yield qml
    qml.deleteLater()
    qapp.processEvents()


@pytest.mark.parametrize("theme", THEME_KEYS)
def test_tum_renk_belirtecleri_gecerli_renk_cozer(engine, qapp, theme):
    props = "\n".join(f"    property color t_{name}: Theme.{name}" for name in COLOR_TOKENS)
    source = f'import QtQuick\nimport "theme"\nItem {{\n{props}\n    Component.onCompleted: Theme.themeKey = "{theme}"\n}}'
    component = QQmlComponent(engine)
    component.setData(source.encode("utf-8"), QUrl.fromLocalFile(str(QML_DIR / "probe.qml")))
    item = component.create()
    assert item is not None, [e.toString() for e in component.errors()]
    qapp.processEvents()
    try:
        invalid = [name for name in COLOR_TOKENS if not item.property(f"t_{name}").isValid()]
        assert not invalid, f"{theme}: geçersiz renk: {invalid}"
        # Düğme ve sayaç yazısı: açık temalarda beyaz, koyu temada koyu zemin rengi.
        on_primary = item.property("t_textOnPrimary").name().lower()
        assert on_primary == ("#09130f" if theme == "dark" else "#ffffff")
        assert item.property("t_textOnHero").name().lower() == "#ffffff"
    finally:
        item.deleteLater()
        component.deleteLater()
        qapp.processEvents()
