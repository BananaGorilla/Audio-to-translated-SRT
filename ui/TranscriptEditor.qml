import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: editor
    required property var editorModel
    objectName: "transcriptBoundaryEditor"

    function commitEdit() {
        if (!editDialog.opened)
            return true
        if (!editorModel.updateText(editDialog.selectedRowId, draft.text))
            return false
        editDialog.close()
        return true
    }

    Shortcut {
        sequences: [StandardKey.Undo]
        enabled: editor.visible && editor.enabled && !editDialog.opened && !timingDialog.opened
                 && editor.editorModel.canUndo
        onActivated: editor.editorModel.undo()
    }
    Shortcut {
        sequences: [StandardKey.Redo]
        enabled: editor.visible && editor.enabled && !editDialog.opened && !timingDialog.opened
                 && editor.editorModel.canRedo
        onActivated: editor.editorModel.redo()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: "Drag the first word up, or the last word down."
                wrapMode: Text.Wrap
                color: "#475569"
                font.pixelSize: 12
            }
            Button {
                objectName: "undoTranscriptEdit"
                text: "Undo"
                enabled: editor.editorModel.canUndo
                onClicked: editor.editorModel.undo()
            }
            Button {
                objectName: "redoTranscriptEdit"
                text: "Redo"
                enabled: editor.editorModel.canRedo
                onClicked: editor.editorModel.redo()
            }
        }

        Label {
            Layout.fillWidth: true
            visible: text.length > 0
            text: editor.editorModel.errorMessage
            color: "#b91c1c"
            wrapMode: Text.Wrap
        }

        ListView {
            id: rows
            property real savedContentY: 0
            objectName: "transcriptRows"
            Layout.fillWidth: true
            Layout.fillHeight: true
            model: editor.editorModel
            spacing: 10
            clip: true
            boundsBehavior: Flickable.StopAtBounds
            ScrollBar.vertical: ScrollBar { }

            delegate: Rectangle {
                id: card
                required property int index
                required property string rowId
                required property string rowText
                required property string timestamp
                required property var wordTokens
                objectName: "transcriptRow_" + index
                width: rows.width - 14
                height: contents.implicitHeight + 24
                radius: 8
                color: dropZone.containsDrag ? "#ecfdf5" : "#f8fafc"
                border.color: dropZone.containsDrag ? "#059669" : "#cbd5e1"
                border.width: dropZone.containsDrag ? 2 : 1

                DropArea {
                    id: dropZone
                    anchors.fill: parent
                    keys: ["transcript-boundary-word"]
                    onEntered: function(event) {
                        event.accepted = !!event.source && editor.editorModel.canDrop(
                            event.source.sourceRowId, event.source.wordEdge, card.rowId)
                    }
                    onDropped: function(event) {
                        if (!event.source || !editor.editorModel.canDrop(
                                event.source.sourceRowId, event.source.wordEdge, card.rowId)) {
                            event.accepted = false
                            return
                        }
                        const sourceId = event.source.sourceRowId
                        const edge = event.source.wordEdge
                        const targetId = card.rowId
                        event.accept(Qt.MoveAction)
                        // Resetting the model destroys delegates. Finish the
                        // drag event before applying the mutation.
                        Qt.callLater(function() {
                            editor.editorModel.moveBoundaryWord(sourceId, edge, targetId)
                        })
                    }
                }

                ColumnLayout {
                    id: contents
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: "[" + card.timestamp + "]"
                            font.family: "Menlo"
                            color: "#475569"
                        }
                        Item { Layout.fillWidth: true }
                        ToolButton {
                            objectName: "moveFirstUp_" + card.index
                            text: "First word ↑"
                            enabled: card.index > 0
                            onClicked: editor.editorModel.moveFirstWordUp(card.rowId)
                        }
                        ToolButton {
                            objectName: "moveLastDown_" + card.index
                            text: "Last word ↓"
                            enabled: card.index < editor.editorModel.count - 1
                            onClicked: editor.editorModel.moveLastWordDown(card.rowId)
                        }
                        Button {
                            objectName: "editRow_" + card.index
                            text: "Edit / Split"
                            onClicked: {
                                editDialog.selectedRowId = card.rowId
                                draft.text = card.rowText
                                editDialog.open()
                                draft.forceActiveFocus()
                            }
                        }
                    }

                    Flow {
                        Layout.fillWidth: true
                        spacing: 2
                        Repeater {
                            model: card.wordTokens
                            TranscriptWord {
                                required property int index
                                required property var modelData
                                objectName: "word_" + card.index + "_" + index
                                word: modelData
                                sourceRowId: card.rowId
                                wordEdge: card.wordTokens.length === 1 ? "both"
                                          : index === 0 ? "first" : "last"
                                movable: (index === 0 && card.index > 0)
                                         || (index === card.wordTokens.length - 1
                                             && card.index < editor.editorModel.count - 1)
                                dragLayer: overlay
                            }
                        }
                    }
                }
            }
        }
    }

    Item {
        id: overlay
        anchors.fill: parent
        z: 100
        property Item activeProxy: null
        Timer {
            interval: 16
            running: overlay.activeProxy !== null
            repeat: true
            onTriggered: {
                const proxy = overlay.activeProxy
                if (!proxy)
                    return
                const point = rows.mapFromItem(overlay, proxy.x, proxy.y + proxy.height / 2)
                const speed = point.y < 32 ? -8 : point.y > rows.height - 32 ? 8 : 0
                if (speed !== 0)
                    rows.contentY = Math.max(0, Math.min(rows.contentY + speed,
                                                       rows.contentHeight - rows.height))
            }
        }
    }

    Dialog {
        id: editDialog
        objectName: "transcriptEditDialog"
        property string selectedRowId: ""
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(640, editor.width)
        title: "Edit transcript line"
        modal: true
        closePolicy: Popup.CloseOnEscape

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: "Correct the text, or place the cursor between words and choose Split here."
                wrapMode: Text.Wrap
            }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 160
                TextArea {
                    id: draft
                    objectName: "transcriptDraft"
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    textFormat: TextEdit.PlainText
                }
            }
            Label {
                Layout.fillWidth: true
                visible: text.length > 0
                text: editor.editorModel.errorMessage
                color: "#b91c1c"
                wrapMode: Text.Wrap
            }
        }
        footer: DialogButtonBox {
            Button {
                text: "Cancel"
                onClicked: editDialog.close()
            }
            Button {
                objectName: "splitTranscriptRow"
                text: "Split here"
                onClicked: {
                    if (editor.editorModel.splitEditedRow(
                            editDialog.selectedRowId, draft.text, draft.cursorPosition))
                        editDialog.close()
                }
            }
            Button {
                objectName: "saveTranscriptChanges"
                text: "Save changes"
                onClicked: editor.commitEdit()
            }
        }
    }

    Dialog {
        id: timingDialog
        objectName: "transcriptTimingDialog"
        parent: Overlay.overlay
        anchors.centerIn: parent
        width: Math.min(480, editor.width)
        title: "Choose the boundary time"
        modal: true
        closePolicy: Popup.CloseOnEscape
        onRejected: editor.editorModel.cancelTiming()

        contentItem: ColumnLayout {
            spacing: 12
            Label {
                Layout.fillWidth: true
                text: "The edited words have no reliable timing at this boundary. Enter seconds or m:ss.sss between "
                      + Number(editor.editorModel.pendingTiming.minimum || 0).toFixed(3)
                      + " and " + Number(editor.editorModel.pendingTiming.maximum || 0).toFixed(3) + " seconds."
                wrapMode: Text.Wrap
            }
            TextField {
                id: boundaryTime
                objectName: "transcriptBoundaryTime"
                Layout.fillWidth: true
                placeholderText: "For example: 1:05.250"
            }
            Label {
                Layout.fillWidth: true
                text: editor.editorModel.errorMessage
                color: "#b91c1c"
                wrapMode: Text.Wrap
            }
        }
        footer: DialogButtonBox {
            Button {
                objectName: "cancelTranscriptTiming"
                text: "Cancel"
                onClicked: {
                    editor.editorModel.cancelTiming()
                    timingDialog.close()
                }
            }
            Button {
                objectName: "applyTranscriptTiming"
                text: "Apply time"
                onClicked: {
                    if (editor.editorModel.resolveTiming(boundaryTime.text))
                        timingDialog.close()
                }
            }
        }
    }

    Connections {
        target: editor.editorModel
        function onModelAboutToBeReset() {
            rows.savedContentY = rows.contentY
        }
        function onModelReset() {
            Qt.callLater(function() {
                rows.contentY = Math.max(0, Math.min(rows.savedContentY,
                                                   rows.contentHeight - rows.height))
            })
        }
        function onPendingChanged() {
            if (!editor.editorModel.pendingTiming.kind && timingDialog.opened)
                timingDialog.close()
        }
        function onTimingRequested() {
            editDialog.close()
            boundaryTime.text = ""
            timingDialog.open()
            boundaryTime.forceActiveFocus()
        }
    }
}
