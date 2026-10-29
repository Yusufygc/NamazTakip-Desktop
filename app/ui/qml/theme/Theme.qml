pragma Singleton
import QtQuick

// Beş tema (mobil app_theme.dart ile aynı paletler). Seçili anahtar Main.qml'deki Binding ile
// settingsBridge.themeKey'den gelir; renkler buradan okunur.
QtObject {
    id: root

    property string themeKey: "default"

    readonly property var palettes: ({
        "default": {
            primary: "#1B5E43", secondary: "#C89D3C", accent: "#EBE3D0", dark: "#103F2C",
            background: "#F8F5EE", card: "#FFFFFF", text: "#18261F", textLight: "#5A6D63",
            danger: "#C62828", secondaryText: "#7E6B30", heroAccent: "#DFC68E",
            isDark: false
        },
        "dark": {
            primary: "#38B281", secondary: "#E2B553", accent: "#1F362D", dark: "#1F7A56",
            background: "#0C1411", card: "#15221D", text: "#EAF2EE", textLight: "#93A89E",
            danger: "#EF6C6C", secondaryText: "#E2B553", heroAccent: "#E2B553",
            isDark: true
        },
        "ocean": {
            primary: "#175D85", secondary: "#2EA3B8", accent: "#D9ECF5", dark: "#0E3F5C",
            background: "#F3F8FB", card: "#FFFFFF", text: "#142734", textLight: "#556E7F",
            danger: "#C62828", secondaryText: "#257688", heroAccent: "#A7D8E1",
            isDark: false
        },
        "rose": {
            primary: "#8C3747", secondary: "#C87A82", accent: "#F5E1E4", dark: "#63212E",
            background: "#FCF6F7", card: "#FFFFFF", text: "#2B171B", textLight: "#73565C",
            danger: "#C62828", secondaryText: "#965A61", heroAccent: "#E6C2C6",
            isDark: false
        },
        "gold": {
            primary: "#8E6918", secondary: "#D1A234", accent: "#F4E9CE", dark: "#63480C",
            background: "#FAF6EC", card: "#FFFFFF", text: "#282011", textLight: "#6E6045",
            danger: "#C62828", secondaryText: "#876925", heroAccent: "#FAF6EB",
            isDark: false
        }
    })

    readonly property var current: palettes[themeKey] !== undefined ? palettes[themeKey] : palettes["default"]

    readonly property color primary: current.primary
    readonly property color secondary: current.secondary
    readonly property color accent: current.accent
    readonly property color dark: current.dark
    readonly property color background: current.background
    readonly property color card: current.card
    readonly property color text: current.text
    readonly property color textLight: current.textLight
    readonly property color danger: current.danger
    // `secondary` yalnızca çizgi/dolgu içindir. Küçük yazıda okunaklı (>= 4,5:1) karşılıkları:
    readonly property color secondaryText: current.secondaryText  // kart ve vurgulu satır üstünde
    readonly property color heroAccent: current.heroAccent        // sayaç kartı (koyu degrade) üstünde
    readonly property bool isDark: current.isDark

    // Birincil renk üstündeki yazı/ikon rengi.
    readonly property color textOnPrimary: isDark ? "#09130F" : "#FFFFFF"
    // Sayaç kartı (Hero) degrade uçları.
    readonly property color heroStart: isDark ? "#16382B" : dark
    readonly property color heroEnd: isDark ? "#0F261D" : primary
    readonly property color textOnHero: "#FFFFFF"

    readonly property string fontFamily: "Segoe UI"
    readonly property string monoFamily: "Consolas"

    readonly property int radiusCard: 18
    readonly property int radiusButton: 14

    function withAlpha(c, a) {
        return Qt.rgba(c.r, c.g, c.b, a)
    }

    // `c` rengini `a` saydamlığıyla `base` üstüne harmanlar (Color.alphaBlend karşılığı).
    function blend(c, a, base) {
        return Qt.tint(base, withAlpha(c, a))
    }
}
