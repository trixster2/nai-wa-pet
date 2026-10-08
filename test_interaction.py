"""Synthetic interaction check for pet.py — no real cursor involved.

    python test_interaction.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import pet

fails = []


def check(label, got, want):
    ok = got == want
    print("%-26s %s   (%r)" % (label, "PASS" if ok else "FAIL", got))
    if not ok:
        fails.append(label)


app = QApplication(sys.argv)
p = pet.Pet()
p.show()

check("startup mode", p.mode, "idle")
start = p.pos()

QTest.mousePress(p, Qt.LeftButton, Qt.NoModifier, QPoint(p.width() // 2, p.height() - 30))
check("press enters drag", p.mode, "drag")

QTest.mouseMove(p, QPoint(p.width() // 2 - 120, p.height() - 160))
p._tick()
moved = p.pos()
check("drag moves window", moved != start, True)

QTest.mouseRelease(p, Qt.LeftButton, Qt.NoModifier, QPoint(p.width() // 2 - 120, p.height() - 160))
check("release leaves drag", p.mode, "idle")

before = p.react
QTest.mousePress(p, Qt.LeftButton, Qt.NoModifier, QPoint(p.width() // 2, p.height() - 30))
QTest.mouseRelease(p, Qt.LeftButton, Qt.NoModifier, QPoint(p.width() // 2, p.height() - 30))
check("tap triggers react", p.react > 0 and p.react != before, True)

p._set_mode("walk")
for _ in range(30):
    p._tick()
check("walk keeps facing", p.facing in (1, -1), True)

p._set_scale(pet.SCALE_STEPS["大"])
check("resize grows canvas", p.width() > 0 and p.height() > 0, True)
big = p.height()
p._set_scale(pet.SCALE_STEPS["小"])
check("small < large", p.height() < big, True)

for frames in range(40):
    p._tick()
check("still alive after 40 ticks", p.t > 1.0, True)

print()
print("FAILURES:", fails if fails else "none")
sys.exit(1 if fails else 0)
