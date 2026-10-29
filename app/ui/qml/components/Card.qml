import QtQuick
import "../theme"

Rectangle {
    property color fill: Theme.card
    property color borderColor: Theme.withAlpha(Theme.primary, Theme.isDark ? 0.16 : 0.09)
    property real borderWidth: 1

    color: fill
    radius: Theme.radiusCard
    border.color: borderColor
    border.width: borderWidth
}
