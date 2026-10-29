import QtQuick
import QtQuick.Controls
import "../theme"

// Başlık + açıklama + anahtar. `checked` değişimini `toggled` sinyali bildirir (Switch'ten gelir).
Switch {
    id: root

    property string title: ""
    property string subtitle: ""

    text: title
    implicitHeight: Math.max(64, textColumn.implicitHeight + 24)
    leftPadding: 14
    rightPadding: 14 + 48 + 14
    focusPolicy: Qt.StrongFocus
    hoverEnabled: true
    Accessible.name: title
    Accessible.description: subtitle

    indicator: Rectangle {
        x: root.width - width - 14
        y: (root.height - height) / 2
        width: 48
        height: 28
        radius: 14
        color: root.checked ? Theme.primary : Theme.withAlpha(Theme.textLight, 0.38)
        opacity: root.enabled ? 1 : 0.5

        Rectangle {
            x: root.checked ? parent.width - width - 3 : 3
            y: 3
            width: 22
            height: 22
            radius: 11
            color: "#FFFFFF"
        }
        Rectangle {
            visible: root.visualFocus
            anchors.fill: parent
            anchors.margins: -3
            radius: 17
            color: "transparent"
            border.width: 2
            border.color: Theme.secondary
        }
    }

    contentItem: Column {
        id: textColumn
        spacing: 2
        opacity: root.enabled ? 1 : 0.55

        Text {
            width: parent.width
            text: root.title
            wrapMode: Text.WordWrap
            font.family: Theme.fontFamily
            font.pixelSize: 16
            font.weight: Font.DemiBold
            color: Theme.text
        }
        Text {
            width: parent.width
            visible: root.subtitle !== ""
            text: root.subtitle
            wrapMode: Text.WordWrap
            font.family: Theme.fontFamily
            font.pixelSize: 12
            color: Theme.textLight
        }
    }

    background: Rectangle {
        radius: Theme.radiusCard - 4
        color: root.hovered && root.enabled ? Theme.withAlpha(Theme.primary, 0.05) : "transparent"
    }
}
