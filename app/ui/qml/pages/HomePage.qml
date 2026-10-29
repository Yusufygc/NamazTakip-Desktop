import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"

// Vakitler (ana ekran): sol sütunda geri sayım, sağ sütunda seçili günün 6 vakti.
Item {
    id: page

    readonly property var rows: homeBridge.prayers
    readonly property int doneCount: {
        var count = 0
        for (var i = 0; i < rows.length; ++i) {
            if (!rows[i].isSunrise && (rows[i].status === "performed" || rows[i].status === "compensated"))
                count++
        }
        return count
    }

    function openCityPicker() {
        cityPicker.open()
    }

    Item {
        anchors.fill: parent
        anchors.margins: 24

        ColumnLayout {
            width: Math.min(parent.width, 1000)
            height: parent.height
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: 14

            DayNavigator {
                Layout.fillWidth: true
                visible: homeBridge.hasLocation
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: homeBridge.hasLocation
                spacing: 22

                CountdownCard {
                    Layout.preferredWidth: 380
                    Layout.alignment: Qt.AlignTop
                    visible: homeBridge.isToday
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            Layout.fillWidth: true
                            text: (homeBridge.isToday ? strings.home.todayPrayers : strings.home.dayPrayers)
                                      .arg(homeBridge.selectedDateLabel)
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            font.weight: Font.Bold
                            font.letterSpacing: 1
                            color: Theme.textLight
                        }
                        Text {
                            objectName: "completedSummaryText"
                            text: strings.home.completedSummary.arg(page.doneCount).arg(5)
                            font.family: Theme.fontFamily
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            color: Theme.primary
                        }
                    }

                    Text {
                        visible: homeBridge.isFuture
                        text: strings.home.futureDayNote
                        font.family: Theme.fontFamily
                        font.pixelSize: 12
                        color: Theme.textLight
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        Repeater {
                            model: page.rows

                            delegate: PrayerRow {
                                required property int index
                                required property var modelData

                                objectName: "prayerRow_" + modelData.key
                                Layout.fillWidth: true
                                rowData: modelData
                                isFirst: index === 0
                                isLast: index === page.rows.length - 1
                                onActivated: (row) => prayerDialog.openFor(row)
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }
                }
            }

            // Şehir seçilmemişse
            Card {
                id: noLocationCard
                objectName: "noLocationCard"
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !homeBridge.hasLocation

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 18

                    AppIcon {
                        Layout.alignment: Qt.AlignHCenter
                        name: "pin"
                        size: 48
                        strokeWidth: 1.6
                        color: Theme.secondary
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: strings.location.needed
                        font.family: Theme.fontFamily
                        font.pixelSize: 18
                        color: Theme.text
                    }
                    AppButton {
                        objectName: "chooseCityButton"
                        Layout.alignment: Qt.AlignHCenter
                        text: strings.location.chooseCity
                        iconName: "pin"
                        onClicked: cityPicker.open()
                    }
                }
            }
        }
    }

    PrayerDialog { id: prayerDialog }
    CityPickerDialog { id: cityPicker }
}
