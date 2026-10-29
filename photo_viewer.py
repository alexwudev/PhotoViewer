#!/usr/bin/env python3
# Photo Viewer - Win10-like image viewer with animated GIF/WebP slideshow.
# Requires: pip install PyQt6
# Usage: python3 photo_viewer.py [path]
import os
import re
import subprocess
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QFileDialog, QToolBar,
    QComboBox, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QMessageBox, QMenu,
)
from PyQt6.QtGui import (
    QPixmap, QMovie, QAction, QActionGroup, QKeySequence, QImageReader,
    QPainter, QImage, QClipboard, QGuiApplication,
)
from PyQt6.QtCore import Qt, QTimer, QSize, QRect, QPoint

SUPPORTED_EXTS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp",
    ".tif", ".tiff", ".ico", ".svg",
}
ANIMATED_EXTS = {".gif", ".webp"}

INTERVALS = [
    ("\u6975\u5feb 1 \u79d2", 1000),
    ("2 \u79d2", 2000),
    ("\u5feb 3 \u79d2", 3000),
    ("4 \u79d2", 4000),
    ("\u6a19\u6e96 5 \u79d2", 5000),
    ("7 \u79d2", 7000),
    ("\u6162 10 \u79d2", 10000),
    ("\u6975\u6162 30 \u79d2", 30000),
]

ZOOM_STEP = 1.2
ZOOM_MIN = 0.05
ZOOM_MAX = 20.0


def _natural(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


def natural_key(p):
    """Sort key on the file name so that p2 comes before p10."""
    return _natural(p.name)


def folder_then_name_key(p):
    """Group by folder (natural order of each path part), then by file name."""
    return ([_natural(part) for part in p.parent.parts], natural_key(p))


# ---- Windows shell helpers ----

def send_to_recycle_bin(path):
    """Move a file to the Recycle Bin. Raises OSError on failure."""
    if sys.platform != "win32":
        path.unlink()
        return
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", ctypes.c_uint),
            ("pFrom", ctypes.c_wchar_p),
            ("pTo", ctypes.c_wchar_p),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", ctypes.c_wchar_p),
        ]

    FO_DELETE = 3
    FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 0x4, 0x10, 0x40, 0x400
    op = SHFILEOPSTRUCTW()
    op.wFunc = FO_DELETE
    op.pFrom = str(path) + "\0"  # list must be double-null terminated
    op.fFlags = FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI
    rc = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    if rc != 0 or op.fAnyOperationsAborted:
        raise OSError("SHFileOperation failed (code " + hex(rc) + ")")


