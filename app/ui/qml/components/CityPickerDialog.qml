import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// 81 il arasından şehir seçici: Türkçe harf duyarsız arama, Yukarı/Aşağı + Enter ile seçim.
Popup {
    id: root

    property var results: settingsBridge.searchCities(searchField.text)

    objectName: "cityPicker"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 420
    height: Math.min(parent ? parent.height - 80 : 560, 560)
    padding: 22
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    // Şehri seçer ve kapatır (listedeki satırlar ve testler bunu çağırır).
    function choose(cityName) {
        if (settingsBridge.selectCity(cityName))
            close()
    }

    onAboutToShow: searchField.text = ""
    onOpened: searchField.forceActiveFocus()

    background: Rectangle {
        radius: 24
        color: Theme.card
        border.width: 1
        border.color: Theme.withAlpha(Theme.primary, 0.18)
    }

    contentItem: ColumnLayout {
        spacing: 12

        Text {
            text: strings.location.pickerTitle
            font.family: Theme.fontFamily
            font.pixelSize: 20
            font.weight: Font.Bold
            color: Theme.text
            Accessible.role: Accessible.Heading
        }

        TextField {
            id: searchField
            objectName: "citySearchField"
            Layout.fillWidth: true
            placeholderText: strings.location.searchHint
            placeholderTextColor: Theme.textLight
            color: Theme.text
            font.family: Theme.fontFamily
            font.pixelSize: 15
            leftPadding: 42
            Accessible.name: strings.location.searchHint

            background: Rectangle {
                implicitHeight: 44
                radius: 14
                color: Theme.blend(Theme.primary, 0.05, Theme.card)
                border.width: searchField.activeFocus ? 2 : 1
                border.color: searchField.activeFocus ? Theme.secondary : Theme.withAlpha(Theme.primary, 0.2)

                AppIcon {
                    x: 12
                    anchors.verticalCenter: parent.verticalCenter
                    name: "search"
                    size: 20
                    color: Theme.textLight
                }
            }

            Keys.onDownPressed: cityList.incrementCurrentIndex()
            Keys.onUpPressed: cityList.decrementCurrentIndex()
            Keys.onReturnPressed: {
                if (cityList.count > 0)
                    root.choose(root.results[cityList.currentIndex].city)
            }
            Keys.onEnterPressed: {
                if (cityList.count > 0)
                    root.choose(root.results[cityList.currentIndex].city)
            }
            onTextChanged: cityList.currentIndex = 0
        }

        ListView {
            id: cityList
            objectName: "cityList"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 2
            model: root.results
            currentIndex: 0
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar {}

            delegate: AbstractButton {
                id: cityRow

                required property int index
                required property var modelData

                width: ListView.view.width
                height: 44
                hoverEnabled: true
                focusPolicy: Qt.NoFocus
                Accessible.name: modelData.label
                Accessible.role: Accessible.ListItem
                onClicked: root.choose(modelData.city)

                background: Rectangle {
                    radius: 12
                    color: cityRow.index === cityList.currentIndex
                           ? Theme.withAlpha(Theme.primary, Theme.isDark ? 0.24 : 0.13)
                           : (cityRow.hovered ? Theme.withAlpha(Theme.primary, 0.07) : "transparent")
                }
                contentItem: Text {
                    leftPadding: 14
                    verticalAlignment: Text.AlignVCenter
                    text: cityRow.modelData.city
                    font.family: Theme.fontFamily
                    font.pixelSize: 15
                    color: Theme.text
                }
            }

            Text {
                anchors.centerIn: parent
                visible: cityList.count === 0
                text: strings.location.noResults
                font.family: Theme.fontFamily
                font.pixelSize: 14
                color: Theme.textLight
            }
        }
    }
}
