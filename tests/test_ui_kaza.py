"""Kaza sayfası: gerçek Main.qml ekransız yüklenir, kartlar, onay ve planlayıcı akışları çalıştırılır."""

import pytest

from tests.qml_support import close_ui, find, js, load_ui
from tests.support import at

PRAYER_KEYS = ("fajr", "dhuhr", "asr", "maghrib", "isha")


@pytest.fixture
def ui(qapp):
    """Yeni kurulmuş uygulama: kaza yok."""
    handle = load_ui(qapp)
    handle.root.setProperty("pageIndex", 1)
    handle.qapp.processEvents()
    yield handle
    close_ui(handle)


@pytest.fixture
def ui_kaza(qapp):
    """24 Ekim'de kurulmuş, 26 Ekim'de açılmış uygulama: 24 ve 25 Ekim kaza listesinde (10 vakit)."""
    handle = load_ui(qapp, now=at(2026, 10, 26, 12), installed=at(2026, 10, 24, 12))
    handle.root.setProperty("pageIndex", 1)
    handle.qapp.processEvents()
    yield handle
    close_ui(handle)


def test_bos_durum(ui):
    assert find(ui, "qazaEmptyCard").property("visible") is True
    assert find(ui, "qazaOverviewCard").property("visible") is False
    assert find(ui, "qazaBacklogCard").property("visible") is False


def test_bos_durumdan_planlayici_acilir(ui):
    js(ui, find(ui, "qazaEmptyPlannerButton"), "clicked()")
    assert find(ui, "qazaPlannerDialog").property("opened") is True


def test_ozet_karti(ui_kaza):
    ui = ui_kaza
    assert find(ui, "qazaEmptyCard").property("visible") is False
    assert find(ui, "qazaOverviewCard").property("visible") is True
    assert find(ui, "qazaTotalText").property("text") == "10"
    assert find(ui, "qazaTargetText").property("text") == "Günde 2 Vakit"
    assert find(ui, "qazaEstimateText").property("text") == "Hedefinize uyarsanız tahmini bitiş: 31 Ekim 2026 (5 gün)"


def test_gun_kartlari_ilk_gun_acik(ui_kaza):
    ui = ui_kaza
    assert find(ui, "qazaDayCard_2026-10-25").property("expanded") is True
    assert find(ui, "qazaDayCard_2026-10-24").property("expanded") is False
    assert find(ui, "qazaCompensate_2026-10-25_fajr").property("visible") is True
    assert find(ui, "qazaCompensate_2026-10-24_fajr").property("visible") is False


def test_kart_acma_kapama_durumu_yenilemede_korunur(ui_kaza):
    ui = ui_kaza
    js(ui, find(ui, "qazaDayCard_2026-10-24"), "toggle()")
    assert find(ui, "qazaDayCard_2026-10-24").property("expanded") is True
    js(ui, find(ui, "qazaDayCard_2026-10-25"), "toggle()")
    assert find(ui, "qazaDayCard_2026-10-25").property("expanded") is False
    # Veri yenilenince kart nesneleri yeniden oluşur; seçim kaybolmamalı.
    ui.container.qaza_bridge.refresh()
    ui.qapp.processEvents()
    assert find(ui, "qazaDayCard_2026-10-24").property("expanded") is True
    assert find(ui, "qazaDayCard_2026-10-25").property("expanded") is False


def test_kaza_et_onay_akisi(ui_kaza):
    ui = ui_kaza
    dialog = find(ui, "qazaConfirmDialog")
    js(ui, find(ui, "qazaCompensate_2026-10-25_fajr"), "clicked()")
    assert dialog.property("opened") is True
    assert find(ui, "qazaConfirmBody").property("text") == "25 Ekim 2026 tarihli Sabah namazını kaza ettiniz mi?"
    js(ui, dialog, "confirm()")
    assert dialog.property("opened") is False
    assert find(ui, "qazaTotalText").property("text") == "9"
    assert find(ui, "qazaDayCard_2026-10-25").property("group")["count"] == 4
    assert find(ui, "qazaDayCard_2026-10-25").property("expanded") is True  # açık kart açık kalır
    # Vakitler ekranında "kaza edildi" görünür.
    ui.container.home_bridge.openDay("2026-10-25")
    assert next(r for r in ui.container.home_bridge.prayers if r["key"] == "fajr")["status"] == "compensated"


def test_kaza_et_iptal_etkisiz(ui_kaza):
    ui = ui_kaza
    dialog = find(ui, "qazaConfirmDialog")
    js(ui, find(ui, "qazaCompensate_2026-10-25_dhuhr"), "clicked()")
    js(ui, find(ui, "qazaConfirmCancel"), "clicked()")
    assert dialog.property("opened") is False
    assert find(ui, "qazaTotalText").property("text") == "10"


