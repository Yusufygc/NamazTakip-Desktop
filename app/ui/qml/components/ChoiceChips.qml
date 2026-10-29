import QtQuick
import QtQuick.Controls
import "../theme"

// Tek seçimli düğme grubu (radyo davranışı). `choices`: [{value, label}]; seçim `chosen(value)` ile bildirilir.
Flow {
    id: root

    property var choices: []
    property var current: null
    property bool chipsEnabled: true

    signal chosen(var value)

    spacing: 8

    Repeater {
        model: root.choices

        delegate: AbstractButton {
            id: chip

            required property var modelData
            readonly property bool selected: modelData.value === root.current

            objectName: root.objectName + "_" + modelData.value
            enabled: root.chipsEnabled
            implicitWidth: Math.max(56, label.implicitWidth + 28)
            implicitHeight: 38
            focusPolicy: Qt.StrongFocus
            hoverEnabled: true
            onClicked: root.chosen(modelData.value)
            Accessible.role: Accessible.RadioButton
            Accessible.name: modelData.label
            Accessible.checked: selected

            contentItem: Text {
                id: label
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                text: chip.modelData.label
                font.family: Theme.fontFamily
                font.pixelSize: 14
                font.weight: chip.selected ? Font.Bold : Font.Medium
                color: chip.selected ? Theme.textOnPrimary : Theme.text
                opacity: chip.enabled ? 1 : 0.5
            }

            background: Rectangle {
                radius: 12
                color: chip.selected ? Theme.primary
                       : (chip.hovered && chip.enabled ? Theme.withAlpha(Theme.primary, 0.12)
                                                       : Theme.blend(Theme.primary, 0.06, Theme.card))
                border.width: 1
                border.color: chip.selected ? Theme.primary : Theme.withAlpha(Theme.primary, 0.22)
                opacity: chip.enabled ? 1 : 0.55

                Rectangle {
                    visible: chip.visualFocus
                    anchors.fill: parent
                    anchors.margins: -3
                    radius: 15
                    color: "transparent"
                    border.width: 2
                    border.color: Theme.secondary
                }
            }
        }
    }
}
