pragma Singleton
import QtQuick

// Merkezi ikon tanımı: 24x24 görünüm kutusunda çizgi (stroke) yolları. Ekranlarda ikon yolu yazılmaz;
// AppIcon.qml ad ile bu tablodan okur.
QtObject {
    readonly property var paths: ({
        "clock": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M12 7v5l3 2",
        "list": "M9 6h11 M9 12h11 M9 18h11 M4.5 6h.01 M4.5 12h.01 M4.5 18h.01",
        "tune": "M4 7h9 M17 7h3 M4 17h3 M11 17h9 M15 4v6 M9 14v6",
        "check": "M5 12.5l4.5 4.5L19 7.5",
        "close": "M6 6l12 12 M18 6L6 18",
        "hourglass": "M7 3h10 M7 21h10 M8 3v4l4 5-4 5v4 M16 3v4l-4 5 4 5v4",
        "sun": "M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z M12 2v2.5 M12 19.5V22 M2 12h2.5 M19.5 12H22 M4.9 4.9l1.8 1.8 M17.3 17.3l1.8 1.8 M4.9 19.1l1.8-1.8 M17.3 6.7l1.8-1.8",
        "circle": "M12 4a8 8 0 1 0 0 16a8 8 0 1 0 0-16z",
        "chevronLeft": "M15 5l-7 7 7 7",
        "chevronRight": "M9 5l7 7-7 7",
        "chevronDown": "M5 9l7 7 7-7",
        "mihrab": "M3 23V10.5C3 6 8 3.5 12 1C16 3.5 21 6 21 10.5V23 M7 23V11.5C7 9 9.5 7.5 12 5.5C14.5 7.5 17 9 17 11.5V23",
        "pin": "M12 21s-6-5.6-6-10a6 6 0 1 1 12 0c0 4.4-6 10-6 10z M12 8.5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5z",
        "search": "M10.5 4a6.5 6.5 0 1 0 0 13a6.5 6.5 0 1 0 0-13z M15.5 15.5L20 20",
        "star8": "M22.00 12.00 L16.25 10.24 L19.07 4.93 L13.76 7.75 L12.00 2.00 L10.24 7.75 L4.93 4.93 L7.75 10.24 L2.00 12.00 L7.75 13.76 L4.93 19.07 L10.24 16.25 L12.00 22.00 L13.76 16.25 L19.07 19.07 L16.25 13.76 Z"
    })
}
