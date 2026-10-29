from app.version import APP_NAME
from tests.qml_support import close_ui, load_ui


def test_ana_pencere_yuklenir_ve_qml_hatasi_yok(qapp):
    ui = load_ui(qapp)
    try:
        assert ui.root is not None, ui.messages.problems()
        assert ui.root.property("title") == APP_NAME
        assert ui.root.property("minimumWidth") == 900
        assert ui.root.property("minimumHeight") == 600
        assert ui.messages.problems() == []
    finally:
        close_ui(ui)


def test_konum_yokken_de_yuklenir(qapp):
    ui = load_ui(qapp, with_location=False)
    try:
        assert ui.root is not None, ui.messages.problems()
        assert ui.messages.problems() == []
    finally:
        close_ui(ui)
