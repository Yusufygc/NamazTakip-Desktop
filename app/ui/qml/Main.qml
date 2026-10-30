import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme"
import "components"
import "pages"

ApplicationWindow {
    id: root

    property int pageIndex: 0
    // Sistem tepsisi yoksa pencere kapatılınca uygulama kapanır (aksi halde uygulamaya ulaşılamaz).
    property bool trayAvailable: tray.available
    readonly property bool hideOnClose: settingsBridge.closeToTray && trayAvailable

    objectName: "mainWindow"
    visible: false  // Component.onCompleted'ta, gizli başlatma kararından sonra gösterilir
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

    // Pencereyi öne getirir (tepsi tıklaması, ikinci örnek, bildirim tıklaması).
    function showFromTray() {
        show()
        raise()
        requestActivate()
    }

    // Kapat düğmesi: tepsiye küçült (ayar açık ve tepsi varsa), değilse uygulamadan çık.
    onClosing: (close) => {
        if (root.hideOnClose) {
            close.accepted = false
            root.hide()
            tray.showHintOnce()
        } else {
            shellBridge.requestQuit()
        }
    }

    // İlk açılışta (şehir seçildikten sonra) "Windows açılınca başlasın mı?" sorusu.
    function maybePromptAutostart() {
        if (settingsBridge.needsAutostartPrompt && homeBridge.hasLocation && visible)
            autostartPrompt.open()
    }

    // Uygulama kapalıyken giren vakitler sorusu: pencere görünürken ve işaretlenmemiş vakit varken açılır.
    function maybeShowMissed() {
        if (visible && missedBridge.count > 0 && !missedDialog.opened && !autostartPrompt.opened
                && !settingsBridge.needsAutostartPrompt)
            missedDialog.open()
    }

    // "Yeni sürüm var" penceresi: yalnızca pencere görünürken ve başka bir soru açık değilken açılır; aksi hâlde bekler.
    property bool updatePending: false

    function maybeShowUpdate() {
        if (updatePending && visible && !updateDialog.opened && !missedDialog.opened && !autostartPrompt.opened
                && !settingsBridge.needsAutostartPrompt && missedBridge.count === 0) {
            updatePending = false
            updateDialog.open()
        }
    }

    onVisibleChanged: { maybeShowMissed(); maybeShowUpdate() }

    Connections {
        target: missedBridge
        function onChanged() { root.maybeShowMissed(); root.maybeShowUpdate() }
    }

    Connections {
        target: autostartPrompt
        function onClosed() { root.maybeShowMissed(); root.maybeShowUpdate() }
    }

    Connections {
        target: missedDialog
        function onClosed() { root.maybeShowUpdate() }
    }

    Connections {
        target: updateBridge
        function onPopupRequested() {
            root.updatePending = true
            if (root.visible)
                root.maybeShowUpdate()
            else
                tray.notify(strings.update.notificationTitle, strings.update.notificationBody.arg(updateBridge.latestVersion))
        }
    }

    Connections {
        target: shellBridge
        function onNotificationRequested(title, body) { tray.notify(title, body) }
        function onShowWindowRequested() { root.showFromTray() }
        function onPromptRequested(dateKey, prayerKey) {
            root.showFromTray()
            root.pageIndex = 0
            homeBridge.openDay(dateKey)
            homePage.promptPrayer(prayerKey)
        }
    }

    AppTrayIcon {
        id: tray
        objectName: "appTray"
        mainWindow: root
        onShowRequested: root.showFromTray()
    }

    AutostartPromptDialog { id: autostartPrompt }
    MissedPrayersDialog { id: missedDialog }
    UpdateDialog { id: updateDialog }

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

            HomePage { id: homePage; onCityPickerClosed: root.maybePromptAutostart() }
            QazaPage { objectName: "qazaPage" }
            SettingsPage { objectName: "settingsPage" }
        }
    }

    // Şehir seçilmemişse ilk açılışta seçici kendiliğinden açılır.
    Component.onCompleted: {
        // `--autostart` ile açıldıysa ve tepsi varsa pencere gizli kalır (yalnızca tepside çalışır).
        if (shellBridge.startHidden && trayAvailable) {
            // Gizli başlatmada diyalog açılmaz; bildirime tıklayınca pencere gelir ve diyalog açılır.
            if (missedBridge.count > 0) {
                shellBridge.forgetLastNotification()
                tray.notify(strings.missed.notificationTitle, strings.missed.notificationBody)
            }
            return
        }
        show()
        if (!homeBridge.hasLocation)
            homePage.openCityPicker()
        else
            maybePromptAutostart()
    }
}
