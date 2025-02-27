from qtsymbols import *
import os, functools
from traceback import print_exc
from myutils.wrapper import threader, Singleton_close
from myutils.utils import find_or_create_uid, duplicateconfig
from myutils.hwnd import getExeIcon
import gobject, hashlib
from gui.inputdialog import autoinitdialog
from gui.dynalang import LFormLayout, LDialog
from myutils.localetools import localeswitchedrun
from myutils.config import (
    savehook_new_data,
    savegametaged,
    uid2gamepath,
    get_launchpath,
    _TR,
    savehook_new_list,
    globalconfig,
)
from gui.usefulwidget import (
    getIconButton,
    getsimplecombobox,
    getspinbox,
    getcolorbutton,
    getsimpleswitch,
    getsimplepatheditor,
    getspinbox,
    selectcolor,
    SplitLine,
)


def showcountgame(window, num):
    if num:
        window.setWindowTitle("游戏管理____-_" + str(num))
    else:
        window.setWindowTitle("游戏管理")


class ItemWidget(QWidget):
    focuschanged = pyqtSignal(bool, str)
    doubleclicked = pyqtSignal(str)
    globallashfocus = None

    @classmethod
    def clearfocus(cls):
        try:  # 可能已被删除
            if ItemWidget.globallashfocus:
                ItemWidget.globallashfocus.focusOut()
        except:
            pass
        ItemWidget.globallashfocus = None

    def click(self):
        try:
            self.bottommask.show()
            if self != ItemWidget.globallashfocus:
                ItemWidget.clearfocus()
            ItemWidget.globallashfocus = self
            self.focuschanged.emit(True, self.gameuid)
        except:
            print_exc()

    def mousePressEvent(self, ev) -> None:
        self.click()

    def focusOut(self):
        self.bottommask.hide()
        self.focuschanged.emit(False, self.gameuid)

    def mouseDoubleClickEvent(self, e):
        self.doubleclicked.emit(self.gameuid)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.bottommask.resize(a0.size())
        self.maskshowfileexists.resize(a0.size())
        self.resizex()

    def resizex(self):
        margin = globalconfig["dialog_savegame_layout"]["margin"]
        textH = (
            globalconfig["dialog_savegame_layout"]["textH"]
            if globalconfig["showgametitle"]
            else 0
        )
        self._w.setFixedHeight(self.height() - textH)
        self.wrap.setContentsMargins(margin, margin, margin, margin)

    def others(self):
        self._lb.setText(self.file if globalconfig["showgametitle"] else "")
        self.resizex()
        self._img.switch()

    def __init__(self, gameuid, pixmap, file) -> None:
        super().__init__()
        self.file = file
        self.maskshowfileexists = QLabel(self)
        exists = os.path.exists(get_launchpath(gameuid))
        self.maskshowfileexists.setObjectName("savegame_exists" + str(exists))
        self.bottommask = QLabel(self)
        self.bottommask.hide()
        self.bottommask.setObjectName("savegame_onselectcolor1")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._img = IMGWidget(pixmap)
        _w = QWidget()
        _w.setStyleSheet("background-color: rgba(255,255,255, 0);")
        wrap = QVBoxLayout()
        _w.setLayout(wrap)
        self._w = _w
        wrap.addWidget(self._img)
        self.wrap = wrap
        layout.addWidget(_w)
        layout.setSpacing(0)
        self._lb = QLabel()
        self._lb.setText(file if globalconfig["showgametitle"] else "")
        self._lb.setWordWrap(True)
        self._lb.setObjectName("savegame_textfont1")
        self._lb.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._lb)
        self.setLayout(layout)
        self.gameuid = gameuid


