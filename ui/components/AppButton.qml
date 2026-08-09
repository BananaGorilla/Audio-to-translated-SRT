import QtQuick
import QtQuick.Controls

Button {
    id: control

    property color fillColor: "#2563eb"
    property color hoverColor: "#1d4ed8"
    property color pressedColor: "#1e40af"
    property color textColor: "#ffffff"

    implicitHeight: 44
    implicitWidth: Math.max(120, contentItem.implicitWidth + 32)
    leftPadding: 16
    rightPadding: 16

    contentItem: Text {
        text: control.text
        color: control.enabled ? control.textColor : "#94a3b8"
        font.pixelSize: 14
        font.weight: Font.DemiBold
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        radius: 10
        color: {
            if (!control.enabled)
                return "#e2e8f0"
            if (control.down)
                return control.pressedColor
            if (control.hovered)
                return control.hoverColor
            return control.fillColor
        }
    }
}
