import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Liste biçiminde tek seçimli satır (hesaplama yöntemi gibi).
AbstractButton {
    id: root

    property string title: ""
    property bool selected: false

    implicitHeight: 46
    focusPolicy: Qt.StrongFocus
    hoverEnabled: true
    Accessible.role: Accessible.RadioButton
    Accessible.name: title
    Accessible.checked: selected

    contentItem: RowLayout {
        spacing: 12

        Rectangle {
            Layout.leftMargin: 14
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: 22
            implicitHeight: 22
            radius: 11
            color: "transparent"
            border.width: 2
            border.color: root.selected ? Theme.primary : Theme.withAlpha(Theme.textLight, 0.7)

            Rectangle {
                anchors.centerIn: parent
                width: 10
                height: 10
                radius: 5
                color: Theme.primary
                visible: root.selected
            }
        }
        Text {
            Layout.fillWidth: true
            text: root.title
            font.family: Theme.fontFamily
            font.pixelSize: 15
            font.weight: root.selected ? Font.DemiBold : Font.Normal
            color: Theme.text
        }
    }

    background: Rectangle {
        radius: 12
        color: root.selected ? Theme.withAlpha(Theme.primary, Theme.isDark ? 0.16 : 0.08)
                             : (root.hovered ? Theme.withAlpha(Theme.primary, 0.05) : "transparent")
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
