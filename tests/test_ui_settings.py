"""Ayarlar sayfası: gerçek Main.qml ekransız yüklenir, anahtarlar, seçenekler ve tema kartları çalıştırılır."""

import pytest

from tests.qml_support import close_ui, find, js, load_ui

THEME_KEYS = ["default", "dark", "ocean", "rose", "gold"]
METHOD_KEYS = ["diyanet", "mwl", "egyptian", "karachi", "ummalqura", "isna"]
REMINDERS = [5, 10, 15, 20, 30, 45, 60]


@pytest.fixture
def ui(qapp):
    handle = load_ui(qapp)
    handle.root.setProperty("pageIndex", 2)
    handle.qapp.processEvents()
    yield handle
    close_ui(handle)


@pytest.fixture
def ui_without_location(qapp):
    handle = load_ui(qapp, with_location=False)
    handle.root.setProperty("pageIndex", 2)
    handle.qapp.processEvents()
    yield handle
    close_ui(handle)


def click(ui, name):
    js(ui, find(ui, name), "clicked()")


def toggle(ui, name):
    """Kullanıcı tıklaması gibi: `toggle()` `toggled` sinyalini yayınlamaz, `click()` yayınlar."""
    js(ui, find(ui, name), "click()")


def test_sayfa_yuklenir_ve_qml_hatasi_yok(ui):
    assert find(ui, "settingsPage") is not None
    assert ui.messages.problems() == []


class TestBildirimler:
    def test_anahtar_ve_hatirlatma_suresi_baslangic_degerleri(self, ui):
        assert find(ui, "notificationsSwitch").property("checked") is True
        for minutes in REMINDERS:
            chip = find(ui, f"reminderChip_{minutes}")
            assert chip.property("selected") is (minutes == 15)

    def test_hatirlatma_suresi_secilir_ve_kalici(self, ui):
        click(ui, "reminderChip_30")
        assert ui.container.settings_bridge.reminderMinutes == 30
        assert ui.container.settings_service.settings.reminder_minutes == 30
        assert find(ui, "reminderChip_30").property("selected") is True
        assert find(ui, "reminderChip_15").property("selected") is False

    def test_bildirim_kapaliyken_sureler_pasif(self, ui):
        toggle(ui, "notificationsSwitch")
        assert ui.container.settings_bridge.notificationsEnabled is False
        assert find(ui, "notificationsSwitch").property("checked") is False
        assert find(ui, "reminderChip_15").property("enabled") is False
        toggle(ui, "notificationsSwitch")
        assert ui.container.settings_bridge.notificationsEnabled is True
        assert find(ui, "reminderChip_15").property("enabled") is True

    def test_secilen_sure_saat_servisine_yansir(self, ui):
        """Ayar yalnızca saklanmaz: hatırlatma bildirimi seçilen süreye göre gelir."""
        from datetime import date

        from app.core.domain.prayer import PrayerType
        from tests.support import at

        click(ui, "reminderChip_30")
        logic = ui.container.clock_service._logic
        assert logic.tick(at(2026, 10, 26, 13, 8, 0)).notifications == ()  # 12:53 + 15 dk artık erken
        due = logic.tick(at(2026, 10, 26, 13, 23, 0)).notifications  # 12:53 + 30 dk
        assert [(n.prayer, n.day) for n in due] == [(PrayerType.DHUHR, date(2026, 10, 26))]


class TestKonumVeYontem:
    def test_sehir_etiketi_ve_secici(self, ui):
        assert find(ui, "settingsCityText").property("text") == "İstanbul, Türkiye"
        picker = find(ui, "settingsCityPicker")
        assert picker.property("opened") is False
        click(ui, "settingsChooseCityButton")
        assert picker.property("opened") is True
        js(ui, picker, "choose('Kars')")
        assert picker.property("opened") is False
        assert find(ui, "settingsCityText").property("text") == "Kars, Türkiye"
        assert ui.container.home_bridge.cityLabel == "Kars, Türkiye"  # Vakitler ekranı da güncellenir

    def test_sehir_yokken_uyari_metni(self, ui_without_location):
        assert find(ui_without_location, "settingsCityText").property("text") == "Şehir seçilmedi"

    def test_alti_yontem_ve_secim(self, ui):
        for key in METHOD_KEYS:
            assert find(ui, f"calcMethod_{key}").property("selected") is (key == "diyanet")
        before = ui.container.home_bridge.prayers[0]["time"]
        click(ui, "calcMethod_egyptian")
        assert ui.container.settings_bridge.calcMethodKey == "egyptian"
        assert find(ui, "calcMethod_egyptian").property("selected") is True
        assert find(ui, "calcMethod_diyanet").property("selected") is False
        assert ui.container.home_bridge.prayers[0]["time"] != before  # vakitler yeniden hesaplandı


class TestMasaustu:
    def test_baslangic_degerleri(self, ui):
        assert find(ui, "autostartSwitch").property("checked") is False
        assert find(ui, "closeToTraySwitch").property("checked") is True

    def test_anahtarlar_ayari_yazar(self, ui):
        toggle(ui, "autostartSwitch")
        toggle(ui, "closeToTraySwitch")
        settings = ui.container.settings_service.settings
        assert settings.autostart is True
        assert settings.close_to_tray is False
        toggle(ui, "autostartSwitch")
        assert ui.container.settings_service.settings.autostart is False
        assert ui.container.settings_bridge.needsAutostartPrompt is False  # cevap verildi


class TestTema:
    def test_bes_kart_ve_secili_olan(self, ui):
        for key in THEME_KEYS:
            assert find(ui, f"themeCard_{key}").property("selected") is (key == "default")

    @pytest.mark.parametrize(
        ("key", "background"),
        [("dark", "#0c1411"), ("ocean", "#f3f8fb"), ("rose", "#fcf6f7"), ("gold", "#faf6ec"), ("default", "#f8f5ee")],
    )
    def test_karta_tiklayinca_tema_degisir_ve_kalici(self, ui, key, background):
        click(ui, f"themeCard_{key}")
        assert ui.root.property("color").name().lower() == background
        assert ui.container.settings_service.settings.theme_key == key
        assert find(ui, f"themeCard_{key}").property("selected") is True
        assert sum(find(ui, f"themeCard_{k}").property("selected") for k in THEME_KEYS) == 1

    def test_kartlarin_ornek_renkleri_kendi_temasindan(self, ui):
        dark_card = find(ui, "themeCard_dark")
        assert dark_card.property("palette").toVariant()["primary"] == "#38B281"
        assert dark_card.property("names")["name"] == "Koyu"


def test_ayarlar_etkilesimlerinden_sonra_qml_hatasi_yok(ui):
    toggle(ui, "notificationsSwitch")
    toggle(ui, "notificationsSwitch")
    click(ui, "reminderChip_45")
    click(ui, "calcMethod_karachi")
    click(ui, "themeCard_dark")
    click(ui, "themeCard_gold")
    toggle(ui, "autostartSwitch")
    toggle(ui, "closeToTraySwitch")
    ui.qapp.processEvents()
    assert ui.messages.problems() == []
