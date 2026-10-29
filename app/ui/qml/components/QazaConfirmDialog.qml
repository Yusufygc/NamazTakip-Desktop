import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// "<tarih> tarihli <vakit> namazını kaza ettiniz mi?" onayı.
Popup {
    id: root

    property string dateKey: ""
    property string dateLabel: ""
    property string prayerKey: ""
    property string prayerName: ""

    objectName: "qazaConfirmDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 400
    padding: 28
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    function openFor(newDateKey, newDateLabel, newPrayerKey, newPrayerName) {
        dateKey = newDateKey
        dateLabel = newDateLabel
        prayerKey = newPrayerKey
        prayerName = newPrayerName
        open()
    }

    // "Evet, Kıldım" düğmesinin işi (testlerde doğrudan çağrılır)
    function confirm() {
        if (qazaBridge.compensate(dateKey, prayerKey))
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
            Layout.alignment: Qt.AlignHCenter
            text: strings.qaza.confirmTitle
            font.family: Theme.fontFamily
            font.pixelSize: 20
            font.weight: Font.Bold
            color: Theme.text
            Accessible.role: Accessible.Heading
        }
        Text {
            objectName: "qazaConfirmBody"
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
            text: strings.qaza.confirmBody.arg(root.dateLabel).arg(root.prayerName)
            font.family: Theme.fontFamily
            font.pixelSize: 15
            color: Theme.textLight
        }
        AppButton {
            id: yesButton
            objectName: "qazaConfirmYes"
            Layout.fillWidth: true
            Layout.topMargin: 6
            text: strings.qaza.confirmYes
            iconName: "check"
            onClicked: root.confirm()
        }
        AppButton {
            objectName: "qazaConfirmCancel"
            Layout.fillWidth: true
            variant: "text"
            text: strings.common.cancel
            onClicked: root.close()
        }
    }
}
