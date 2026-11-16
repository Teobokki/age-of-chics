"""AGE OF CHICS — standalone presentation app for the bundled deck.
©2026 EX Inc./HYPERION DIGITAL ©2026
"""
from __future__ import annotations

import json
import os
import re
import shutil
import ssl
import sys
import threading
import time
from urllib.request import Request, urlopen

APP = "AGE OF CHICS™ BY HYPERION"
APP_VERSION = "2.3.0"
COPYRIGHT = "\u00a92026 EX Inc./HYPERION DIGITAL \u00a92026"
REPO = "Teobokki/age-of-chics"
UPDATE_URL = "https://raw.githubusercontent.com/%s/main/latest.json" % REPO
SLIDE_COUNT = 7
DECK_PPTX = "AGE OF CHICS.pptx"
DECK_PDF = "AGE OF CHICS.pdf"

# Cinematic dark palette. Accent is the gold from the EX/H mark. No glow.
BG = "#0B0B0D"
PANEL = "#141416"
CARD = "#1B1B1E"
BORDER = "#2A2A2E"
TXT = "#F4F4F0"
MUT = "#9A9A94"
DIM = "#6E6E68"
ACC = "#F5A804"
ACC_DN = "#C48403"
DANGER = "#C44A3A"

from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QEvent, Signal, QObject, QEventLoop, QThread
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QAction, QFont, QKeySequence, QColor, QDesktopServices,
    QShortcut, QFontDatabase, QCursor,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QStackedWidget, QDialog, QProgressBar, QSizePolicy,
    QFrame, QScrollArea, QStatusBar, QMenuBar, QMenu,
)


def res_path(*parts):
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)


def load_app_icon():
    """Window / taskbar / exe icon: the character photo, never the in-app H emblem."""
    icon = QIcon()
    for s in (16, 32, 48, 64, 128, 256):
        path = res_path("assets", "appicon-%d.png" % s)
        if os.path.isfile(path):
            icon.addFile(path, QSize(s, s))
    ico = res_path("assets", "logo.ico")
    if os.path.isfile(ico):
        icon.addFile(ico)
    if icon.isNull():
        png = res_path("assets", "logo256.png")
        if os.path.isfile(png):
            icon.addFile(png)
    return icon


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v))[:4]) or (0,)


def is_wine():
    if os.name != "nt":
        return False
    try:
        import ctypes
        return hasattr(ctypes.windll.ntdll, "wine_get_version")
    except Exception:
        return False


def downloads_dir():
    home = os.path.expanduser("~")
    for key in ("USERPROFILE", "HOME"):
        if os.environ.get(key):
            home = os.environ[key]
            break
    d = os.path.join(home, "Downloads")
    return d if os.path.isdir(d) else home


def deck_file(name):
    return res_path("assets", "deck", name)


def slide_path(i):
    return deck_file("slide-%d.png" % i)