class IMGWidget(QLabel):

    def adaptsize(self, size: QSize):

        if globalconfig["imagewrapmode"] == 0:
            h, w = size.height(), size.width()
            r = float(w) / h
            max_r = float(self.width()) / self.height()
            if r < max_r:
                new_w = self.width()
                new_h = int(new_w / r)
            else:
                new_h = self.height()
                new_w = int(new_h * r)
            return QSize(new_w, new_h)
        elif globalconfig["imagewrapmode"] == 1:
            h, w = size.height(), size.width()
            r = float(w) / h
            max_r = float(self.width()) / self.height()
            if r > max_r:
                new_w = self.width()
                new_h = int(new_w / r)
            else:
                new_h = self.height()
                new_w = int(new_h * r)
            return QSize(new_w, new_h)
        elif globalconfig["imagewrapmode"] == 2:
            return self.size()
        elif globalconfig["imagewrapmode"] == 3:
            return size

    def setimg(self, pixmap: QPixmap):
        if not (self.height() and self.width()):
            return
        if self.__last == (self.size(), globalconfig["imagewrapmode"]):
            return
        self.__last = (self.size(), globalconfig["imagewrapmode"])
        rate = self.devicePixelRatioF()
        newpixmap = QPixmap(self.size() * rate)
        newpixmap.setDevicePixelRatio(rate)
        newpixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(newpixmap)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(self.getrect(pixmap.size()), pixmap)
        painter.end()
        self.setPixmap(newpixmap)

    def getrect(self, size):
        size = self.adaptsize(size)
        rect = QRect()
        rect.setX(int((self.width() - size.width()) / 2))
        rect.setY(int((self.height() - size.height()) / 2))
        rect.setSize(size)
        return rect

    def resizeEvent(self, a0):
        self.setimg(self._pixmap)
        return super().resizeEvent(a0)

    def __init__(self, pixmap) -> None:
        super().__init__()
        self.setScaledContents(True)
        if type(pixmap) != QPixmap:
            pixmap = pixmap()
        self._pixmap = pixmap
        self.__last = None

    def switch(self):
        self.setimg(self._pixmap)


class ClickableLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setClickable(True)

    def setClickable(self, clickable):
        self._clickable = clickable

    def mousePressEvent(self, event):
        if self._clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    clicked = pyqtSignal()


class tagitem(QFrame):
    # search game
    TYPE_SEARCH = 0
    TYPE_DEVELOPER = 1
    TYPE_TAG = 2
    TYPE_USERTAG = 3
    TYPE_EXISTS = 4
    removesignal = pyqtSignal(tuple)
    labelclicked = pyqtSignal(tuple)

    @staticmethod
    def setstyles(parent: QWidget):
        parent.setStyleSheet(
            """
            tagitem#red {
                border: 1px solid red;
            }
            tagitem#black {
                border: 1px solid black;
            }
            tagitem#green {
                border: 1px solid green;
            }
            tagitem#blue {
                border: 1px solid blue;
            }
            tagitem#yellow {
                border: 1px solid yellow;
            }
        """
        )

    def __init__(self, tag, removeable=True, _type=TYPE_SEARCH, refdata=None) -> None:
        super().__init__()
        if _type == tagitem.TYPE_SEARCH:
            border_color = "black"
        elif _type == tagitem.TYPE_DEVELOPER:
            border_color = "red"
        elif _type == tagitem.TYPE_TAG:
            border_color = "green"
        elif _type == tagitem.TYPE_USERTAG:
            border_color = "blue"
        elif _type == tagitem.TYPE_EXISTS:
            border_color = "yellow"
        self.setObjectName(border_color)

        tagLayout = QHBoxLayout()
        tagLayout.setContentsMargins(0, 0, 0, 0)
        tagLayout.setSpacing(0)

        key = (tag, _type, refdata)
        self.setLayout(tagLayout)
        lb = ClickableLabel()
        lb.setStyleSheet("background: transparent;")
        lb.setText(tag)
        lb.clicked.connect(functools.partial(self.labelclicked.emit, key))
        if removeable:
            button = getIconButton(
                functools.partial(self.removesignal.emit, key), icon="fa.times"
            )
            tagLayout.addWidget(button)
        tagLayout.addWidget(lb)


def opendirforgameuid(gameuid):
    f = get_launchpath(gameuid)
    f = os.path.dirname(f)
    if os.path.exists(f) and os.path.isdir(f):
        os.startfile(f)


def startgame(gameuid):
    try:
        game = get_launchpath(gameuid)
        if os.path.exists(game):
            mode = savehook_new_data[gameuid]["onloadautochangemode2"]
            if mode > 0:
                _ = {1: "texthook", 2: "copy", 3: "ocr"}
                if globalconfig["sourcestatus2"][_[mode]]["use"] == False:
                    globalconfig["sourcestatus2"][_[mode]]["use"] = True

                    for k in globalconfig["sourcestatus2"]:
                        globalconfig["sourcestatus2"][k]["use"] = k == _[mode]
                        try:
                            getattr(gobject.baseobject.settin_ui, "sourceswitchs")[
                                k
                            ].setChecked(k == _[mode])
                        except:
                            pass

                    gobject.baseobject.starttextsource(use=_[mode], checked=True)

            threader(localeswitchedrun)(gameuid)

    except:
        print_exc()


