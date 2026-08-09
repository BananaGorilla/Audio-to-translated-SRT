import QtQuick
import QtQuick.Controls

Button {
    id: control

    property bool selected: false

    implicitHeight: 46
    leftPadding: 16
    rightPadding: 14

    contentItem: Row {
        spacing: 12

        Rectangle {
            width: 8
            height: 8
            radius: 4
            anchors.verticalCenter: parent.verticalCenter
            color: control.selected ? "#60a5fa" : "#64748b"
        }

        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: control.text
            color: control.selected ? "#ffffff" : "#cbd5e1"
            font.pixelSize: 14
            font.weight: control.selected ? Font.DemiBold : Font.Normal
        }
    }

    background: Rectangle {
        radius: 10
        color: control.selected ? "#1e3a5f" : (control.hovered ? "#172b45" : "transparent")
    }
}
