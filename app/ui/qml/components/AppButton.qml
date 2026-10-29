import QtQuick
import QtQuick.Controls
import "../theme"

// variant: "filled" | "outlined" | "text" | "light". danger=true kırmızı vurgu kullanır.
Button {
    id: root

    property string variant: "filled"
    property bool danger: false
    property string iconName: ""

    readonly property color accentColor: danger ? Theme.danger : Theme.primary
    // "light": koyu sayaç/özet kartı üstünde beyaz düğme (yazı kartın koyu rengi).
    readonly property color foreground: variant === "filled" ? Theme.textOnPrimary
        : (variant === "light" ? Theme.heroStart : accentColor)

    implicitHeight: 44
    implicitWidth: Math.max(96, contentRow.implicitWidth + leftPadding + rightPadding)
    leftPadding: 18
    rightPadding: 18
    focusPolicy: Qt.StrongFocus
    font.family: Theme.fontFamily
    font.pixelSize: 14
    font.weight: Font.DemiBold
    Accessible.name: text

    contentItem: Item {
        implicitWidth: contentRow.implicitWidth
        implicitHeight: contentRow.implicitHeight

        Row {
            id: contentRow
            anchors.centerIn: parent
            spacing: 8

            AppIcon {
                visible: root.iconName !== ""
                name: root.iconName
                size: 18
                color: root.foreground
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: root.text
                font: root.font
                color: root.foreground
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    background: Rectangle {
        radius: Theme.radiusButton
        color: {
            if (root.variant === "light")
                return root.down ? "#E6E6E6" : (root.hovered ? "#F2F2F2" : "#FFFFFF")
            if (root.variant === "filled") {
                var base = root.danger ? Theme.danger : Theme.primary
                return root.down ? Qt.darker(base, 1.15) : (root.hovered ? Qt.lighter(base, 1.08) : base)
            }
            if (root.down) return Theme.withAlpha(root.accentColor, 0.18)
            if (root.hovered) return Theme.withAlpha(root.accentColor, 0.10)
            return "transparent"
        }
        border.width: root.variant === "outlined" ? 1.5 : 0
        border.color: Theme.withAlpha(root.accentColor, 0.55)

        // Klavye odak halkası
        Rectangle {
            visible: root.visualFocus
            anchors.fill: parent
            anchors.margins: -3
            radius: Theme.radiusButton + 3
            color: "transparent"
            border.width: 2
            border.color: Theme.secondary
        }
    }
}
