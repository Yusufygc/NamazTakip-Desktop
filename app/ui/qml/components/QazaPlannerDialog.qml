import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// Geçmiş yıllar kaza borcu hesaplayıcı ve günlük hedef. Kaydedilene kadar hiçbir şey yazılmaz.
Popup {
    id: root

    // Başlıklı sayı alanı sütunu (Yıl / Ay / Gün)
    component DurationColumn: ColumnLayout {
        property string title: ""
        property alias field: input

        Layout.fillWidth: true
        spacing: 4

        Text {
            text: title
            font.family: Theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.DemiBold
            color: Theme.textLight
        }
        NumberField {
            id: input
            Layout.fillWidth: true
            maximum: 999
            label: title
        }
    }

    // Vakit adı + sayı alanı satırı
    component CountRow: RowLayout {
        property string title: ""
        property alias field: input

        Layout.fillWidth: true
        spacing: 12

        Text {
            Layout.fillWidth: true
            text: title
            font.family: Theme.fontFamily
            font.pixelSize: 15
            font.weight: Font.DemiBold
            color: Theme.text
        }
        NumberField {
            id: input
            label: title
        }
    }

    objectName: "qazaPlannerDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: 460
    height: Math.min(layoutRoot.implicitHeight + topPadding + bottomPadding, parent ? parent.height - 48 : 600)
    padding: 24
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    // Açılışta mevcut plan alanlara yüklenir.
    function openPlanner() {
        yearsColumn.field.setNumber(0)
        monthsColumn.field.setNumber(0)
        daysColumn.field.setNumber(0)
        for (var i = 0; i < qazaBridge.backlog.length; ++i)
            countRepeater.itemAt(i).field.setNumber(qazaBridge.backlog[i].count)
        targetField.setNumber(qazaBridge.summary.dailyTarget)
        open()
    }

    // Vakit alanlarındaki sayıları {vakitAnahtarı: sayı} olarak verir.
    function currentCounts() {
        var counts = {}
        for (var i = 0; i < qazaBridge.backlog.length; ++i)
            counts[qazaBridge.backlog[i].key] = countRepeater.itemAt(i).field.numberValue
        return counts
    }

    // "Süreden Hesapla ve Vakitlere Ekle": süreyi her vakte ekler, süre alanlarını sıfırlar.
    function applyDuration() {
        var result = qazaBridge.previewDuration(
            yearsColumn.field.numberValue, monthsColumn.field.numberValue, daysColumn.field.numberValue,
            currentCounts())
        for (var i = 0; i < qazaBridge.backlog.length; ++i)
            countRepeater.itemAt(i).field.setNumber(result[qazaBridge.backlog[i].key])
        yearsColumn.field.setNumber(0)
        monthsColumn.field.setNumber(0)
        daysColumn.field.setNumber(0)
    }

    function save() {
        qazaBridge.savePlan(currentCounts(), Math.max(1, targetField.numberValue))
        close()
    }

    onOpened: yearsColumn.field.forceActiveFocus()

    background: Rectangle {
        radius: 24
        color: Theme.card
        border.width: 1
        border.color: Theme.withAlpha(Theme.primary, 0.18)
    }

    // Form kaydırılır; Kaydet/İptal düğmeleri altta sabit kalır (küçük pencerede de klavyeyle erişilir).
    contentItem: ColumnLayout {
        id: layoutRoot
        spacing: 12

        ScrollView {
            id: scroll
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            implicitHeight: form.implicitHeight

            ColumnLayout {
                id: form
                width: scroll.availableWidth
                spacing: 12

                Text {
                    text: strings.qaza.wizardTitle
                    font.family: Theme.fontFamily
                    font.pixelSize: 20
                    font.weight: Font.Bold
                    color: Theme.text
                    Accessible.role: Accessible.Heading
                }
                Text {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: strings.qaza.wizardSubtitle
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    color: Theme.textLight
                }

                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: 6
                    spacing: 12

                    DurationColumn { id: yearsColumn; title: strings.qaza.wizardYears; field.objectName: "planYears" }
                    DurationColumn { id: monthsColumn; title: strings.qaza.wizardMonths; field.objectName: "planMonths" }
                    DurationColumn { id: daysColumn; title: strings.qaza.wizardDays; field.objectName: "planDays" }
                }
                AppButton {
                    objectName: "planApplyDuration"
                    Layout.fillWidth: true
                    variant: "outlined"
                    text: strings.qaza.wizardApplyDuration
                    onClicked: root.applyDuration()
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    implicitHeight: 1
                    color: Theme.withAlpha(Theme.primary, 0.12)
                }

                // Vakit bazlı sayılar
                Repeater {
                    id: countRepeater
                    model: qazaBridge.backlog

                    delegate: CountRow {
                        required property var modelData
                        title: modelData.name
                        field.objectName: "planCount_" + modelData.key
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: Theme.withAlpha(Theme.primary, 0.12)
                }

                // Günlük hedef
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Text {
                            text: strings.qaza.wizardDailyTarget
                            font.family: Theme.fontFamily
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            color: Theme.text
                        }
                        Text {
                            text: strings.qaza.dailyTargetValue.arg(Math.max(1, targetField.numberValue))
                            font.family: Theme.fontFamily
                            font.pixelSize: 12
                            color: Theme.textLight
                        }
                    }
                    NumberField {
                        id: targetField
                        objectName: "planTarget"
                        minimum: 1
                        maximum: 50
                        label: strings.qaza.wizardDailyTarget
                    }
                }
            }
        }

        AppButton {
            objectName: "planSave"
            Layout.fillWidth: true
            text: strings.qaza.wizardSave
            iconName: "check"
            onClicked: root.save()
        }
        AppButton {
            objectName: "planCancel"
            Layout.fillWidth: true
            variant: "text"
            text: strings.common.cancel
            onClicked: root.close()
        }
    }
}
