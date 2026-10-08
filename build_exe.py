"""Build a standalone windowed exe for the pet.

    python build_exe.py

Produces dist/NaiWaPet.exe on Windows (run the same way for onedir builds on
other platforms by dropping --onefile).
"""
import os
import sys

from PyInstaller.__main__ import run

HERE = os.path.dirname(os.path.abspath(__file__))

# The Qt wheel ships every module; the pet only touches QtCore/Gui/Widgets.
EXCLUDES = [
    "QtWebEngineCore", "QtWebEngineWidgets", "QtWebEngineQuick", "QtWebChannel",
    "QtWebSockets", "QtQml", "QtQuick", "QtQuick3D", "QtQuickWidgets",
    "QtQuickEffects", "Qt3DCore", "Qt3DRender", "Qt3DExtras", "QtCharts",
    "QtDataVisualization", "QtGraphs", "QtLocation", "QtPositioning",
    "QtMultimedia", "QtMultimediaWidgets", "QtSpatialAudio", "QtNfc",
    "QtBluetooth", "QtScxml", "QtSensors", "QtSerialPort", "QtSerialBus",
    "QtRemoteObjects", "QtTest", "QtPdf", "QtPdfWidgets", "QtPdfQuick",
    "QtHelp", "QtDesigner", "QtUiTools", "QtTextToSpeech", "QtStateMachine",
    "QtHttpServer", "QtLogin", "QtGrpc",
]


def main():
    args = [
        os.path.join(HERE, "pet.py"),
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", "NaiWaPet",
        "--distpath", os.path.join(HERE, "dist"),
        "--workpath", os.path.join(HERE, "build"),
        "--specpath", HERE,
        "--add-data", os.path.join(HERE, "sprites") + os.pathsep + "sprites",
    ]
    args += ["--exclude-module", "tkinter"]
    for mod in EXCLUDES:
        args += ["--exclude-module", "PySide6." + mod]

    run(args)

    exe = os.path.join(HERE, "dist", "NaiWaPet.exe" if sys.platform == "win32" else "NaiWaPet")
    if os.path.exists(exe):
        print("\nOK  %s  %.1f MB" % (exe, os.path.getsize(exe) / 1048576))
    else:
        raise SystemExit("\nbuild produced no executable at " + exe)


if __name__ == "__main__":
    main()