def __b64string(a: str):
    return hashlib.md5(a.encode("utf8")).hexdigest()


def __scaletosize(_pix: QPixmap, tgt):

    if max(_pix.width(), _pix.height()) > 400:

        if _pix.width() > _pix.height():
            sz = QSize(400, 400 * _pix.height() // _pix.width())
        else:
            sz = QSize(400, _pix.width() * 400 // _pix.height())
        _pix = _pix.scaled(
            sz,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    _pix.save(tgt)


def getcachedimage(src, small):
    if not small:
        _pix = QPixmap(src)
        if _pix.isNull():
            return None
        return _pix
    if not os.path.exists(src):
        return None
    src2 = gobject.getcachedir("icon2/{}.jpg".format(__b64string(src)))
    _pix = QPixmap(src2)
    if not _pix.isNull():
        return _pix
    _pix = QPixmap(src)
    if _pix.isNull():
        return None
    __scaletosize(_pix, src2)
    return _pix


def getpixfunction(kk, small=False, iconfirst=False):
    if iconfirst:
        if (
            savehook_new_data[kk].get("currenticon")
            in savehook_new_data[kk]["imagepath_all"]
        ):
            src = savehook_new_data[kk].get("currenticon")
            pix = getcachedimage(src, small)
            if pix:
                return pix
        _pix = getExeIcon(uid2gamepath[kk], False, cache=True)
        return _pix
    if (
        savehook_new_data[kk].get("currentmainimage")
        in savehook_new_data[kk]["imagepath_all"]
    ):
        src = savehook_new_data[kk].get("currentmainimage")
        pix = getcachedimage(src, small)
        if pix:
            return pix
    for _ in savehook_new_data[kk]["imagepath_all"]:
        pix = getcachedimage(_, small)
        if pix:
            return pix
    _pix = getExeIcon(uid2gamepath[kk], False, cache=True)
    return _pix


def startgamecheck(self, reflist, gameuid):
    if not gameuid:
        return
    if not os.path.exists(get_launchpath(gameuid)):
        return
    if globalconfig["startgamenototop"] == False:
        idx = reflist.index(gameuid)
        reflist.insert(0, reflist.pop(idx))
    self.parent().parent().close()
    startgame(gameuid)


def addgamesingle(parent, callback, targetlist):
    f = QFileDialog.getOpenFileName(options=QFileDialog.Option.DontResolveSymlinks)

    res = f[0]
    if res == "":
        return
    res = os.path.normpath(res)
    uid = find_or_create_uid(targetlist, res)
    if uid in targetlist:
        idx = targetlist.index(uid)
        response = QMessageBox.question(
            parent,
            "",
            _TR("游戏已存在，是否重复添加？"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response == QMessageBox.StandardButton.No:
            if idx == 0:
                return
            targetlist.pop(idx)
        else:
            uid = duplicateconfig(uid)
    targetlist.insert(0, uid)
    callback(uid)


def addgamebatch_x(callback, targetlist, paths):
    for path in paths:
        if not os.path.isfile(path):
            continue
        path = os.path.normpath(path)
        uid = find_or_create_uid(targetlist, path)
        if uid in targetlist:
            targetlist.pop(targetlist.index(uid))
        targetlist.insert(0, uid)
        callback(uid)


def addgamebatch(callback, targetlist):
    res = QFileDialog.getExistingDirectory(
        options=QFileDialog.Option.DontResolveSymlinks
    )
    if res == "":
        return
    paths = []
    for _dir, _, _fs in os.walk(res):
        for _f in _fs:
            path = os.path.normpath(os.path.abspath(os.path.join(_dir, _f)))
            if path.lower().endswith(".exe") == False:
                continue
            paths.append(path)
    addgamebatch_x(callback, targetlist, paths)


def loadvisinternal(skipid=False, skipidid=None):
    __vis = []
    __uid = []
    for _ in savegametaged:
        if _ is None:
            __vis.append("GLOBAL")
            __uid.append(None)
        else:
            __vis.append(_["title"])
            __uid.append(_["uid"])
        if skipid:
            if skipidid == __uid[-1]:
                __uid.pop(-1)
                __vis.pop(-1)
    return __vis, __uid


def getalistname(parent, callback, skipid=False, skipidid=None, title="添加到列表"):
    __d = {"k": 0}
    __vis, __uid = loadvisinternal(skipid, skipidid)

    def __wrap(callback, __d, __uid):
        if len(__uid) == 0:
            return

        uid = __uid[__d["k"]]
        callback(uid)

    if len(__uid) > 1:
        autoinitdialog(
            parent,
            __d,
            title,
            600,
            [
                {
                    "type": "combo",
                    "name": "目标列表",
                    "k": "k",
                    "list": __vis,
                },
                {
                    "type": "okcancel",
                    "callback": functools.partial(__wrap, callback, __d, __uid),
                },
            ],
            exec_=True
        )
    elif len(__uid):

        callback(__uid[0])


def calculatetagidx(tagid):
    i = 0
    for save in savegametaged:
        if save is None and tagid is None:
            return i
        elif save and tagid and save["uid"] == tagid:
            return i
        i += 1

    return None


def getreflist(reftagid):
    _idx = calculatetagidx(reftagid)
    if _idx is None:
        return None
    tag = savegametaged[_idx]
    if tag is None:
        return savehook_new_list
    return tag["games"]


@Singleton_close
class dialog_syssetting(LDialog):
    def selectfont(self, key, fontstring):
        globalconfig[key] = fontstring

        self.parent().setstyle()

    def closeEvent(self, e):
        self.parent().callchange()

    def __init__(self, parent, type_=1) -> None:
        super().__init__(parent, Qt.WindowType.WindowCloseButtonHint)
        self.setWindowTitle("其他设置")
        formLayout = LFormLayout(self)

        formLayout.addRow(
            "隐藏不存在的游戏",
            getsimpleswitch(globalconfig, "hide_not_exists"),
        )

        formLayout.addRow(
            "启动游戏不修改顺序",
            getsimpleswitch(globalconfig, "startgamenototop"),
        )

        formLayout.addRow(SplitLine())
        if type_ == 1:
            for key, name in [
                ("itemw", "宽度"),
                ("itemh", "高度"),
                ("margin", "边距"),
                ("textH", "文字区高度"),
            ]:
                formLayout.addRow(
                    name,
                    getspinbox(0, 1000, globalconfig["dialog_savegame_layout"], key),
                )
            formLayout.addRow(
                "字体",
                getsimplepatheditor(
                    text=globalconfig.get("savegame_textfont1", ""),
                    callback=functools.partial(self.selectfont, "savegame_textfont1"),
                    icons=("fa.font", "fa.refresh"),
                    isfontselector=True,
                ),
            )
            formLayout.addRow(
                "显示标题",
                getsimpleswitch(globalconfig, "showgametitle"),
            )
            formLayout.addRow(
                "缩放",
                getsimplecombobox(
                    ["填充", "适应", "拉伸", "居中"],
                    globalconfig,
                    "imagewrapmode",
                ),
            )

        elif type_ == 2:
            for key, name in [
                ("listitemheight", "高度"),
            ]:
                formLayout.addRow(
                    name,
                    getspinbox(0, 1000, globalconfig["dialog_savegame_layout"], key),
                )
            formLayout.addRow(
                "字体",
                getsimplepatheditor(
                    text=globalconfig.get("savegame_textfont2", ""),
                    callback=functools.partial(self.selectfont, "savegame_textfont2"),
                    icons=("fa.font", "fa.refresh"),
                    isfontselector=True,
                ),
            )

        formLayout.addRow(SplitLine())
        for key, key2, name in [
            ("backcolor1", "transparent", "颜色"),
            ("onselectcolor1", "transparentselect", "选中时颜色"),
            ("onfilenoexistscolor1", "transparentnotexits", "游戏不存在时颜色"),
        ]:
            formLayout.addRow(
                name,
                getcolorbutton(
                    globalconfig["dialog_savegame_layout"],
                    key,
                    callback=functools.partial(
                        selectcolor,
                        self,
                        globalconfig["dialog_savegame_layout"],
                        key,
                        None,
                        self,
                        key,
                        callback=self.parent().setstyle,
                    ),
                    name=key,
                    parent=self,
                ),
            )
            formLayout.addRow(
                name + "_" + "不透明度",
                getspinbox(
                    0,
                    100,
                    globalconfig["dialog_savegame_layout"],
                    key2,
                    callback=lambda _: self.parent().setstyle(),
                ),
            )
        self.show()
