import QtQuick 2.15

Rectangle {
    id: scannerDash
    color: "#101726"
    border.color: "#1E293B"
    border.width: 1
    radius: 8
    height: 54

    property int checkedCount: 0
    property int totalCount: 0
    property int hitsCount: 0
    property int hotCount: 0
    property string speedText: "0.0 MAC/s"
    property string etaText: "ETA: —"
    property bool scanning: false

    Row {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 20

        Rectangle {
            width: 12
            height: 12
            radius: 6
            anchors.verticalCenter: parent.verticalCenter
            color: scannerDash.scanning ? "#06B6D4" : "#475569"

            SequentialAnimation on scale {
                running: scannerDash.scanning
                loops: Animation.Infinite
                NumberAnimation { from: 1.0; to: 1.35; duration: 600 }
                NumberAnimation { from: 1.35; to: 1.0; duration: 600 }
            }
        }

        Text {
            text: "Geprüft: " + scannerDash.checkedCount + " / " + scannerDash.totalCount
            color: "#F8FAFC"
            font.pixelSize: 13
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: "🔥 Hot: " + scannerDash.hotCount
            color: "#10B981"
            font.pixelSize: 13
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: "✅ Hits: " + scannerDash.hitsCount
            color: "#F59E0B"
            font.pixelSize: 13
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            text: "⚡ " + scannerDash.speedText + "  |  " + scannerDash.etaText
            color: "#38BDF8"
            font.pixelSize: 12
            font.family: "Consolas"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
