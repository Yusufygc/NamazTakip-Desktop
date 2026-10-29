import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme"
import "components"
import "pages"

ApplicationWindow {
    id: root

    property int pageIndex: 0

    objectName: "mainWindow"
    visible: true
    width: 1100
    height: 760
    minimumWidth: 900
    minimumHeight: 600
    title: Qt.application.name
    color: Theme.background
    font.family: Theme.fontFamily

    // Seçili tema anahtarı ayarlardan gelir.
    Binding {
        target: Theme
        property: "themeKey"
        value: settingsBridge.themeKey
    }

    Shortcut { sequence: "Ctrl+1"; onActivated: root.pageIndex = 0 }
    Shortcut { sequence: "Ctrl+2"; onActivated: root.pageIndex = 1 }
    Shortcut { sequence: "Ctrl+3"; onActivated: root.pageIndex = 2 }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        SideBar {
            Layout.fillHeight: true
            currentIndex: root.pageIndex
            onPageRequested: (index) => root.pageIndex = index
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.pageIndex

            HomePage { id: homePage }
            QazaPage { objectName: "qazaPage" }
            SettingsPage { objectName: "settingsPage" }
        }
    }

    // Şehir seçilmemişse ilk açılışta seçici kendiliğinden açılır.
    Component.onCompleted: {
        if (!homeBridge.hasLocation)
            homePage.openCityPicker()
    }
}
