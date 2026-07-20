import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2

import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami
import org.kde.plasma.plasma5support as Plasma5Support

PlasmoidItem {
    id: root

    readonly property string serviceName: "edp-blank.service"

    property bool serviceActive: false
    property string backlightState: i18n("N/A")
    property string hdmiState: i18n("N/A")
    property string soundbarState: i18n("N/A")

    readonly property string cmdStatus: "systemctl --user is-active " + serviceName
    readonly property string cmdStart: "systemctl --user start " + serviceName
    readonly property string cmdStop: "systemctl --user stop " + serviceName
    readonly property string cmdBacklight: "bash -c \"cat /sys/class/backlight/*/brightness 2>/dev/null | head -n1\""
    readonly property string cmdHdmi: "bash -c \"xrandr --query 2>/dev/null | grep HDMI\""
    readonly property string cmdSoundbar: "bash -c \"pactl list short sinks 2>/dev/null\""

    // A tényleges kijelző-profilváltást a monitor-config projekt (main.py) végzi,
    // a widget csak meghívja azt --apply-jal — a kapcsolási logika ott marad egy helyen.
    readonly property string monitorConfigPython: "/home/szaboger/Projects/Kijelzo/.venv/bin/python"
    readonly property string monitorConfigMain: "/home/szaboger/Projects/Kijelzo/main.py"

    readonly property var profileButtons: [
        { name: "Laptop (csak)", label: i18n("💻  Laptop (csak)") },
        { name: "Laptop + Soundbar", label: i18n("💻 🔊  Laptop + Soundbar") },
        { name: "Laptop + TV + Soundbar", label: i18n("💻 📺 🔊  Laptop + TV + Soundbar") }
    ]

    function applyProfileCommand(profileName) {
        return monitorConfigPython + " " + monitorConfigMain + " --apply \"" + profileName + "\"";
    }

    readonly property string cmdCurrentProfile: monitorConfigPython + " " + monitorConfigMain + " --status"
    property string currentProfileName: i18n("Lekérdezés…")

    Plasmoid.icon: "video-display"
    Plasmoid.status: serviceActive ? PlasmaCore.Types.ActiveStatus : PlasmaCore.Types.PassiveStatus

    toolTipMainText: currentProfileName
    toolTipSubText: i18n("eDP elsötétítés: %1\neDP: %2  ·  HDMI: %3  ·  Soundbar: %4",
        serviceActive ? i18n("AKTÍV") : i18n("INAKTÍV"), backlightState, hdmiState, soundbarState)

    switchWidth: Kirigami.Units.gridUnit * 14
    switchHeight: Kirigami.Units.gridUnit * 14

    Plasma5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []

        onNewData: (sourceName, data) => {
            const out = (data["stdout"] || "").toString().trim();

            if (sourceName === root.cmdStatus) {
                root.serviceActive = (out === "active");
            } else if (sourceName === root.cmdBacklight) {
                root.backlightState = out === ""
                    ? i18n("N/A")
                    : (parseInt(out, 10) === 0 ? i18n("Elsötétítve") : i18n("Aktív"));
            } else if (sourceName === root.cmdHdmi) {
                if (out === "") {
                    root.hdmiState = i18n("Nincs HDMI kimenet");
                } else if (out.indexOf(" connected") !== -1) {
                    root.hdmiState = i18n("Aktív");
                } else {
                    root.hdmiState = i18n("Lecsatlakoztatva");
                }
            } else if (sourceName === root.cmdSoundbar) {
                root.soundbarState = out.indexOf("RUNNING") !== -1
                    ? i18n("Aktív (lejátszás)")
                    : i18n("Üresjárat / felfüggesztve");
            } else if (sourceName === root.cmdStart || sourceName === root.cmdStop) {
                root.refreshStatus();
            } else if (sourceName === root.cmdCurrentProfile) {
                root.currentProfileName = out === "" ? i18n("ismeretlen") : out;
            } else if (sourceName.indexOf(root.monitorConfigPython) === 0) {
                root.profileBusy = false;
                root.refreshStatus();
            }

            disconnectSource(sourceName);
        }

        function exec(cmd) {
            connectSource(cmd);
        }
    }

    property bool profileBusy: false

    function refreshStatus() {
        executable.exec(cmdStatus);
        executable.exec(cmdBacklight);
        executable.exec(cmdHdmi);
        executable.exec(cmdSoundbar);
        executable.exec(cmdCurrentProfile);
    }

    function startService() {
        executable.exec(cmdStart);
    }

    function stopService() {
        executable.exec(cmdStop);
    }

    function applyProfile(profileName) {
        // A monitor-config a profilváltás után újraindítja a plasmashell-t,
        // emiatt ez a popup is bezáródhat egy pillanatra a váltás közben.
        profileBusy = true;
        executable.exec(applyProfileCommand(profileName));
    }

    Timer {
        interval: 5000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.refreshStatus()
    }

    compactRepresentation: MouseArea {
        id: compactMouseArea
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded

        Kirigami.Icon {
            anchors.fill: parent
            source: Plasmoid.icon
            active: compactMouseArea.containsMouse
        }
    }

    fullRepresentation: ColumnLayout {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 16
        Layout.maximumWidth: Kirigami.Units.gridUnit * 24
        Layout.minimumHeight: implicitHeight

        spacing: Kirigami.Units.smallSpacing

        PlasmaExtras.Heading {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            level: 3
            text: i18n("Laptop kijelző energiakezelés")
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: Kirigami.Units.smallSpacing
            Layout.rightMargin: Kirigami.Units.smallSpacing

            QQC2.Label {
                text: i18n("Jelenlegi profil:")
                opacity: 0.7
            }
            QQC2.Label {
                Layout.fillWidth: true
                text: root.currentProfileName
                font.bold: true
                elide: Text.ElideRight
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing

            QQC2.Label {
                Layout.fillWidth: true
                text: i18n("Automatikus elsötétítés idle esetén")
            }

            PlasmaComponents3.Switch {
                checked: root.serviceActive
                onToggled: checked ? root.startService() : root.stopService()
            }
        }

        Kirigami.Separator {
            Layout.fillWidth: true
        }

        GridLayout {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            columns: 2
            columnSpacing: Kirigami.Units.largeSpacing
            rowSpacing: Kirigami.Units.smallSpacing

            QQC2.Label {
                text: i18n("Szolgáltatás:")
                opacity: 0.7
            }
            QQC2.Label {
                text: root.serviceActive ? i18n("AKTÍV") : i18n("INAKTÍV")
                color: root.serviceActive ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.negativeTextColor
                font.bold: true
            }

            QQC2.Label {
                text: i18n("eDP panel:")
                opacity: 0.7
            }
            QQC2.Label {
                text: root.backlightState
            }

            QQC2.Label {
                text: i18n("HDMI kimenet:")
                opacity: 0.7
            }
            QQC2.Label {
                text: root.hdmiState
            }

            QQC2.Label {
                text: i18n("Soundbar:")
                opacity: 0.7
            }
            QQC2.Label {
                text: root.soundbarState
            }
        }

        PlasmaComponents3.ToolButton {
            Layout.alignment: Qt.AlignRight
            Layout.margins: Kirigami.Units.smallSpacing
            icon.name: "view-refresh"
            text: i18n("Frissítés")
            onClicked: root.refreshStatus()
        }

        Kirigami.Separator {
            Layout.fillWidth: true
        }

        PlasmaExtras.Heading {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            level: 4
            text: i18n("Kijelző-profilok")
        }

        Repeater {
            model: root.profileButtons

            delegate: PlasmaComponents3.Button {
                Layout.fillWidth: true
                Layout.leftMargin: Kirigami.Units.smallSpacing
                Layout.rightMargin: Kirigami.Units.smallSpacing
                text: modelData.label
                enabled: !root.profileBusy
                onClicked: root.applyProfile(modelData.name)
            }
        }

        QQC2.Label {
            Layout.fillWidth: true
            Layout.margins: Kirigami.Units.smallSpacing
            visible: root.profileBusy
            opacity: 0.7
            font.italic: true
            text: i18n("Profil alkalmazása… (a plasmashell röviden újraindul)")
            wrapMode: Text.WordWrap
        }
    }

    Component.onCompleted: refreshStatus()
}