def test_vakitler_ekranindan_kilmadim_kaza_sayfasina_yansir(ui_kaza):
    ui = ui_kaza
    assert ui.container.home_bridge.markMissed("fajr") is True  # bugün (26 Ekim) kılmadım
    ui.qapp.processEvents()
    assert find(ui, "qazaTotalText").property("text") == "11"
    assert find(ui, "qazaDayCard_2026-10-26") is not None


def test_gecmis_borc_satirlari_ve_bir_kaza_dus(ui_kaza):
    ui = ui_kaza
    assert find(ui, "qazaBacklogCard").property("visible") is False
    ui.container.qaza_bridge.savePlan({"fajr": 10, "isha": 3}, 3)
    ui.qapp.processEvents()
    assert find(ui, "qazaBacklogCard").property("visible") is True
    assert find(ui, "qazaBacklogRow_fajr").property("visible") is True
    assert find(ui, "qazaBacklogRow_isha").property("visible") is True
    assert find(ui, "qazaBacklogRow_dhuhr").property("visible") is False  # borcu olmayan vakit gizli
    assert find(ui, "qazaTotalText").property("text") == "23"  # 10 otomatik + 13 geçmiş borç
    assert find(ui, "qazaTargetText").property("text") == "Günde 3 Vakit"
    js(ui, find(ui, "qazaDecrement_fajr"), "clicked()")
    assert ui.container.qaza_bridge.backlog[0]["count"] == 9
    assert find(ui, "qazaTotalText").property("text") == "22"


def test_planlayici_sureden_hesapla_ve_kaydet(ui_kaza):
    ui = ui_kaza
    planner = find(ui, "qazaPlannerDialog")
    js(ui, find(ui, "qazaPlannerButton"), "clicked()")
    assert planner.property("opened") is True
    assert find(ui, "planTarget").property("text") == "2"
    assert find(ui, "planCount_fajr").property("text") == "0"
    find(ui, "planYears").setProperty("text", "1")
    find(ui, "planDays").setProperty("text", "5")
    js(ui, planner, "applyDuration()")
    for key in PRAYER_KEYS:
        assert find(ui, f"planCount_{key}").property("text") == "370"  # 365 + 5
    assert find(ui, "planYears").property("text") == "0"  # süre alanları sıfırlanır
    # Kaydedilene kadar hiçbir şey yazılmaz.
    assert ui.container.qaza_bridge.summary["backlogTotal"] == 0
    find(ui, "planTarget").setProperty("text", "4")
    js(ui, planner, "save()")
    assert planner.property("opened") is False
    assert ui.container.qaza_bridge.summary["backlogTotal"] == 5 * 370
    assert ui.container.qaza_bridge.summary["dailyTarget"] == 4
    assert find(ui, "qazaTargetText").property("text") == "Günde 4 Vakit"


def test_planlayici_bos_alan_ve_iptal(ui_kaza):
    ui = ui_kaza
    planner = find(ui, "qazaPlannerDialog")
    js(ui, planner, "openPlanner()")
    find(ui, "planYears").setProperty("text", "")
    js(ui, planner, "applyDuration()")  # boş alan 0 sayılır, hata yok
    assert find(ui, "planCount_fajr").property("text") == "0"
    find(ui, "planCount_fajr").setProperty("text", "99")
    js(ui, find(ui, "planCancel"), "clicked()")
    assert planner.property("opened") is False
    assert ui.container.qaza_bridge.summary["backlogTotal"] == 0


def test_planlayici_gecersiz_hedef_1e_kirpilir(ui_kaza):
    ui = ui_kaza
    planner = find(ui, "qazaPlannerDialog")
    js(ui, planner, "openPlanner()")
    find(ui, "planTarget").setProperty("text", "")
    js(ui, planner, "save()")
    assert ui.container.qaza_bridge.summary["dailyTarget"] == 1


def test_planlayici_acilista_mevcut_plani_yukler(ui_kaza):
    ui = ui_kaza
    ui.container.qaza_bridge.savePlan({"asr": 42}, 7)
    js(ui, find(ui, "qazaPlannerDialog"), "openPlanner()")
    assert find(ui, "planCount_asr").property("text") == "42"
    assert find(ui, "planCount_fajr").property("text") == "0"
    assert find(ui, "planTarget").property("text") == "7"


def test_kaza_sayfasi_etkilesimlerinde_qml_hatasi_yok(ui_kaza):
    ui = ui_kaza
    js(ui, find(ui, "qazaCompensate_2026-10-25_asr"), "clicked()")
    js(ui, find(ui, "qazaConfirmDialog"), "confirm()")
    js(ui, find(ui, "qazaPlannerButton"), "clicked()")
    js(ui, find(ui, "qazaPlannerDialog"), "applyDuration()")
    js(ui, find(ui, "qazaPlannerDialog"), "save()")
    ui.container.settings_bridge.setThemeKey("dark")
    ui.qapp.processEvents()
    assert ui.messages.problems() == []
