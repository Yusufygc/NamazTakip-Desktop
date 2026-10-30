from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.domain.prayer import PrayerType
from app.core.domain.prayer_times import CalcMethod
from app.core.formatters import format_countdown, format_time
from app.core.strings import (
    CalcMethodStrings,
    DateStrings,
    NotificationStrings,
    PrayerDialogStrings,
    PrayerStrings,
    ui_strings,
)


def test_vakit_adlari():
    assert [PrayerStrings.name(p) for p in PrayerType] == ["Sabah", "Öğle", "İkindi", "Akşam", "Yatsı"]
    assert PrayerStrings.SUNRISE == "Güneş"


def test_her_yontemin_adi_dolu():
    names = [CalcMethodStrings.name(m) for m in CalcMethod]
    assert all(name.strip() for name in names)
    assert len(set(names)) == len(CalcMethod)


def test_uzun_tarih():
    assert DateStrings.long(date(2026, 1, 25)) == "25 Ocak 2026"
    assert DateStrings.long(date(2026, 12, 3)) == "3 Aralık 2026"


def test_bildirim_metinleri_mobille_ayni():
    assert NotificationStrings.adhan_title("İkindi") == "İkindi Vakti"
    assert NotificationStrings.adhan_body("İkindi") == "İkindi vakti girdi."
    assert NotificationStrings.reminder_title("Yatsı") == "Yatsı Namazını Kıldınız mı?"
    assert NotificationStrings.REMINDER_BODY == "Namazınızı işaretlemek için dokunun."


def test_saat_bicimi():
    assert format_time(datetime(2026, 1, 1, 5, 7, tzinfo=timezone.utc)) == "05:07"


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [(0, "00:00:00"), (59.4, "00:01:00"), (60, "00:01:00"), (3661, "01:01:01"), (86399, "23:59:59"), (-5, "00:00:00")],
)
def test_sayac_bicimi(seconds, expected):
    assert format_countdown(timedelta(seconds=seconds)) == expected


def _leaves(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _leaves(value, f"{path}.{key}" if path else key)
    else:
        yield path, node


def test_ui_metinleri_dolu_ve_metin():
    leaves = dict(_leaves(ui_strings()))
    assert len(leaves) >= 30
    assert all(isinstance(v, str) and v.strip() for v in leaves.values()), [k for k, v in leaves.items() if not str(v).strip()]


def test_ui_metin_yer_tutuculari():
    ui = ui_strings()
    expected = {
        ("home", "nextPrayer"): ["%1"],
        ("home", "todayPrayers"): ["%1"],
        ("home", "dayPrayers"): ["%1"],
        ("home", "completedSummary"): ["%1", "%2"],
        ("home", "countdownSemantics"): ["%1", "%2"],
        ("home", "prayerSemantics"): ["%1", "%2", "%3"],
        ("qaza", "dailyTargetValue"): ["%1"],
        ("qaza", "estimatedFinish"): ["%1", "%2"],
        ("qaza", "remainingPrayerCount"): ["%1"],
        ("qaza", "badge"): ["%1"],
        ("qaza", "confirmBody"): ["%1", "%2"],
        ("settings", "minutes"): ["%1"],
        ("missed", "rowSemantics"): ["%1", "%2"],
        ("update", "headline"): ["%1"],
        ("update", "versions"): ["%1"],
        ("update", "published"): ["%1"],
        ("update", "file"): ["%1"],
        ("update", "downloading"): ["%1"],
        ("update", "notificationBody"): ["%1"],
        ("update", "currentVersion"): ["%1"],
        ("tray", "nextPrayer"): ["%1", "%2"],
        ("tray", "tooltip"): ["%1", "%2"],
        ("settings", "themeSemantics"): ["%1"],
    }
    for (group, key), placeholders in expected.items():
        assert all(p in ui[group][key] for p in placeholders), (group, key)
    # Yer tutucusu olmayan metinlerde "%" kalmamalı (QML .arg() yanlışlıkla uygulanmasın).
    for path, value in _leaves(ui):
        if path not in {f"{g}.{k}" for g, k in expected}:
            assert "%" not in value, path


def test_her_temanin_adi_ve_alt_basligi_var():
    from app.services.settings_service import THEME_KEYS

    themes = ui_strings()["settings"]["themes"]
    assert sorted(themes) == sorted(THEME_KEYS)
    assert all(t["name"].strip() and t["subtitle"].strip() for t in themes.values())
    assert len({t["name"] for t in themes.values()}) == len(THEME_KEYS)


def test_diyalog_basligi_turkce_buyuk_harf():
    assert PrayerDialogStrings.title("İkindi") == "İKİNDİ NAMAZINI"
    assert PrayerDialogStrings.title("Yatsı") == "YATSI NAMAZINI"
    assert PrayerDialogStrings.title("Öğle") == "ÖĞLE NAMAZINI"
    assert PrayerDialogStrings.title("Sabah") == "SABAH NAMAZINI"
