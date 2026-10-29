import QtQuick
import QtQuick.Controls
import "../theme"

// Yalnızca rakam kabul eden sayı alanı. `numberValue` boşsa 0'dır.
TextField {
    id: root

    property int minimum: 0
    property int maximum: 1000000
    property string label: ""
    readonly property int numberValue: text === "" ? 0 : parseInt(text)

    function setNumber(value) {
        text = String(value)
    }

    implicitWidth: 110
    implicitHeight: 40
    validator: IntValidator { bottom: root.minimum; top: root.maximum }
    inputMethodHints: Qt.ImhDigitsOnly
    selectByMouse: true
    horizontalAlignment: TextInput.AlignRight
    color: Theme.text
    font.family: Theme.fontFamily
    font.pixelSize: 15
    leftPadding: 12
    rightPadding: 12
    Accessible.name: label

    onActiveFocusChanged: if (activeFocus) selectAll()

    background: Rectangle {
        radius: 12
        color: Theme.blend(Theme.primary, 0.05, Theme.card)
        border.width: root.activeFocus ? 2 : 1
        border.color: root.activeFocus ? Theme.secondary : Theme.withAlpha(Theme.primary, 0.22)
    }
}
