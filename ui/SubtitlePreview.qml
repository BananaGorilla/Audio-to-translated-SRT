import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import "components"

Item {
    id: preview
    objectName: "subtitlePreviewPage"

    property string activeSubtitle: ""
    property string playerError: ""

    function formatTime(milliseconds) {
        if (!milliseconds || milliseconds < 0)
            return "00:00"
        const totalSeconds = Math.floor(milliseconds / 1000)
        const minutes = Math.floor(totalSeconds / 60)
        const seconds = totalSeconds % 60
        return String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0")
    }

    MediaPlayer {
        id: player
        objectName: "subtitlePreviewPlayer"
        source: appController.previewAudioUrl
        audioOutput: AudioOutput {
            volume: volumeSlider.value
        }
        onPositionChanged: (position) => preview.activeSubtitle = appController.previewSubtitleAt(position)
        onSourceChanged: {
            preview.activeSubtitle = ""
            preview.playerError = ""
        }
        onErrorOccurred: (error, errorString) => preview.playerError = errorString
    }

    Connections {
        target: appController
        function onPreviewSubtitleFilePathChanged() {
            preview.activeSubtitle = appController.previewSubtitleAt(player.position)
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 16

        Panel {
            Layout.fillWidth: true
            Layout.preferredHeight: 210

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Preview files"
                        color: "#0f172a"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    StatusPill {
                        text: preview.playerError || appController.previewStatus
                        busy: player.mediaStatus === MediaPlayer.LoadingMedia
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        Layout.preferredWidth: 54
                        text: "Audio"
                        color: "#475569"
                        font.pixelSize: 12
                        font.weight: Font.Medium
                    }
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
                            text: appController.previewAudioFilePath || "Choose an audio file"
                            color: appController.previewAudioFilePath ? "#334155" : "#94a3b8"
                            elide: Text.ElideMiddle
                            font.pixelSize: 13
                        }
                    }
                    AppButton {
                        text: "Browse"
                        fillColor: "#e2e8f0"
                        hoverColor: "#cbd5e1"
                        pressedColor: "#94a3b8"
                        textColor: "#1e293b"
                        onClicked: appController.choosePreviewAudioFile()
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        Layout.preferredWidth: 54
                        text: "SRT"
                        color: "#475569"
                        font.pixelSize: 12
                        font.weight: Font.Medium
                    }
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
                            text: appController.previewSubtitleFilePath || "Choose an SRT subtitle file"
                            color: appController.previewSubtitleFilePath ? "#334155" : "#94a3b8"
                            elide: Text.ElideMiddle
                            font.pixelSize: 13
                        }
                    }
                    AppButton {
                        text: "Browse"
                        fillColor: "#e2e8f0"
                        hoverColor: "#cbd5e1"
                        pressedColor: "#94a3b8"
                        textColor: "#1e293b"
                        onClicked: appController.choosePreviewSubtitleFile()
                    }
                }
            }
        }

        Panel {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Subtitle playback"
                        color: "#0f172a"
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                        text: appController.previewSubtitleCount + " cues loaded"
                        color: "#64748b"
                        font.pixelSize: 12
                    }
                }

                Rectangle {
                    id: playbackSurface
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 14
                    color: "#0f172a"
                    clip: true

                    Column {
                        anchors.centerIn: parent
                        z: 1
                        width: Math.min(parent.width - 64, 760)
                        spacing: 18
                        visible: preview.activeSubtitle.length === 0

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: player.playbackState === MediaPlayer.PlayingState ? "PLAYING" : "AUDIO PREVIEW"
                            color: player.playbackState === MediaPlayer.PlayingState ? "#5eead4" : "#64748b"
                            font.pixelSize: 10
                            font.weight: Font.Bold
                            font.letterSpacing: 1.2
                        }

                        Text {
                            width: parent.width
                            text: !appController.previewAudioFilePath
                                ? "Choose an audio file"
                                : (!appController.previewSubtitleFilePath
                                    ? "Load an SRT file to preview synchronized subtitles"
                                    : "No subtitle at the current playback position")
                            color: "#94a3b8"
                            font.pixelSize: 16
                            horizontalAlignment: Text.AlignHCenter
                            wrapMode: Text.WordWrap
                            lineHeight: 1.25
                        }
                    }

                    Rectangle {
                        z: 2
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.leftMargin: Math.max(28, parent.width * 0.1)
                        anchors.rightMargin: Math.max(28, parent.width * 0.1)
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 22
                        height: subtitleText.implicitHeight + 24
                        radius: 8
                        visible: preview.activeSubtitle.length > 0
                        color: "#d9020617"
                        border.color: "#334155"

                        Text {
                            id: subtitleText
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            anchors.topMargin: 10
                            anchors.bottomMargin: 10
                            text: preview.activeSubtitle
                            color: "#ffffff"
                            font.pixelSize: 22
                            font.weight: Font.DemiBold
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            wrapMode: Text.WordWrap
                            lineHeight: 1.2
                            style: Text.Outline
                            styleColor: "#000000"
                        }
                    }
                }

                Slider {
                    id: positionSlider
                    Layout.fillWidth: true
                    from: 0
                    to: Math.max(1, player.duration)
                    value: player.position
                    enabled: player.duration > 0
                    onMoved: player.setPosition(value)
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    AppButton {
                        text: player.playbackState === MediaPlayer.PlayingState ? "Pause" : "Play"
                        enabled: appController.previewAudioFilePath.length > 0
                        onClicked: {
                            if (player.playbackState === MediaPlayer.PlayingState)
                                player.pause()
                            else
                                player.play()
                        }
                    }

                    AppButton {
                        text: "Stop"
                        enabled: appController.previewAudioFilePath.length > 0
                        fillColor: "#e2e8f0"
                        hoverColor: "#cbd5e1"
                        pressedColor: "#94a3b8"
                        textColor: "#1e293b"
                        onClicked: player.stop()
                    }

                    Text {
                        text: preview.formatTime(player.position) + " / " + preview.formatTime(player.duration)
                        color: "#475569"
                        font.pixelSize: 12
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: "Volume"
                        color: "#64748b"
                        font.pixelSize: 12
                    }
                    Slider {
                        id: volumeSlider
                        Layout.preferredWidth: 130
                        from: 0
                        to: 1
                        value: 0.8
                    }
                }
            }
        }
    }
}
