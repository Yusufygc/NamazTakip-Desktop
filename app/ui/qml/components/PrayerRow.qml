import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Zaman çizelgesi bağlantılı vakit satırı. `rowData`: HomeBridge.prayers satırı.
AbstractButton {
    id: root

    property var rowData: ({})
    property bool isFirst: false
    property bool isLast: false

    readonly property string status: rowData.status !== undefined ? rowData.status : ""
    readonly property bool isSunrise: rowData.isSunrise === true
    readonly property bool isNext: rowData.isNext === true
    readonly property bool markable: rowData.markable === true
    readonly property bool done: status === "performed" || status === "compensated"
    readonly property bool missed: status === "missed"

    // Düğüm (zaman çizelgesi noktası) rengi
    readonly property color nodeColor: done ? Theme.primary
        : (missed ? Theme.danger
        : (isNext ? Theme.secondary
        : (isSunrise ? Theme.withAlpha(Theme.secondary, 0.75) : Theme.withAlpha(Theme.textLight, 0.35))))

    readonly property string statusText: {
        if (isSunrise) return strings.home.sunriseTag
        if (status === "performed") return strings.home.performed
        if (status === "compensated") return strings.home.compensated
        if (status === "missed") return strings.home.missed
        return strings.home.pending
    }

    signal activated(var row)

    function activate() {
        if (markable)
            activated(rowData)
    }

    implicitHeight: 66
    focusPolicy: markable ? Qt.StrongFocus : Qt.NoFocus
    hoverEnabled: markable
    onClicked: activate()
    Keys.onReturnPressed: activate()
    Keys.onEnterPressed: activate()

    Accessible.role: markable ? Accessible.Button : Accessible.StaticText
    Accessible.name: strings.home.prayerSemantics.arg(rowData.name).arg(rowData.time).arg(statusText)

    contentItem: RowLayout {
        spacing: 0

        // Sol dikey zaman çizelgesi sütunu
        Item {
            Layout.preferredWidth: 30
            Layout.fillHeight: true

            Rectangle {
                visible: !root.isFirst
                x: parent.width / 2 - 1
                y: 0
                width: 2
                height: parent.height / 2
                color: Theme.withAlpha(Theme.primary, 0.20)
            }
            Rectangle {
                visible: !root.isLast
                x: parent.width / 2 - 1
                y: parent.height / 2
                width: 2
                height: parent.height / 2
                color: Theme.withAlpha(Theme.primary, 0.20)
            }
            Rectangle {
                anchors.centerIn: parent
                width: root.isNext ? 26 : 22
                height: width
                radius: width / 2
                color: (root.done || root.isNext) ? root.nodeColor : Theme.background
                border.width: root.isNext ? 2.4 : 1.8
                border.color: root.nodeColor

                AppIcon {
                    anchors.centerIn: parent
                    visible: name !== ""
                    name: root.done ? "check" : (root.missed ? "close" : (root.isNext ? "hourglass" : (root.isSunrise ? "sun" : "")))
                    size: root.isNext ? 14 : 12
                    strokeWidth: 2.2
                    color: (root.done || root.isNext) ? "#FFFFFF" : root.nodeColor
                }
            }
        }

        // Kart
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 3
            Layout.bottomMargin: 3
            radius: 16

            color: {
                if (root.isNext) return Theme.blend(Theme.secondary, Theme.isDark ? 0.14 : 0.12, Theme.card)
                if (root.done) return Theme.blend(Theme.primary, Theme.isDark ? 0.18 : 0.08, Theme.card)
                if (root.missed) return Theme.blend(Theme.danger, Theme.isDark ? 0.12 : 0.07, Theme.card)
                if (root.isSunrise) return Theme.withAlpha(Theme.card, Theme.isDark ? 0.65 : 0.80)
                return root.hovered ? Theme.blend(Theme.primary, 0.05, Theme.card) : Theme.card
            }
            border.width: root.isNext ? 1.8 : 1
            border.color: root.isNext ? Theme.secondary
                : (root.done ? Theme.withAlpha(Theme.primary, 0.45)
                : (root.missed ? Theme.withAlpha(Theme.danger, 0.45)
                : Theme.withAlpha(Theme.primary, Theme.isDark ? 0.16 : 0.10)))

            Rectangle {
                visible: root.visualFocus
                anchors.fill: parent
                anchors.margins: -2
                radius: 18
                color: "transparent"
                border.width: 2
                border.color: Theme.secondary
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 18
                spacing: 12

                ColumnLayout {
                    spacing: 2
                    Text {
                        text: root.rowData.name !== undefined ? root.rowData.name : ""
                        font.family: Theme.fontFamily
                        font.pixelSize: 17
                        font.weight: Font.DemiBold
                        color: Theme.text
                    }
                    Row {
                        spacing: 8
                        Text {
                            text: root.statusText
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            color: root.missed ? Theme.danger : (root.done ? Theme.primary : Theme.textLight)
                        }
                        Text {
                            visible: root.rowData.isCongregation === true
                            text: "•  " + strings.home.congregationBadge
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                            color: Theme.primary
                        }
                        Text {
                            visible: root.isNext
                            text: "•  " + strings.home.nextTag
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                            color: Theme.secondaryText
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.rowData.time !== undefined ? root.rowData.time : ""
                    font.family: Theme.monoFamily
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    color: Theme.text
                }
            }
        }
    }

    background: Item {}
}
