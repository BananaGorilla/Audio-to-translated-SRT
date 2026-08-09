import QtQuick

Rectangle {
    id: root

    property string eyebrow: "WORKFLOW"
    property string title: "Feature"
    property string description: ""
    property string actionText: "Open"
    property color accentColor: "#2563eb"
    property bool available: true
    signal triggered()

    radius: 18
    color: "#ffffff"
    border.color: mouse.containsMouse ? root.accentColor : "#e2e8f0"
    border.width: 1

    Behavior on border.color {
        ColorAnimation { duration: 140 }
    }

    Column {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 12

        Rectangle {
            width: eyebrowText.implicitWidth + 16
            height: 26
            radius: 13
            color: Qt.alpha(root.accentColor, 0.1)

            Text {
                id: eyebrowText
                anchors.centerIn: parent
                text: root.eyebrow
                color: root.accentColor
                font.pixelSize: 10
                font.weight: Font.Bold
                font.letterSpacing: 0.8
            }
        }

        Text {
            width: parent.width
            text: root.title
            color: "#0f172a"
            font.pixelSize: 21
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }

        Text {
            width: parent.width
            text: root.description
            color: "#64748b"
            font.pixelSize: 13
            lineHeight: 1.35
            wrapMode: Text.WordWrap
        }

        Item { width: 1; height: 4 }

        Text {
            text: root.available ? root.actionText + "  →" : "Coming next"
            color: root.available ? root.accentColor : "#94a3b8"
            font.pixelSize: 13
            font.weight: Font.DemiBold
        }
    }

    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: root.available ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: {
            if (root.available)
                root.triggered()
        }
    }
}
