import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: "#0C111C"
    border.color: "#1E293B"
    border.width: 1
    radius: 8
    height: 44

    property string channelName: "Kein Sender aktiv"
    property string codecText: "Codec: —"
    property string bitrateText: "Bitrate: —"
    property string bufferText: "Buffer: Direct"
    property bool isLive: false

    Row {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 14

        Rectangle {
            width: 10
            height: 10
            radius: 5
            anchors.verticalCenter: parent.verticalCenter
            color: root.isLive ? "#10B981" : "#64748B"

            SequentialAnimation on opacity {
                running: root.isLive
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 0.35; duration: 750 }
                NumberAnimation { from: 0.35; to: 1.0; duration: 750 }
            }
        }

        Text {
            text: root.channelName
            color: "#F8FAFC"
            font.pixelSize: 13
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: root.codecText
            color: "#06B6D4"
            font.pixelSize: 12
            font.family: "Consolas"
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: root.bitrateText
            color: "#10B981"
            font.pixelSize: 12
            font.family: "Consolas"
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: root.bufferText
            color: "#818CF8"
            font.pixelSize: 12
            font.family: "Consolas"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
