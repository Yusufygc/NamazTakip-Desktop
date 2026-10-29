"""Masaüstü kabuğu: tepsi, bildirim iletimi, kapatma davranışı, bildirime tıklama, autostart sorusu.

Ekransız ortamda sistem tepsisi yoktur (`tray.available` False). Tepsi gerektiren davranışlar, Main.qml'deki
`trayAvailable` özelliği testte doğrudan ayarlanarak sınanır; gerçek tepsiyle doğrulama ayrıca elle yapılır.
"""

import pytest

from app.services.autostart_service import VALUE_NAME
from tests.qml_support import close_ui, find, js, load_ui
from tests.support import FAKE_EXE, at


def record(signal) -> list:
    received: list = []
    signal.connect(lambda *args: received.append(args))
    return received


@pytest.fixture
def ui(qapp):
    handle = load_ui(qapp)
    # Bu testlerde "sormaya hazır" durumu değil, cevaplanmış autostart durumu temel alınır.
    yield handle
    close_ui(handle)


@pytest.fixture
def ui_answered(qapp):
    """Autostart sorusu cevaplanmış uygulama (diyalog açık değil)."""
    handle = load_ui(qapp)
    js(handle, find(handle, "autostartPromptDialog"), "answer(false)")
    handle.registry.values.clear()
    yield handle
    close_ui(handle)


class TestTepsi:
    def test_ipucu_siradaki_vakti_gosterir(self, ui):
        tray = find(ui, "appTray")
        assert tray.property("tooltip") == "Namaz Takip  •  Sıradaki: Öğle 12:53"
        ui.clock.set(at(2026, 10, 26, 12, 53, 1))
        ui.container.clock_service.tick_now()
        ui.qapp.processEvents()
        assert tray.property("tooltip") == "Namaz Takip  •  Sıradaki: İkindi 15:46"

    def test_sehir_yokken_ipucu_yalniz_ad(self, qapp):
        handle = load_ui(qapp, with_location=False)
        try:
            assert find(handle, "appTray").property("tooltip") == "Namaz Takip"
        finally:
            close_ui(handle)

    def test_ekransiz_ortamda_tepsi_yok(self, ui):
        assert find(ui, "appTray").property("available") is False
        assert ui.root.property("trayAvailable") is False
        assert ui.root.property("hideOnClose") is False  # tepsi yoksa kapatınca çıkılır


class TestBildirim:
    def test_saat_servisi_bildirimi_tepsiye_ulasir(self, ui):
        ui.clock.set(at(2026, 10, 26, 12, 53, 0))
        ui.container.clock_service.tick_now()
        ui.qapp.processEvents()
        assert find(ui, "appTray").property("lastMessageTitle") == "Öğle Vakti"

    def test_bildirim_kapaliyken_gelmez(self, ui):
        ui.container.settings_service.set_notifications_enabled(False)
        ui.clock.set(at(2026, 10, 26, 12, 53, 0))
        ui.container.clock_service.tick_now()
        ui.qapp.processEvents()
        assert find(ui, "appTray").property("lastMessageTitle") == ""

    def test_bildirime_tiklayinca_o_vaktin_diyalogu_acilir(self, ui_answered):
        ui = ui_answered
        ui.clock.set(at(2026, 10, 26, 15, 46, 0))
        ui.container.clock_service.tick_now()  # İkindi bildirimi
        ui.qapp.processEvents()
        ui.container.home_bridge.nextDay()  # kullanıcı başka güne bakıyor
        assert ui.container.home_bridge.isToday is False
        ui.container.shell_bridge.activateLastNotification()  # tepsi `messageClicked` yerine
        ui.qapp.processEvents()
        dialog = find(ui, "prayerDialog")
        assert dialog.property("opened") is True
        assert dialog.property("rowData")["key"] == "asr"
        assert ui.container.home_bridge.isToday is True  # bildirimin günü seçildi
        assert ui.root.property("pageIndex") == 0

    def test_bildirim_tiklamasi_baska_sayfadayken_vakitler_sayfasina_doner(self, ui_answered):
        ui = ui_answered
        ui.root.setProperty("pageIndex", 2)
        ui.clock.set(at(2026, 10, 26, 12, 53, 0))
        ui.container.clock_service.tick_now()
        ui.container.shell_bridge.activateLastNotification()
        ui.qapp.processEvents()
        assert ui.root.property("pageIndex") == 0
        assert find(ui, "prayerDialog").property("rowData")["key"] == "dhuhr"

    def test_ikinci_ornek_istegi_pencereyi_one_getirir(self, ui_answered):
        ui = ui_answered
        ui.root.hide()
        assert ui.root.property("visible") is False
        ui.container.shell_bridge.showWindowRequested.emit()
        ui.qapp.processEvents()
        assert ui.root.property("visible") is True


