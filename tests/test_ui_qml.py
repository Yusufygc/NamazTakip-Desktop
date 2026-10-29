"""Vakitler sayfası: gerçek Main.qml ekransız yüklenir, nesneler bulunur, işlemler çalıştırılır."""

import pytest
from PySide6.QtCore import QObject, QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent, QQmlEngine

from tests.qml_support import QmlMessages, close_ui, find, js, load_ui
from tests.support import OCT26, at

ROW_KEYS = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]


@pytest.fixture
def ui(qapp):
    handle = load_ui(qapp)
    yield handle
    close_ui(handle)


@pytest.fixture
def ui_without_location(qapp):
    handle = load_ui(qapp, with_location=False)
    yield handle
    close_ui(handle)


def test_hata_dedektoru_gercekten_hata_yakalar(qapp):
    """Boş sonuç sahte yeşil olmasın: bilerek bozuk QML'de dedektör dolu liste vermeli."""
    messages = QmlMessages()
    qInstallMessageHandler(messages)
    try:
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(b"import QtQuick\nItem { property int broken: notDefinedAnywhere.value }", QUrl("bozuk.qml"))
        item = component.create()
        qapp.processEvents()
        assert messages.problems(), "ReferenceError yakalanmadı"
        if item is not None:
            item.deleteLater()
        component.deleteLater()
        engine.deleteLater()
    finally:
        qInstallMessageHandler(None)


class TestVakitlerSayfasi:
    def test_geri_sayim_karti(self, ui):
        assert find(ui, "countdownText").property("text") == "00:53:00"
        assert find(ui, "nextPrayerNameText").property("text") == "Öğle"
        assert find(ui, "cityText").property("text") == "İstanbul, Türkiye"
        assert find(ui, "selectedDateText").property("text") == "26 Ekim 2026"

    def test_altı_satir_vakit_ve_siradaki_vurgu(self, ui):
        for key in ROW_KEYS:
            row = find(ui, f"prayerRow_{key}")
            data = row.property("rowData")
            assert data["time"] == OCT26[key]
            assert row.property("isNext") is (key == "dhuhr")
            assert row.property("isSunrise") is (key == "sunrise")
            assert row.property("markable") is (key != "sunrise")
        assert find(ui, "prayerRow_fajr").property("isFirst") is True
        assert find(ui, "prayerRow_isha").property("isLast") is True

    def test_tamamlanan_ozeti(self, ui):
        assert find(ui, "completedSummaryText").property("text") == "0 / 5 Vakit Eda Edildi"
        ui.container.home_bridge.markPerformed("fajr", False)
        ui.container.home_bridge.markPerformed("asr", False)
        ui.qapp.processEvents()
        assert find(ui, "completedSummaryText").property("text") == "2 / 5 Vakit Eda Edildi"

    def test_satira_tiklayinca_diyalog_acilir(self, ui):
        dialog = find(ui, "prayerDialog")
        assert dialog.property("opened") is False
        js(ui, find(ui, "prayerRow_asr"), "activate()")
        assert dialog.property("opened") is True
        assert dialog.property("rowData")["dialogTitle"] == "İKİNDİ NAMAZINI"

    def test_diyalogdan_cemaatle_kildim(self, ui):
        dialog = find(ui, "prayerDialog")
        js(ui, find(ui, "prayerRow_asr"), "activate()")
        find(ui, "congregationCheck").setProperty("checked", True)
        js(ui, dialog, "submitPerformed()")
        assert dialog.property("opened") is False
        row = find(ui, "prayerRow_asr").property("rowData")
        assert (row["status"], row["isCongregation"]) == ("performed", True)
        assert find(ui, "prayerRow_asr").property("done") is True

    def test_diyalogdan_kilmadim(self, ui):
        dialog = find(ui, "prayerDialog")
        js(ui, find(ui, "prayerRow_fajr"), "activate()")
        js(ui, dialog, "submitMissed()")
        assert dialog.property("opened") is False
        assert find(ui, "prayerRow_fajr").property("missed") is True
        # Kaza ekranı verisi de güncellendi (bridge zinciri).
        assert ui.container.qaza_bridge.summary["autoCount"] == 1

    def test_vazgec_isaret_yazmaz(self, ui):
        dialog = find(ui, "prayerDialog")
        js(ui, find(ui, "prayerRow_dhuhr"), "activate()")
        js(ui, dialog, "close()")
        assert dialog.property("opened") is False
        assert find(ui, "prayerRow_dhuhr").property("status") == "pending"

    def test_gunes_satiri_diyalog_acmaz(self, ui):
        js(ui, find(ui, "prayerRow_sunrise"), "activate()")
        assert find(ui, "prayerDialog").property("opened") is False

    def test_gun_gezinme_dugmeleri(self, ui):
        assert find(ui, "previousDayButton").property("enabled") is False  # takip başlangıcı bugün
        assert find(ui, "goTodayButton").property("visible") is False
        js(ui, find(ui, "nextDayButton"), "clicked()")
        assert find(ui, "selectedDateText").property("text") == "27 Ekim 2026"
        assert find(ui, "goTodayButton").property("visible") is True
        # Gelecek günde satırlar işaretlenemez, diyalog açılmaz.
        assert find(ui, "prayerRow_fajr").property("markable") is False
        js(ui, find(ui, "prayerRow_fajr"), "activate()")
        assert find(ui, "prayerDialog").property("opened") is False
        js(ui, find(ui, "goTodayButton"), "clicked()")
        assert find(ui, "selectedDateText").property("text") == "26 Ekim 2026"

    def test_sayac_saatle_ilerler(self, ui):
        ui.clock.set(at(2026, 10, 26, 12, 30, 0))
        ui.container.clock_service.tick_now()
        ui.qapp.processEvents()
        assert find(ui, "countdownText").property("text") == "00:23:00"
        ui.clock.set(at(2026, 10, 26, 12, 53, 1))
        ui.container.clock_service.tick_now()
        ui.qapp.processEvents()
        assert find(ui, "nextPrayerNameText").property("text") == "İkindi"
        assert find(ui, "prayerRow_asr").property("isNext") is True
        assert find(ui, "prayerRow_dhuhr").property("isNext") is False

    def test_etkilesim_sonrasi_qml_hatasi_yok(self, ui):
        js(ui, find(ui, "prayerRow_asr"), "activate()")
        js(ui, find(ui, "prayerDialog"), "submitPerformed()")
        js(ui, find(ui, "nextDayButton"), "clicked()")
        ui.container.settings_bridge.setThemeKey("dark")
        ui.qapp.processEvents()
        assert ui.messages.problems() == []


