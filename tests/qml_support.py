"""QML arayüz testleri için yardımcılar: ekransız yükleme, Qt mesajlarını toplama, JS çalıştırma."""

import re
from types import SimpleNamespace

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QtMsgType, qInstallMessageHandler
from PySide6.QtQml import QQmlExpression
from PySide6.QtQuick import QQuickWindow
from shiboken6 import getCppPointer, wrapInstance

from app.container import AppContainer
from app.core.database import AppDatabase
from app.services.autostart_service import AutostartService
from tests.support import FAKE_EXE, ISTANBUL, FakeClock, FakeRegistry, at

_PROBLEM_TYPES = (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg)
# Font ve platform uyarıları arayüz hatası değildir; QML/bağlama hataları böyle görünür.
_QML_ERROR = re.compile(
    r"ReferenceError|TypeError|Unable to assign|is not a type|is not installed|Binding loop|"
    r"Cannot read property|Cannot assign|Invalid property|Non-existent attached|depends on non-NOTIFYable"
)


class QmlMessages:
    """Qt günlük iletilerini toplar (qInstallMessageHandler)."""

    def __init__(self):
        self.items: list[tuple[QtMsgType, str, str]] = []

    def __call__(self, mode, context, message):
        self.items.append((mode, context.file or "", message))

    def problems(self) -> list[str]:
        return [
            f"{file}: {message}"
            for mode, file, message in self.items
            if mode in _PROBLEM_TYPES and (file.endswith(".qml") or _QML_ERROR.search(message))
        ]


def load_ui(
    qapp, with_location: bool = True, now=None, installed=None, start_hidden: bool = False, last_active=None
) -> SimpleNamespace:
    """Gerçek Main.qml'i bellek içi veritabanı ve sahte saatle yükler.

    `installed` verilirse uygulama o anda ilk kez açılmış gibi kurulur (takip başlangıcı o gündür), sonra
    saat `now`a alınır; böylece geçmiş günler kaza listesine düşer. `last_active` verilirse uygulama o anda
    kapanmış gibi kurulur ve açılış sorusu için kaçırılan vakitler yüklenir.
    """
    import main  # kök dizindeki main.py

    messages = QmlMessages()
    qInstallMessageHandler(messages)
    now = now or at(2026, 10, 26, 12)
    clock = FakeClock(installed or now)
    registry = FakeRegistry()  # gerçek Run anahtarına dokunulmaz
    autostart = AutostartService(registry, lambda: FAKE_EXE)
    container = AppContainer(AppDatabase.open_in_memory(), now=clock, start_hidden=start_hidden, autostart=autostart)
    clock.set(now)
    if with_location:
        container.settings_service.use_manual_location(ISTANBUL)
        container.home_bridge.refresh()
        container.qaza_bridge.refresh()
    if last_active is not None:
        container.settings_service.set_last_active_at(last_active)
        container.missed_bridge.load()
    engine = main.build_engine(container)
    qapp.processEvents()
    roots = engine.rootObjects()
    return SimpleNamespace(
        qapp=qapp,
        messages=messages,
        clock=clock,
        registry=registry,
        container=container,
        engine=engine,
        root=roots[0] if roots else None,
    )


def close_ui(ui) -> None:
    ui.engine.deleteLater()
    # `processEvents` ertelenmiş silmeleri işlemez; motor sonraki testin sırasında çöp toplayıcıyla yıkılıp
    # o testin Qt mesajlarına karışmasın diye silmeyi burada tamamla.
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    ui.qapp.processEvents()
    ui.container.shutdown()
    qInstallMessageHandler(None)


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def find(ui, object_name: str) -> QObject:
    """Nesneyi önce QObject ağacında, bulunamazsa görsel (Item) ağacında arar.

    Repeater temsilcileri ve ListView öğeleri QObject ağacında görünmeyebilir; görsel ağaçta bulunur.
    """
    item = ui.root.findChild(QObject, object_name)
    if item is None:
        window = wrapInstance(getCppPointer(ui.root)[0], QQuickWindow)  # rootObjects() QWindow olarak sarar
        content = window.contentItem()
        item = next((node for node in _walk(content) if node.objectName() == object_name), None)
    assert item is not None, f"QML nesnesi bulunamadı: {object_name}"
    return item


def js(ui, scope: QObject, code: str):
    """`scope` nesnesinin bağlamında JS ifadesi çalıştırır (fonksiyon çağırma, özellik okuma)."""
    expression = QQmlExpression(ui.engine.contextForObject(scope), scope, code)
    value = expression.evaluate()
    assert not expression.hasError(), expression.error().toString()
    ui.qapp.processEvents()
    return value