QSS = """
QWidget { background: %s; color: %s; font-family: 'Segoe UI', 'DejaVu Sans', sans-serif; font-size: 13px; }
QMainWindow, QDialog, QWidget#root, QWidget#splash, QWidget#stage, QWidget#present {
  background: %s; color: %s; border: 0;
}
QWidget#topbar, QWidget#bar, QWidget#thumbs, QWidget#home { background: %s; }
QWidget#hline { background: %s; }
QLabel#apptitle { color: %s; font-size: 15px; font-weight: 700; letter-spacing: 2px; }
QLabel#muted, QLabel#foot { color: %s; font-size: 11px; }
QLabel#kicker { color: %s; font-size: 13px; font-weight: 700; letter-spacing: 4px; }
QLabel#hero { color: %s; font-size: 36px; font-weight: 700; letter-spacing: 2px; }
QLabel#sub { color: %s; font-size: 14px; font-weight: 700; letter-spacing: 3px; }
QLabel#splashTitle { color: %s; font-size: 16px; font-weight: 700; letter-spacing: 1px; }
QLabel#splashMsg { color: %s; font-size: 13px; }
QLabel#counter { color: %s; font-size: 13px; font-weight: 700; letter-spacing: 1px; }
QPushButton {
  background: %s; color: %s; border: 1px solid %s; border-radius: 2px;
  padding: 8px 16px; font-weight: 700; letter-spacing: 1px; outline: none;
}
QPushButton:hover { background: %s; border-color: %s; }
QPushButton:pressed { background: %s; }
QPushButton:disabled { color: %s; border-color: %s; background: %s; }
QPushButton#accent {
  background: %s; color: #111; border: 1px solid %s; padding: 10px 28px;
  font-size: 14px; letter-spacing: 2px;
}
QPushButton#accent:hover { background: %s; }
QPushButton#accent:pressed { background: %s; }
QPushButton#flat {
  background: transparent; color: %s; border: 1px solid %s; padding: 7px 14px;
}
QPushButton#flat:hover { color: %s; border-color: %s; }
QPushButton#navbtn {
  background: %s; color: %s; border: 1px solid %s; min-width: 44px; padding: 8px 14px;
  font-size: 16px;
}
QPushButton#thumb {
  background: transparent; border: 2px solid %s; border-radius: 0; padding: 0;
}
QPushButton#thumb:hover { border-color: %s; }
QPushButton#thumb[current="true"] { border-color: %s; }
QProgressBar { background: %s; border: 0; border-radius: 0; max-height: 3px; min-height: 3px; }
QProgressBar::chunk { background: %s; }
QMenuBar { background: %s; color: %s; border: 0; }
QMenuBar::item { background: transparent; padding: 6px 10px; }
QMenuBar::item:selected { background: %s; }
QMenu { background: %s; color: %s; border: 1px solid %s; }
QMenu::item:selected { background: %s; }
QStatusBar { background: %s; color: %s; border: 0; }
QScrollArea { border: 0; background: %s; }
QScrollBar:horizontal { background: %s; height: 8px; border: 0; }
QScrollBar::handle:horizontal { background: %s; min-width: 32px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QMessageBox { background: %s; }
""" % (
    BG, TXT,
    BG, TXT,
    PANEL,
    BORDER,
    TXT,
    MUT,
    ACC,
    TXT,
    MUT,
    TXT,
    MUT,
    TXT,
    CARD, TXT, BORDER,
    "#222226", ACC,
    "#101012",
    DIM, BORDER, PANEL,
    ACC, ACC,
    "#FFC43A",
    ACC_DN,
    MUT, BORDER,
    TXT, ACC,
    CARD, TXT, BORDER,
    BORDER,
    MUT,
    ACC,
    CARD,
    ACC,
    PANEL, TXT,
    CARD,
    PANEL, TXT, BORDER,
    CARD,
    PANEL, MUT,
    PANEL,
    BG,
    BORDER,
    PANEL,
)


def check_update_sync(timeout=10):
    """Fetch latest.json. Returns ('ok', data) or ('error', message). Never disables TLS."""
    try:
        req = Request(
            UPDATE_URL + "?t=%d" % int(time.time()),
            headers={"User-Agent": "%s/%s" % (APP, APP_VERSION)},
        )
        ctx = ssl.create_default_context()
        with urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return "ok", data if isinstance(data, dict) else {}
    except Exception as e:
        return "error", str(getattr(e, "reason", None) or e)


def installer_url_of(data):
    if not isinstance(data, dict):
        return ""
    for k in ("installer_url", "url", "release_url"):
        v = str(data.get(k) or "").strip()
        if v.startswith("https://"):
            return v
    return ""