def explorer_view_files(target):
    """If `target` was opened from an Explorer window showing search results
    (or a library), return that window's items in view order; else None."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import POINTER, byref, c_int, c_uint, c_void_p
        import comtypes
        import comtypes.client
        from comtypes import GUID, IUnknown, COMMETHOD, HRESULT
    except ImportError:
        return None

    class IServiceProvider(IUnknown):
        _iid_ = GUID("{6D5140C1-7436-11CE-8034-00AA006009FA}")
        _methods_ = [
            COMMETHOD([], HRESULT, "QueryService",
                      (["in"], POINTER(GUID)), (["in"], POINTER(GUID)),
                      (["out"], POINTER(POINTER(IUnknown)))),
        ]

    class IShellItem(IUnknown):
        _iid_ = GUID("{43826D1E-E718-42EE-BC55-A1E261C37BFE}")
        _methods_ = [
            COMMETHOD([], HRESULT, "BindToHandler", (["in"], c_void_p), (["in"], c_void_p),
                      (["in"], c_void_p), (["in"], c_void_p)),
            COMMETHOD([], HRESULT, "GetParent", (["in"], c_void_p)),
            COMMETHOD([], HRESULT, "GetDisplayName", (["in"], c_uint), (["out"], POINTER(c_void_p))),
        ]

    class IShellItemArray(IUnknown):
        _iid_ = GUID("{B63EA76D-1F85-456F-A19C-48159EFA858B}")
        _methods_ = [
            COMMETHOD([], HRESULT, name, *[(["in"], c_void_p)] * n)
            for name, n in (("BindToHandler", 4), ("GetPropertyStore", 3),
                            ("GetPropertyDescriptionList", 3), ("GetAttributes", 3))
        ] + [
            COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(c_uint))),
            COMMETHOD([], HRESULT, "GetItemAt", (["in"], c_uint), (["out"], POINTER(POINTER(IShellItem)))),
        ]

    class IFolderView(IUnknown):
        _iid_ = GUID("{CDE725B0-CCC9-4519-917E-325D72FAB4CE}")
        _methods_ = [
            COMMETHOD([], HRESULT, "GetCurrentViewMode", (["in"], c_void_p)),
            COMMETHOD([], HRESULT, "SetCurrentViewMode", (["in"], c_uint)),
            COMMETHOD([], HRESULT, "GetFolder", (["in"], c_void_p), (["in"], c_void_p)),
            COMMETHOD([], HRESULT, "Item", (["in"], c_int), (["in"], c_void_p)),
            COMMETHOD([], HRESULT, "ItemCount", (["in"], c_uint), (["out"], POINTER(c_int))),
            COMMETHOD([], HRESULT, "Items", (["in"], c_uint), (["in"], POINTER(GUID)),
                      (["out"], POINTER(POINTER(IShellItemArray)))),
        ]

    class IShellBrowser(IUnknown):
        # only QueryActiveShellView is called; earlier slots keep the vtable layout
        _iid_ = GUID("{000214E2-0000-0000-C000-000000000046}")
        _methods_ = [
            COMMETHOD([], HRESULT, name, (["in"], c_void_p)) for name in (
                "GetWindow", "ContextSensitiveHelp", "InsertMenusSB", "SetMenuSB",
                "RemoveMenusSB", "SetStatusTextSB", "EnableModelessSB",
                "TranslateAcceleratorSB", "BrowseObject", "GetViewStateStream",
                "GetControlWindow", "SendControlMsg")
        ] + [
            COMMETHOD([], HRESULT, "QueryActiveShellView", (["out"], POINTER(POINTER(IUnknown)))),
        ]

    SID_STopLevelBrowser = GUID("{4C96BE40-915C-11CF-99D3-00AA004AE837}")
    SVGIO_ALLVIEW_VIEWORDER = 0x00000002 | 0x80000000
    SIGDN_FILESYSPATH = 0x80058000
    free = ctypes.windll.ole32.CoTaskMemFree

    def view_paths(win):
        sp = win.QueryInterface(IServiceProvider)
        unk = sp.QueryService(byref(SID_STopLevelBrowser), byref(IShellBrowser._iid_))
        fv = unk.QueryInterface(IShellBrowser).QueryActiveShellView().QueryInterface(IFolderView)
        arr = fv.Items(SVGIO_ALLVIEW_VIEWORDER, byref(IShellItemArray._iid_))
        out = []
        for i in range(arr.GetCount()):
            try:
                p = arr.GetItemAt(i).GetDisplayName(SIGDN_FILESYSPATH)
            except comtypes.COMError:
                continue  # virtual item without a file-system path
            out.append(ctypes.wstring_at(p))
            free(c_void_p(p))
        return out

    key = os.path.normcase(str(target))
    try:
        windows = comtypes.client.CreateObject("Shell.Application", dynamic=True).Windows()
        for i in range(windows.Count):
            w = windows.Item(i)
            if w is None:
                continue
            try:
                # plain folder windows keep the normal folder behaviour
                if str(w.LocationURL).lower().startswith("file:"):
                    continue
                paths = view_paths(w._comobj)
            except (comtypes.COMError, AttributeError, OSError):
                continue
            if any(os.path.normcase(p) == key for p in paths):
                return [Path(p) for p in paths]
    except (comtypes.COMError, OSError):
        return None
    return None


class ImageView(QWidget):
    """Custom widget that paints the image/movie with zoom & pan support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #111;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

        self._pixmap = None
        self._movie = None
        self._orig_size = QSize(0, 0)

        # zoom=0 means fit-to-window; >0 means manual factor
        self._zoom = 0.0
        # pan offset (in widget coords, from center)
        self._pan = QPoint(0, 0)
        self._dragging = False
        self._drag_start = QPoint(0, 0)
        self._pan_start = QPoint(0, 0)

        self.on_left_click = None
        self.left_click_enabled = False
        self._left_press_pos = None

    # ---- paint ----

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)

        if self._movie is not None:
            pm = self._movie.currentPixmap()
        elif self._pixmap is not None:
            pm = self._pixmap
        else:
            return

        if pm.isNull():
            return

        scale = self._effective_scale()
        dw = int(pm.width() * scale)
        dh = int(pm.height() * scale)

        # center + pan offset
        x = (self.width() - dw) // 2 + self._pan.x()
        y = (self.height() - dh) // 2 + self._pan.y()

        target = QRect(x, y, dw, dh)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(target, pm)

    def _fit_scale(self):
        if self._orig_size.width() <= 0 or self._orig_size.height() <= 0:
            return 1.0
        # small images are enlarged too, until the limiting side meets the window edge
        sx = self.width() / self._orig_size.width()
        sy = self.height() / self._orig_size.height()
        return min(sx, sy)

    def _effective_scale(self):
        if self._zoom > 0:
            return self._zoom
        return self._fit_scale()

    # ---- mouse: drag to pan (only when zoomed in) ----

    def _is_zoomed_in(self):
        return self._zoom > 0 and self._zoom > self._fit_scale()

    def _clamp_pan(self):
        """Limit pan so the image edge cannot move past the widget center."""
        scale = self._effective_scale()
        iw = int(self._orig_size.width() * scale)
        ih = int(self._orig_size.height() * scale)
        max_x = max((iw - self.width()) // 2, 0)
        max_y = max((ih - self.height()) // 2, 0)
        px = max(-max_x, min(max_x, self._pan.x()))
        py = max(-max_y, min(max_y, self._pan.y()))
        self._pan = QPoint(px, py)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._left_press_pos = e.pos()
            if self._is_zoomed_in():
                self._drag_start = e.pos()
                self._pan_start = QPoint(self._pan)
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if (e.buttons() & Qt.MouseButton.LeftButton
                and self._left_press_pos is not None
                and self._is_zoomed_in()):
            delta = e.pos() - self._drag_start
            if not self._dragging and delta.manhattanLength() > 5:
                self._dragging = True
            if self._dragging:
                self._pan = self._pan_start + delta
                self._clamp_pan()
                self.update()
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            if not self._dragging and self.left_click_enabled and callable(self.on_left_click):
                self.on_left_click()
            self._dragging = False
            self._left_press_pos = None
        super().mouseReleaseEvent(e)

    # ---- wheel = zoom ----

    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        if delta == 0:
            return
        e.accept()

        old_scale = self._effective_scale()
        if self._zoom <= 0:
            self._zoom = old_scale

        # fit-to-window scale is the floor for zoom out
        fit_scale = self._fit_scale()
        if delta > 0:
            self._zoom = min(self._zoom * ZOOM_STEP, ZOOM_MAX)
        else:
            self._zoom = self._zoom / ZOOM_STEP
            if self._zoom <= fit_scale:
                # snap back to fit mode
                self._zoom = 0.0
                self._pan = QPoint(0, 0)
                self.update()
                return

        # adjust pan so the point under the cursor stays fixed
        new_scale = self._zoom
        if old_scale > 0 and new_scale > 0:
            ratio = new_scale / old_scale
            cursor = e.position().toPoint()
            center = QPoint(self.width() // 2, self.height() // 2)
            old_img_pt = cursor - center - self._pan
            new_pan = cursor - center - QPoint(
                int(old_img_pt.x() * ratio), int(old_img_pt.y() * ratio)
            )
            self._pan = new_pan

        self.update()

    # ---- load ----

    def clear_content(self):
        if self._movie is not None:
            self._movie.stop()
            self._movie.deleteLater()
            self._movie = None
        self._pixmap = None
        self._orig_size = QSize(0, 0)
        self._zoom = 0.0
        self._pan = QPoint(0, 0)
        self.update()

    def load(self, path):
        self.clear_content()
        suffix = path.suffix.lower()
        if suffix in ANIMATED_EXTS:
            movie = QMovie(str(path))
            if movie.isValid():
                self._movie = movie
                # Use QImageReader for reliable original size
                # (jumpToFrame(0) often fails for WebP, returning empty pixmap)
                reader = QImageReader(str(path))
                rsize = reader.size()
                if rsize.isValid() and rsize.width() > 0:
                    self._orig_size = rsize
                else:
                    movie.jumpToFrame(0)
                    self._orig_size = movie.currentPixmap().size()
                movie.frameChanged.connect(lambda: self.update())
                movie.start()
                return True
        return self._load_static(path)

    def _load_static(self, path):
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        img = reader.read()
        if img.isNull():
            return False
        self._pixmap = QPixmap.fromImage(img)
        self._orig_size = self._pixmap.size()
        self.update()
        return True

    def reset_zoom(self):
        self._zoom = 0.0
        self._pan = QPoint(0, 0)
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._zoom <= 0:
            self._pan = QPoint(0, 0)
        self.update()


class PhotoViewer(QMainWindow):
    def __init__(self, initial=None):
        super().__init__()
        self.setWindowTitle("Photo Viewer")
        self.resize(1100, 750)

        self.files = []
        self.index = -1
        self.from_search = False
        self.slideshow_active = False
        self.slideshow_paused = False

        self.view = ImageView(self)
        self.view.on_left_click = self.next_image
        self.view.left_click_enabled = False
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._show_context_menu)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.view, 1)

        self.nav_bar = QWidget()
        self.nav_bar.setStyleSheet("background-color: #1a1a1a;")
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(8, 6, 8, 6)
        btn_style = (
            "QPushButton { color: #eee; background: #333; border: none;"
            " padding: 6px 20px; font-size: 18px; border-radius: 4px; }"
            "QPushButton:hover { background: #555; }"
            "QPushButton:pressed { background: #222; }"
        )
        self.btn_prev = QPushButton("\u25c0")
        self.btn_prev.setStyleSheet(btn_style)
        self.btn_prev.setFixedWidth(80)
        self.btn_prev.clicked.connect(self.prev_image)
        self.btn_next = QPushButton("\u25b6")
        self.btn_next.setStyleSheet(btn_style)
        self.btn_next.setFixedWidth(80)
        self.btn_next.clicked.connect(self.next_image)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addSpacing(16)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addStretch(1)
        layout.addWidget(self.nav_bar)

        self.setCentralWidget(central)

        self.slideshow_timer = QTimer(self)
        self.slideshow_timer.timeout.connect(self.next_image)

        self._build_toolbar()
        self._build_shortcuts()

        if initial:
            p = Path(initial).expanduser().resolve()
            if p.is_dir():
                self.load_folder(p)
            elif p.is_file():
                found = explorer_view_files(p)
                if found:
                    self.load_list(found, select=p)
                else:
                    self.load_folder(p.parent, select=p)

    def _build_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        a = QAction("\u958b\u555f\u5716\u7247\u2026", self); a.triggered.connect(self.action_open_file); tb.addAction(a)
        a = QAction("\u958b\u555f\u8cc7\u6599\u593e\u2026", self); a.triggered.connect(self.action_open_dir); tb.addAction(a)
        tb.addSeparator()
        a = QAction("\u25c0 \u4e0a\u4e00\u5f35", self); a.triggered.connect(self.prev_image); tb.addAction(a)
        a = QAction("\u4e0b\u4e00\u5f35 \u25b6", self); a.triggered.connect(self.next_image); tb.addAction(a)
        tb.addSeparator()

        tb.addWidget(QLabel(" \u5e7b\u71c8\u7247\u9593\u9694\uff1a "))
        self.interval_box = QComboBox()
        for label, _ in INTERVALS:
            self.interval_box.addItem(label)
        self.interval_box.setCurrentIndex(2)
        self.interval_box.currentIndexChanged.connect(self._on_interval_changed)
        tb.addWidget(self.interval_box)

        self.btn_slideshow = QPushButton("\u25b6 \u64ad\u653e\u5e7b\u71c8\u7247 (F5)")
        self.btn_slideshow.clicked.connect(self.toggle_slideshow)
        tb.addWidget(self.btn_slideshow)

        tb.addSeparator()
        a = QAction("\u5168\u87a2\u5e55\u5e7b\u71c8\u7247 (F5/F11/F12)", self); a.triggered.connect(self.toggle_slideshow); tb.addAction(a)

    def _build_shortcuts(self):
        def add(seq, slot):
            a = QAction(self)
            a.setShortcut(QKeySequence(seq))
            a.triggered.connect(slot)
            self.addAction(a)

        add("Right", self.next_image)
        add("Left", self.prev_image)
        add("Space", self.toggle_pause_or_next)
        add("F5", self.toggle_slideshow)
        add("F11", self.toggle_slideshow)
        add("F12", self.toggle_slideshow)
        add("Escape", self.on_escape)
        add("Delete", self.delete_image)
        add("Ctrl+O", self.action_open_file)
        add("Ctrl+Shift+O", self.action_open_dir)
        add("Ctrl+0", self.view.reset_zoom)

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        menu.addAction("\u958b\u555f\u5716\u7247\u2026", self.action_open_file)
        menu.addAction("\u958b\u555f\u8cc7\u6599\u593e\u2026", self.action_open_dir)
        menu.addSeparator()
        menu.addAction("\u25c0 \u4e0a\u4e00\u5f35 (\u2190)", self.prev_image)
        menu.addAction("\u4e0b\u4e00\u5f35 \u25b6 (\u2192)", self.next_image)
        menu.addSeparator()

        if not self.slideshow_active:
            menu.addAction("\u25b6 \u64ad\u653e\u5e7b\u71c8\u7247 (F5)", self.start_slideshow)
        else:
            if self.slideshow_paused:
                menu.addAction("\u25b6 \u7e7c\u7e8c\u5e7b\u71c8\u7247", self.resume_slideshow)
            else:
                menu.addAction("\u23f8 \u66ab\u505c\u5e7b\u71c8\u7247", self.pause_slideshow)
            menu.addAction("\u23f9 \u505c\u6b62\u5e7b\u71c8\u7247", self.stop_slideshow)

        speed_menu = menu.addMenu("\u5e7b\u71c8\u7247\u901f\u7387")
        group = QActionGroup(self)
        group.setExclusive(True)
        cur = self.interval_box.currentIndex()
        for i, (label, _) in enumerate(INTERVALS):
            act = QAction(label, self, checkable=True)
            act.setChecked(i == cur)
            act.triggered.connect(lambda _checked=False, idx=i: self._set_interval(idx))
            group.addAction(act)
            speed_menu.addAction(act)

        menu.addSeparator()
        menu.addAction("\u9069\u5408\u8996\u7a97 (Ctrl+0)", self.view.reset_zoom)

        menu.addSeparator()
        has_file = bool(self.files and 0 <= self.index < len(self.files))
        a = menu.addAction("\u958b\u555f\u6240\u5728\u8cc7\u6599\u593e", self.open_containing_folder)
        a.setEnabled(has_file)
        a = menu.addAction("\u8907\u88fd\u5716\u7247", self.copy_image)
        a.setEnabled(has_file)
        a = menu.addAction("\u522a\u9664\u5716\u7247 (Del)", self.delete_image)
        a.setEnabled(has_file)

        menu.addSeparator()
        if self.slideshow_active:
            menu.addAction("\u96e2\u958b\u5e7b\u71c8\u7247 (Esc)", self.stop_slideshow)
        else:
            menu.addAction("\u5168\u87a2\u5e55\u5e7b\u71c8\u7247 (F5/F11/F12)", self.start_slideshow)
        menu.addSeparator()
        if self.slideshow_active:
            menu.addAction("\u96e2\u958b\u5e7b\u71c8\u7247\u6a21\u5f0f", self.stop_slideshow)
        else:
            menu.addAction("\u95dc\u9589 PhotoViewer", self.close)

        menu.exec(self.view.mapToGlobal(pos))

    def _current_path(self):
        if self.files and 0 <= self.index < len(self.files):
            return self.files[self.index]
        return None

    def open_containing_folder(self):
        p = self._current_path()
        if p is None:
            return
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])

    def copy_image(self):
        p = self._current_path()
        if p is None:
            return
        reader = QImageReader(str(p))
        reader.setAutoTransform(True)
        img = reader.read()
        if not img.isNull():
            QGuiApplication.clipboard().setImage(img)

    def delete_image(self):
        """Move the current image to the Recycle Bin and show the next one."""
        p = self._current_path()
        if p is None:
            return
        self.view.clear_content()  # release the file handle (animated images)
        try:
            send_to_recycle_bin(p)
        except OSError as ex:
            QMessageBox.warning(self, "\u522a\u9664\u5931\u6557", str(ex))
            self.show_current()
            return
        self.files.pop(self.index)
        if not self.files:
            self.index = -1
            self.stop_slideshow()
            self.setWindowTitle("Photo Viewer")
            return
        if self.index >= len(self.files):
            self.index = 0
        self.show_current()
        self._restart_slideshow_timer()

    def _set_interval(self, idx):
        self.interval_box.setCurrentIndex(idx)

    def action_open_file(self):
        exts = " ".join("*" + e for e in sorted(SUPPORTED_EXTS))
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (" + exts + ")")
        if path:
            p = Path(path)
            self.load_folder(p.parent, select=p)

    def action_open_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if path:
            self.load_folder(Path(path))

    def load_folder(self, folder, select=None):
        files = sorted(
            [p for p in folder.iterdir()
             if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS],
            key=natural_key,
        )
        if not files:
            QMessageBox.information(self, "Info", "No supported images in folder.")
            return
        self.from_search = False
        self.files = files
        self.index = files.index(select) if (select is not None and select in files) else 0
        self.show_current()

    def load_list(self, paths, select):
        """Use an explicit file list (Explorer search results), possibly spanning folders."""
        key = os.path.normcase(str(select))
        # finish one folder (by file name: p1, p2, ..., p10) before the next,
        # regardless of the order Explorer shows
        files = sorted(
            (p for p in paths if p.suffix.lower() in SUPPORTED_EXTS),
            key=folder_then_name_key,
        )
        self.from_search = True
        self.files = files
        self.index = next(
            (i for i, p in enumerate(files) if os.path.normcase(str(p)) == key), 0)
        self.show_current()

    def show_current(self):
        if not self.files or self.index < 0:
            return
        path = self.files[self.index]
        ok = self.view.load(path)
        title = "[" + str(self.index + 1) + "/" + str(len(self.files)) + "] " + path.name
        if self.from_search:
            # results span folders, so show where this one lives
            title += "  —  " + str(path.parent) + "  (搜尋結果)"
        if not ok:
            title += "  (load failed)"
        self.setWindowTitle("Photo Viewer - " + title)

    def _restart_slideshow_timer(self):
        """Reset the slideshow countdown after a manual image switch."""
        if self.slideshow_active and not self.slideshow_paused:
            self.slideshow_timer.start(INTERVALS[self.interval_box.currentIndex()][1])

    def next_image(self):
        if not self.files:
            return
        self.index = (self.index + 1) % len(self.files)
        self.show_current()
        self._restart_slideshow_timer()

    def prev_image(self):
        if not self.files:
            return
        self.index = (self.index - 1) % len(self.files)
        self.show_current()
        self._restart_slideshow_timer()

    def _on_interval_changed(self, _idx):
        if self.slideshow_active and not self.slideshow_paused:
            self.slideshow_timer.start(INTERVALS[self.interval_box.currentIndex()][1])

    def toggle_slideshow(self):
        if self.slideshow_active:
            self.stop_slideshow()
        else:
            self.start_slideshow()

    def toggle_pause_or_next(self):
        if self.slideshow_active:
            if self.slideshow_paused:
                self.resume_slideshow()
            else:
                self.pause_slideshow()
        else:
            self.next_image()

    def start_slideshow(self):
        if not self.files:
            return
        self.slideshow_active = True
        self.slideshow_paused = False
        self.view.left_click_enabled = True
        self.nav_bar.hide()
        self.btn_slideshow.setText("\u23f9 \u505c\u6b62\u5e7b\u71c8\u7247 (F5)")
        self.slideshow_timer.start(INTERVALS[self.interval_box.currentIndex()][1])
        if not self.isFullScreen():
            self.showFullScreen()

    def pause_slideshow(self):
        if self.slideshow_active and not self.slideshow_paused:
            self.slideshow_paused = True
            self.slideshow_timer.stop()
            self.btn_slideshow.setText("\u25b6 \u7e7c\u7e8c\u5e7b\u71c8\u7247 (F5)")

    def resume_slideshow(self):
        if self.slideshow_active and self.slideshow_paused:
            self.slideshow_paused = False
            self.slideshow_timer.start(INTERVALS[self.interval_box.currentIndex()][1])
            self.btn_slideshow.setText("\u23f9 \u505c\u6b62\u5e7b\u71c8\u7247 (F5)")

    def stop_slideshow(self):
        self.slideshow_active = False
        self.slideshow_paused = False
        self.view.left_click_enabled = False
        self.nav_bar.show()
        self.slideshow_timer.stop()
        self.btn_slideshow.setText("\u25b6 \u64ad\u653e\u5e7b\u71c8\u7247 (F5)")
        if self.isFullScreen():
            self.showNormal()

    def on_escape(self):
        if self.slideshow_active:
            self.stop_slideshow()
        elif self.isFullScreen():
            self.showNormal()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PhotoViewer")
    initial = sys.argv[1] if len(sys.argv) > 1 else None
    w = PhotoViewer(initial)
    w.show()
    app.exec()


if __name__ == "__main__":
    main()
