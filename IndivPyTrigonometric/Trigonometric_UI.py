# -*- coding: utf-8 -*-
from importlib import reload
import os
import sys

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

try:
    from PySide6 import QtCore, QtWidgets, QtGui
    from shiboken6 import wrapInstance
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui
    from shiboken2 import wrapInstance


COLOR_GREEN = [0.3, 0.9, 0.3]
COLOR_RED = [0.9, 0.3, 0.3]
TRIGONOMETRIC_UI_INSTANCE = None
script_dir = os.path.dirname(__file__)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)


def maya_to_qt(control_name):
    ptr = omui.MQtUtil.findControl(control_name)
    if ptr is None:
        ptr = omui.MQtUtil.findLayout(control_name)
    if ptr is None:
        ptr = omui.MQtUtil.findMenuItem(control_name)

    if ptr is not None:
        return wrapInstance(int(ptr), QtWidgets.QWidget)

    return None


class GifPreviewPopup(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(GifPreviewPopup, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.ToolTip | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setStyleSheet("background-color: #1f1f1f; border: 1px solid #555555;")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.movie = None

    def show_gif(self, gif_path, global_pos):
        if not gif_path or not os.path.exists(gif_path):
            self.hide_popup()
            return

        if self.movie:
            self.movie.stop()

        self.movie = QtGui.QMovie(gif_path)
        if not self.movie.isValid():
            self.hide_popup()
            return

        self.label.setMovie(self.movie)
        self.movie.start()

        size = self.movie.currentPixmap().size()
        if size.isEmpty():
            size = self.movie.frameRect().size()
        if size.isEmpty():
            size = QtCore.QSize(220, 140)

        self.resize(size)
        self.move(global_pos)
        self.show()
        self.raise_()

    def hide_popup(self):
        if self.movie:
            self.movie.stop()
        self.hide()


class TrigImageHoverFilter(QtCore.QObject):
    def __init__(self, window_instance):
        super(TrigImageHoverFilter, self).__init__()
        self.window_instance = window_instance

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if self.window_instance.is_cursor_in_trig_preview_area():
                self.window_instance.trig_image_pressed = True
                self.window_instance.set_trig_preview_cursor(pressed=True)
                self.window_instance.show_trig_gif_popup()
            else:
                self.window_instance.trig_image_pressed = False
                self.window_instance.set_trig_preview_cursor(pressed=False)
                self.window_instance.hide_trig_gif_popup()
        elif event.type() in [QtCore.QEvent.MouseMove, QtCore.QEvent.HoverMove]:
            if self.window_instance.trig_image_pressed and self.window_instance.is_cursor_in_trig_preview_area():
                self.window_instance.set_trig_preview_cursor(pressed=True)
                self.window_instance.show_trig_gif_popup()
            else:
                self.window_instance.set_trig_preview_cursor(pressed=False)
                self.window_instance.hide_trig_gif_popup()
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            self.window_instance.trig_image_pressed = False
            self.window_instance.set_trig_preview_cursor(pressed=False)
            self.window_instance.hide_trig_gif_popup()
        elif event.type() in [QtCore.QEvent.Enter, QtCore.QEvent.HoverEnter]:
            self.window_instance.set_trig_preview_cursor(pressed=False)
        elif event.type() in [
            QtCore.QEvent.Leave,
            QtCore.QEvent.HoverLeave,
        ]:
            if not self.window_instance.trig_image_pressed:
                self.window_instance.clear_trig_preview_cursor()
                self.window_instance.hide_trig_gif_popup()
        return False

class TrigonometricWindow(object):
    WINDOW_NAME = "Trigonometric_Wave"
    DEFAULT_TRIGONOMETRIC = "-"
    VALID_NUMERIC_TYPES = [
        "double",
        "doubleLinear",
        "doubleAngle",
        "float",
        "long",
        "short",
        "byte",
    ]
    TRIG_IMAGE_MAP = {
        "-": "none.png",
        "SIN": "sin.png",
        "COS": "cos.png",
        "TAN": "tan.png",
    }

    def __init__(self):
        self.window = None
        self.form = None
        self.ctrl_form = None
        self.setup_setting_form = None
        self.trig_settings_fl = None
        self.trig_inner_form = None
        self.trig_attr_settings_fl = None
        self.attr_main_setting_form = None
        self.attr_setting_form = None
        self.radio_fl = None

        self.main_ctrl_txt = None
        self.main_ctrl_ul_txt = None
        self.main_ctrl_tf = None
        self.main_ctrl_btn = None
        self.main_ctrl_sep = None

        self.sel_tri_txt = None
        self.sel_option_menu = None
        self.image_tri = None
        self.target_attr_txt = None
        self.target_attr_tf = None
        self.target_pum = None
        self.target_attr_inst = None

        self.target_txt = None
        self.offset_txt = None
        self.wavelength_txt = None
        self.wavelength_offset_txt = None
        self.amplitude_txt = None
        self.speed_txt = None
        self.time_scale_txt = None
        self.on_txt = None
        self.off_txt = None

        self.setting_sep = None
        self.generate_inst_txt = None
        self.generate_btn = None
        self.generate_sep = None

        self.target_coll = None
        self.target_on_rb = None
        self.target_off_rb = None
        self.offset_coll = None
        self.offset_on_rb = None
        self.offset_off_rb = None
        self.wave_coll = None
        self.wave_on_rb = None
        self.wave_off_rb = None
        self.wave_off_coll = None
        self.wave_off_on_rb = None
        self.wave_off_off_rb = None
        self.amp_coll = None
        self.amp_on_rb = None
        self.amp_off_rb = None
        self.speed_coll = None
        self.speed_on_rb = None
        self.speed_off_rb = None
        self.time_scale_coll = None
        self.time_scale_on_rb = None
        self.time_scale_off_rb = None

        self.radio_attr_map = {}
        self.image_tri_widget = None
        self.trig_inner_widget = None
        self.gif_popup = None
        self.trig_image_hover_filter = None
        self.trig_image_pressed = False
        self.show()

    def show(self):
        self._delete_existing_window()
        self._build_ui()
        cmds.showWindow(self.window)
        self._update_trig_image()
        self._install_trig_gif_hover()
        return self

    def _delete_existing_window(self):
        if cmds.window(self.WINDOW_NAME, q=True, exists=True):
            cmds.deleteUI(self.WINDOW_NAME, window=True)

    def _build_ui(self):
        self.window = cmds.window(self.WINDOW_NAME,title=self.WINDOW_NAME,menuBar=True,widthHeight=(200, 300),sizeable=True,resizeToFitChildren=True,)
        cmds.menu(l='Help')
        cmds.menuItem(l='- Instruction', divider=True)
        cmds.menuItem(l='Tutorial', i='menuIconHelp.png', c=lambda x:self.TutorialHelp())
        cmds.menuItem(l='Notes', i='SP_FileIcon.png', c=lambda x:self.NotesLogList())
        cmds.menuItem(divider=True)
        cmds.menu(l='Reload')
        cmds.menuItem(l='- ReloadUI', divider=True)
        cmds.menuItem(l='Reload',i='QR_refresh.png',en=True,c=lambda x:self.reload_UI())
        cmds.menuItem(divider=True)

        self.form = cmds.formLayout()

        self.ctrl_form = cmds.formLayout(p=self.form)
        cmds.formLayout(self.form,e=True,attachForm=[(self.ctrl_form, "top", 5),(self.ctrl_form, "left", 5),(self.ctrl_form, "right", 5)],)

        self.main_ctrl_txt = cmds.text(l=" 1. MainController", p=self.ctrl_form)
        self.main_ctrl_ul_txt = cmds.text(l=" ______________________", p=self.ctrl_form)
        self.main_ctrl_tf = cmds.textField(pht="< Controller Input >", h=20, en=True, p=self.ctrl_form)
        self.main_ctrl_btn = cmds.button(l="Grab", w=50,h=18,bgc=(0.4, 0.4, 0.4),p=self.ctrl_form,c=lambda *_: self.mainCtrlFunc(),)
        self.main_ctrl_sep = cmds.separator(style="none", p=self.ctrl_form)

        cmds.formLayout(self.ctrl_form,e=True,attachControl=[(self.main_ctrl_tf, "top", 5, self.main_ctrl_ul_txt),
                                                             (self.main_ctrl_tf, "right", 5, self.main_ctrl_btn),
                                                             (self.main_ctrl_btn, "top", 6, self.main_ctrl_ul_txt),
                                                             (self.main_ctrl_sep, "top", 10, self.main_ctrl_btn)],
                                                 attachForm=[(self.main_ctrl_tf, "top", 0),
                                                             (self.main_ctrl_tf, "left", 0),
                                                             (self.main_ctrl_ul_txt, "top", 2),
                                                             (self.main_ctrl_btn, "right", 0)])

        self.setup_setting_form = cmds.formLayout(p=self.form)
        cmds.formLayout(self.form,e=True,attachControl=[(self.setup_setting_form, "top", 0, self.ctrl_form)],
                                            attachForm=[(self.setup_setting_form, "left", 5),
                                                        (self.setup_setting_form, "right", 5)])

        self.trig_settings_fl = cmds.frameLayout(l="Trigonometric Settings",la="center",cll=True,mw=1,mh=1,p=self.setup_setting_form,)
        cmds.formLayout(self.setup_setting_form,e=True,attachForm=[(self.trig_settings_fl, "left", 0),
                                                                   (self.trig_settings_fl, "right", 0)],)

        self.trig_inner_form = cmds.formLayout(p=self.trig_settings_fl)

        self.sel_tri_txt = cmds.text(l="Trigonometric     :", p=self.trig_inner_form)
        self.sel_option_menu = cmds.optionMenu(h=20,p=self.trig_inner_form,cc=lambda *_: self.trigOptionToggle(),)
        cmds.menuItem(l="-", parent=self.sel_option_menu)
        cmds.menuItem(l="SIN", parent=self.sel_option_menu)
        cmds.menuItem(l="COS", parent=self.sel_option_menu)
        cmds.menuItem(l="TAN", parent=self.sel_option_menu)

        self.image_tri = cmds.image(i=self._get_trig_image_path(self.DEFAULT_TRIGONOMETRIC),p=self.trig_inner_form,pma=True)

        self.target_attr_txt = cmds.text(l="Target_Attribute :", p=self.trig_inner_form)
        self.target_attr_tf = cmds.textField(pht="< Attribute Choose >", p=self.trig_inner_form)
        self.target_pum = cmds.popupMenu(p=self.target_attr_tf)
        cmds.menuItem(dl="- Manual", d=True, p=self.target_pum)
        cmds.menuItem(l="Insert_Selection", p=self.target_pum, c=lambda *_: self.manualSelAttrFunc())
        cmds.menuItem(dl="- Preset", d=True, p=self.target_pum)
        cmds.menuItem(l=".translateX", p=self.target_pum, c=lambda *_: self.presetAttrFunc(".translateX"))
        cmds.menuItem(l=".translateY", p=self.target_pum, c=lambda *_: self.presetAttrFunc(".translateY"))
        cmds.menuItem(l=".translateZ", p=self.target_pum, c=lambda *_: self.presetAttrFunc(".translateZ"))
        cmds.menuItem(l=".rotateX", p=self.target_pum, c=lambda *_: self.presetAttrFunc(".rotateX"))
        cmds.menuItem(l=".rotateY", p=self.target_pum, c=lambda *_: self.presetAttrFunc(".rotateY"))
        cmds.menuItem(l=".rotateZ", p=self.target_pum, c=lambda *_: self.presetAttrFunc(".rotateZ"))

        self.target_attr_inst = cmds.text(l="*Right Click to Choose",en=False,fn="obliqueLabelFont",p=self.trig_inner_form)

        cmds.formLayout(self.trig_inner_form,e=True,attachControl=[(self.sel_option_menu, "left", 2, self.sel_tri_txt),
                                                                   (self.sel_option_menu, "right", 5, self.image_tri),
                                                                   (self.target_attr_txt, "top", 10, self.sel_tri_txt),
                                                                   (self.target_attr_tf, "top", 3, self.sel_option_menu),
                                                                   (self.target_attr_tf, "left", 2, self.target_attr_txt),
                                                                   (self.target_attr_inst, "top", 0, self.target_attr_tf)],
                                                        attachForm=[(self.sel_tri_txt, "top", 5),
                                                                    (self.sel_tri_txt, "left", 2),
                                                                    (self.sel_option_menu, "top", 2),
                                                                    (self.image_tri, "top", 2),
                                                                    (self.image_tri, "right", 0),
                                                                    (self.target_attr_txt, "left", 2),
                                                                    (self.target_attr_tf, "left", 5),
                                                                    (self.target_attr_tf, "right", 0),
                                                                    (self.target_attr_inst, "left", 0),
                                                                    (self.target_attr_inst, "right", 0)])

        self.trig_attr_settings_fl = cmds.frameLayout(l="Attribute Settings",la="center",cll=True,mw=1,mh=1,p=self.setup_setting_form,)
        cmds.formLayout(self.setup_setting_form,e=True,attachControl=[(self.trig_attr_settings_fl, "top", 5, self.trig_settings_fl)],
                                                          attachForm=[(self.trig_attr_settings_fl, "left", 0),
                                                                      (self.trig_attr_settings_fl, "right", 0)])

        self.attr_main_setting_form = cmds.formLayout(p=self.trig_attr_settings_fl)
        self.attr_setting_form = cmds.formLayout(p=self.attr_main_setting_form)
        cmds.formLayout(self.attr_main_setting_form, e=True, attachForm=[(self.attr_setting_form, "left", 5)])

        self.target_txt = cmds.text(l="Target_Blend", p=self.attr_setting_form)
        self.offset_txt = cmds.text(l="Offset", p=self.attr_setting_form)
        self.wavelength_txt = cmds.text(l="WaveLength", p=self.attr_setting_form)
        self.wavelength_offset_txt = cmds.text(l="WaveLength_Offset", p=self.attr_setting_form)
        self.amplitude_txt = cmds.text(l="Amplitude", p=self.attr_setting_form)
        self.speed_txt = cmds.text(l="Speed", p=self.attr_setting_form)
        self.time_scale_txt = cmds.text(l="Time_Scale", p=self.attr_setting_form)

        cmds.formLayout(self.attr_setting_form,e=True,attachControl=[(self.offset_txt, "top", 2, self.target_txt),
                                                                     (self.wavelength_txt, "top", 2, self.offset_txt),
                                                                     (self.wavelength_offset_txt, "top", 2, self.wavelength_txt),
                                                                     (self.amplitude_txt, "top", 2, self.wavelength_offset_txt),
                                                                     (self.speed_txt, "top", 2, self.amplitude_txt),
                                                                     (self.time_scale_txt, "top", 2, self.speed_txt)],
                                                         attachForm=[(self.target_txt, "top", 15),
                                                                     (self.target_txt, "left", 2),
                                                                     (self.offset_txt, "left", 2),
                                                                     (self.wavelength_txt, "left", 2),
                                                                     (self.wavelength_offset_txt, "left", 2),
                                                                     (self.amplitude_txt, "left", 2),
                                                                     (self.speed_txt, "left", 2),
                                                                     (self.time_scale_txt, "left", 2)])

        self.radio_fl = cmds.formLayout(p=self.attr_main_setting_form)
        cmds.formLayout(self.attr_main_setting_form,e=True,attachForm=[(self.radio_fl, "right", 0)],
                                                        attachControl=[(self.radio_fl, "left", 10, self.attr_setting_form)])

        self.on_txt = cmds.text(l="ON", p=self.radio_fl)
        self.off_txt = cmds.text(l="OFF", p=self.radio_fl)

        self.target_coll = cmds.radioCollection(p=self.radio_fl)
        self.target_on_rb = cmds.radioButton(l="", sl=True, collection=self.target_coll, p=self.radio_fl)
        self.target_off_rb = cmds.radioButton(l="", collection=self.target_coll, p=self.radio_fl)
        self.offset_coll = cmds.radioCollection(p=self.radio_fl)
        self.offset_on_rb = cmds.radioButton(l="", sl=True, collection=self.offset_coll, p=self.radio_fl)
        self.offset_off_rb = cmds.radioButton(l="", collection=self.offset_coll, p=self.radio_fl)
        self.wave_coll = cmds.radioCollection(p=self.radio_fl)
        self.wave_on_rb = cmds.radioButton(l="", sl=True, collection=self.wave_coll, p=self.radio_fl)
        self.wave_off_rb = cmds.radioButton(l="", collection=self.wave_coll, p=self.radio_fl)
        self.wave_off_coll = cmds.radioCollection(p=self.radio_fl)
        self.wave_off_on_rb = cmds.radioButton(l="", sl=True, collection=self.wave_off_coll, p=self.radio_fl)
        self.wave_off_off_rb = cmds.radioButton(l="", collection=self.wave_off_coll, p=self.radio_fl)
        self.amp_coll = cmds.radioCollection(p=self.radio_fl)
        self.amp_on_rb = cmds.radioButton(l="", sl=True, collection=self.amp_coll, p=self.radio_fl)
        self.amp_off_rb = cmds.radioButton(l="", collection=self.amp_coll, p=self.radio_fl)
        self.speed_coll = cmds.radioCollection(p=self.radio_fl)
        self.speed_on_rb = cmds.radioButton(l="", sl=True, collection=self.speed_coll, p=self.radio_fl)
        self.speed_off_rb = cmds.radioButton(l="", collection=self.speed_coll, p=self.radio_fl)
        self.time_scale_coll = cmds.radioCollection(p=self.radio_fl)
        self.time_scale_on_rb = cmds.radioButton(l="", sl=True, collection=self.time_scale_coll, p=self.radio_fl)
        self.time_scale_off_rb = cmds.radioButton(l="", collection=self.time_scale_coll, p=self.radio_fl)

        cmds.formLayout(self.radio_fl,e=True,attachControl=[(self.target_off_rb, "right", 2, self.target_on_rb),
                                                            (self.offset_on_rb, "top", 1, self.target_on_rb),
                                                            (self.offset_off_rb, "top", 1, self.target_off_rb),
                                                            (self.wave_on_rb, "top", 1, self.offset_on_rb),
                                                            (self.wave_off_rb, "top", 1, self.offset_off_rb),
                                                            (self.wave_off_on_rb, "top", 1, self.wave_on_rb),
                                                            (self.wave_off_off_rb, "top", 1, self.wave_off_rb),
                                                            (self.amp_on_rb, "top", 1, self.wave_off_on_rb),
                                                            (self.amp_off_rb, "top", 1, self.wave_off_off_rb),
                                                            (self.speed_on_rb, "top", 1, self.amp_on_rb),
                                                            (self.speed_off_rb, "top", 1, self.amp_off_rb),
                                                            (self.time_scale_on_rb, "top", 1, self.speed_on_rb),
                                                            (self.time_scale_off_rb, "top", 1, self.speed_off_rb)],
                                                 attachForm=[(self.target_on_rb, "top", 16),(self.target_off_rb, "top", 16)],
                                                 attachPosition=[(self.on_txt, "right", 0, 30),
                                                                 (self.off_txt, "left", 0, 62),
                                                                 (self.target_on_rb, "right", 0, 29),
                                                                 (self.target_off_rb, "left", 0, 65),
                                                                 (self.offset_on_rb, "right", 0, 29),
                                                                 (self.offset_off_rb, "left", 0, 65),
                                                                 (self.wave_on_rb, "right", 0, 29),
                                                                 (self.wave_off_rb, "left", 0, 65),
                                                                 (self.wave_off_on_rb, "right", 0, 29),
                                                                 (self.wave_off_off_rb, "left", 0, 65),
                                                                 (self.amp_on_rb, "right", 0, 29),
                                                                 (self.amp_off_rb, "left", 0, 65),
                                                                 (self.speed_on_rb, "right", 0, 29),
                                                                 (self.speed_off_rb, "left", 0, 65),
                                                                 (self.time_scale_on_rb, "right", 0, 29),
                                                                 (self.time_scale_off_rb, "left", 0, 65)])

        self.radio_attr_map = {
            "target": {"on": self.target_on_rb, "off": self.target_off_rb},
            "offset": {"on": self.offset_on_rb, "off": self.offset_off_rb},
            "wavelength": {"on": self.wave_on_rb, "off": self.wave_off_rb},
            "wavelengthOffset": {"on": self.wave_off_on_rb, "off": self.wave_off_off_rb},
            "amplitude": {"on": self.amp_on_rb, "off": self.amp_off_rb},
            "speed": {"on": self.speed_on_rb, "off": self.speed_off_rb},
            "timeScale": {"on": self.time_scale_on_rb, "off": self.time_scale_off_rb},
        }

        self.setting_sep = cmds.separator(style="in", p=self.attr_main_setting_form)
        cmds.formLayout(self.attr_main_setting_form,e=True,attachControl=[(self.setting_sep, "top", 10, self.attr_setting_form)],
                                                              attachForm=[(self.setting_sep, "left", 0),
                                                                          (self.setting_sep, "right", 0)])

        self.generate_inst_txt = cmds.text(l="- Select controller null to set -", p=self.setup_setting_form)
        self.generate_btn = cmds.button(l="Generate",h=25,p=self.setup_setting_form,c=lambda *_: self.generateFunc())
        self.generate_sep = cmds.separator(style="none", p=self.setup_setting_form)
        cmds.formLayout(self.setup_setting_form,e=True,attachControl=[(self.generate_inst_txt, "top", 0, self.trig_attr_settings_fl),
                                                                       (self.generate_btn, "top", 4, self.generate_inst_txt),
                                                                       (self.generate_sep, "top", 10, self.generate_btn)],
                                                          attachForm=[(self.generate_inst_txt, "left", 0),
                                                                       (self.generate_inst_txt, "right", 0),
                                                                       (self.generate_btn, "left", 0),
                                                                       (self.generate_btn, "right", 0)])

    def _get_root_dir(self):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _get_icon_dir(self):
        return os.path.join(self._get_root_dir(), "Icon_Trigonometric")

    def _get_gif_dir(self):
        return os.path.join(self._get_root_dir(), "Gifs")

    def _get_trig_image_path(self, trig_label):
        trig_key = (trig_label or self.DEFAULT_TRIGONOMETRIC)
        trig_key = trig_key.upper() if trig_key != "-" else "-"
        file_name = self.TRIG_IMAGE_MAP.get(trig_key, self.TRIG_IMAGE_MAP["-"])
        return os.path.join(self._get_icon_dir(), file_name).replace("\\", "/")

    def _get_trig_gif_path(self, trig_label):
        if not trig_label or trig_label == "-":
            return None
        file_name = "{0}.gif".format(trig_label.lower())
        return os.path.join(self._get_gif_dir(), file_name).replace("\\", "/")

    def _install_trig_gif_hover(self):
        self.image_tri_widget = maya_to_qt(self.image_tri)
        self.trig_inner_widget = maya_to_qt(self.trig_inner_form)

        if not self.image_tri_widget:
            return

        self.gif_popup = GifPreviewPopup(self.image_tri_widget.window())
        self.trig_image_hover_filter = TrigImageHoverFilter(self)
        self.image_tri_widget.setMouseTracking(True)
        self.image_tri_widget.setAttribute(QtCore.Qt.WA_Hover, True)
        self.image_tri_widget.setToolTip("Trigonometric Preview")
        self.image_tri_widget.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
        self.image_tri_widget.installEventFilter(self.trig_image_hover_filter)

        for child_widget in self.image_tri_widget.findChildren(QtWidgets.QWidget):
            child_widget.setMouseTracking(True)
            child_widget.setAttribute(QtCore.Qt.WA_Hover, True)
            child_widget.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))
            child_widget.installEventFilter(self.trig_image_hover_filter)

        if self.trig_inner_widget:
            self.trig_inner_widget.setMouseTracking(True)
            self.trig_inner_widget.setAttribute(QtCore.Qt.WA_Hover, True)
            self.trig_inner_widget.installEventFilter(self.trig_image_hover_filter)

    def set_trig_preview_cursor(self, pressed=False):
        cursor_shape = QtCore.Qt.ClosedHandCursor if pressed else QtCore.Qt.OpenHandCursor

        if self.image_tri_widget:
            self.image_tri_widget.setCursor(QtGui.QCursor(cursor_shape))

            for child_widget in self.image_tri_widget.findChildren(QtWidgets.QWidget):
                child_widget.setCursor(QtGui.QCursor(cursor_shape))

    def clear_trig_preview_cursor(self):
        if self.image_tri_widget:
            self.image_tri_widget.unsetCursor()

            for child_widget in self.image_tri_widget.findChildren(QtWidgets.QWidget):
                child_widget.unsetCursor()

    def is_cursor_in_trig_preview_area(self, padding=5):
        if not self.image_tri_widget:
            return False

        rect = self.image_tri_widget.rect().adjusted(-padding, -padding, padding, padding)
        cursor_pos = self.image_tri_widget.mapFromGlobal(QtGui.QCursor.pos())
        return rect.contains(cursor_pos)

    def show_trig_gif_popup(self):
        if not self.gif_popup or not self.image_tri_widget:
            return

        trig_label = cmds.optionMenu(self.sel_option_menu, q=True, v=True)
        if not trig_label or trig_label == "-":
            self.hide_trig_gif_popup()
            return

        gif_path = self._get_trig_gif_path(trig_label)
        if not gif_path:
            self.hide_trig_gif_popup()
            return

        cursor_pos = QtGui.QCursor.pos()
        popup_pos = QtCore.QPoint(cursor_pos.x() + 20, cursor_pos.y() - 20)
        self.gif_popup.show_gif(gif_path, popup_pos)

    def hide_trig_gif_popup(self):
        if self.gif_popup:
            self.gif_popup.hide_popup()

    def _update_trig_image(self):
        trig_label = cmds.optionMenu(self.sel_option_menu, q=True, v=True)
        if not trig_label or trig_label == "-":
            trig_label = self.DEFAULT_TRIGONOMETRIC

        cmds.image(self.image_tri, e=True, i=self._get_trig_image_path(trig_label))
        return trig_label

    def TutorialHelp(self):
        tutorial_dir = os.path.dirname(os.path.abspath(__file__))
        tutorial_dir = script_dir.replace("IndivPyTrigonometric","Tutorial")
        if os.path.exists(tutorial_dir):
            os.startfile(tutorial_dir)

    def NotesLogList(self):
        log_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = script_dir.replace("IndivPyTrigonometric","Log")
        if os.path.exists(log_dir):
            os.startfile(log_dir)

    def reload_UI(self):
        Trigonometric_UI()

    def mainCtrlFunc(self):
        sel = cmds.ls(sl=True, l=True) or []
        if not sel:
            cmds.textField(self.main_ctrl_tf, e=True, tx="")
            cmds.button(self.main_ctrl_btn, e=True, bgc=COLOR_RED)
            cmds.warning("Please select one main controller as setup")
            return None

        if len(sel) != 1:
            cmds.textField(self.main_ctrl_tf, e=True, tx="")
            cmds.button(self.main_ctrl_btn, e=True, bgc=COLOR_RED)
            cmds.warning("Only one selection controller to input")
            return None

        ctrl = sel[0]
        node_type = cmds.nodeType(ctrl)
        if node_type in ["nurbsCurve", "mesh", "locator"]:
            node_parent = cmds.listRelatives(ctrl, parent=True, fullPath=True) or []
            if node_parent:
                ctrl = node_parent[0]

        cmds.textField(self.main_ctrl_tf, e=True, tx=ctrl)
        cmds.button(self.main_ctrl_btn, e=True, bgc=COLOR_GREEN)
        mel.eval('print("REMINDER : [ {} ] input successful \\n")'.format(ctrl))
        return ctrl

    def trigOptionToggle(self):
        toggle_menu = cmds.optionMenu(self.sel_option_menu, q=True, v=True)
        self._update_trig_image()

        if toggle_menu and toggle_menu != "-":
            mel.eval('print("REMINDER : [ {} ] trigonometric selected \\n")'.format(toggle_menu))

        return toggle_menu

    def manualSelAttrFunc(self):
        c_box = mel.eval('global string $gChannelBoxName; $temp=$gChannelBoxName;')
        attr_box = cmds.channelBox(c_box, q=True, sma=True) or []

        if not attr_box:
            cmds.textField(self.target_attr_tf, e=True, tx="")
            cmds.warning("Please select only one attribute to input")
            return None

        if len(attr_box) != 1:
            cmds.textField(self.target_attr_tf, e=True, tx="")
            cmds.warning("Only one attribute to input")
            return None

        sel = cmds.ls(sl=True, l=True) or []
        if not sel:
            cmds.textField(self.target_attr_tf, e=True, tx="")
            cmds.warning("Please select the controller/object that owns the attribute")
            return None

        obj = sel[0]
        attr = attr_box[0].lstrip(".")
        plug = "{}.{}".format(obj, attr)

        if not cmds.objExists(plug):
            cmds.textField(self.target_attr_tf, e=True, tx="")
            cmds.warning("Attribute does not exist: {}".format(plug))
            return None

        attr_type = cmds.getAttr(plug, type=True)
        if attr_type not in self.VALID_NUMERIC_TYPES:
            cmds.textField(self.target_attr_tf, e=True, tx="")
            cmds.warning(
                "Invalid attribute type: {}. Please select integer or float attribute only.".format(attr_type)
            )
            return None

        long_attr = cmds.attributeQuery(attr, node=obj, longName=True)
        att = ".{}".format(long_attr)

        cmds.textField(self.target_attr_tf, e=True, tx=att)
        mel.eval('print("REMINDER : [ {} ] input successful \\n")'.format(att))
        return att

    def presetAttrFunc(self, input_attr=""):
        cmds.textField(self.target_attr_tf, e=True, tx=input_attr)
        mel.eval('print("REMINDER : [ {} ] input successful \\n")'.format(input_attr))
        return input_attr

    def _query_radio_settings(self):
        radio_settings = {}
        for attr_name, btns in self.radio_attr_map.items():
            radio_settings[attr_name] = cmds.radioButton(btns["on"], q=True, sl=True)
        return radio_settings

    def _short_node_name(self, node):
        """
        Convert long Maya path:
            |group1|pCube1
        into:
            pCube1
    
        Expression normally works cleaner with short names.
        """
        if not node:
            return ""
    
        return node.split("|")[-1]
    
    def _build_expression_line(self, data, target_node, sdk, index):
        """
        Build one expression line.
    
        Example:
        target.rotateY = cos(time * sdk.Speed + sdk.Offset + sdk.WaveLength * sdk.WaveLength_Offset * 1) * sdk.Amplitude;
        """
    
        trig = data["trigonometric"]
        target_attr = data["targetAttribute"].lstrip(".")
        settings = data["settings"]
    
        target_node = self._short_node_name(target_node)
        sdk = self._short_node_name(sdk)
    
        # ---------------------------------------
        # Time part
        # ---------------------------------------
        time_part = "time"
    
        if settings.get("timeScale"):
            time_part += " * {0}.Time_Scale".format(sdk)
    
        if settings.get("speed"):
            time_part += " * {0}.Speed".format(sdk)
    
        # ---------------------------------------
        # Inside sin/cos/tan
        # ---------------------------------------
        inside_parts = [time_part]
    
        if settings.get("offset"):
            inside_parts.append("{0}.Offset".format(sdk))
    
        if settings.get("wavelength"):
            wave_part = "{0}.WaveLength".format(sdk)
    
            if settings.get("wavelengthOffset"):
                wave_part += " * {0}.WaveLength_Offset".format(sdk)
    
            wave_part += " * {0}".format(index)
    
            inside_parts.append(wave_part)
    
        inside_trig = " + ".join(inside_parts)
    
        # ---------------------------------------
        # Main trig output
        # ---------------------------------------
        output_part = "{0}({1})".format(trig, inside_trig)
    
        if settings.get("amplitude"):
            output_part = "({0} * {1}.Amplitude)".format(output_part, sdk)

        if settings.get("target"):
            output_part = "({0} * {1}.BlendExpression)".format(output_part, target_node)
    
        script = "{0}.{1} = {2};".format(
            target_node,
            target_attr,
            output_part
        )
    
        return script

    def _build_expression_script(self, data, sdk=None):
        """
        Build full expression script based on selected target objects.
        """
    
        selection, selection_count = self.selectionNumToSpawn()
    
        if not selection:
            return None
    
        if sdk is None:
            sdk = data["mainController"]
    
        script_lines = []
    
        script_lines.append("// Generated Trigonometric Expression")
        script_lines.append("// Main Controller : {0}".format(self._short_node_name(sdk)))
        script_lines.append("// Target Count    : {0}".format(selection_count))
        script_lines.append("")
    
        for i, target_node in enumerate(selection, start=1):
            line = self._build_expression_line(
                data=data,
                target_node=target_node,
                sdk=sdk,
                index=i
            )
            script_lines.append(line)
    
        return "\n".join(script_lines)
    
    def _build_expression_script_name(self, data):
        target_node = self._short_node_name(data["mainController"])
        target_attr = data["targetAttribute"].lstrip(".")
        trig = data["trigonometric"].lower()
        return "{0}_{1}_{2}_EXP".format(target_node, target_attr, trig)

    def _open_expression_window(self, expression_script, script_name="", main_controller="", target_nodes=None, settings=None):
        try:
            from . import Trigonometric_UI_Expression as expression_ui
        except ImportError:
            import Trigonometric_UI_Expression as expression_ui

        reload(expression_ui)

        return expression_ui.Trigonometric_UI_Expression(
            expression_text=expression_script,
            script_name=script_name,
            main_controller=main_controller,
            target_nodes=target_nodes or [],
            settings=settings or {},
        )
    
    def selectionNumToSpawn(self):
        selection = cmds.ls(sl=True, l=True) or []
    
        if not selection:
            cmds.warning("Please select target objects to generate expression lines.")
            return [], 0
    
        return selection, len(selection)
    
    def generateFunc(self):
        main_ctrl = cmds.textField(self.main_ctrl_tf, q=True, tx=True).strip()
        if not main_ctrl:
            cmds.warning("Main controller input is empty.")
            return None

        if not cmds.objExists(main_ctrl):
            cmds.warning("Main controller does not exist: {}".format(main_ctrl))
            return None

        trig_option = cmds.optionMenu(self.sel_option_menu, q=True, v=True)
        if not trig_option or trig_option == "-":
            cmds.warning("Please select SIN, COS or TAN.")
            return None

        target_attr = cmds.textField(self.target_attr_tf, q=True, tx=True).strip()
        if not target_attr:
            cmds.warning("Target attribute input is empty.")
            return None

        if not target_attr.startswith("."):
            target_attr = "." + target_attr

        target_plug = main_ctrl + target_attr
        if not cmds.objExists(target_plug):
            cmds.warning("Target attribute does not exist: {}".format(target_plug))
            return None

        result = {
            "mainController": main_ctrl,
            "trigonometric": trig_option.lower(),
            "targetAttribute": target_attr,
            "targetPlug": target_plug,
            "settings": self._query_radio_settings(),
        }

        expression_script = self._build_expression_script(result, sdk=main_ctrl)
        
        if not expression_script:
            cmds.warning("Expression script generation failed.")
            return None

        expression_node_name = self._build_expression_script_name(result)
        
        result["expressionScript"] = expression_script
        result["expressionNodeName"] = expression_node_name
        
        print(result)
        print(expression_script)

        target_nodes, target_count = self.selectionNumToSpawn()
        self._open_expression_window(
            expression_script=expression_script,
            script_name=expression_node_name,
            main_controller=main_ctrl,
            target_nodes=target_nodes,
            settings=result["settings"],
        )
        
        mel.eval('print("REMINDER : Generate expression script successfully \\n")')
        
        return result


def Trigonometric_UI():
    global TRIGONOMETRIC_UI_INSTANCE
    TRIGONOMETRIC_UI_INSTANCE = TrigonometricWindow()
    return TRIGONOMETRIC_UI_INSTANCE


if __name__ == "__main__":
    Trigonometric_UI()
    