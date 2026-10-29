import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Açılışta "uygulama kapalıyken giren bu vakitleri kıldınız mı?" sorusu. Liste `missedBridge.items`'tan gelir;
// her cevap hemen yazılır. "Sonra" (veya Esc) kalanları sormaz: işaretlenmezse zamanla kaza olurlar.
Popup {
    id: root

    objectName: "missedPrayersDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 500
    padding: 28
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    // "Sonra" düğmesinin işi (testlerde doğrudan çağrılır).
    function later() {
        missedBridge.dismiss()
        close()
    }

    // Esc veya başka yolla kapanırsa kalanlar sorulmaz.
    onClosed: missedBridge.dismiss()

    // Hepsi cevaplanınca kendiliğinden kapanır.
    Connections {
        target: missedBridge
        function onChanged() {
            if (missedBridge.count === 0 && root.opened)
                root.close()
        }
    }

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
            text: strings.missed.title
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
            text: strings.missed.body
            font.family: Theme.fontFamily
            font.pixelSize: 14
            color: Theme.textLight
        }

        ListView {
            id: list
            objectName: "missedList"
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(contentHeight, 300)
            Layout.topMargin: 4
            clip: true
            spacing: 8
            model: missedBridge.items
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                id: row

                required property var modelData
                readonly property string suffix: modelData.dayKey + "_" + modelData.prayerKey

                objectName: "missedRow_" + suffix
                width: ListView.view.width
                implicitHeight: 64
                radius: 16
                color: Theme.blend(Theme.primary, 0.06, Theme.card)
                border.width: 1
                border.color: Theme.withAlpha(Theme.primary, 0.14)
                Accessible.role: Accessible.Grouping
                Accessible.name: strings.missed.rowSemantics.arg(modelData.name).arg(modelData.dateLabel)

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 12
                    spacing: 8

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: row.modelData.name
                            font.family: Theme.fontFamily
                            font.pixelSize: 16
                            font.weight: Font.Bold
                            color: Theme.text
                        }
                        Text {
                            text: row.modelData.dateLabel + "  •  " + row.modelData.timeLabel
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            color: Theme.secondaryText
                        }
                    }
                    AppButton {
                        objectName: "missedPerformed_" + row.suffix
                        implicitHeight: 38
                        leftPadding: 14
                        rightPadding: 14
                        text: strings.missed.performed
                        onClicked: missedBridge.answer(row.modelData.dayKey, row.modelData.prayerKey, true)
                    }
                    AppButton {
                        objectName: "missedMissed_" + row.suffix
                        implicitHeight: 38
                        leftPadding: 14
                        rightPadding: 14
                        variant: "outlined"
                        text: strings.missed.missed
                        onClicked: missedBridge.answer(row.modelData.dayKey, row.modelData.prayerKey, false)
                    }
                }
            }
        }

        AppButton {
            objectName: "missedLater"
            Layout.fillWidth: true
            Layout.topMargin: 4
            variant: "text"
            text: strings.missed.later
            onClicked: root.later()
        }
    }
}
