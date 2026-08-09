import QtQuick
import QtQuick.Controls

Rectangle {
    id: root

    property string text: "Ready"
    property bool busy: false

    implicitHeight: 34
    implicitWidth: content.implicitWidth + 24
    radius: 17
    color: busy ? "#eff6ff" : "#f1f5f9"
    border.color: busy ? "#bfdbfe" : "#e2e8f0"

    Row {
        id: content
        anchors.centerIn: parent
        spacing: 8

        BusyIndicator {
            anchors.verticalCenter: parent.verticalCenter
            width: 18
            height: 18
            running: root.busy
            visible: root.busy
        }

        Rectangle {
            anchors.verticalCenter: parent.verticalCenter
            width: 7
            height: 7
            radius: 4
            color: "#22c55e"
            visible: !root.busy
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: root.text
            color: "#334155"
            font.pixelSize: 12
            font.weight: Font.Medium
        }
    }
}
