import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Soldaki gezinme çubuğu (NavigationRail). Sayfa değiştirme isteği pageRequested ile bildirilir.
Rectangle {
    id: root

    property int currentIndex: 0
    signal pageRequested(int index)

    readonly property var items: [
        { icon: "clock", label: strings.nav.home },
        { icon: "list", label: strings.nav.qaza },
        { icon: "tune", label: strings.nav.settings }
    ]

    objectName: "sidebar"
    width: 88
    color: Theme.card

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: Theme.withAlpha(Theme.primary, 0.12)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: 20
        anchors.bottomMargin: 14
        spacing: 6

        AppIcon {
            Layout.alignment: Qt.AlignHCenter
            name: "star8"
            size: 34
            strokeWidth: 1.6
            color: Theme.secondary
        }

        Item { Layout.preferredHeight: 14 }

        Repeater {
            model: root.items

            delegate: AbstractButton {
                id: navItem

                required property int index
                required property var modelData
                readonly property bool selected: index === root.currentIndex

                objectName: "navItem" + index
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 72
                Layout.preferredHeight: 62
                focusPolicy: Qt.StrongFocus
                hoverEnabled: true
                Accessible.name: modelData.label
                Accessible.role: Accessible.PageTab
                onClicked: root.pageRequested(index)

                background: Rectangle {
                    radius: 16
                    color: navItem.selected ? Theme.withAlpha(Theme.primary, Theme.isDark ? 0.22 : 0.12)
                                            : (navItem.hovered ? Theme.withAlpha(Theme.primary, 0.07) : "transparent")
                    Rectangle {
                        visible: navItem.visualFocus
                        anchors.fill: parent
                        anchors.margins: -2
                        radius: 18
                        color: "transparent"
                        border.width: 2
                        border.color: Theme.secondary
                    }
                }

                contentItem: Column {
                    spacing: 4
                    anchors.centerIn: parent

                    AppIcon {
                        anchors.horizontalCenter: parent.horizontalCenter
                        name: navItem.modelData.icon
                        size: 24
                        color: navItem.selected ? Theme.primary : Theme.textLight
                    }
                    Text {
                        anchors.horizontalCenter: parent.horizontalCenter
                        text: navItem.modelData.label
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        font.weight: navItem.selected ? Font.Bold : Font.Medium
                        color: navItem.selected ? Theme.text : Theme.textLight
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: strings.common.versionLabel
            font.family: Theme.fontFamily
            font.pixelSize: 10
            color: Theme.textLight
        }
    }
}
