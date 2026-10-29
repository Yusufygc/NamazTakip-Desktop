import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Günlük takipten düşen kazaların gün kartı (açılır). `group`: QazaBridge.groups öğesi.
Card {
    id: root

    property var group: ({})
    property bool expanded: false

    signal toggled(bool expanded)
    signal compensateRequested(string dateKey, string dateLabel, string prayerKey, string prayerName)

    function toggle() {
        toggled(!expanded)
    }

    objectName: "qazaDayCard_" + (group.dateKey !== undefined ? group.dateKey : "")
    implicitHeight: content.implicitHeight

    ColumnLayout {
        id: content
        width: parent.width
        spacing: 0

        // Başlık: tarih + "N Kaza" rozeti + ok
        AbstractButton {
            id: header
            objectName: "qazaDayHeader_" + (root.group.dateKey !== undefined ? root.group.dateKey : "")
            Layout.fillWidth: true
            implicitHeight: 58
            focusPolicy: Qt.StrongFocus
            hoverEnabled: true
            onClicked: root.toggle()
            Accessible.role: Accessible.Button
            Accessible.name: (root.group.dateLabel !== undefined ? root.group.dateLabel : "") + ", "
                             + strings.qaza.badge.arg(root.group.count !== undefined ? root.group.count : 0)

            background: Rectangle {
                radius: Theme.radiusCard
                color: header.hovered ? Theme.withAlpha(Theme.primary, 0.05) : "transparent"
                Rectangle {
                    visible: header.visualFocus
                    anchors.fill: parent
                    anchors.margins: -2
                    radius: Theme.radiusCard + 2
                    color: "transparent"
                    border.width: 2
                    border.color: Theme.secondary
                }
            }

            contentItem: RowLayout {
                spacing: 12

                Text {
                    Layout.leftMargin: 18
                    text: root.group.dateLabel !== undefined ? root.group.dateLabel : ""
                    font.family: Theme.fontFamily
                    font.pixelSize: 16
                    font.weight: Font.DemiBold
                    color: Theme.text
                }
                Rectangle {
                    implicitWidth: badgeText.implicitWidth + 20
                    implicitHeight: 24
                    radius: 12
                    color: Theme.blend(Theme.primary, 0.06, Theme.card)
                    Text {
                        id: badgeText
                        anchors.centerIn: parent
                        text: strings.qaza.badge.arg(root.group.count !== undefined ? root.group.count : 0)
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.Bold
                        color: Theme.primary
                    }
                }
                Item { Layout.fillWidth: true }
                AppIcon {
                    Layout.rightMargin: 16
                    name: root.expanded ? "chevronDown" : "chevronRight"
                    size: 20
                    color: Theme.textLight
                }
            }
        }

        // Açılınca vakit satırları
        ColumnLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 18
            Layout.rightMargin: 18
            Layout.bottomMargin: 12
            spacing: 0
            visible: root.expanded

            Repeater {
                model: root.group.items !== undefined ? root.group.items : []

                delegate: ColumnLayout {
                    id: itemRow

                    required property var modelData

                    Layout.fillWidth: true
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 1
                        color: Theme.withAlpha(Theme.primary, 0.10)
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.topMargin: 8
                        Layout.bottomMargin: 8
                        spacing: 12

                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: itemRow.modelData.prayerName
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                                color: Theme.text
                            }
                            Text {
                                text: itemRow.modelData.autoDetected ? strings.qaza.autoDetected : strings.qaza.markedMissed
                                font.family: Theme.fontFamily
                                font.pixelSize: 12
                                color: itemRow.modelData.autoDetected ? Theme.textLight : Theme.danger
                            }
                        }
                        Item { Layout.fillWidth: true }
                        AppButton {
                            objectName: "qazaCompensate_" + root.group.dateKey + "_" + itemRow.modelData.prayerKey
                            variant: "outlined"
                            text: strings.qaza.compensate
                            implicitHeight: 38
                            onClicked: root.compensateRequested(
                                root.group.dateKey, root.group.dateLabel,
                                itemRow.modelData.prayerKey, itemRow.modelData.prayerName)
                        }
                    }
                }
            }
        }
    }
}
