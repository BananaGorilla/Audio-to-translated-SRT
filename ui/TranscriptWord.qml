import QtQuick
import QtQuick.Controls

Rectangle {
    id: token

    required property var word
    required property string sourceRowId
    required property string wordEdge
    required property Item dragLayer
    property bool movable: false

    width: label.implicitWidth + 12
    height: 32
    radius: 5
    color: movable ? (mouse.containsMouse ? "#bfdbfe" : "#dbeafe") : "transparent"
    border.color: movable ? "#93c5fd" : "transparent"
    opacity: mouse.drag.active ? 0.45 : 1

    Text {
        id: label
        anchors.centerIn: parent
        text: token.word.separator + token.word.text
        textFormat: Text.PlainText
        color: "#1e293b"
        font.pixelSize: 14
    }

    ToolTip.visible: mouse.containsMouse && token.movable
    ToolTip.delay: 500
    ToolTip.text: token.wordEdge === "both" ? "Drag to either neighboring line"
                 : token.wordEdge === "first" ? "Drag to the end of the previous line"
                 : "Drag to the start of the next line"

    // The proxy lives above the clipped ListView; dragging never moves a card.
    Rectangle {
        id: proxy
        parent: token.dragLayer
        property string sourceRowId: token.sourceRowId
        property string wordEdge: token.wordEdge
        width: label.implicitWidth + 20
        height: 34
        radius: 6
        color: "#2563eb"
        visible: mouse.drag.active
        z: 100
        Drag.active: mouse.drag.active
        Drag.source: proxy
        Drag.keys: ["transcript-boundary-word"]
        Drag.hotSpot.x: width / 2
        Drag.hotSpot.y: height / 2
        Drag.supportedActions: Qt.MoveAction
        Text {
            anchors.centerIn: parent
            text: token.word.text
            textFormat: Text.PlainText
            color: "white"
            font.pixelSize: 14
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        enabled: token.movable
        hoverEnabled: true
        preventStealing: true
        cursorShape: drag.active ? Qt.ClosedHandCursor : Qt.OpenHandCursor
        drag.target: proxy
        drag.onActiveChanged: {
            token.dragLayer.activeProxy = drag.active ? proxy : null
        }
        onPressed: function(event) {
            const point = token.mapToItem(token.dragLayer, event.x, event.y)
            proxy.x = point.x - proxy.width / 2
            proxy.y = point.y - proxy.height / 2
        }
        onReleased: {
            if (drag.active)
                proxy.Drag.drop()
        }
    }
}
