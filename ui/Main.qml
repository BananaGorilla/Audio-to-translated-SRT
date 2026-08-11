import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"

ApplicationWindow {
    id: root

    width: 1240
    height: 800
    minimumWidth: 980
    minimumHeight: 680
    visible: true
    title: "Audio Subtitle Studio"
    color: "#f8fafc"

    property int currentSection: 0
    property var transcriptionLanguages: ["English", "Chinese", "Thai", "Cantonese", "Bahasa Indonesia", "Malay"]
    property var translationSourceLanguages: ["English", "Simplified Chinese", "Traditional Chinese", "Thai", "Bahasa Indonesia", "Malay"]
    property var translationTargetLanguages: ["Simplified Chinese", "English", "Traditional Chinese", "Thai", "Bahasa Indonesia", "Malay"]

    function pageTitle() {
        const titles = ["Download media", "Transcribe audio", "Translate subtitles", "Preview subtitles", "Settings"]
        return titles[currentSection]
    }

    function pageDescription() {
        if (currentSection === 0)
            return "Save a video and create a transcription-ready audio file."
        return "Create accurate subtitles and translations without command-line setup."
    }

    function selectedModelText() {
        if (currentSection === 0)
            return "Video download + audio extraction"
        if (currentSection === 1)
            return "Model · " + appController.selectedTranscriptionModelLabel
        if (currentSection === 2)
            return "Model · " + appController.selectedTranslationModelLabel
        if (currentSection === 3)
            return "Audio + SRT preview"
        return "Configure models below"
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.preferredWidth: 232
            Layout.fillHeight: true
            color: "#0f2238"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                Row {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.topMargin: 8
                    Layout.bottomMargin: 24
                    spacing: 11

                    Rectangle {
                        width: 36
                        height: 36
                        radius: 11
                        gradient: Gradient {
                            GradientStop { position: 0; color: "#3b82f6" }
                            GradientStop { position: 1; color: "#14b8a6" }
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "A"
                            color: "white"
                            font.pixelSize: 17
                            font.weight: Font.Bold
                        }
                    }

                    Column {
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 1

                        Text {
                            text: "Audio Subtitle"
                            color: "#ffffff"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: "Studio"
                            color: "#7dd3fc"
                            font.pixelSize: 12
                        }
                    }
                }

                NavButton {
                    Layout.fillWidth: true
                    text: "Download & Extract"
                    selected: root.currentSection === 0
                    onClicked: root.currentSection = 0
                }
                NavButton {
                    Layout.fillWidth: true
                    text: "Transcribe"
                    selected: root.currentSection === 1
                    onClicked: root.currentSection = 1
                }
                NavButton {
                    Layout.fillWidth: true
                    text: "Translate"
                    selected: root.currentSection === 2
                    onClicked: root.currentSection = 2
                }
                NavButton {
                    Layout.fillWidth: true
                    text: "Subtitle Preview"
                    selected: root.currentSection === 3
                    onClicked: root.currentSection = 3
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 86
                    radius: 12
                    color: "#152e49"

                    Column {
                        anchors.fill: parent
                        anchors.margins: 13
                        spacing: 5

                        Text {
                            text: "Local-first workflow"
                            color: "#e2e8f0"
                            font.pixelSize: 12
                            font.weight: Font.DemiBold
                        }
                        Text {
                            width: parent.width
                            text: "Cloud and offline models in one workspace."
                            color: "#94a3b8"
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                        }
                    }
                }

                NavButton {
                    Layout.fillWidth: true
                    text: "Settings"
                    selected: root.currentSection === 4
                    onClicked: root.currentSection = 4
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 72
                color: "#ffffff"
                border.color: "#e2e8f0"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 28
                    anchors.rightMargin: 28

                    Column {
                        spacing: 2
                        Text {
                            text: root.pageTitle()
                            color: "#0f172a"
                            font.pixelSize: 20
                            font.weight: Font.DemiBold
                        }
                        Text {
                            text: root.pageDescription()
                            color: "#64748b"
                            font.pixelSize: 12
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        implicitWidth: modelLabel.implicitWidth + 24
                        implicitHeight: 34
                        radius: 17
                        color: "#f8fafc"
                        border.color: "#e2e8f0"

                        Text {
                            id: modelLabel
                            anchors.centerIn: parent
                            text: root.selectedModelText()
                            color: "#475569"
                            font.pixelSize: 11
                        }
                    }
                }
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: root.currentSection

                // Video download and audio extraction
                MediaDownload { }

                // Transcription
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 28
                        spacing: 16

                        Panel {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 168

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 14

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: "Audio input"
                                        color: "#0f172a"
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                    }
                                    Item { Layout.fillWidth: true }
                                    StatusPill {
                                        text: appController.transcriptionStatus
                                        busy: appController.transcriptionBusy
                                    }
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
                                            text: appController.audioFilePath || "Choose an audio file"
                                            color: appController.audioFilePath ? "#334155" : "#94a3b8"
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
                                        onClicked: appController.chooseAudioFile()
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 12

                                    ComboBox {
                                        id: transcriptionLanguage
                                        Layout.preferredWidth: 210
                                        model: root.transcriptionLanguages
                                    }

                                    CheckBox {
                                        id: timestampCheck
                                        text: "Generate SRT timestamps"
                                        checked: true
                                    }

                                    Item { Layout.fillWidth: true }

                                    AppButton {
                                        text: appController.transcriptionBusy ? "Working…" : "Transcribe"
                                        enabled: !appController.transcriptionBusy
                                        onClicked: appController.startTranscription(transcriptionLanguage.currentText, timestampCheck.checked)
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
                                spacing: 12

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: "Transcript"
                                        color: "#0f172a"
                                        font.pixelSize: 15
                                        font.weight: Font.DemiBold
                                    }
                                    Item { Layout.fillWidth: true }
                                    Text {
                                        text: transcriptionEditor.length + " characters"
                                        color: "#94a3b8"
                                        font.pixelSize: 11
                                    }
                                }

                                TextArea {
                                    id: transcriptionEditor
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    text: appController.transcribedText
                                    placeholderText: "Your transcript will appear here. You can edit it before saving."
                                    wrapMode: TextEdit.Wrap
                                    selectByMouse: true
                                    font.family: "Menlo"
                                    font.pixelSize: 13
                                    color: "#1e293b"
                                    background: Rectangle {
                                        radius: 10
                                        color: "#f8fafc"
                                        border.color: transcriptionEditor.activeFocus ? "#60a5fa" : "#e2e8f0"
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    Item { Layout.fillWidth: true }
                                    AppButton {
                                        text: "Save as…"
                                        enabled: transcriptionEditor.text.length > 0
                                        fillColor: "#0f766e"
                                        hoverColor: "#115e59"
                                        pressedColor: "#134e4a"
                                        onClicked: appController.saveTranscription(transcriptionEditor.text)
                                    }
                                }
                            }
                        }
                    }
                }

                // Translation
                Item {
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 28
                        spacing: 16

                        Panel {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 168

                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 14

                                RowLayout {
                                    Layout.fillWidth: true
                                    Text {
                                        text: "Subtitle source"
                                        color: "#0f172a"
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                    }
                                    Item { Layout.fillWidth: true }
                                    StatusPill {
                                        text: appController.translationStatus
                                        busy: appController.translationBusy
                                    }
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
                                            text: appController.subtitleFilePath || "Choose an SRT or text file"
                                            color: appController.subtitleFilePath ? "#334155" : "#94a3b8"
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
                                        onClicked: appController.chooseSubtitleFile()
                                    }
                                }

                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 10
                                    ComboBox {
                                        id: sourceLanguage
                                        Layout.preferredWidth: 210
                                        model: root.translationSourceLanguages
                                    }
                                    Text { text: "→"; color: "#64748b"; font.pixelSize: 18 }
                                    ComboBox {
                                        id: targetLanguage
                                        Layout.preferredWidth: 210
                                        model: root.translationTargetLanguages
                                    }
                                    Item { Layout.fillWidth: true }
                                    AppButton {
                                        text: appController.translationBusy ? "Working…" : "Translate"
                                        fillColor: "#0f766e"
                                        hoverColor: "#115e59"
                                        pressedColor: "#134e4a"
                                        enabled: !appController.translationBusy && originalEditor.text.length > 0
                                        onClicked: appController.startTranslation(sourceLanguage.currentText, targetLanguage.currentText, originalEditor.text)
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 14

                            Panel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 10
                                    Text {
                                        text: "Original"
                                        color: "#0f172a"
                                        font.pixelSize: 14
                                        font.weight: Font.DemiBold
                                    }
                                    TextArea {
                                        id: originalEditor
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        text: appController.originalText
                                        placeholderText: "Open an SRT file or paste subtitle text here."
                                        wrapMode: TextEdit.Wrap
                                        selectByMouse: true
                                        font.family: "Menlo"
                                        font.pixelSize: 12
                                        color: "#1e293b"
                                        background: Rectangle {
                                            radius: 10
                                            color: "#f8fafc"
                                            border.color: originalEditor.activeFocus ? "#60a5fa" : "#e2e8f0"
                                        }
                                    }
                                }
                            }

                            Panel {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 16
                                    spacing: 10
                                    Text {
                                        text: "Translation"
                                        color: "#0f172a"
                                        font.pixelSize: 14
                                        font.weight: Font.DemiBold
                                    }
                                    TextArea {
                                        id: translationEditor
                                        Layout.fillWidth: true
                                        Layout.fillHeight: true
                                        text: appController.translatedText
                                        placeholderText: "The translated subtitles will appear here."
                                        wrapMode: TextEdit.Wrap
                                        selectByMouse: true
                                        font.family: "Menlo"
                                        font.pixelSize: 12
                                        color: "#1e293b"
                                        background: Rectangle {
                                            radius: 10
                                            color: "#f8fafc"
                                            border.color: translationEditor.activeFocus ? "#2dd4bf" : "#e2e8f0"
                                        }
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        Item { Layout.fillWidth: true }
                                        AppButton {
                                            text: "Save as…"
                                            enabled: translationEditor.text.length > 0
                                            fillColor: "#0f766e"
                                            hoverColor: "#115e59"
                                            pressedColor: "#134e4a"
                                            onClicked: appController.saveTranslation(translationEditor.text)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // Subtitle preview
                SubtitlePreview { }

                // Settings
                ScrollView {
                    clip: true

                    Item {
                        implicitWidth: Math.max(760, settingsColumn.implicitWidth + 56)
                        implicitHeight: settingsColumn.implicitHeight + 56

                        ColumnLayout {
                            id: settingsColumn
                            anchors.top: parent.top
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.margins: 28
                            spacing: 18

                            Column {
                                Layout.fillWidth: true
                                spacing: 6
                                Text {
                                    text: "Models and providers"
                                    color: "#0f172a"
                                    font.pixelSize: 24
                                    font.weight: Font.DemiBold
                                }
                                Text {
                                    text: "Choose the services used for transcription and translation. Keys stay on this computer."
                                    color: "#64748b"
                                    font.pixelSize: 13
                                }
                            }

                            Panel {
                                Layout.fillWidth: true
                                Layout.preferredHeight: transcriptionModel.currentValue === "local/whisper" ? 314 : 190

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 22
                                    spacing: 12
                                    Text {
                                        text: "Transcription"
                                        color: "#0f172a"
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 14
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Model"; color: "#475569"; font.pixelSize: 12 }
                                            ComboBox {
                                                id: transcriptionModel
                                                Layout.fillWidth: true
                                                model: appController.transcriptionModels
                                                textRole: "label"
                                                valueRole: "value"
                                                Component.onCompleted: {
                                                    for (let index = 0; index < model.length; index++) {
                                                        if (model[index].value === appController.selectedTranscriptionModel) {
                                                            currentIndex = index
                                                            break
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            visible: transcriptionModel.currentValue !== "local/whisper"
                                            Text { text: "API key"; color: "#475569"; font.pixelSize: 12 }
                                            TextField {
                                                id: transcriptionKey
                                                Layout.fillWidth: true
                                                text: appController.transcriptionApiKey
                                                echoMode: TextInput.Password
                                                placeholderText: "Not required for local Whisper"
                                            }
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        visible: transcriptionModel.currentValue === "local/whisper"
                                        spacing: 7

                                        Text {
                                            text: "Local Whisper setup"
                                            color: "#475569"
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                        }
                                        Text {
                                            text: "Enter the whisper.cpp executable and GGUF model file paths."
                                            color: "#64748b"
                                            font.pixelSize: 11
                                        }
                                        TextField {
                                            id: localWhisperCliPath
                                            Layout.fillWidth: true
                                            text: appController.localWhisperCliPath
                                            placeholderText: "Whisper CLI path, e.g. /path/to/whisper-cli"
                                        }
                                        TextField {
                                            id: localWhisperModelPath
                                            Layout.fillWidth: true
                                            text: appController.localWhisperModelPath
                                            placeholderText: "Whisper model path, e.g. /path/to/ggml-model.bin"
                                        }
                                    }
                                }
                            }

                            Panel {
                                Layout.fillWidth: true
                                Layout.preferredHeight: translationModel.currentValue === "local/translator" ? 274 : 190

                                ColumnLayout {
                                    anchors.fill: parent
                                    anchors.margins: 22
                                    spacing: 12
                                    Text {
                                        text: "Translation"
                                        color: "#0f172a"
                                        font.pixelSize: 16
                                        font.weight: Font.DemiBold
                                    }
                                    RowLayout {
                                        Layout.fillWidth: true
                                        spacing: 14
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            Text { text: "Model"; color: "#475569"; font.pixelSize: 12 }
                                            ComboBox {
                                                id: translationModel
                                                Layout.fillWidth: true
                                                model: appController.translationModels
                                                textRole: "label"
                                                valueRole: "value"
                                                Component.onCompleted: {
                                                    for (let index = 0; index < model.length; index++) {
                                                        if (model[index].value === appController.selectedTranslationModel) {
                                                            currentIndex = index
                                                            break
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                        ColumnLayout {
                                            Layout.fillWidth: true
                                            visible: translationModel.currentValue !== "local/translator"
                                            Text { text: "API key"; color: "#475569"; font.pixelSize: 12 }
                                            TextField {
                                                id: translationKey
                                                Layout.fillWidth: true
                                                text: appController.translationApiKey
                                                echoMode: TextInput.Password
                                                placeholderText: "Not required for a local translator"
                                            }
                                        }
                                    }

                                    ColumnLayout {
                                        Layout.fillWidth: true
                                        visible: translationModel.currentValue === "local/translator"
                                        spacing: 7

                                        Text {
                                            text: "Local translator setup"
                                            color: "#475569"
                                            font.pixelSize: 12
                                            font.weight: Font.DemiBold
                                        }
                                        Text {
                                            text: "Enter the GGUF model file used by the local translator."
                                            color: "#64748b"
                                            font.pixelSize: 11
                                        }
                                        TextField {
                                            id: localTranslatorModelPath
                                            Layout.fillWidth: true
                                            text: appController.localTranslatorModelPath
                                            placeholderText: "GGUF model path, e.g. /path/to/model.gguf"
                                        }
                                    }
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Text {
                                    text: appController.settingsStatus
                                    color: "#0f766e"
                                    font.pixelSize: 12
                                }
                                Item { Layout.fillWidth: true }
                                AppButton {
                                    text: "Save settings"
                                    onClicked: appController.saveSettings(
                                        transcriptionModel.currentValue,
                                        transcriptionKey.text,
                                        translationModel.currentValue,
                                        translationKey.text,
                                        localWhisperCliPath.text,
                                        localWhisperModelPath.text,
                                        localTranslatorModelPath.text
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Popup {
        id: notification
        x: root.width - width - 28
        y: root.height - height - 28
        width: Math.min(360, notificationText.implicitWidth + 38)
        height: 52
        padding: 0
        closePolicy: Popup.NoAutoClose

        background: Rectangle {
            radius: 12
            color: "#0f172a"
            border.color: "#334155"
        }

        contentItem: Text {
            id: notificationText
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            verticalAlignment: Text.AlignVCenter
            color: "#f8fafc"
            font.pixelSize: 13
            elide: Text.ElideRight
        }
    }

    Timer {
        id: notificationTimer
        interval: 3200
        onTriggered: notification.close()
    }

    Connections {
        target: appController
        function onNotificationRequested(message) {
            notificationText.text = message
            notification.open()
            notificationTimer.restart()
        }
    }
}