class UpdateSplash(QDialog):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Dialog)
        self.setObjectName("splash")
        self.setWindowTitle(APP)
        self.setWindowIcon(load_app_icon())
        self.setModal(True)
        self.setFixedSize(520, 300)
        self.setStyleSheet(QSS)
        v = QVBoxLayout(self)
        v.setContentsMargins(24, 28, 24, 24)
        v.setSpacing(0)
        v.addStretch(1)
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        pm = QPixmap(res_path("assets", "emblem.png"))
        logo.setPixmap(pm.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        v.addWidget(logo, 0, Qt.AlignCenter)
        v.addSpacing(16)
        t = QLabel(APP)
        t.setObjectName("splashTitle")
        t.setAlignment(Qt.AlignCenter)
        t.setWordWrap(True)
        v.addWidget(t)
        v.addSpacing(10)
        self.msg = QLabel("Checking for updates\u2026")
        self.msg.setObjectName("splashMsg")
        self.msg.setAlignment(Qt.AlignCenter)
        v.addWidget(self.msg)
        v.addSpacing(18)
        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setTextVisible(False)
        v.addWidget(bar)
        v.addStretch(1)
        foot = QLabel(COPYRIGHT)
        foot.setObjectName("foot")
        foot.setAlignment(Qt.AlignCenter)
        v.addWidget(foot)

    def set_message(self, text):
        self.msg.setText(text)


def offer_update(data):
    remote = str((data or {}).get("version") or "")
    notes = str((data or {}).get("notes") or "").strip()
    url = installer_url_of(data)
    msg = "Version %s is available (you have %s)." % (remote, APP_VERSION)
    if notes:
        msg += "\n\n" + notes
    if url:
        msg += "\n\nOpen the new installer?"
        if QMessageBox.question(None, APP, msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes) == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(url))
    else:
        QMessageBox.information(None, APP, msg)


def run_startup_update_check(app, force_shots=False):
    """Show the splash, check latest.json, offer an update if one exists, then continue.
    Network failures (offline, timeout, missing file) are ignored and the app starts."""
    splash = UpdateSplash()
    splash.show()
    splash.raise_()
    app.processEvents()
    grabbed = None
    box = [None]

    def work():
        box[0] = check_update_sync(timeout=10)

    th = threading.Thread(target=work, daemon=True)
    t0 = time.time()
    th.start()
    # Keep the splash visible long enough to read, and pump the UI.
    min_s = 1.2 if force_shots else 0.85
    while th.is_alive() or (time.time() - t0) < min_s:
        if force_shots and grabbed is None and (time.time() - t0) > 0.25:
            grabbed = splash.grab()
        app.processEvents()
        time.sleep(0.03)
        if time.time() - t0 > 14:
            break
    th.join(timeout=0.2)
    st, data = box[0] if box[0] else ("error", "timeout")
    splash.close()
    app.processEvents()
    if st == "ok" and vtuple(str((data or {}).get("version") or "")) > vtuple(APP_VERSION):
        offer_update(data)
    return grabbed


