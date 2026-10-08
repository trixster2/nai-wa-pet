"""奶蛙桌宠 — a transparent desktop pet.

    python pet.py            # run

Depends on PySide6 only. Windows / macOS / Linux.

    pip install PySide6
"""
import math
import os
import random
import sys

from PySide6.QtCore import Qt, QTimer, QPoint, QRectF
from PySide6.QtGui import QCursor, QGuiApplication, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QWidget

def _root():
    """PyInstaller unpacks bundled data next to the interpreter, not next to this file."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


HERE = _root()
SPRITES = os.path.join(HERE, "sprites")

FPS_MS = 33
SCALE_STEPS = {"小": 0.75, "中": 1.0, "大": 1.35}


def load(name):
    path = os.path.join(SPRITES, name)
    if os.path.exists(path):
        return QPixmap(path)
    return None


class Pet(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.front = load("idle.png")
        self.blink = load("blink.png") or self.front
        self.side = load("turn_b.png") or self.front
        self.base_w = self.front.width()
        self.base_h = self.front.height()

        self.scale = 1.0
        self.t = 0.0
        self.mode = "idle"          # idle | walk | drag | react
        self.facing = 1
        self.vx = 0.0
        self.react = 0.0
        self.drag_tilt = 0.0
        self.grab = QPoint()
        self.press_at = QPoint()
        self.moved = 0
        self.next_blink = random.uniform(2.0, 5.0)
        self.blink_left = 0.0
        self.idle_until = random.uniform(3.0, 9.0)

        self._resize()
        self._place_bottom_right()

        self.clock = QTimer(self)
        self.clock.setTimerType(Qt.PreciseTimer)
        self.clock.timeout.connect(self._tick)
        self.clock.start(FPS_MS)

    # ---------- geometry ----------

    def _screen(self):
        return QGuiApplication.primaryScreen().availableGeometry()

    def _resize(self):
        w = int(self.base_w * self.scale)
        h = int(self.base_h * self.scale)
        pad = int(self.base_h * self.scale * 0.18)
        self.canvas = (w + pad * 2, h + pad * 2)
        self.setFixedSize(*self.canvas)
        self.update()

    def _place_bottom_right(self):
        s = self._screen()
        self.move(s.right() - self.width() - 60, s.bottom() - self.height() + int(self.height() * 0.14))

    def _feet_y(self):
        return self._screen().bottom() - self.height() + int(self.height() * 0.14)

    # ---------- animation ----------

    def _tick(self):
        dt = FPS_MS / 1000.0
        self.t += dt

        if self.blink_left > 0:
            self.blink_left -= dt
        elif self.t > self.next_blink:
            self.blink_left = 0.13
            self.next_blink = self.t + random.uniform(2.4, 6.5)

        if self.react > 0:
            self.react = max(0.0, self.react - dt)

        if self.mode == "walk":
            s = self._screen()
            self.vx = 62.0 * self.facing
            x = self.x() + self.vx * dt
            if x <= s.left():
                x, self.facing = s.left(), 1
            elif x + self.width() >= s.right():
                x, self.facing = s.right() - self.width(), -1
            # After being dropped mid-air, ease back down instead of teleporting.
            ground = self._feet_y()
            y = self.y() + (ground - self.y()) * min(1.0, dt * 6.0)
            if abs(y - ground) < 1.0:
                y = ground
            self.move(int(round(x)), int(round(y)))
        elif self.mode == "idle":
            self.idle_until -= dt
            if self.idle_until <= 0:
                self.mode = "walk"
                self.facing = random.choice((1, -1))
                self.walk_for = random.uniform(2.5, 7.0)
                self.idle_until = random.uniform(4.0, 12.0)

        if self.mode == "walk":
            self.walk_for -= dt
            if self.walk_for <= 0:
                self.mode = "idle"

        if self.mode == "drag":
            self.drag_tilt *= 0.86

        self.update()

    def _transform(self):
        """Return (scale_x, scale_y, degrees, dy) for the current frame."""
        walking = self.mode == "walk"
        sy = 1.0 + math.sin(self.t * 2.4) * 0.014
        sx = 1.0 - math.sin(self.t * 2.4) * 0.010
        deg = math.sin(self.t * 0.95) * 1.8
        dy = 0.0

        if walking:
            w = self.t * 9.5
            dy = -abs(math.sin(w)) * 4.0 * self.scale
            deg = math.sin(w) * 4.2 * self.facing
            sy *= 1.0 + math.sin(w * 2) * 0.02
        if self.mode == "drag":
            deg = self.drag_tilt
            sy *= 1.04
            sx *= 0.97
        if self.react > 0:
            k = self.react / 0.45
            wob = math.sin(k * math.pi * 3.0) * (k ** 0.6)
            sy *= 1.0 - wob * 0.16
            sx *= 1.0 + wob * 0.13
            dy -= wob * 10.0 * self.scale
        return sx, sy, deg, dy

    # ---------- painting ----------

    def paintEvent(self, _):
        art = self.blink if self.blink_left > 0 else self.front
        if self.mode == "walk":
            art = self.side
        w, h = self.canvas
        p = QPainter(self)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.setRenderHint(QPainter.Antialiasing)

        sx, sy, deg, dy = self._transform()
        dw, dh = int(art.width() * self.scale), int(art.height() * self.scale)
        cx, cy = w / 2, h - dh / 2 - int(self.base_h * self.scale * 0.06) + dy

        p.translate(cx, cy)
        p.rotate(deg)
        p.scale(sx * self.facing, sy)
        p.drawPixmap(QRectF(-dw / 2, -dh / 2, dw, dh), art, QRectF(0, 0, art.width(), art.height()))
        p.end()

    # ---------- interaction ----------

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.grab = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.press_at = e.globalPosition().toPoint()
            self.moved = 0
            self.prev_x = e.globalPosition().x()
            self.mode = "drag"
        elif e.button() == Qt.RightButton:
            self._menu()

    def mouseMoveEvent(self, e):
        if self.mode != "drag":
            return
        gp = e.globalPosition().toPoint()
        self.moved = max(self.moved, (gp - self.press_at).manhattanLength())
        speed = e.globalPosition().x() - self.prev_x
        self.prev_x = e.globalPosition().x()
        self.drag_tilt = max(-13.0, min(13.0, self.drag_tilt * 0.6 + speed * 0.35))
        self.move(gp - self.grab)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        if self.moved < 6:
            self.react = 0.45
            self.mode = "idle"
        else:
            self.mode = "idle"
            self.facing = 1 if self.drag_tilt < 0 else -1
        self.drag_tilt = 0.0

    def _menu(self):
        m = QMenu(self)
        m.addAction("走动", lambda: self._set_mode("walk"))
        m.addAction("停下", lambda: self._set_mode("idle"))
        m.addSeparator()
        size_menu = m.addMenu("大小")
        for label, value in SCALE_STEPS.items():
            act = size_menu.addAction(label)
            act.setCheckable(True)
            act.setChecked(abs(self.scale - value) < 0.01)
            act.triggered.connect(lambda _=False, v=value: self._set_scale(v))
        m.addSeparator()
        m.addAction("回到右下角", self._place_bottom_right)
        m.addAction("退出", QApplication.instance().quit)
        m.exec(QCursor.pos())

    def _set_mode(self, mode):
        self.mode = mode
        if mode == "walk":
            self.walk_for = random.uniform(3.0, 8.0)

    def _set_scale(self, value):
        anchor = self.mapToGlobal(QPoint(self.width() // 2, self.height()))
        self.scale = value
        self._resize()
        self.move(anchor.x() - self.width() // 2, anchor.y() - self.height())


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("奶蛙桌宠")
    missing = [n for n in ("idle.png",) if not os.path.exists(os.path.join(SPRITES, n))]
    if missing:
        if getattr(sys, "frozen", False):
            raise SystemExit("安装包内缺少素材 %s，包不完整" % ", ".join(missing))
        raise SystemExit("缺少素材 %s —— 先运行 python make_sprites.py" % ", ".join(missing))
    pet = Pet()
    pet.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
