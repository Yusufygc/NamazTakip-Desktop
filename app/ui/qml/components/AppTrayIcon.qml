import QtQuick
import Qt.labs.platform as Labs

// Sistem tepsisi simgesi: ipucu, menü ve bildirim. Pencere davranışı Main.qml'dedir.
Labs.SystemTrayIcon {
    id: root

    property var mainWindow: null
    // Son gösterilen bildirimin başlığı (testlerde ve hata ayıklamada görünür kılar).
    property string lastMessageTitle: ""
    // İlk kapatma bilgisinin kaç kez gösterildiği (yalnızca bir kez olmalı).
    property int hintCount: 0

    readonly property bool windowVisible: mainWindow !== null && mainWindow.visible

    signal showRequested()

    // Bildirim göster (Windows toast); tepsi yoksa yalnızca kaydedilir.
    function notify(title, body) {
        lastMessageTitle = title
        if (available)
            showMessage(title, body, Labs.SystemTrayIcon.NoIcon, 10000)
    }

    // İlk kapatmada bir kez "tepside çalışıyor" bilgisi.
    function showHintOnce() {
        if (settingsBridge.trayHintShown)
            return
        hintCount += 1
        notify(strings.tray.hintTitle, strings.tray.hintBody)
        settingsBridge.markTrayHintShown()
    }

    visible: true
    icon.source: shellBridge.trayIconUrl
    tooltip: homeBridge.nextPrayerName === ""
        ? strings.tray.tooltipIdle
        : strings.tray.tooltip.arg(homeBridge.nextPrayerName).arg(homeBridge.nextPrayerTime)

    menu: Labs.Menu {
        Labs.MenuItem {
            text: root.windowVisible ? strings.tray.hide : strings.tray.show
            onTriggered: {
                if (root.windowVisible)
                    root.mainWindow.hide()
                else
                    root.showRequested()
            }
        }
        Labs.MenuItem {
            enabled: false
            text: homeBridge.nextPrayerName === ""
                ? strings.tray.tooltipIdle
                : strings.tray.nextPrayer.arg(homeBridge.nextPrayerName).arg(homeBridge.nextPrayerTime)
        }
        Labs.MenuItem {
            text: settingsBridge.notificationsEnabled ? strings.tray.notificationsOn : strings.tray.notificationsOff
            onTriggered: settingsBridge.setNotificationsEnabled(!settingsBridge.notificationsEnabled)
        }
        Labs.MenuSeparator {}
        Labs.MenuItem {
            text: strings.tray.quit
            onTriggered: shellBridge.requestQuit()
        }
    }

    onActivated: (reason) => {
        if (reason === Labs.SystemTrayIcon.Trigger || reason === Labs.SystemTrayIcon.DoubleClick)
            root.showRequested()
    }

    // Bildirime tıklama: pencere öne gelir, o vaktin işaretleme diyaloğu açılır.
    onMessageClicked: {
        root.showRequested()
        shellBridge.activateLastNotification()
    }
}
