"""Güncelleme köprüsü: sessiz açılış denetimi, elle denetim, atlama, indirme, kurulum başlatma ve Windows engeli.

Referans: GitClean Archiver testleri uyarlandı (docs/wiki/guncelleme.md). Ağ ve kurulum her zaman sahtedir.
"""

import threading
import time

import pytest
from PySide6.QtCore import QCoreApplication

from app.bridge import update_bridge as module
from app.bridge.update_bridge import UpdateBridge
from app.services import update_service as svc
from app.services.update_service import InstallerBlockedError, UpdateCheckError, UpdateInfo
from app.version import __version__
from tests.support import at, build_services

BASE = "https://github.com/Yusufygc/NamazTakip-Desktop"


@pytest.fixture
def settings():
    return build_services(at(2026, 10, 30, 12)).settings


@pytest.fixture(autouse=True)
def no_real_cleanup(monkeypatch):
    """Açılış denetimi gerçek %TEMP% klasörüne dokunmasın."""
    monkeypatch.setattr(svc, "cleanup_update_directory", lambda directory=None: None)


def info(version="99.0.0", download=True):
    return UpdateInfo(
        version=version,
        tag="v" + version,
        page_url=f"{BASE}/releases/tag/v{version}",
        download_url=f"{BASE}/releases/download/v{version}/NamazTakip-Setup-{version}.exe" if download else "",
        asset_name=f"NamazTakip-Setup-{version}.exe",
        size=50 * 1024 * 1024,
        notes="Yenilikler:\n- vakitten önce haber",
        published="2026-10-30",
    )


