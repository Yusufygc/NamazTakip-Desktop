import QtQuick
import QtQuick.Controls
import "../theme"

// Yalnızca ikonlu düğme. `label` erişilebilirlik adıdır (ekranda görünmez).
AbstractButton {
    id: root

    property string iconName: ""
    property string label: ""
    property color iconColor: Theme.primary

    implicitWidth: 40
    implicitHeight: 40
    focusPolicy: Qt.StrongFocus
    hoverEnabled: true
    Accessible.name: label
    Accessible.role: Accessible.Button

    contentItem: Item {
        AppIcon {
            anchors.centerIn: parent
            name: root.iconName
            size: 22
            color: root.enabled ? root.iconColor : Theme.withAlpha(Theme.textLight, 0.45)
        }
    }

    background: Rectangle {
        radius: 12
        color: root.down ? Theme.withAlpha(Theme.primary, 0.18)
                         : (root.hovered && root.enabled ? Theme.withAlpha(Theme.primary, 0.10) : "transparent")
        Rectangle {
            visible: root.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: 14
            color: "transparent"
            border.width: 2
            border.color: Theme.secondary
        }
    }
}
