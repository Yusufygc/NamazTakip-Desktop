"""5 temada metin kontrastı (WCAG AA, küçük yazı için >= 4,5:1).

Palet tek kaynaktan, `Theme.qml`'den okunur. Harmanlama oranları QML bileşenlerindeki değerlerle
aynı tutulur (PrayerRow, CountdownCard, SideBar); orada değişirse burada da güncellenmeli.
"""

import re
from pathlib import Path

import pytest

THEME = Path(__file__).resolve().parent.parent / "app" / "ui" / "qml" / "theme" / "Theme.qml"
THEME_KEYS = ["default", "dark", "ocean", "rose", "gold"]
MIN_RATIO = 4.5


def _load_palettes() -> dict[str, dict]:
    source = THEME.read_text(encoding="utf-8")
    block = source[source.index("readonly property var palettes") : source.index("readonly property var current")]
    palettes = {}
    for match in re.finditer(r'"(\w+)":\s*\{(.*?)\}', block, re.S):
        body = match.group(2)
        colors = {k: _rgb(v) for k, v in re.findall(r'(\w+):\s*"(#[0-9A-Fa-f]{6})"', body)}
        colors["isDark"] = "isDark: true" in body
        palettes[match.group(1)] = colors
    return palettes


def _rgb(value: str) -> tuple[float, float, float]:
    return tuple(int(value[i : i + 2], 16) / 255 for i in (1, 3, 5))


def _luminance(color) -> float:
    def channel(v: float) -> float:
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def blend(over, alpha: float, base):
    return tuple(o * alpha + b * (1 - alpha) for o, b in zip(over, base))


PALETTES = _load_palettes()
WHITE = (1.0, 1.0, 1.0)


def pairs(p: dict) -> dict[str, tuple]:
    dark = p["isDark"]
    card, background = p["card"], p["background"]
    next_row = blend(p["secondary"], 0.14 if dark else 0.12, card)  # PrayerRow: sıradaki
    done_row = blend(p["primary"], 0.18 if dark else 0.08, card)  # PrayerRow: kılındı
    missed_row = blend(p["danger"], 0.12 if dark else 0.07, card)  # PrayerRow: kılınmadı
    hero_start = _rgb("#16382B") if dark else p["dark"]
    hero_end = _rgb("#0F261D") if dark else p["primary"]
    on_primary = _rgb("#09130F") if dark else WHITE
    return {
        "metin / kart": (p["text"], card),
        "metin / arka plan": (p["text"], background),
        "ikincil metin / kart": (p["textLight"], card),
        "ikincil metin / arka plan": (p["textLight"], background),
        "ikincil metin / sıradaki satır": (p["textLight"], next_row),
        "ikincil metin / kılındı satırı": (p["textLight"], done_row),
        "birincil / kart": (p["primary"], card),
        "birincil / arka plan": (p["primary"], background),
        "birincil / kılındı satırı": (p["primary"], done_row),
        "tehlike / kart": (p["danger"], card),
        "tehlike / kılınmadı satırı": (p["danger"], missed_row),
        "vurgu yazısı / kart": (p["secondaryText"], card),
        "vurgu yazısı / sıradaki satır": (p["secondaryText"], next_row),
        "kaza rozeti: birincil / kart %6": (p["primary"], blend(p["primary"], 0.06, card)),  # DayCard
        "açık düğme yazısı / beyaz": (hero_start, WHITE),  # AppButton variant "light" (özet kartı üstü)
        "seçenek yazısı / %6 dolgu": (p["text"], blend(p["primary"], 0.06, card)),  # ChoiceChips (seçilmemiş)
        "seçili satır yazısı / %8 dolgu": (p["text"], blend(p["primary"], 0.16 if dark else 0.08, card)),  # RadioRow
        "düğme yazısı / birincil": (on_primary, p["primary"]),
        "düğme yazısı / tehlike": (on_primary, p["danger"]),
        "sayaç beyaz / degrade başı": (WHITE, hero_start),
        "sayaç beyaz / degrade sonu": (WHITE, hero_end),
        "sayaç soluk beyaz / degrade başı": (blend(WHITE, 0.92, hero_start), hero_start),
        "sayaç soluk beyaz / degrade sonu": (blend(WHITE, 0.92, hero_end), hero_end),
        "sayaç vurgusu / degrade başı": (p["heroAccent"], hero_start),
        "sayaç vurgusu / degrade sonu": (p["heroAccent"], hero_end),
    }


def test_bes_tema_okundu():
    assert sorted(PALETTES) == sorted(THEME_KEYS)
    for palette in PALETTES.values():
        assert {"primary", "secondary", "secondaryText", "heroAccent", "danger", "card", "background", "text", "textLight"} <= set(palette)


@pytest.mark.parametrize("theme", THEME_KEYS)
def test_metin_kontrasti_aa(theme):
    failures = {name: round(contrast(a, b), 2) for name, (a, b) in pairs(PALETTES[theme]).items() if contrast(a, b) < MIN_RATIO}
    assert not failures, f"{theme}: {MIN_RATIO}:1 altında: {failures}"


def test_olcum_gercekten_ayirt_eder():
    # Ham `secondary` küçük yazıda yetersizdir; bu yüzden secondaryText/heroAccent ayrı belirteçtir.
    default = PALETTES["default"]
    assert contrast(default["secondary"], default["card"]) < MIN_RATIO
    assert contrast(default["secondaryText"], default["card"]) >= MIN_RATIO