def pump_until(predicate, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        QCoreApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    return False


def make(settings, result, calls=None, **kwargs):
    def check():
        if calls is not None:
            calls.append(1)
        if isinstance(result, Exception):
            raise result
        return result

    kwargs.setdefault("installable", True)
    return UpdateBridge(settings, check=check, **kwargs)


def run_check(bridge, manual):
    popups = []
    bridge.popupRequested.connect(lambda: popups.append(True))
    (bridge.checkNow if manual else bridge.startupCheck)()
    assert pump_until(lambda: not bridge.checking)
    QCoreApplication.processEvents()
    return popups


class TestDenetim:
    def test_acilis_denetimi_yeni_surum_varsa_pencereyi_ister(self, qapp, settings):
        bridge = make(settings, info())
        assert run_check(bridge, manual=False) == [True]
        assert bridge.updateAvailable and bridge.latestVersion == "99.0.0" and "vakitten önce haber" in bridge.releaseNotes
        assert bridge.installerLabel == "NamazTakip-Setup-99.0.0.exe, 50 MB" and bridge.publishedDate == "2026-10-30"

    def test_acilis_denetimi_guncelken_ve_ag_hatasinda_sessiz(self, qapp, settings):
        assert run_check(make(settings, None), manual=False) == []
        bridge = make(settings, UpdateCheckError("GitHub'a ulaşılamadı."))
        assert run_check(bridge, manual=False) == [] and bridge.statusText == ""  # açılışta hata gösterilmez

    def test_elle_denetim_her_sonucu_durum_satirinda_bildirir(self, qapp, settings):
        bridge = make(settings, None)
        run_check(bridge, manual=True)
        assert bridge.statusText == f"Güncelsiniz: v{__version__} en son sürüm." and not bridge.updateAvailable
        bridge = make(settings, UpdateCheckError("GitHub'a ulaşılamadı."))
        run_check(bridge, manual=True)
        assert bridge.statusText == "GitHub'a ulaşılamadı."
        bridge = make(settings, RuntimeError("beklenmedik"))
        run_check(bridge, manual=True)
        assert bridge.statusText == "Güncelleme denetimi yapılamadı."  # beklenmeyen hata da arayüzü düşürmez

    def test_atlanan_surum_acilista_sessiz_elle_denetimde_gorunur(self, qapp, settings):
        bridge = make(settings, info("99.0.0"))
        run_check(bridge, manual=False)
        bridge.skipVersion()
        assert settings.update_skipped_version == "99.0.0"
        again = make(settings, info("99.0.0"))
        assert run_check(again, manual=False) == []  # aynı sürüm: açılışta sessiz
        assert run_check(again, manual=True) == [True]  # elle denetim: yine gösterilir
        newer = make(settings, info("99.1.0"))
        assert run_check(newer, manual=False) == [True]  # daha yeni sürüm: yeniden sorulur

    def test_kapali_denetim_acilista_aga_cikmaz(self, qapp, settings, monkeypatch):
        calls = []
        bridge = make(settings, info(), calls)
        settings.set_update_check_enabled(False)
        assert settings.settings.update_check_enabled is False
        bridge.startupCheck()
        QCoreApplication.processEvents()
        assert calls == [] and not bridge.checking
        settings.set_update_check_enabled(True)
        monkeypatch.setenv(svc.OPT_OUT_ENV, "1")  # ortam değişkeni de kapatır
        bridge.startupCheck()
        assert calls == []
        run_check(bridge, manual=True)  # elle denetim her zaman çalışır
        assert calls == [1]

    def test_acilis_denetimi_onceki_guncellemenin_artiklarini_temizler(self, qapp, settings, monkeypatch):
        cleaned = []
        monkeypatch.setattr(svc, "cleanup_update_directory", lambda directory=None: cleaned.append(True))
        bridge = make(settings, None)
        bridge.startupCheck()
        assert cleaned == [True]
        assert pump_until(lambda: not bridge.checking)

    def test_ikinci_denetim_ilki_surerken_yok_sayilir(self, qapp, settings):
        calls = []
        bridge = make(settings, None, calls)
        bridge.checkNow()
        bridge.checkNow()
        assert pump_until(lambda: not bridge.checking)
        assert calls == [1]


def make_updating(settings, download, launcher, **kwargs):
    return UpdateBridge(settings, check=lambda: info(), download=download, launcher=launcher, installable=True, **kwargs)


class TestIndirmeVeKurulum:
    def test_indirir_dogrular_kurulumu_baslatir_ve_uygulamadan_cikis_ister(self, qapp, settings, tmp_path):
        launched, quits, states = [], [], []

        def download(update_info, progress):
            for percent in (10, 60, 100):
                progress(percent)
            return tmp_path / "NamazTakip-Setup-99.0.0.exe"

        bridge = make_updating(settings, download, launched.append)
        bridge.quitRequested.connect(lambda: quits.append(True))
        bridge.stateChanged.connect(lambda: states.append(bridge.downloadProgress))
        run_check(bridge, manual=True)
        assert bridge.canInstall is True and bridge.isDownloading is False
        bridge.startUpdate()
        assert bridge.isDownloading is True
        assert pump_until(lambda: quits)
        assert launched == [tmp_path / "NamazTakip-Setup-99.0.0.exe"] and {10, 60, 100} <= set(states)

    def test_basarisiz_indirme_hatayi_gosterir_ne_baslatir_ne_kapatir(self, qapp, settings, tmp_path):
        launched, quits = [], []

        def download(update_info, progress):
            raise UpdateCheckError("İndirilen dosya doğrulanamadı; özet uyuşmuyor.")

        bridge = make_updating(settings, download, launched.append)
        bridge.quitRequested.connect(lambda: quits.append(True))
        run_check(bridge, manual=True)
        bridge.startUpdate()
        assert pump_until(lambda: bridge.errorMessage != "")
        assert bridge.errorMessage == "İndirilen dosya doğrulanamadı; özet uyuşmuyor." and bridge.isDownloading is False
        assert launched == [] and quits == []
        bridge.startUpdate()  # yeniden denenebilir
        assert bridge.isDownloading is True and bridge.errorMessage == ""
        assert pump_until(lambda: bridge.errorMessage != "")

    def test_beklenmeyen_indirme_hatasi_genel_mesaj_verir(self, qapp, settings):
        def download(update_info, progress):
            raise RuntimeError("beklenmedik")

        bridge = make_updating(settings, download, lambda path: None)
        run_check(bridge, manual=True)
        bridge.startUpdate()
        assert pump_until(lambda: bridge.errorMessage != "")
        assert bridge.errorMessage == "Güncelleme indirilemedi."

    def test_baslatici_hatasi_bildirilir_uygulama_acik_kalir(self, qapp, settings, tmp_path):
        quits = []

        def launcher(path):
            raise UpdateCheckError("Kurulum dosyası bulunamadı.")

        bridge = make_updating(settings, lambda i, p: tmp_path / "NamazTakip-Setup-99.0.0.exe", launcher)
        bridge.quitRequested.connect(lambda: quits.append(True))
        run_check(bridge, manual=True)
        bridge.startUpdate()
        assert pump_until(lambda: bridge.errorMessage != "")
        assert bridge.errorMessage == "Kurulum dosyası bulunamadı." and quits == []

    def test_kurulum_dosyasi_yoksa_surum_sayfasi_acilir_indirme_olmaz(self, qapp, settings, monkeypatch):
        opened = []
        monkeypatch.setattr(module.QDesktopServices, "openUrl", staticmethod(lambda url: opened.append(url.toString())))
        bridge = UpdateBridge(
            settings,
            check=lambda: info(download=False),
            download=lambda i, p: pytest.fail("indirilmemeli"),
            launcher=lambda p: pytest.fail("başlatılmamalı"),
            installable=True,
        )
        bridge.startUpdate()
        assert opened == []  # bilgi yokken hiçbir şey açılmaz
        run_check(bridge, manual=True)
        bridge.startUpdate()
        assert opened[-1].endswith("/releases/tag/v99.0.0") and bridge.canInstall is False and bridge.isDownloading is False
        assert bridge.installerLabel == "Sürüm sayfası tarayıcıda açılır."

    def test_paketlenmemis_calismada_kurulum_baslatilmaz_surum_sayfasi_acilir(self, qapp, settings, monkeypatch):
        """`python main.py` ile çalışırken yanlışlıkla kurulum başlatılıp geliştirme oturumu kapatılmasın."""
        opened = []
        monkeypatch.setattr(module.QDesktopServices, "openUrl", staticmethod(lambda url: opened.append(url.toString())))
        bridge = UpdateBridge(
            settings,
            check=lambda: info(),
            download=lambda i, p: pytest.fail("indirilmemeli"),
            launcher=lambda p: pytest.fail("başlatılmamalı"),
            installable=False,
        )
        run_check(bridge, manual=True)
        assert bridge.canInstall is False
        bridge.startUpdate()
        assert len(opened) == 1 and opened[0].endswith("/releases/tag/v99.0.0")

    def test_varsayilan_kurulabilirlik_paketlenmis_calismaya_bagli(self, qapp, settings, monkeypatch):
        monkeypatch.delattr(module.sys, "frozen", raising=False)
        assert UpdateBridge(settings).canInstall is False
        monkeypatch.setattr(module.sys, "frozen", True, raising=False)
        bridge = UpdateBridge(settings, check=lambda: info())
        run_check(bridge, manual=True)
        assert bridge.canInstall is True

    def test_indirme_surerken_ikinci_baslatma_yok_sayilir(self, qapp, settings, tmp_path):
        release_download, started = threading.Event(), []

        def download(update_info, progress):
            started.append(1)
            release_download.wait(10)
            return tmp_path / "NamazTakip-Setup-99.0.0.exe"

        bridge = make_updating(settings, download, lambda path: None)
        run_check(bridge, manual=True)
        bridge.startUpdate()
        bridge.startUpdate()
        pump_until(lambda: started, timeout=3)
        release_download.set()
        assert pump_until(lambda: bridge._worker.isFinished())
        assert started == [1]  # ikinci tık ikinci indirme başlatmadı


def blocked_then(settings, tmp_path, blocked_times, **kwargs):
    """İlk `blocked_times` başlatma engellenir, sonrakiler çalışır."""
    downloaded = tmp_path / "NamazTakip-Setup-99.0.0.exe"
    attempts, revealed, quits = [], [], []

    def launcher(path):
        attempts.append(path)
        if len(attempts) <= blocked_times:
            raise InstallerBlockedError(path)

    bridge = UpdateBridge(
        settings,
        check=lambda: info(),
        download=lambda i, p: downloaded,
        launcher=launcher,
        revealer=revealed.append,
        retry_interval_ms=20,
        installable=True,
        **kwargs,
    )
    bridge.quitRequested.connect(lambda: quits.append(True))
    run_check(bridge, manual=True)
    return bridge, attempts, revealed, quits, downloaded


class TestWindowsEngeli:
    def test_engel_dosyayi_gezginde_gosterir_ve_ne_yapilacagini_soyler(self, qapp, settings, tmp_path):
        bridge, attempts, revealed, quits, downloaded = blocked_then(settings, tmp_path, 999, retry_limit=0)
        bridge.startUpdate()
        assert pump_until(lambda: bridge.errorMessage != "")
        assert revealed == [downloaded] and quits == [] and bridge.isDownloading is False
        assert "Akıllı Uygulama Denetimi" in bridge.errorMessage and "çift tıklayarak" in bridge.errorMessage

    def test_engel_kalkana_dek_otomatik_yeniden_denenir(self, qapp, settings, tmp_path):
        bridge, attempts, revealed, quits, _ = blocked_then(settings, tmp_path, 3, retry_limit=40)
        bridge.startUpdate()
        assert pump_until(lambda: bridge.isWaitingForWindows)
        assert "denetliyor" in bridge.errorMessage and bridge.isDownloading is True  # bekleme sırasında pencere kilitli
        assert pump_until(lambda: quits)
        assert len(attempts) == 4 and revealed == [] and bridge.isWaitingForWindows is False

    def test_engel_hic_kalkmazsa_dosya_elle_kurulum_icin_gosterilir(self, qapp, settings, tmp_path):
        bridge, attempts, revealed, quits, _ = blocked_then(settings, tmp_path, 999, retry_limit=3)
        bridge.startUpdate()
        assert pump_until(lambda: revealed)
        assert len(attempts) == 4 and quits == [] and bridge.isWaitingForWindows is False and bridge.isDownloading is False
        assert "çift tıklayarak" in bridge.errorMessage

    def test_kullanici_beklemeyi_birakip_elle_kurabilir(self, qapp, settings, tmp_path):
        bridge, attempts, revealed, quits, _ = blocked_then(settings, tmp_path, 999, retry_limit=1000)
        bridge.startUpdate()
        assert pump_until(lambda: bridge.isWaitingForWindows)
        bridge.stopWaiting()
        assert bridge.isWaitingForWindows is False and len(revealed) == 1 and quits == []
        count = len(attempts)
        pump_until(lambda: False, timeout=0.3)
        assert len(attempts) == count  # zamanlayıcı durdu, yeniden denenmiyor
