import QtQuick
import QtQuick.Layouts
import "../theme"

// Başlıklı ayar grubu: üstte küçük başlık, altında kart. Alt öğeler karta eklenir.
ColumnLayout {
    id: root

    property string title: ""
    default property alias content: body.data

    spacing: 8

    Text {
        text: root.title
        font.family: Theme.fontFamily
        font.pixelSize: 13
        font.weight: Font.Bold
        font.letterSpacing: 1
        color: Theme.textLight
        Accessible.role: Accessible.Heading
    }

    Card {
        Layout.fillWidth: true
        implicitHeight: body.implicitHeight + 12

        ColumnLayout {
            id: body
            anchors.fill: parent
            anchors.margins: 6
            spacing: 0
        }
    }
}
