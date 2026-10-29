import QtQuick
import QtQuick.Layouts
import "../theme"

// Sıradaki vakte geri sayım (Hero) kartı.
Rectangle {
    id: root

    objectName: "countdownCard"
    radius: 24
    clip: true
    implicitHeight: 260

    gradient: Gradient {
        orientation: Gradient.Horizontal
        GradientStop { position: 0.0; color: Theme.heroStart }
        GradientStop { position: 1.0; color: Theme.heroEnd }
    }

    Accessible.role: Accessible.StaticText
    Accessible.name: homeBridge.nextPrayerName === ""
        ? strings.home.noTimes
        : strings.home.countdownSemantics.arg(homeBridge.nextPrayerName).arg(homeBridge.countdown)

    // Selçuklu yıldızı motifi (süs; erişilebilirlikte yok sayılır)
    AppIcon {
        x: parent.width - width * 0.62
        y: -height * 0.18
        name: "star8"
        size: 190
        strokeWidth: 1
        color: Theme.withAlpha(Theme.secondary, 0.28)
    }
    AppIcon {
        x: parent.width - width * 0.55
        y: -height * 0.1
        name: "star8"
        size: 130
        strokeWidth: 1
        color: Theme.withAlpha(Theme.secondary, 0.22)
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 4
        visible: homeBridge.nextPrayerName !== ""

        Text {
            text: strings.home.nextBadge
            font.family: Theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.Bold
            font.letterSpacing: 1.6
            color: Theme.heroAccent
        }
        Text {
            objectName: "nextPrayerNameText"
            text: homeBridge.nextPrayerName
            font.family: Theme.fontFamily
            font.pixelSize: 30
            font.weight: Font.Bold
            color: Theme.textOnHero
        }
        Item { Layout.fillHeight: true }
        Text {
            objectName: "countdownText"
            text: homeBridge.countdown
            font.family: Theme.monoFamily
            font.pixelSize: 54
            font.weight: Font.Bold
            color: Theme.textOnHero
        }
        Text {
            text: strings.home.nextPrayer.arg(homeBridge.nextPrayerName) + "  •  " + homeBridge.nextPrayerTime
            font.family: Theme.fontFamily
            font.pixelSize: 14
            color: Theme.withAlpha(Theme.textOnHero, 0.92)
        }
        Item { Layout.preferredHeight: 10 }
        RowLayout {
            spacing: 6
            AppIcon { name: "pin"; size: 16; strokeWidth: 1.8; color: Theme.heroAccent }
            Text {
                objectName: "cityText"
                text: homeBridge.cityLabel
                font.family: Theme.fontFamily
                font.pixelSize: 14
                color: Theme.withAlpha(Theme.textOnHero, 0.92)
            }
        }
    }

    Text {
        anchors.centerIn: parent
        visible: homeBridge.nextPrayerName === ""
        text: strings.home.noTimes
        font.family: Theme.fontFamily
        font.pixelSize: 16
        color: Theme.textOnHero
    }
}