class TestSehirSecici:
    def test_konum_yokken_secici_kendiliginden_acilir(self, ui_without_location):
        ui = ui_without_location
        assert find(ui, "cityPicker").property("opened") is True
        assert find(ui, "noLocationCard").property("visible") is True
        assert find(ui, "chooseCityButton") is not None

    def test_arama_turkce_duyarsiz_ve_secim_vakitleri_getirir(self, ui_without_location):
        ui = ui_without_location
        picker = find(ui, "cityPicker")
        find(ui, "citySearchField").setProperty("text", "istanbul")
        ui.qapp.processEvents()
        assert [r["city"] for r in picker.property("results")] == ["İstanbul"]
        js(ui, picker, "choose('İstanbul')")
        assert picker.property("opened") is False
        assert ui.container.home_bridge.hasLocation is True
        assert find(ui, "cityText").property("text") == "İstanbul, Türkiye"
        assert find(ui, "noLocationCard").property("visible") is False

    def test_ilk_sehir_secimi_sayaci_hemen_gosterir(self, ui_without_location):
        """Yenileme `countdownChanged` yayınlamazsa sayaç ilk tike kadar boş kalır (ekran görüntüsünde yakalandı)."""
        ui = ui_without_location
        assert find(ui, "countdownText").property("text") == ""
        js(ui, find(ui, "cityPicker"), "choose('İstanbul')")
        text = find(ui, "countdownText").property("text")
        assert len(text) == 8 and text[2] == ":" and text != "00:00:00"
        assert find(ui, "nextPrayerNameText").property("text") != ""

    def test_sonuc_yoksa_liste_bos(self, ui_without_location):
        ui = ui_without_location
        find(ui, "citySearchField").setProperty("text", "zzzz")
        ui.qapp.processEvents()
        assert find(ui, "cityList").property("count") == 0

    def test_olmayan_sehir_secici_acik_kalir(self, ui_without_location):
        ui = ui_without_location
        picker = find(ui, "cityPicker")
        js(ui, picker, "choose('Atlantis')")
        assert picker.property("opened") is True
        assert ui.container.home_bridge.hasLocation is False

    def test_konum_varken_secici_acilmaz(self, ui):
        assert find(ui, "cityPicker").property("opened") is False
        assert find(ui, "noLocationCard").property("visible") is False


class TestKabukVeTema:
    def test_kenar_cubugu_uc_oge_ve_sayfa_degisimi(self, ui):
        for index in range(3):
            assert find(ui, f"navItem{index}") is not None
        assert find(ui, "navItem0").property("selected") is True
        js(ui, find(ui, "navItem1"), "clicked()")
        assert ui.root.property("pageIndex") == 1
        assert find(ui, "navItem1").property("selected") is True
        assert find(ui, "navItem0").property("selected") is False

    def test_tema_degisince_pencere_rengi_degisir(self, ui):
        assert ui.root.property("color").name().lower() == "#f8f5ee"
        ui.container.settings_bridge.setThemeKey("dark")
        ui.qapp.processEvents()
        assert ui.root.property("color").name().lower() == "#0c1411"
        for key, expected in {"ocean": "#f3f8fb", "rose": "#fcf6f7", "gold": "#faf6ec", "default": "#f8f5ee"}.items():
            ui.container.settings_bridge.setThemeKey(key)
            ui.qapp.processEvents()
            assert ui.root.property("color").name().lower() == expected

    def test_bilinmeyen_tema_degismez(self, ui):
        assert ui.container.settings_bridge.setThemeKey("neon") is False
        assert ui.root.property("color").name().lower() == "#f8f5ee"


def test_nesne_agaci_bos_degil(ui):
    assert len(ui.root.findChildren(QObject)) > 50
