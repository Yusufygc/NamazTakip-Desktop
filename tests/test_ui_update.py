"""Güncelleme arayüzü: "Yeni sürüm var" penceresi, öncelik sırası ve Ayarlar kartı (gerçek Main.qml, ekransız)."""

import threading
import time

import pytest
from PySide6.QtCore import QCoreApplication

from app.services import update_service as svc
from app.services.update_service import UpdateInfo
from app.version import __version__
from tests.qml_support import close_ui, find, js, load_ui
from tests.support import at

BASE = "https://github.com/Yusufygc/NamazTakip-Desktop"


def info(version="99.0.0"):
    return UpdateInfo(
        version=version,
        tag="v" + version,
        page_url=f"{BASE}/releases/tag/v{version}",
        download_url=f"{BASE}/releases/download/v{version}/NamazTakip-Setup-{version}.exe",
        asset_name=f"NamazTakip-Setup-{version}.exe",
        size=50 * 1024 * 1024,
        notes="Yenilikler:\n- vakitten önce haber",
        published="2026-10-30",
    )


def pump_until(predicate, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def ui(qapp, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Arayüz kurulurken ağ isteği yapılmamalı")

    monkeypatch.setattr(svc.urllib.request, "urlopen", no_network)
    handle = load_ui(qapp)
    js(handle, find(handle, "autostartPromptDialog"), "answer(false)")  # ilk açılış sorusu önce gelir
    handle.bridge = handle.container.update_bridge
    handle.bridge._installable = True
    yield handle
    close_ui(handle)


def offer(ui, update=None):
    ui.bridge._info = update or info()
    ui.bridge.stateChanged.emit()
    ui.bridge.popupRequested.emit()
    ui.qapp.processEvents()


def dialog(ui):
    return find(ui, "updateDialog")


class TestPencere:
    def test_arayuz_kurulurken_ag_istegi_yok_ve_qml_hatasi_yok(self, ui):
        assert ui.messages.problems() == []
        assert dialog(ui).property("opened") is False

    def test_yeni_surum_bulununca_pencere_acilir_ve_surumu_gosterir(self, ui):
        offer(ui)
        assert dialog(ui).property("opened") is True
        assert find(ui, "updateHeadline").property("text") == "Namaz Takip v99.0.0 yayınlandı"
        assert "vakitten önce haber" in find(ui, "updateNotes").property("text")
        assert find(ui, "downloadButton").property("text") == "Güncelle"
        assert ui.messages.problems() == []

    def test_surum_notu_duz_metin_gosterilir(self, ui):
        offer(ui)
        assert js(ui, find(ui, "updateNotes"), "textFormat === Text.PlainText")[0] is True  # bağlantı/biçim çalıştırılmaz

    def test_surum_notu_alani_gorunur_genislikte(self, ui):
        offer(ui)
        # Yerleşim ilk karelerde tamamlanır; Flickable içinde kalıcı negatif genişlik hatası olmasın.
        assert pump_until(lambda: find(ui, "updateNotes").property("width") > 200)

    def test_bu_surumu_atla_kaydeder_ve_kapatir(self, ui):
        offer(ui)
        js(ui, find(ui, "skipVersionButton"), "clicked()")
        assert dialog(ui).property("opened") is False
        assert ui.container.settings_service.update_skipped_version == "99.0.0"

    def test_sonra_hicbir_sey_kaydetmeden_kapatir(self, ui):
        offer(ui)
        js(ui, find(ui, "laterButton"), "clicked()")
        assert dialog(ui).property("opened") is False
        assert ui.container.settings_service.update_skipped_version == ""

    def test_surum_dosyasi_yoksa_dugme_surum_sayfasi_der(self, ui):
        bare = info()
        object.__setattr__(bare, "download_url", "")
        offer(ui, bare)
        assert find(ui, "downloadButton").property("text") == "Sürüm Sayfası"

    def test_indirme_surerken_pencere_kilitlenir_ve_ilerleme_gorunur(self, ui, tmp_path):
        hold, launched = threading.Event(), []
        ui.bridge._download = lambda update_info, progress: (progress(40), hold.wait(10), tmp_path / "NamazTakip-Setup-99.0.0.exe")[2]
        ui.bridge._launcher = launched.append
        offer(ui)
        js(ui, find(ui, "downloadButton"), "clicked()")
        assert pump_until(lambda: ui.bridge.downloadProgress == 40)
        assert find(ui, "downloadButton").property("text") == "İndiriliyor… 40%"
        assert find(ui, "laterButton").property("enabled") is False
        assert find(ui, "skipVersionButton").property("enabled") is False
        assert find(ui, "downloadProgress").property("visible") is True
        assert js(ui, dialog(ui), "closePolicy === Popup.NoAutoClose")[0] is True  # Esc ile kapanmaz
        hold.set()
        assert pump_until(lambda: launched)

    def test_kurulum_baslayinca_uygulama_cikis_ister(self, ui, tmp_path):
        quits = []
        ui.container.shell_bridge.quitRequested.connect(lambda: quits.append(True))
        ui.bridge._download = lambda update_info, progress: tmp_path / "NamazTakip-Setup-99.0.0.exe"
        ui.bridge._launcher = lambda path: None
        offer(ui)
        js(ui, find(ui, "downloadButton"), "clicked()")
        assert pump_until(lambda: quits)  # köprü -> kabuk köprüsü -> app.quit

    def test_hata_mesaji_ve_surum_sayfasi_dugmesi_gorunur(self, ui):
        def failing(update_info, progress):
            raise svc.UpdateCheckError("İndirilen dosya doğrulanamadı; özet uyuşmuyor.")

        ui.bridge._download = failing
        offer(ui)
        assert find(ui, "updateError").property("visible") is False
        js(ui, find(ui, "downloadButton"), "clicked()")
        assert pump_until(lambda: ui.bridge.errorMessage != "")
        assert find(ui, "updateError").property("text") == "İndirilen dosya doğrulanamadı; özet uyuşmuyor."
        assert find(ui, "releasePageButton").property("visible") is True
        assert find(ui, "downloadButton").property("enabled") is True  # yeniden denenebilir


class TestOncelikSirasi:
    def test_pencere_gizliyken_bildirim_gider_gorununce_pencere_acilir(self, ui):
        ui.root.setProperty("visible", False)
        ui.qapp.processEvents()
        ui.bridge._info = info()
        ui.bridge.stateChanged.emit()
        ui.bridge.popupRequested.emit()
        ui.qapp.processEvents()
        assert find(ui, "appTray").property("lastMessageTitle") == "Yeni sürüm var"
        assert dialog(ui).property("opened") is False  # görünmeyen pencerede diyalog açılmaz
        ui.root.show()
        ui.qapp.processEvents()
        assert dialog(ui).property("opened") is True

    def test_otomatik_baslatma_sorusu_aciksa_guncelleme_bekler(self, qapp):
        handle = load_ui(qapp)  # autostart sorusu cevaplanmadı
        try:
            bridge = handle.container.update_bridge
            bridge._info = info()
            bridge.stateChanged.emit()
            bridge.popupRequested.emit()
            qapp.processEvents()
            assert find(handle, "autostartPromptDialog").property("opened") is True
            assert find(handle, "updateDialog").property("opened") is False
            js(handle, find(handle, "autostartPromptDialog"), "answer(false)")
            assert find(handle, "updateDialog").property("opened") is True
        finally:
            close_ui(handle)

    def test_kacirilan_vakit_sorusu_acikken_guncelleme_ondan_sonra_gelir(self, qapp):
        handle = load_ui(qapp, now=at(2026, 10, 26, 20), installed=at(2026, 10, 26, 8), last_active=at(2026, 10, 26, 17))
        try:
            js(handle, find(handle, "autostartPromptDialog"), "answer(false)")
            assert find(handle, "missedPrayersDialog").property("opened") is True
            bridge = handle.container.update_bridge
            bridge._info = info()
            bridge.stateChanged.emit()
            bridge.popupRequested.emit()
            qapp.processEvents()
            assert find(handle, "updateDialog").property("opened") is False
            js(handle, find(handle, "missedLater"), "clicked()")
            assert find(handle, "missedPrayersDialog").property("opened") is False
            assert find(handle, "updateDialog").property("opened") is True
        finally:
            close_ui(handle)


class TestAyarlarKarti:
    @pytest.fixture
    def settings_ui(self, ui):
        ui.root.setProperty("pageIndex", 2)
        ui.qapp.processEvents()
        return ui

    def test_kurulu_surum_gorunur_durum_baslangicta_gizli(self, settings_ui):
        assert find(settings_ui, "updateCurrentVersion").property("text") == f"Kurulu sürüm: v{__version__}"
        assert find(settings_ui, "updateStatusText").property("visible") is False

    def test_simdi_denetle_durumu_gosterir(self, settings_ui):
        settings_ui.bridge._check = lambda: None
        js(settings_ui, find(settings_ui, "checkUpdatesButton"), "clicked()")
        assert pump_until(lambda: not settings_ui.bridge.checking)
        settings_ui.qapp.processEvents()
        assert find(settings_ui, "updateStatusText").property("text") == f"Güncelsiniz: v{__version__} en son sürüm."

    def test_elle_denetimde_yeni_surum_pencereyi_acar(self, settings_ui):
        settings_ui.bridge._check = lambda: info()
        js(settings_ui, find(settings_ui, "checkUpdatesButton"), "clicked()")
        assert pump_until(lambda: find(settings_ui, "updateDialog").property("opened") is True)

    def test_denetim_sirasinda_dugme_pasif(self, settings_ui):
        hold = threading.Event()
        settings_ui.bridge._check = lambda: (hold.wait(10), None)[1]
        js(settings_ui, find(settings_ui, "checkUpdatesButton"), "clicked()")
        assert find(settings_ui, "checkUpdatesButton").property("enabled") is False
        hold.set()
        assert pump_until(lambda: not settings_ui.bridge.checking)

    def test_acilista_denetim_anahtari_ayari_degistirir(self, settings_ui):
        switch = find(settings_ui, "updateCheckSwitch")
        assert switch.property("checked") is True
        js(settings_ui, switch, "click()")
        assert settings_ui.container.settings_service.settings.update_check_enabled is False
        assert find(settings_ui, "updateCheckSwitch").property("checked") is False
        js(settings_ui, switch, "click()")
        assert settings_ui.container.settings_service.settings.update_check_enabled is True
        assert settings_ui.messages.problems() == []
