import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// "X NAMAZINI KILDINIZ MI?" işaretleme diyaloğu. Esc veya dışarı tıklama kapatır.
Popup {
    id: root

    property var rowData: ({})

    objectName: "prayerDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 400
    padding: 28
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    function openFor(row) {
        rowData = row
        congregation.checked = row.isCongregation === true
        open()
    }

    // Düğmelerin yaptığı iş (testlerde doğrudan çağrılır)
    function submitPerformed() {
        if (homeBridge.markPerformed(rowData.key, congregation.checked))
            close()
    }

    function submitMissed() {
        if (homeBridge.markMissed(rowData.key))
            close()
    }

    onOpened: performedButton.forceActiveFocus()

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
            horizontalAlignment: Text.AlignHCenter
            text: root.rowData.dialogTitle !== undefined ? root.rowData.dialogTitle : ""
            font.family: Theme.fontFamily
            font.pixelSize: 18
            font.weight: Font.Bold
            font.letterSpacing: 0.6
            color: Theme.text
            Accessible.role: Accessible.Heading
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: strings.dialog.question
            font.family: Theme.fontFamily
            font.pixelSize: 18
            font.weight: Font.Bold
            font.letterSpacing: 0.6
            color: Theme.primary
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: (root.rowData.name !== undefined ? root.rowData.name : "") + "  •  "
                  + (root.rowData.time !== undefined ? root.rowData.time : "")
            font.family: Theme.fontFamily
            font.pixelSize: 13
            color: Theme.textLight
        }

        // Cemaat kutusu
        CheckBox {
            id: congregation
            objectName: "congregationCheck"
            Layout.fillWidth: true
            Layout.topMargin: 6
            text: strings.dialog.congregation
            focusPolicy: Qt.StrongFocus
            font.family: Theme.fontFamily
            font.pixelSize: 15
            font.weight: Font.DemiBold

            indicator: Rectangle {
                x: congregation.leftPadding
                y: (congregation.height - height) / 2
                width: 22
                height: 22
                radius: 6
                color: congregation.checked ? Theme.primary : "transparent"
                border.width: 1.8
                border.color: congregation.checked ? Theme.primary : Theme.withAlpha(Theme.textLight, 0.7)

                AppIcon {
                    anchors.centerIn: parent
                    visible: congregation.checked
                    name: "check"
                    size: 15
                    strokeWidth: 2.6
                    color: Theme.textOnPrimary
                }
                Rectangle {
                    visible: congregation.visualFocus
                    anchors.fill: parent
                    anchors.margins: -3
                    radius: 8
                    color: "transparent"
                    border.width: 2
                    border.color: Theme.secondary
                }
            }
            contentItem: Column {
                leftPadding: 22 + 12 + congregation.leftPadding
                spacing: 2
                Text {
                    text: congregation.text
                    font: congregation.font
                    color: Theme.text
                }
                Text {
                    text: strings.dialog.congregationHint
                    font.family: Theme.fontFamily
                    font.pixelSize: 12
                    color: Theme.textLight
                }
            }
        }

        AppButton {
            id: performedButton
            objectName: "performedButton"
            Layout.fillWidth: true
            Layout.topMargin: 6
            text: strings.dialog.performed
            iconName: "check"
            onClicked: root.submitPerformed()
        }
        AppButton {
            objectName: "missedButton"
            Layout.fillWidth: true
            variant: "outlined"
            danger: true
            text: strings.dialog.missed
            iconName: "close"
            onClicked: root.submitMissed()
        }
        AppButton {
            objectName: "dismissButton"
            Layout.fillWidth: true
            variant: "text"
            text: strings.dialog.dismiss
            onClicked: root.close()
        }
    }
}
