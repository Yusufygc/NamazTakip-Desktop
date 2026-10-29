"""Bekçi testleri: mimari ve kodlama kuralları teste bağlıdır, yalnızca belgeye değil."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"venv", ".venv", "build", "dist", ".git", ".pytest_cache", ".ruff_cache", "__pycache__"}
TEXT_SUFFIXES = {".py", ".qml", ".md", ".toml", ".ini", ".txt", ".yml", ".yaml", ".json"}


def _files(*suffixes: str):
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        yield path


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def test_kaynak_dosyalarda_utf8_bom_yok():
    offenders = [_rel(p) for p in _files(*TEXT_SUFFIXES) if p.read_bytes().startswith(b"\xef\xbb\xbf")]
    assert not offenders, f"BOM'lu dosyalar: {offenders}"


def test_ciplak_veya_sessiz_except_yok():
    offenders = []
    for path in _files(".py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.type is None:
                offenders.append(f"{_rel(path)}:{node.lineno} çıplak except")
            elif all(isinstance(stmt, ast.Pass) for stmt in node.body):
                offenders.append(f"{_rel(path)}:{node.lineno} sessiz except (yalnızca pass)")
    assert not offenders, offenders


def test_domain_katmani_pyside_icerik_aktarmaz():
    domain = ROOT / "app" / "core" / "domain"
    if not domain.is_dir():
        return
    offenders = []
    for path in domain.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            if any(name.split(".")[0] in {"PySide6", "shiboken6"} for name in names):
                offenders.append(f"{_rel(path)}:{node.lineno}")
    assert not offenders, f"core/domain Qt içe aktarıyor: {offenders}"


# Katman yönü: ui/qml → bridge → services → core/repositories → core/domain. Her katmanın içe aktaramayacakları.
FORBIDDEN_IMPORTS = {
    "app/core/domain/": ("PySide6", "shiboken6", "sqlite3", "app.core.repositories", "app.core.database", "app.services", "app.bridge"),
    "app/core/repositories/": ("PySide6", "app.services", "app.bridge", "app.container"),
    "app/services/": ("app.bridge", "app.container"),
    "app/bridge/": ("sqlite3", "app.core.repositories", "app.core.database", "app.container"),
}


def _imported_modules(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [(alias.name, node.lineno) for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.module, node.lineno))
    return found


def test_katman_yonu_ihlal_edilmez():
    offenders = []
    for path in _files(".py"):
        rel = _rel(path)
        for prefix, forbidden in FORBIDDEN_IMPORTS.items():
            if not rel.startswith(prefix):
                continue
            for module, line in _imported_modules(path):
                if any(module == name or module.startswith(name + ".") for name in forbidden):
                    offenders.append(f"{rel}:{line} {module}")
    assert not offenders, f"Katman yönü ihlali: {offenders}"


def test_sqlite_yalnizca_veri_katmaninda():
    allowed = {"app/core/database.py"}
    offenders = []
    for path in _files(".py"):
        rel = _rel(path)
        if not rel.startswith("app/") or rel in allowed or rel.startswith("app/core/repositories/"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "sqlite3" for a in node.names):
                offenders.append(f"{rel}:{node.lineno}")
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "sqlite3":
                offenders.append(f"{rel}:{node.lineno}")
    assert not offenders, f"sqlite3 veri katmanı dışında: {offenders}"


QML_DIR = ROOT / "app" / "ui" / "qml"
_QML_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
_TURKISH_LETTERS = re.compile("[ÇĞİÖŞÜçğıöşü]")


def user_text_literals(source: str) -> list[str]:
    """QML kaynağında kullanıcıya görünecek gibi duran metin sabitlerini bulur.

    Kimlik/anahtar (`prayerRow_`, `star8`), renk, kısayol (`Ctrl+1`), yalnızca simge/noktalama içeren
    ayraçlar (`"•  "`) metin sayılmaz; boşluklu İngilizce/Türkçe kelime öbeği veya Türkçe harf içeren sabit sayılır.
    """
    found = []
    for line in source.splitlines():
        code = line.strip()
        if code.startswith(("import ", "pragma ", "//")):
            continue
        for literal in _QML_STRING.findall(code):
            has_words = re.search(r"[A-Za-zÇĞİÖŞÜçğıöşü]{2,}", literal) is not None
            if has_words and (" " in literal.strip() or _TURKISH_LETTERS.search(literal)):
                found.append(literal)
    return found


def test_qml_sabit_metin_yok():
    """Kullanıcıya görünen metin `strings`'ten gelir. `theme/` (yazı tipi adı, ikon yolu) hariçtir."""
    offenders = []
    for path in QML_DIR.rglob("*.qml"):
        if "theme" in path.relative_to(QML_DIR).parts:
            continue
        for literal in user_text_literals(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(ROOT).as_posix()}: {literal!r}")
    assert not offenders, offenders


def test_sabit_metin_dedektoru_ayirt_eder():
    assert user_text_literals('Text { text: "Sıradaki Namaz" }') == ["Sıradaki Namaz"]
    assert user_text_literals('Text { text: "Kıldım" }') == ["Kıldım"]
    assert user_text_literals('Text { text: "Next prayer" }') == ["Next prayer"]
    # Kimlik, anahtar, renk, kısayol ve simge/noktalama ayraçları metin sayılmaz.
    ok = 'objectName: "prayerRow_" + key; name: "star8"; sequence: "Ctrl+1"; text: "•  " + a; color: "#FFFFFF"'
    assert user_text_literals(ok) == []
    assert user_text_literals('import "../theme"\n// "Türkçe yorum"') == []