class SlideStage(QWidget):
    """Letterboxed slide on a black stage. No glow."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stage")
        self._pm = QPixmap()
        self.setMinimumSize(320, 180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_pixmap(self, pm: QPixmap):
        self._pm = pm
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0))
        if self._pm.isNull():
            p.end()
            return
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        r = self.rect()
        scaled = self._pm.scaled(r.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = r.x() + (r.width() - scaled.width()) // 2
        y = r.y() + (r.height() - scaled.height()) // 2
        p.drawPixmap(x, y, scaled)
        p.end()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.clicked.emit()


class ThumbBar(QWidget):
    jumped = Signal(int)

    def __init__(self, pixmaps, parent=None):
        super().__init__(parent)
        self.setObjectName("thumbs")
        self.buttons = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)
        lay.addStretch(1)
        for i, pm in enumerate(pixmaps, start=1):
            b = QPushButton()
            b.setObjectName("thumb")
            b.setCursor(Qt.PointingHandCursor)
            b.setFocusPolicy(Qt.NoFocus)
            thumb = pm.scaled(128, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            b.setIcon(QIcon(thumb))
            b.setIconSize(QSize(thumb.width(), thumb.height()))
            b.setFixedSize(thumb.width() + 8, thumb.height() + 8)
            b.setProperty("index", i)
            b.clicked.connect(lambda _=False, n=i: self.jumped.emit(n))
            self.buttons.append(b)
            lay.addWidget(b)
        lay.addStretch(1)

    def set_current(self, index):
        for b in self.buttons:
            on = b.property("index") == index
            b.setProperty("current", "true" if on else "false")
            b.style().unpolish(b)
            b.style().polish(b)


class PresentWindow(QWidget):
    closed = Signal()

    def __init__(self, pixmaps, index, parent=None):
        super().__init__(None, Qt.Window)
        self.setObjectName("present")
        self.setWindowTitle(APP + " \u2014 Present")
        self.setWindowIcon(load_app_icon())
        self.setStyleSheet(QSS)
        self.pixmaps = pixmaps
        self.index = index
        self.stage = SlideStage(self)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.stage)
        self.badge = QLabel(self)
        self.badge.setObjectName("counter")
        self.badge.setStyleSheet(
            "QLabel#counter { background: rgba(0,0,0,180); color: #F4F4F0; padding: 4px 10px; }"
        )
        self.badge.adjustSize()
        self._hide_badge = QTimer(self)
        self._hide_badge.setSingleShot(True)
        self._hide_badge.timeout.connect(lambda: self.badge.hide())
        self._apply()
        self.setMouseTracking(True)
        self.stage.clicked.connect(self.next_slide)

    def _apply(self):
        self.stage.set_pixmap(self.pixmaps[self.index - 1])
        self.badge.setText("%d / %d" % (self.index, len(self.pixmaps)))
        self.badge.adjustSize()
        self.badge.move(16, 16)
        self.badge.show()
        self._hide_badge.start(1800)

    def next_slide(self):
        if self.index < len(self.pixmaps):
            self.index += 1
            self._apply()

    def prev_slide(self):
        if self.index > 1:
            self.index -= 1
            self._apply()

    def keyPressEvent(self, ev):
        k = ev.key()
        if k in (Qt.Key_Escape, Qt.Key_Q):
            self.close()
        elif k in (Qt.Key_Right, Qt.Key_Down, Qt.Key_Space, Qt.Key_PageDown, Qt.Key_N):
            self.next_slide()
        elif k in (Qt.Key_Left, Qt.Key_Up, Qt.Key_Backspace, Qt.Key_PageUp, Qt.Key_P):
            self.prev_slide()
        elif k == Qt.Key_Home:
            self.index = 1
            self._apply()
        elif k == Qt.Key_End:
            self.index = len(self.pixmaps)
            self._apply()
        elif k == Qt.Key_F5:
            self.close()
        else:
            super().keyPressEvent(ev)

    def mouseMoveEvent(self, ev):
        self.badge.show()
        self._hide_badge.start(1800)
        super().mouseMoveEvent(ev)

    def closeEvent(self, ev):
        ev.accept()
        self.closed.emit()


class HomePage(QWidget):
    start = Signal()
    present = Signal()
    export_pdf = Signal()
    open_deck = Signal()
    about = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("home")
        v = QVBoxLayout(self)
        v.setContentsMargins(40, 32, 40, 24)
        v.setSpacing(0)
        v.addStretch(2)
        logo = QLabel()
        logo.setAlignment(Qt.AlignCenter)
        pm = QPixmap(res_path("assets", "emblem.png"))
        logo.setPixmap(pm.scaled(140, 140, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        v.addWidget(logo, 0, Qt.AlignCenter)
        v.addSpacing(28)
        kicker = QLabel("EX PRESENTS")
        kicker.setObjectName("kicker")
        kicker.setAlignment(Qt.AlignCenter)
        v.addWidget(kicker)
        v.addSpacing(8)
        hero = QLabel(APP)
        hero.setObjectName("hero")
        hero.setAlignment(Qt.AlignCenter)
        hero.setWordWrap(True)
        v.addWidget(hero)
        v.addSpacing(8)
        sub = QLabel("ARVICIA CITY")
        sub.setObjectName("sub")
        sub.setAlignment(Qt.AlignCenter)
        v.addWidget(sub)
        v.addSpacing(36)
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addStretch(1)
        b = QPushButton("START")
        b.setObjectName("accent")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(self.start.emit)
        row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)
        v.addStretch(3)
        v.addStretch(3)
        foot = QLabel(COPYRIGHT)
        foot.setObjectName("foot")
        foot.setAlignment(Qt.AlignCenter)
        v.addWidget(foot)


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP)
        self.setWindowIcon(load_app_icon())
        self.resize(1280, 800)
        self.setMinimumSize(960, 600)
        self.index = 1
        self.present_win = None
        self.pixmaps = []
        for i in range(1, SLIDE_COUNT + 1):
            pm = QPixmap(slide_path(i))
            if pm.isNull():
                pm = QPixmap(1280, 720)
                pm.fill(QColor(0, 0, 0))
            self.pixmaps.append(pm)

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        top = QWidget()
        top.setObjectName("topbar")
        th = QHBoxLayout(top)
        th.setContentsMargins(12, 8, 12, 8)
        th.setSpacing(10)
        emblem = QLabel()
        epm = QPixmap(res_path("assets", "emblem.png"))
        emblem.setPixmap(epm.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        th.addWidget(emblem)
        title = QLabel(APP)
        title.setObjectName("apptitle")
        th.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("muted")
        th.addWidget(ver)
        th.addStretch(1)
        self.btn_home = QPushButton("Home")
        self.btn_home.setObjectName("flat")
        self.btn_home.clicked.connect(self.show_home)
        th.addWidget(self.btn_home)
        b_upd = QPushButton("Check for updates")
        b_upd.setObjectName("flat")
        b_upd.clicked.connect(self.check_updates_manual)
        th.addWidget(b_upd)
        b_ab = QPushButton("About")
        b_ab.setObjectName("flat")
        b_ab.clicked.connect(self.about)
        th.addWidget(b_ab)
        v.addWidget(top)
        line = QWidget()
        line.setFixedHeight(1)
        line.setObjectName("hline")
        v.addWidget(line)

        self.stack = QStackedWidget()
        v.addWidget(self.stack, 1)

        self.home = HomePage()
        self.home.start.connect(self.show_slides)
        self.home.present.connect(self.present_from_home)
        self.home.export_pdf.connect(self.export_pdf)
        self.home.open_deck.connect(self.open_original)
        self.home.about.connect(self.about)
        self.stack.addWidget(self.home)

        viewer = QWidget()
        vv = QVBoxLayout(viewer)
        vv.setContentsMargins(0, 0, 0, 0)
        vv.setSpacing(0)
        self.stage = SlideStage()
        self.stage.clicked.connect(self.next_slide)
        vv.addWidget(self.stage, 1)

        bar = QWidget()
        bar.setObjectName("bar")
        bh = QHBoxLayout(bar)
        bh.setContentsMargins(16, 10, 16, 10)
        bh.setSpacing(10)
        self.btn_prev = QPushButton("\u25c0")
        self.btn_prev.setObjectName("navbtn")
        self.btn_prev.setToolTip("Previous slide (Left)")
        self.btn_prev.clicked.connect(self.prev_slide)
        bh.addWidget(self.btn_prev)
        self.counter = QLabel()
        self.counter.setObjectName("counter")
        self.counter.setAlignment(Qt.AlignCenter)
        self.counter.setMinimumWidth(80)
        bh.addWidget(self.counter)
        self.btn_next = QPushButton("\u25b6")
        self.btn_next.setObjectName("navbtn")
        self.btn_next.setToolTip("Next slide (Right)")
        self.btn_next.clicked.connect(self.next_slide)
        bh.addWidget(self.btn_next)
        bh.addSpacing(12)
        b_pres = QPushButton("Present")
        b_pres.setObjectName("accent")
        b_pres.setToolTip("Fullscreen present mode (F5)")
        b_pres.clicked.connect(self.start_present)
        bh.addWidget(b_pres)
        bh.addStretch(1)
        b_pdf = QPushButton("Export PDF")
        b_pdf.setObjectName("flat")
        b_pdf.clicked.connect(self.export_pdf)
        bh.addWidget(b_pdf)
        b_open = QPushButton("Open original deck")
        b_open.setObjectName("flat")
        b_open.setToolTip("Open the bundled presentation in your default app")
        b_open.clicked.connect(self.open_original)
        bh.addWidget(b_open)
        vv.addWidget(bar)

        self.thumbs = ThumbBar(self.pixmaps)
        self.thumbs.jumped.connect(self.goto_slide)
        vv.addWidget(self.thumbs)
        self.stack.addWidget(viewer)

        self._build_menus()
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(COPYRIGHT)

        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_slide)
        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_slide)
        QShortcut(QKeySequence(Qt.Key_Space), self, self.next_slide)
        QShortcut(QKeySequence(Qt.Key_PageDown), self, self.next_slide)
        QShortcut(QKeySequence(Qt.Key_PageUp), self, self.prev_slide)
        QShortcut(QKeySequence(Qt.Key_Home), self, lambda: self.goto_slide(1))
        QShortcut(QKeySequence(Qt.Key_End), self, lambda: self.goto_slide(SLIDE_COUNT))
        QShortcut(QKeySequence(Qt.Key_F5), self, self.start_present)
        QShortcut(QKeySequence("Ctrl+E"), self, self.export_pdf)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_original)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self._esc)

        self.show_home()
        self._refresh()

    def _build_menus(self):
        mb = self.menuBar()
        f = mb.addMenu("File")
        f.addAction("Export PDF\tCtrl+E", self.export_pdf)
        f.addAction("Open original deck\tCtrl+O", self.open_original)
        f.addSeparator()
        f.addAction("Exit", self.close)
        v = mb.addMenu("View")
        v.addAction("Home", self.show_home)
        v.addAction("Slides", self.show_slides)
        v.addAction("Present\tF5", self.start_present)
        v.addSeparator()
        v.addAction("Previous slide\tLeft", self.prev_slide)
        v.addAction("Next slide\tRight", self.next_slide)
        h = mb.addMenu("Help")
        h.addAction("Check for updates", self.check_updates_manual)
        h.addAction("About " + APP, self.about)

    def _esc(self):
        if self.stack.currentIndex() == 1:
            self.show_home()

    def show_home(self):
        self.stack.setCurrentIndex(0)
        self.btn_home.setEnabled(False)
        self.status.showMessage(COPYRIGHT)

    def show_slides(self):
        self.stack.setCurrentIndex(1)
        self.btn_home.setEnabled(True)
        self._refresh()

    def present_from_home(self):
        self.index = 1
        self.show_slides()
        self.start_present()

    def goto_slide(self, n):
        n = max(1, min(SLIDE_COUNT, int(n)))
        self.index = n
        if self.stack.currentIndex() != 1:
            self.show_slides()
        else:
            self._refresh()

    def next_slide(self):
        if self.stack.currentIndex() != 1:
            return
        if self.index < SLIDE_COUNT:
            self.index += 1
            self._refresh()

    def prev_slide(self):
        if self.stack.currentIndex() != 1:
            return
        if self.index > 1:
            self.index -= 1
            self._refresh()

    def _refresh(self):
        self.stage.set_pixmap(self.pixmaps[self.index - 1])
        self.counter.setText("%d / %d" % (self.index, SLIDE_COUNT))
        self.thumbs.set_current(self.index)
        self.btn_prev.setEnabled(self.index > 1)
        self.btn_next.setEnabled(self.index < SLIDE_COUNT)
        if self.stack.currentIndex() == 1:
            self.status.showMessage("Slide %d of %d  \u00b7  %s" % (self.index, SLIDE_COUNT, COPYRIGHT))

    def start_present(self):
        if self.present_win is not None:
            self.present_win.index = self.index
            self.present_win._apply()
            self.present_win.showFullScreen()
            self.present_win.activateWindow()
            return
        win = PresentWindow(self.pixmaps, self.index, self)
        self.present_win = win

        def done():
            self.index = win.index
            self.present_win = None
            self.show_slides()
            self._refresh()
            self.activateWindow()

        win.closed.connect(done)
        win.showFullScreen()
        win.activateWindow()

    def export_pdf(self):
        src = deck_file(DECK_PDF)
        if not os.path.isfile(src):
            QMessageBox.warning(self, APP, "The bundled PDF is missing.")
            return
        suggested = os.path.join(downloads_dir(), DECK_PDF)
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", suggested, "PDF (*.pdf);;All files (*.*)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            shutil.copyfile(src, path)
        except Exception as e:
            QMessageBox.warning(self, APP, "Could not save the PDF.\n%s" % e)
            return
        self.status.showMessage("Saved " + path)
        QMessageBox.information(self, APP, "Saved:\n" + path)

    def open_original(self):
        src = deck_file(DECK_PPTX)
        if not os.path.isfile(src):
            QMessageBox.warning(self, APP, "The bundled presentation is missing.")
            return
        # Copy out of the bundle so the default app can open a normal file path.
        dest = os.path.join(downloads_dir(), DECK_PPTX)
        try:
            if os.path.abspath(src) != os.path.abspath(dest):
                shutil.copyfile(src, dest)
            target = dest if os.path.isfile(dest) else src
        except Exception:
            target = src
        ok = QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(target)))
        if not ok:
            QMessageBox.information(
                self, APP,
                "The presentation was saved here:\n%s\n\nOpen it with your default app." % target,
            )
        else:
            self.status.showMessage("Opened " + target)

    def about(self):
        m = QMessageBox(self)
        m.setWindowTitle("About " + APP)
        m.setIconPixmap(
            QPixmap(res_path("assets", "emblem.png")).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        m.setText("<b>%s</b> &nbsp; v%s" % (APP, APP_VERSION))
        m.setInformativeText(COPYRIGHT)
        m.exec()

    def check_updates_manual(self):
        self.status.showMessage("Checking for updates\u2026")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        st, data = check_update_sync(timeout=12)
        QApplication.restoreOverrideCursor()
        if st != "ok":
            QMessageBox.warning(self, APP, "Could not check for updates.\n%s" % data)
            self.status.showMessage(COPYRIGHT)
            return
        remote = str((data or {}).get("version") or "")
        if remote and vtuple(remote) > vtuple(APP_VERSION):
            offer_update(data)
        else:
            QMessageBox.information(self, APP, "You have the latest version (%s)." % APP_VERSION)
        self.status.showMessage(COPYRIGHT)

    def closeEvent(self, ev):
        if self.present_win is not None:
            self.present_win.close()
        ev.accept()


def take_shots(app, win: Main, splash_pm, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    log = open(os.path.join(out_dir, "shots.log"), "w", encoding="utf-8")

    def L(*a):
        log.write(" ".join(str(x) for x in a) + "\n")
        log.flush()
        print(*a)

    def save(name, widget=None):
        target = widget or win
        path = os.path.join(out_dir, name)
        ok = target.grab().save(path)
        L("shot", name, "ok" if ok else "FAIL", path, os.path.getsize(path) if ok and os.path.isfile(path) else 0)

    win.resize(1280, 800)
    win.show()
    win.setFocus(Qt.OtherFocusReason)
    app.processEvents()
    if splash_pm is not None:
        path = os.path.join(out_dir, "screenshot_splash.png")
        splash_pm.save(path)
        L("shot", "screenshot_splash.png", "ok", path, os.path.getsize(path))
    win.show_home()
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    save("screenshot_home.png")
    # Proof image: title-bar uses the live window icon (photo), home still shows the H emblem.
    def _icon_proof():
        bar_h = 36
        home_pm = win.grab()
        w, h = home_pm.width(), home_pm.height()
        canvas = QPixmap(w, h + bar_h)
        canvas.fill(QColor(32, 32, 32))
        p = QPainter(canvas)
        p.fillRect(0, 0, w, bar_h, QColor(24, 24, 24))
        ico = win.windowIcon().pixmap(24, 24)
        if ico.isNull():
            L("windowIcon pixmap is null")
        else:
            p.drawPixmap(8, (bar_h - 24) // 2, ico)
        p.setPen(QColor(244, 244, 240))
        font = QFont("DejaVu Sans", 11)
        font.setBold(True)
        p.setFont(font)
        p.drawText(40, 0, w - 48, bar_h, int(Qt.AlignVCenter | Qt.AlignLeft), APP)
        p.drawPixmap(0, bar_h, home_pm)
        p.end()
        path = os.path.join(out_dir, "screenshot_window_icon.png")
        ok = canvas.save(path)
        L("shot", "screenshot_window_icon.png", "ok" if ok else "FAIL", path, os.path.getsize(path) if ok else 0)
        icon_path = os.path.join(out_dir, "screenshot_window_icon_only.png")
        win.windowIcon().pixmap(128, 128).save(icon_path)
        L("shot", "screenshot_window_icon_only.png")
    _icon_proof()
    def _grab_about():
        about = None
        for w in app.topLevelWidgets():
            if isinstance(w, QMessageBox) and w.isVisible():
                about = w
                break
        if about is not None:
            save("screenshot_about.png", about)
            about.done(0)
        else:
            L("about dialog missing")
    QTimer.singleShot(400, _grab_about)
    win.about()  # modal; the timer runs inside exec()
    app.processEvents()
    win.goto_slide(4)
    app.processEvents()
    time.sleep(0.2)
    app.processEvents()
    save("screenshot_slide.png")
    win.start_present()
    app.processEvents()
    time.sleep(0.35)
    app.processEvents()
    if win.present_win is not None:
        save("screenshot_present.png", win.present_win)
        win.present_win.close()
        app.processEvents()
    else:
        L("present window missing")
    # one more of the title slide in the viewer
    win.goto_slide(1)
    app.processEvents()
    time.sleep(0.15)
    app.processEvents()
    save("screenshot_slide1.png")
    src_pdf = deck_file(DECK_PDF)
    dest_pdf = os.path.join(out_dir, "export_test.pdf")
    shutil.copyfile(src_pdf, dest_pdf)
    L("pdf_copy", os.path.getsize(dest_pdf), "from", os.path.getsize(src_pdf))
    L("pptx", os.path.getsize(deck_file(DECK_PPTX)))
    L("wine", is_wine())
    L("done")
    log.close()
    QTimer.singleShot(200, app.quit)


def main():
    shots = "--shots" in sys.argv
    skip = "--skip-update" in sys.argv
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP)
    app.setOrganizationName("EX Inc.")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(load_app_icon())
    for f in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
        QFontDatabase.addApplicationFont(res_path("assets", "fonts", f))
    QFont.insertSubstitutions("Segoe UI", ["Segoe UI Symbol", "DejaVu Sans"])
    app.setStyleSheet(QSS)

    splash_pm = None
    if not skip:
        splash_pm = run_startup_update_check(app, force_shots=shots)

    win = Main()
    if shots:
        out = "docs"
        if "--out" in sys.argv:
            i = sys.argv.index("--out")
            if i + 1 < len(sys.argv):
                out = sys.argv[i + 1]
        QTimer.singleShot(100, lambda: take_shots(app, win, splash_pm, out))
    else:
        win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
