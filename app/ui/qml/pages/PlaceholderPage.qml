import QtQuick
import QtQuick.Layouts
import "../theme"

// Henüz yazılmamış ekranlar için geçici sayfa (Faz 5 ve 6).
Item {
    property string title: ""

    ColumnLayout {
        anchors.centerIn: parent
        spacing: 8

        Text {
            Layout.alignment: Qt.AlignHCenter
            text: title
            font.family: Theme.fontFamily
            font.pixelSize: 24
            font.weight: Font.Bold
            color: Theme.text
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: strings.common.comingSoon
            font.family: Theme.fontFamily
            font.pixelSize: 14
            color: Theme.textLight
        }
    }
}