class TestPencereKapatma:
    def test_tepsi_varken_kapat_gizler_uygulama_kapanmaz(self, ui_answered):
        ui = ui_answered
        quits = record(ui.container.shell_bridge.quitRequested)
        ui.root.setProperty("trayAvailable", True)  # gerçek tepsi simülasyonu
        assert ui.root.property("hideOnClose") is True
        ui.root.close()
        ui.qapp.processEvents()
        assert ui.root.property("visible") is False
        assert quits == []

    def test_ilk_kapatmada_bilgi_bir_kez_gosterilir(self, ui_answered):
        ui = ui_answered
        ui.root.setProperty("trayAvailable", True)
        tray = find(ui, "appTray")
        assert ui.container.settings_service.settings.tray_hint_shown is False
        ui.root.close()
        ui.qapp.processEvents()
        assert tray.property("hintCount") == 1
        assert tray.property("lastMessageTitle") == "Namaz Takip tepside çalışıyor"
        assert ui.container.settings_service.settings.tray_hint_shown is True
        ui.container.shell_bridge.showWindowRequested.emit()
        ui.qapp.processEvents()
        ui.root.close()
        ui.qapp.processEvents()
        assert tray.property("hintCount") == 1  # ikinci kapatmada tekrar yok

    def test_ayar_kapaliysa_kapat_cikis_ister(self, ui_answered):
        ui = ui_answered
        quits = record(ui.container.shell_bridge.quitRequested)
        ui.root.setProperty("trayAvailable", True)
        ui.container.settings_bridge.setCloseToTray(False)
        assert ui.root.property("hideOnClose") is False
        ui.root.close()
        ui.qapp.processEvents()
        assert quits == [()]

    def test_tepsi_yokken_kapat_cikis_ister(self, ui_answered):
        ui = ui_answered
        quits = record(ui.container.shell_bridge.quitRequested)
        ui.root.close()  # tepsi yok: gizlenirse uygulamaya bir daha ulaşılamaz
        ui.qapp.processEvents()
        assert quits == [()]

    def test_tepsi_menusundeki_cikis(self, ui_answered):
        ui = ui_answered
        quits = record(ui.container.shell_bridge.quitRequested)
        ui.container.shell_bridge.requestQuit()
        assert quits == [()]


