import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"

// Kaza ekranı: özet, geçmiş yıllar borcu, günlük takipten düşen kazalar.
Item {
    id: page

    readonly property var summary: qazaBridge.summary
    readonly property bool hasEstimate: summary.estimatedDays !== undefined && summary.estimatedDays >= 0
    // Gün kartlarının açık/kapalı durumu (yenilemede korunur). Seçilmemişse ilk gün açıktır.
    property var expandedState: ({})

    function isExpanded(dateKey, index) {
        var explicit = expandedState[dateKey]
        return explicit === undefined ? index === 0 : explicit
    }

    function setExpanded(dateKey, value) {
        var next = Object.assign({}, expandedState)
        next[dateKey] = value
        expandedState = next
    }

    ScrollView {
        id: scroll
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        Item {
            width: scroll.availableWidth
            implicitHeight: column.implicitHeight + 48

            ColumnLayout {
                id: column
                y: 24
                width: Math.min(parent.width - 48, 880)
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 18

                // Boş durum
                Card {
                    objectName: "qazaEmptyCard"
                    Layout.fillWidth: true
                    implicitHeight: 230
                    visible: qazaBridge.isEmpty

                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 10
                        AppIcon {
                            Layout.alignment: Qt.AlignHCenter
                            name: "mihrab"
                            size: 56
                            strokeWidth: 1.4
                            color: Theme.secondary
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: strings.qaza.emptyTitle
                            font.family: Theme.fontFamily
                            font.pixelSize: 20
                            font.weight: Font.Bold
                            color: Theme.text
                        }
                        Text {
                            Layout.alignment: Qt.AlignHCenter
                            text: strings.qaza.emptySubtitle
                            font.family: Theme.fontFamily
                            font.pixelSize: 14
                            color: Theme.textLight
                        }
                        AppButton {
                            objectName: "qazaEmptyPlannerButton"
                            Layout.alignment: Qt.AlignHCenter
                            Layout.topMargin: 8
                            text: strings.qaza.plannerButton
                            onClicked: plannerDialog.openPlanner()
                        }
                    }
                }

                // Özet kartı (mihrap motifli zemin)
                Rectangle {
                    id: overview
                    objectName: "qazaOverviewCard"
                    Layout.fillWidth: true
                    implicitHeight: overviewContent.implicitHeight + 48
                    visible: !qazaBridge.isEmpty
                    radius: 24
                    clip: true
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0.0; color: Theme.heroStart }
                        GradientStop { position: 1.0; color: Theme.heroEnd }
                    }

                    AppIcon {
                        x: parent.width - width * 0.9
                        y: parent.height - height * 0.82
                        name: "mihrab"
                        size: 190
                        strokeWidth: 1
                        color: Theme.withAlpha(Theme.secondary, 0.30)
                    }
                    AppIcon {
                        x: parent.width - width * 1.35
                        y: parent.height - height * 0.7
                        name: "mihrab"
                        size: 120
                        strokeWidth: 1
                        color: Theme.withAlpha(Theme.secondary, 0.20)
                    }

                    ColumnLayout {
                        id: overviewContent
                        anchors.fill: parent
                        anchors.margins: 24
                        spacing: 14

                        Text {
                            text: strings.qaza.overviewTitle
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            font.weight: Font.Bold
                            font.letterSpacing: 1.4
                            color: Theme.heroAccent
                        }

                        RowLayout {
                            spacing: 48

                            ColumnLayout {
                                spacing: 2
                                Text {
                                    text: strings.qaza.totalPrayersLabel
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 13
                                    color: Theme.heroAccent
                                }
                                Text {
                                    objectName: "qazaTotalText"
                                    text: page.summary.grandTotal !== undefined ? page.summary.grandTotal : 0
                                    font.family: Theme.monoFamily
                                    font.pixelSize: 44
                                    font.weight: Font.Bold
                                    color: Theme.textOnHero
                                }
                            }
                            ColumnLayout {
                                spacing: 2
                                Text {
                                    text: strings.qaza.dailyTargetLabel
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 13
                                    color: Theme.heroAccent
                                }
                                Text {
                                    objectName: "qazaTargetText"
                                    text: strings.qaza.dailyTargetValue.arg(
                                              page.summary.dailyTarget !== undefined ? page.summary.dailyTarget : 0)
                                    font.family: Theme.fontFamily
                                    font.pixelSize: 24
                                    font.weight: Font.Bold
                                    color: Theme.textOnHero
                                    Layout.topMargin: 10
                                }
                            }
                        }

                        Text {
                            objectName: "qazaEstimateText"
                            visible: page.hasEstimate
                            text: strings.qaza.estimatedFinish.arg(page.summary.estimatedDateLabel).arg(page.summary.estimatedDays)
                            font.family: Theme.fontFamily
                            font.pixelSize: 14
                            color: Theme.withAlpha(Theme.textOnHero, 0.92)
                        }

                        AppButton {
                            objectName: "qazaPlannerButton"
                            variant: "light"
                            text: strings.qaza.plannerButton
                            onClicked: plannerDialog.openPlanner()
                        }
                    }
                }

                // Geçmiş yıllar kaza borcu
                Text {
                    visible: page.summary.backlogTotal > 0
                    text: strings.qaza.backlogSectionTitle
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                    color: Theme.textLight
                }
                Card {
                    objectName: "qazaBacklogCard"
                    Layout.fillWidth: true
                    implicitHeight: backlogColumn.implicitHeight + 16
                    visible: page.summary.backlogTotal > 0

                    ColumnLayout {
                        id: backlogColumn
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 0

                        Repeater {
                            model: qazaBridge.backlog

                            delegate: RowLayout {
                                id: backlogRow

                                required property var modelData

                                objectName: "qazaBacklogRow_" + modelData.key
                                visible: modelData.count > 0
                                Layout.fillWidth: true
                                Layout.leftMargin: 10
                                Layout.rightMargin: 10
                                Layout.topMargin: 6
                                Layout.bottomMargin: 6
                                spacing: 12

                                ColumnLayout {
                                    spacing: 2
                                    Text {
                                        text: backlogRow.modelData.name
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                        color: Theme.text
                                    }
                                    Text {
                                        text: strings.qaza.remainingPrayerCount.arg(backlogRow.modelData.count)
                                        font.family: Theme.fontFamily
                                        font.pixelSize: 12
                                        color: Theme.textLight
                                    }
                                }
                                Item { Layout.fillWidth: true }
                                AppButton {
                                    objectName: "qazaDecrement_" + backlogRow.modelData.key
                                    variant: "outlined"
                                    text: strings.qaza.decrementBacklog
                                    implicitHeight: 38
                                    onClicked: qazaBridge.decrementBacklog(backlogRow.modelData.key)
                                }
                            }
                        }
                    }
                }

                // Günlük takipten düşen kazalar
                Text {
                    visible: qazaBridge.groups.length > 0
                    text: strings.qaza.trackedSectionTitle
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                    color: Theme.textLight
                }
                Repeater {
                    model: qazaBridge.groups

                    delegate: DayCard {
                        required property int index
                        required property var modelData

                        Layout.fillWidth: true
                        group: modelData
                        expanded: page.isExpanded(modelData.dateKey, index)
                        onToggled: (value) => page.setExpanded(modelData.dateKey, value)
                        onCompensateRequested: (dateKey, dateLabel, prayerKey, prayerName) =>
                            confirmDialog.openFor(dateKey, dateLabel, prayerKey, prayerName)
                    }
                }
            }
        }
    }

    QazaConfirmDialog { id: confirmDialog }
    QazaPlannerDialog { id: plannerDialog }
}
