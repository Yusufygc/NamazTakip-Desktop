"""Tek örnek: ilk örnek kilidi alır, ikinci süreç "göster" isteği gönderir.

İkinci örnek gerçekte ayrı bir süreçtir. Aynı süreçte `QLocalSocket` yazması sunucunun olay döngüsünü bekler
(Windows adlandırılmış boru), bu yüzden istemci tarafı gerçek bir alt süreçle sınanır.
"""

import subprocess
import sys
import textwrap
import time
import uuid
from pathlib import Path

import pytest

from app.services.single_instance import SingleInstance

ROOT = Path(__file__).resolve().parent.parent

SECOND_INSTANCE = textwrap.dedent(
    """
    import os, sys
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    sys.path.insert(0, sys.argv[3])
    from pathlib import Path
    from PySide6.QtCore import QCoreApplication
    from app.services.single_instance import SingleInstance
    app = QCoreApplication([])
    instance = SingleInstance(sys.argv[1], Path(sys.argv[2]))
    if instance.try_acquire():
        sys.exit(3)  # ilk örnek olmamalıydı
    sys.exit(0 if instance.notify_existing() else 1)
    """
)

RAW_MESSAGE = textwrap.dedent(
    """
    import os, sys
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtCore import QCoreApplication
    from PySide6.QtNetwork import QLocalSocket
    app = QCoreApplication([])
    socket = QLocalSocket()
    socket.connectToServer(sys.argv[1])
    if not socket.waitForConnected(2000):
        sys.exit(1)
    socket.write(sys.argv[2].encode())
    socket.flush()
    socket.waitForBytesWritten(2000)
    socket.disconnectFromServer()
    sys.exit(0)
    """
)


def run_child(qapp, code, *args, timeout=20.0) -> int:
    """Alt süreci başlatır; bu sürecin olay döngüsünü (sunucu) çalıştırarak bitmesini bekler."""
    process = subprocess.Popen([sys.executable, "-c", code, *args], cwd=str(ROOT))
    end = time.time() + timeout
    while process.poll() is None and time.time() < end:
        qapp.processEvents()
        time.sleep(0.01)
    if process.poll() is None:
        process.kill()
        pytest.fail("alt süreç zamanında bitmedi")
    return process.returncode


def wait_until(qapp, condition, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        qapp.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


@pytest.fixture
def name():
    return f"NamazTakipTest-{uuid.uuid4().hex}"


@pytest.fixture
def instances(qapp, name, tmp_path):
    created = []

    def make():
        instance = SingleInstance(name, lock_dir=tmp_path)
        created.append(instance)
        return instance

    yield make
    for instance in created:
        instance.release()


def test_ilk_ornek_kilidi_alir_ikinci_alamaz(qapp, instances):
    first, second = instances(), instances()
    assert first.try_acquire() is True
    assert second.try_acquire() is False


def test_ikinci_surec_gosterme_istegi_gonderir(qapp, instances, name, tmp_path):
    first = instances()
    assert first.try_acquire() is True
    received = []
    first.showRequested.connect(lambda: received.append(1))
    code = run_child(qapp, SECOND_INSTANCE, name, str(tmp_path), str(ROOT))
    assert code == 0, f"ikinci süreç çıkış kodu {code} (3: kilidi alabildi, 1: bildirim iletilemedi)"
    assert wait_until(qapp, lambda: len(received) == 1), "göster isteği ilk örneğe ulaşmadı"


def test_birden_fazla_istek_ayri_ayri_ulasir(qapp, instances, name, tmp_path):
    first = instances()
    assert first.try_acquire() is True
    received = []
    first.showRequested.connect(lambda: received.append(1))
    for _ in range(3):
        assert run_child(qapp, SECOND_INSTANCE, name, str(tmp_path), str(ROOT)) == 0
    assert wait_until(qapp, lambda: len(received) == 3)


def test_sunucu_yokken_bildirim_basarisiz_olur(qapp, instances):
    assert instances().notify_existing(timeout_ms=200) is False


def test_birakinca_yeni_ornek_kilidi_alir(qapp, instances):
    first, second = instances(), instances()
    assert first.try_acquire() is True
    first.release()
    assert second.try_acquire() is True


def test_yalnizca_show_mesaji_pencere_acar(qapp, instances, name):
    first = instances()
    assert first.try_acquire() is True
    received = []
    first.showRequested.connect(lambda: received.append(1))
    assert run_child(qapp, RAW_MESSAGE, name, "baska-mesaj") == 0
    wait_until(qapp, lambda: False, timeout=0.3)
    assert received == []
    assert run_child(qapp, RAW_MESSAGE, name, "show") == 0
    assert wait_until(qapp, lambda: len(received) == 1)