class TestAutostartSorusu:
    def test_ilk_acilista_sorulur(self, ui):
        assert find(ui, "autostartPromptDialog").property("opened") is True

    def test_evet_ayari_yazar_kaydi_olusturur_ve_bir_daha_sorulmaz(self, ui):
        dialog = find(ui, "autostartPromptDialog")
        js(ui, find(ui, "autostartPromptYes"), "clicked()")
        assert dialog.property("opened") is False
        assert ui.container.settings_service.settings.autostart is True
        assert ui.registry.values[VALUE_NAME] == f'"{FAKE_EXE}" --autostart'
        assert ui.container.settings_bridge.needsAutostartPrompt is False

    def test_hayir_ayari_false_yapar_kayit_yazmaz(self, ui):
        js(ui, find(ui, "autostartPromptNo"), "clicked()")
        assert ui.container.settings_service.settings.autostart is False
        assert ui.registry.values == {}
        assert ui.container.settings_bridge.needsAutostartPrompt is False

    def test_cevaplaninca_bir_daha_sorulmaz(self, ui):
        dialog = find(ui, "autostartPromptDialog")
        js(ui, dialog, "answer(false)")
        assert dialog.property("opened") is False
        js(ui, ui.root, "maybePromptAutostart()")  # cevaplı: yeniden açılmaz
        assert dialog.property("opened") is False

    def test_kapatilip_cevaplanmayan_soru_tekrar_sorulabilir(self, ui):
        dialog = find(ui, "autostartPromptDialog")
        js(ui, dialog, "close()")  # Esc: cevap sayılmaz
        assert ui.container.settings_bridge.needsAutostartPrompt is True
        js(ui, ui.root, "maybePromptAutostart()")
        assert dialog.property("opened") is True

    def test_sehir_yokken_once_sehir_secici_sonra_soru(self, qapp):
        handle = load_ui(qapp, with_location=False)
        try:
            assert find(handle, "cityPicker").property("opened") is True
            assert find(handle, "autostartPromptDialog").property("opened") is False
            js(handle, find(handle, "cityPicker"), "choose('İstanbul')")  # kapanınca soru gelir
            assert find(handle, "autostartPromptDialog").property("opened") is True
        finally:
            close_ui(handle)

    def test_ayarlardaki_anahtar_da_kaydi_degistirir(self, ui_answered):
        ui = ui_answered
        ui.root.setProperty("pageIndex", 2)
        js(ui, find(ui, "autostartSwitch"), "click()")
        assert ui.registry.values[VALUE_NAME] == f'"{FAKE_EXE}" --autostart'
        js(ui, find(ui, "autostartSwitch"), "click()")
        assert ui.registry.values == {}


class TestGizliBaslatma:
    def test_tepsi_yokken_autostart_penceresi_yine_gorunur(self, qapp):
        """`--autostart` ile ama tepsi yoksa pencere gizli kalırsa uygulama erişilmez olur."""
        handle = load_ui(qapp, start_hidden=True)
        try:
            assert handle.container.shell_bridge.startHidden is True
            assert handle.root.property("visible") is True
        finally:
            close_ui(handle)

    def test_pencere_gorunur_degilken_soru_sorulmaz(self, ui):
        dialog = find(ui, "autostartPromptDialog")
        js(ui, dialog, "close()")
        ui.root.hide()
        ui.qapp.processEvents()
        js(ui, ui.root, "maybePromptAutostart()")  # gizli (yalnızca tepside) çalışırken kullanıcıya soru çıkmaz
        assert dialog.property("opened") is False


def test_kabuk_etkilesimlerinde_qml_hatasi_yok(ui_answered):
    ui = ui_answered
    ui.root.setProperty("trayAvailable", True)
    ui.clock.set(at(2026, 10, 26, 12, 53, 0))
    ui.container.clock_service.tick_now()
    ui.container.shell_bridge.activateLastNotification()
    ui.root.close()
    ui.container.shell_bridge.showWindowRequested.emit()
    ui.qapp.processEvents()
    assert ui.messages.problems() == []


def test_kenar_cubugu_ikon_ve_yazi_kutuda_ortalanir(ui):
    """İçerik düğme kutusunun tam ortasındadır (Column'u contentItem olarak çapalamak yukarı kaydırıyordu)."""
    for index in range(3):
        item = find(ui, f"navItem{index}")
        content = item.property("contentItem")
        column = content.childItems()[0]
        assert column.y() == content.height() - (column.y() + column.height())
        assert abs((content.y() + column.y() + column.height() / 2) - item.height() / 2) < 0.5
