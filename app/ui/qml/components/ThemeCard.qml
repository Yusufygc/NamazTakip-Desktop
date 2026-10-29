import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Tema seçim kartı: ad, alt başlık, 4 renk örneği, seçiliyse kenarlık ve onay simgesi.
AbstractButton {
    id: root

    property string themeKey: ""
    property bool selected: false

    // Örnek renkler `Theme.palettes` tek kaynağından gelir (kartın kendi teması, geçerli tema değil).
    readonly property var palette: Theme.palettes[themeKey] !== undefined ? Theme.palettes[themeKey] : Theme.palettes["default"]
    readonly property var names: strings.settings.themes[themeKey] !== undefined
        ? strings.settings.themes[themeKey] : strings.settings.themes["default"]

    objectName: "themeCard_" + themeKey
    implicitWidth: 210
    implicitHeight: 96
    focusPolicy: Qt.StrongFocus
    hoverEnabled: true
    Accessible.role: Accessible.RadioButton
    Accessible.name: strings.settings.themeSemantics.arg(names.name)
    Accessible.checked: selected

    contentItem: ColumnLayout {
        spacing: 6

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            Layout.leftMargin: 14
            Layout.rightMargin: 12

            ColumnLayout {
                spacing: 1
                Text {
                    text: root.names.name
                    font.family: Theme.fontFamily
                    font.pixelSize: 16
                    font.weight: Font.Bold
                    color: Theme.text
                }
                Text {
                    text: root.names.subtitle
                    font.family: Theme.fontFamily
                    font.pixelSize: 12
                    color: Theme.textLight
                }
            }
            Item { Layout.fillWidth: true }
            AppIcon {
                visible: root.selected
                name: "check"
                size: 20
                strokeWidth: 2.6
                color: Theme.primary
            }
        }

        Row {
            Layout.leftMargin: 14
            Layout.bottomMargin: 12
            spacing: 6

            Repeater {
                model: [root.palette.primary, root.palette.secondary, root.palette.accent, root.palette.background]
                delegate: Rectangle {
                    required property color modelData
                    width: 30
                    height: 18
                    radius: 9
                    color: modelData
                    border.width: 1
                    border.color: Theme.withAlpha(Theme.textLight, 0.35)
                }
            }
        }
    }

    background: Rectangle {
        radius: Theme.radiusCard
        color: Theme.card
        border.width: root.selected ? 2.2 : 1
        border.color: root.selected ? Theme.primary
                      : (root.hovered ? Theme.withAlpha(Theme.primary, 0.4) : Theme.withAlpha(Theme.primary, Theme.isDark ? 0.16 : 0.10))

        Rectangle {
            visible: root.visualFocus
            anchors.fill: parent
            anchors.margins: -3
            radius: Theme.radiusCard + 3
            color: "transparent"
            border.width: 2
            border.color: Theme.secondary
        }
    }
}
