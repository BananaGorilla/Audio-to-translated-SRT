import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

Item {
    id: downloadPage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 16

        Panel {
            Layout.fillWidth: true
            Layout.preferredHeight: 280

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Video source"
                        color: "#0f172a"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    StatusPill {
                        text: appController.mediaDownloadStatus
                        busy: appController.mediaDownloadBusy
                    }
                }

                TextField {
                    id: videoUrl
                    Layout.fillWidth: true
                    placeholderText: "Paste a video URL (for example, https://www.youtube.com/watch?v=…)"
                    selectByMouse: true
                    enabled: !appController.mediaDownloadBusy
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 44
                        radius: 10
                        color: "#f8fafc"
                        border.color: "#cbd5e1"
                        Text {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            verticalAlignment: Text.AlignVCenter
                            text: appController.downloadFolderPath
                            color: "#334155"
                            elide: Text.ElideMiddle
                            font.pixelSize: 13
                        }
                    }
                    AppButton {
                        text: "Choose folder"
                        enabled: !appController.mediaDownloadBusy
                        fillColor: "#e2e8f0"
                        hoverColor: "#cbd5e1"
                        pressedColor: "#94a3b8"
                        textColor: "#1e293b"
                        onClicked: appController.chooseDownloadFolder()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 14
                    Text { text: "Audio format"; color: "#475569"; font.pixelSize: 12 }
                    ComboBox {
                        id: audioFormat
                        Layout.preferredWidth: 120
                        model: ["MP3", "WAV", "M4A"]
                        enabled: !appController.mediaDownloadBusy
                    }
                    CheckBox {
                        id: keepVideo
                        text: "Also save an H.264 MP4 video"
                        checked: false
                        enabled: !appController.mediaDownloadBusy
                    }
                    Item { Layout.fillWidth: true }
                    AppButton {
                        text: appController.mediaDownloadBusy ? "Working…" : "Download & extract"
                        enabled: !appController.mediaDownloadBusy && videoUrl.text.trim().length > 0
                        onClicked: appController.startMediaDownload(
                            videoUrl.text,
                            audioFormat.currentText.toLowerCase(),
                            keepVideo.checked
                        )
                    }
                }

                ProgressBar {
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    value: appController.mediaDownloadProgress
                    visible: appController.mediaDownloadBusy || value > 0
                }
            }
        }

        Panel {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                Text {
                    text: "Saved files"
                    color: "#0f172a"
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                }
                TextArea {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    readOnly: true
                    selectByMouse: true
                    text: appController.mediaDownloadOutput
                    placeholderText: "The video and extracted audio paths will appear here."
                    wrapMode: TextEdit.WrapAnywhere
                    color: "#334155"
                    font.family: "Menlo"
                    font.pixelSize: 12
                    background: Rectangle {
                        radius: 10
                        color: "#f8fafc"
                        border.color: "#e2e8f0"
                    }
                }
                Text {
                    Layout.fillWidth: true
                    text: "Only download media you have permission to save. Site terms and copyright rules still apply."
                    color: "#64748b"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
