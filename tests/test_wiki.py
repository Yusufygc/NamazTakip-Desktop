"""Wiki sağlığı: kırık [[link]], öksüz sayfa ve indeks eksiği olmamalı."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "docs" / "wiki"
LINK = re.compile(r"\[\[([^\]]+)\]\]")


def _strip_code(text: str) -> str:
    """Kod bloklarındaki ve satır içi koddaki örnek [[...]] ifadeleri bağlantı sayılmaz."""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", text)


def _links(path: Path) -> list[str]:
    return LINK.findall(_strip_code(path.read_text(encoding="utf-8")))


def _pages() -> dict[str, Path]:
    return {p.stem: p for p in WIKI.glob("*.md")}


def test_zorunlu_sayfalar_var():
    pages = _pages()
    assert "index" in pages and "log" in pages


def test_kirik_link_yok():
    pages = _pages()
    broken = [
        (path.name, target)
        for path in [*pages.values(), ROOT / "CLAUDE.md"]
        for target in _links(path)
        if target not in pages
    ]
    assert not broken, broken


def test_oksuz_sayfa_yok():
    pages = _pages()
    inbound = {name: set() for name in pages}
    for name, path in pages.items():
        for target in _links(path):
            if target in inbound and target != name:
                inbound[target].add(name)
    orphans = [name for name, sources in inbound.items() if not sources]
    assert not orphans, orphans


def test_indeks_tum_sayfalari_listeler():
    pages = _pages()
    index = _links(WIKI / "index.md")
    missing = [name for name in pages if name != "index" and name not in index]
    assert not missing, missing


def test_claude_md_wiki_girisini_gosterir():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/wiki/index.md" in text
