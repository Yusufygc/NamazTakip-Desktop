import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"
import "../components"

// Ayarlar: bildirimler, konum ve hesaplama yöntemi, masaüstü seçenekleri, tema.
Item {
    id: page

    readonly property var reminderChoices: settingsBridge.reminderChoices.map(
        function (minutes) { return { value: minutes, label: strings.settings.minutes.arg(minutes) } })

    readonly property var preReminderChoices: settingsBridge.preReminderChoices.map(
        function (minutes) {
            return { value: minutes, label: minutes === 0 ? strings.settings.preReminderOff : strings.settings.minutes.arg(minutes) }
        })

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
                width: Math.min(parent.width - 48, 720)
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 22

                // ---- Bildirimler ----
                SettingsSection {
                    Layout.fillWidth: true
                    title: strings.settings.sectionNotifications

                    SwitchRow {
                        objectName: "notificationsSwitch"
                        Layout.fillWidth: true
                        title: strings.settings.notifications
                        subtitle: strings.settings.notificationsSubtitle
                        checked: settingsBridge.notificationsEnabled
                        onToggled: settingsBridge.setNotificationsEnabled(checked)
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.leftMargin: 14
                        Layout.rightMargin: 14
                        Layout.bottomMargin: 14
                        spacing: 8

                        Text {
                            text: strings.settings.preReminder
                            font.family: Theme.fontFamily
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                            color: settingsBridge.notificationsEnabled ? Theme.text : Theme.textLight
                        }
                        Text {
                            text: strings.settings.preReminderSubtitle
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            color: Theme.textLight
                        }
                        ChoiceChips {
                            objectName: "preReminderChip"
                            Layout.fillWidth: true
                            Layout.topMargin: 4
                            Layout.bottomMargin: 10
                            choices: page.preReminderChoices
                            current: settingsBridge.preReminderMinutes
                            chipsEnabled: settingsBridge.notificationsEnabled
                            onChosen: (minutes) => settingsBridge.setPreReminderMinutes(minutes)
                        }

                        Text {
                            text: strings.settings.reminderDelay
                            font.family: Theme.fontFamily
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                            color: settingsBridge.notificationsEnabled ? Theme.text : Theme.textLight
                        }
                        Text {
                            text: strings.settings.reminderDelaySubtitle
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            color: Theme.textLight
                        }
                        ChoiceChips {
                            objectName: "reminderChip"
                            Layout.fillWidth: true
                            Layout.topMargin: 4
                            choices: page.reminderChoices
                            current: settingsBridge.reminderMinutes
                            chipsEnabled: settingsBridge.notificationsEnabled
                            onChosen: (minutes) => settingsBridge.setReminderMinutes(minutes)
                        }
                    }
                }

                // ---- Konum ve vakitler ----
                SettingsSection {
                    Layout.fillWidth: true
                    title: strings.settings.sectionLocation

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.margins: 14
                        spacing: 12

                        ColumnLayout {
                            spacing: 2
                            Text {
                                objectName: "settingsCityText"
                                text: settingsBridge.hasLocation ? settingsBridge.cityLabel : strings.settings.noCity
                                font.family: Theme.fontFamily
                                font.pixelSize: 17
                                font.weight: Font.DemiBold
                                color: Theme.text
                            }
                            Text {
                                text: strings.settings.locationInUse
                                font.family: Theme.fontFamily
                                font.pixelSize: 12
                                color: Theme.textLight
                            }
                        }
                        Item { Layout.fillWidth: true }
                        AppButton {
                            objectName: "settingsChooseCityButton"
                            variant: "outlined"
                            iconName: "pin"
                            text: strings.location.chooseCity
                            onClicked: cityPicker.open()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.leftMargin: 14
                        Layout.rightMargin: 14
                        implicitHeight: 1
                        color: Theme.withAlpha(Theme.primary, 0.12)
                    }

                    Text {
                        Layout.margins: 14
                        Layout.bottomMargin: 6
                        text: strings.settings.calcMethod
                        font.family: Theme.fontFamily
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                        color: Theme.text
                    }
                    Repeater {
                        model: settingsBridge.calcMethods

                        delegate: RadioRow {
                            required property var modelData

                            objectName: "calcMethod_" + modelData.key
                            Layout.fillWidth: true
                            Layout.leftMargin: 6
                            Layout.rightMargin: 6
                            title: modelData.name
                            selected: modelData.key === settingsBridge.calcMethodKey
                            onClicked: settingsBridge.setCalcMethod(modelData.key)
                        }
                    }
                    Item { Layout.preferredHeight: 8 }
                }

                // ---- Masaüstü ----
                SettingsSection {
                    Layout.fillWidth: true
                    title: strings.settings.sectionDesktop

                    SwitchRow {
                        objectName: "autostartSwitch"
                        Layout.fillWidth: true
                        title: strings.settings.autostart
                        subtitle: strings.settings.autostartSubtitle
                        checked: settingsBridge.autostartEnabled
                        onToggled: settingsBridge.setAutostart(checked)
                    }
                    SwitchRow {
                        objectName: "closeToTraySwitch"
                        Layout.fillWidth: true
                        title: strings.settings.closeToTray
                        subtitle: strings.settings.closeToTraySubtitle
                        checked: settingsBridge.closeToTray
                        onToggled: settingsBridge.setCloseToTray(checked)
                    }
                }

                // ---- Güncellemeler ----
                SettingsSection {
                    Layout.fillWidth: true
                    title: strings.update.section

                    SwitchRow {
                        objectName: "updateCheckSwitch"
                        Layout.fillWidth: true
                        title: strings.update.checkOnStart
                        subtitle: strings.update.checkOnStartSubtitle
                        checked: settingsBridge.updateCheckEnabled
                        onToggled: settingsBridge.setUpdateCheckEnabled(checked)
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.margins: 14
                        spacing: 12

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Text {
                                objectName: "updateCurrentVersion"
                                text: strings.update.currentVersion.arg(updateBridge.currentVersion)
                                font.family: Theme.fontFamily
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                                color: Theme.text
                            }
                            Text {
                                objectName: "updateStatusText"
                                Layout.fillWidth: true
                                visible: updateBridge.statusText !== ""
                                wrapMode: Text.WordWrap
                                text: updateBridge.statusText
                                font.family: Theme.fontFamily
                                font.pixelSize: 12
                                color: Theme.textLight
                            }
                        }
                        AppButton {
                            objectName: "checkUpdatesButton"
                            enabled: !updateBridge.checking
                            variant: "outlined"
                            text: strings.update.checkNow
                            onClicked: updateBridge.checkNow()
                        }
                    }
                }

                // ---- Tema ----
                SettingsSection {
                    Layout.fillWidth: true
                    title: strings.settings.sectionTheme

                    Flow {
                        Layout.fillWidth: true
                        Layout.margins: 14
                        spacing: 12

                        Repeater {
                            model: settingsBridge.themeKeys

                            delegate: ThemeCard {
                                required property string modelData

                                themeKey: modelData
                                selected: modelData === settingsBridge.themeKey
                                onClicked: settingsBridge.setThemeKey(modelData)
                            }
                        }
                    }
                }

                // ---- Alt bilgi ----
                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: strings.common.versionLabel + "  •  " + strings.common.tagline
                    font.family: Theme.fontFamily
                    font.pixelSize: 12
                    color: Theme.textLight
                }
            }
        }
    }

    CityPickerDialog {
        id: cityPicker
        objectName: "settingsCityPicker"
    }
}
