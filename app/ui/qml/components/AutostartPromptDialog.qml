import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// İlk açılışta "Windows açılınca başlasın mı?" sorusu. Cevap (evet/hayır) ayara yazılır, bir daha sorulmaz.
Popup {
    id: root

    objectName: "autostartPromptDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 420
    padding: 28
    modal: true
    focus: true
    // Dışarı tıklamak veya Esc cevap sayılmaz; soru bir sonraki açılışta yeniden sorulur.
    closePolicy: Popup.CloseOnEscape

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    function answer(enabled) {
        settingsBridge.setAutostart(enabled)
        close()
    }

    onOpened: yesButton.forceActiveFocus()

    background: Rectangle {
        radius: 24
        color: Theme.card
        border.width: 1
        border.color: Theme.withAlpha(Theme.primary, 0.18)
    }

    contentItem: ColumnLayout {
        spacing: 14

        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: strings.autostart.title
            font.family: Theme.fontFamily
            font.pixelSize: 20
            font.weight: Font.Bold
            color: Theme.text
            Accessible.role: Accessible.Heading
        }
        Text {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: strings.autostart.body
            font.family: Theme.fontFamily
            font.pixelSize: 14
            color: Theme.textLight
        }
        AppButton {
            id: yesButton
            objectName: "autostartPromptYes"
            Layout.fillWidth: true
            Layout.topMargin: 6
            text: strings.autostart.yes
            iconName: "check"
            onClicked: root.answer(true)
        }
        AppButton {
            objectName: "autostartPromptNo"
            Layout.fillWidth: true
            variant: "outlined"
            text: strings.autostart.no
            onClicked: root.answer(false)
        }
    }
}
