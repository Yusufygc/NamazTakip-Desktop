import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

// "Yeni sürüm var" penceresi: sürüm notları ve kurulum dosyası bilgisi; Güncelle / Sonra / Bu Sürümü Atla.
// "Güncelle": kurulum dosyası indirilir (ilerleme çubuğu), SHA-256 doğrulanır, kurulum başlar ve uygulama kapanır.
Popup {
    id: root

    objectName: "updateDialog"
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(540, parent ? parent.width - 40 : 540)
    padding: 28
    modal: true
    focus: true
    // İndirme sürerken pencere kapanmaz.
    closePolicy: updateBridge.isDownloading ? Popup.NoAutoClose : Popup.CloseOnEscape

    Overlay.modal: Rectangle { color: Theme.withAlpha("#000000", 0.45) }

    background: Rectangle {
        radius: 24
        color: Theme.card
        border.width: 1
        border.color: Theme.withAlpha(Theme.primary, 0.18)
    }

    contentItem: ColumnLayout {
        spacing: 12
        Accessible.role: Accessible.Dialog
        Accessible.name: strings.update.headline.arg(updateBridge.latestVersion)

        Text {
            Layout.fillWidth: true
            text: strings.update.dialogTitle
            font.family: Theme.fontFamily
            font.pixelSize: 13
            font.weight: Font.Bold
            font.letterSpacing: 1.2
            color: Theme.secondaryText
            Accessible.role: Accessible.Heading
        }

        Text {
            objectName: "updateHeadline"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: strings.update.headline.arg(updateBridge.latestVersion)
            font.family: Theme.fontFamily
            font.pixelSize: 20
            font.weight: Font.Bold
            color: Theme.text
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: strings.update.versions.arg(updateBridge.currentVersion)
                  + (updateBridge.publishedDate !== "" ? strings.update.published.arg(updateBridge.publishedDate) : "")
            font.family: Theme.fontFamily
            font.pixelSize: 13
            color: Theme.textLight
        }

        // Sürüm notları: düz metin (bağlantı ve biçim çalıştırılmaz).
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(200, Math.max(60, notes.implicitHeight + 24))
            visible: updateBridge.releaseNotes !== ""
            radius: 14
            color: Theme.blend(Theme.primary, 0.06, Theme.card)
            border.width: 1
            border.color: Theme.withAlpha(Theme.primary, 0.14)
            clip: true

            Flickable {
                id: notesFlick
                anchors.fill: parent
                anchors.margins: 12
                contentHeight: notes.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds

                Text {
                    id: notes
                    objectName: "updateNotes"
                    width: notesFlick.width
                    text: updateBridge.releaseNotes
                    textFormat: Text.PlainText
                    wrapMode: Text.WordWrap
                    font.family: Theme.fontFamily
                    font.pixelSize: 13
                    color: Theme.text
                }
            }
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: strings.update.file.arg(updateBridge.installerLabel)
            font.family: Theme.fontFamily
            font.pixelSize: 13
            color: Theme.textLight
        }

        Text {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: strings.update.explanation
            font.family: Theme.fontFamily
            font.pixelSize: 12
            color: Theme.textLight
        }

        // İndirme ilerlemesi
        Rectangle {
            objectName: "downloadProgress"
            Layout.fillWidth: true
            Layout.preferredHeight: 8
            visible: updateBridge.isDownloading
            radius: 4
            color: Theme.withAlpha(Theme.primary, 0.14)

            Rectangle {
                width: parent.width * (updateBridge.downloadProgress / 100)
                height: parent.height
                radius: 4
                color: Theme.primary
            }
        }

        Text {
            objectName: "updateError"
            Layout.fillWidth: true
            visible: updateBridge.errorMessage !== ""
            wrapMode: Text.WordWrap
            text: updateBridge.errorMessage
            font.family: Theme.fontFamily
            font.pixelSize: 13
            font.weight: Font.DemiBold
            color: updateBridge.isWaitingForWindows ? Theme.secondaryText : Theme.danger
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 6
            spacing: 8

            AppButton {
                objectName: "skipVersionButton"
                enabled: !updateBridge.isDownloading
                variant: "text"
                text: strings.update.skip
                onClicked: { updateBridge.skipVersion(); root.close() }
            }

            Item { Layout.fillWidth: true }

            AppButton {
                objectName: "stopWaitingButton"
                visible: updateBridge.isWaitingForWindows
                variant: "outlined"
                text: strings.update.stopWaiting
                onClicked: updateBridge.stopWaiting()
            }

            AppButton {
                objectName: "releasePageButton"
                visible: updateBridge.errorMessage !== ""
                variant: "text"
                text: strings.update.releasePage
                onClicked: updateBridge.openReleasePage()
            }

            AppButton {
                objectName: "laterButton"
                enabled: !updateBridge.isDownloading
                variant: "outlined"
                text: strings.update.later
                onClicked: root.close()
            }

            AppButton {
                id: updateButton
                objectName: "downloadButton"
                enabled: !updateBridge.isDownloading
                text: updateBridge.isWaitingForWindows ? strings.update.waitingButton
                      : (updateBridge.isDownloading ? strings.update.downloading.arg(updateBridge.downloadProgress)
                         : (updateBridge.canInstall ? strings.update.update : strings.update.releasePage))
                onClicked: updateBridge.startUpdate()
            }
        }
    }

    onOpened: updateButton.forceActiveFocus()
}
