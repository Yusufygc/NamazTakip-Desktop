import QtQuick
import QtQuick.Layouts
import "../theme"

// Önceki / sonraki gün okları ve seçili gün başlığı.
RowLayout {
    id: root

    spacing: 8

    IconButton {
        objectName: "previousDayButton"
        iconName: "chevronLeft"
        label: strings.home.previousDay
        enabled: homeBridge.canGoPrevious
        onClicked: homeBridge.previousDay()
    }

    Text {
        objectName: "selectedDateText"
        text: homeBridge.selectedDateLabel
        font.family: Theme.fontFamily
        font.pixelSize: 18
        font.weight: Font.DemiBold
        color: Theme.text
        Layout.alignment: Qt.AlignVCenter
    }

    IconButton {
        objectName: "nextDayButton"
        iconName: "chevronRight"
        label: strings.home.nextDay
        enabled: homeBridge.canGoNext
        onClicked: homeBridge.nextDay()
    }

    AppButton {
        objectName: "goTodayButton"
        visible: !homeBridge.isToday
        variant: "text"
        text: strings.home.goToday
        implicitHeight: 36
        onClicked: homeBridge.goToday()
    }

    Item { Layout.fillWidth: true }
}
