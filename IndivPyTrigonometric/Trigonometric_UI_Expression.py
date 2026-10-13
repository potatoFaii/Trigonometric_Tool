# -*- coding: utf-8 -*-
from importlib import reload

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as omui

TRIGO_QT_REFS = {}
TRIGONOMETRIC_EXPRESSION_UI_INSTANCE = None

try:
    from PySide2 import QtWidgets, QtGui, QtCore
    from shiboken2 import wrapInstance
except ImportError:
    from PySide import QtGui as QtWidgets
    from PySide import QtGui, QtCore
    from shiboken import wrapInstance

def maya_to_qt(control_name):
    ptr = omui.MQtUtil.findControl(control_name)
    if ptr is None:
        ptr = omui.MQtUtil.findLayout(control_name)
    if ptr is None:
        ptr = omui.MQtUtil.findMenuItem(control_name)
        
    if ptr is not None:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    
    return None

def make_format(color, bold=False, italic=False):
    fmt = QtGui.QTextCharFormat()
    fmt.setForeground(QtGui.QColor(color))
    if bold:
        fmt.setFontWeight(QtGui.QFont.Bold)
    if italic:
        fmt.setFontItalic(True)
    return fmt

class ResizeFilter(QtCore.QObject):
    def __init__(self, parent_widget, child_widget):
        super(ResizeFilter, self).__init__(parent_widget)
        self.parent_widget = parent_widget
        self.child_widget = child_widget
        self.parent_widget.installEventFilter(self)
        self.resize_child()

    def eventFilter(self, obj, event):
        if event.type() in [
            QtCore.QEvent.Resize,
            QtCore.QEvent.Show,
            QtCore.QEvent.LayoutRequest
        ]:
            self.resize_child()
        return False

    def resize_child(self):
        if self.parent_widget and self.child_widget:
            self.child_widget.setGeometry(self.parent_widget.rect())
            self.child_widget.show()

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, viewer):
        super(LineNumberArea, self).__init__(viewer)
        self.viewer = viewer

    def sizeHint(self):
        return QtCore.QSize(self.viewer.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.viewer.lineNumberAreaPaintEvent(event)

class CodeViewer(QtWidgets.QPlainTextEdit):
    def __init__(self, parent=None):
        super(CodeViewer, self).__init__(parent)

        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())

        while count >= 10:
            count //= 10
            digits += 1

        fm = self.fontMetrics()

        if hasattr(fm, "horizontalAdvance"):
            char_width = fm.horizontalAdvance("9")
        else:
            char_width = fm.width("9")

        space = 12 + char_width * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0,
                rect.y(),
                self.lineNumberArea.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super(CodeViewer, self).resizeEvent(event)

        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QtCore.QRect(
                cr.left(),
                cr.top(),
                self.lineNumberAreaWidth(),
                cr.height()
            )
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtGui.QColor("#252526"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = self.blockBoundingGeometry(block).translated(
            self.contentOffset()
        ).top()

        bottom = top + self.blockBoundingRect(block).height()
        height = self.fontMetrics().height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                painter.setPen(QtGui.QColor("#858585"))
                painter.drawText(
                    0,
                    int(top),
                    self.lineNumberArea.width() - 4,
                    height,
                    QtCore.Qt.AlignRight,
                    number
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlightCurrentLine(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()

            line_color = QtGui.QColor("#2a2d2e")
            selection.format.setBackground(line_color)
            selection.format.setProperty(
                QtGui.QTextFormat.FullWidthSelection,
                True
            )

            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

class ExpressionHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, document):
        super(ExpressionHighlighter, self).__init__(document)

        self.rules = []

        trig_fmt = make_format("#c883c1", bold=True)
        attr_fmt = make_format("#9cdcfe")
        translate_fmt = make_format("#4fc1ff")
        rotate_fmt = make_format("#d7ba7d")
        scale_fmt = make_format("#b5cea8")
        number_fmt = make_format("#b5cea8")
        operator_fmt = make_format("#ffffff")
        object_fmt = make_format("#dcdcaa")
        comment_fmt = make_format("#6a9955", italic=True)
        time_fmt = make_format("#4fc1ff", bold=True)

        # Trigonometric keywords
        for word in ["sin", "cos", "tan"]:
            self.rules.append((QtCore.QRegExp(r"\b%s\b" % word), trig_fmt))

        self.rules.append((QtCore.QRegExp(r"\btime\b"), time_fmt))
        
        # Common expression attributes
        translate_words = ["translateX", "translateY", "translateZ"]
        rotate_words = ["rotateX", "rotateY", "rotateZ"]
        scale_words = ["scaleX", "scaleY", "scaleZ"]
        attr_words = [
            "BlendExpression",
            "Offset",
            "Wavelength",
            "WaveLength",
            "WaveLength_Offset",
            "Amplitude",
            "Speed",
            "Time_Scale"
        ]

        for word in translate_words:
            self.rules.append(
                (QtCore.QRegExp(r"\b%s\b" % word), translate_fmt)
            )

        for word in rotate_words:
            self.rules.append(
                (QtCore.QRegExp(r"\b%s\b" % word), rotate_fmt)
            )

        for word in scale_words:
            self.rules.append(
                (QtCore.QRegExp(r"\b%s\b" % word), scale_fmt)
            )

        for word in attr_words:
            self.rules.append(
                (QtCore.QRegExp(r"\b%s\b" % word), attr_fmt)
            )

        # Numbers
        self.rules.append(
            (QtCore.QRegExp(r"\b[0-9]+(?:\.[0-9]+)?\b"), number_fmt)
        )

        # Operators and braces
        operators = [
            "=", r"\+", "-", r"\*", "/", r"\(", r"\)",
            r"\.", ";", ","
        ]

        for op in operators:
            self.rules.append(
                (QtCore.QRegExp(op), operator_fmt)
            )

        # Object name before dot
        # Example:
        # controller.rotateX
        # ns:controller.rotateX
        self.rules.append(
            (
                QtCore.QRegExp(r"\b[A-Za-z_][A-Za-z0-9_:]*\b(?=\.)"),
                object_fmt
            )
        )

        # Comment
        self.rules.append(
            (QtCore.QRegExp(r"//[^\n]*"), comment_fmt)
        )

    def highlightBlock(self, text):
        for expression, fmt in self.rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, fmt)
                index = expression.indexIn(text, index + length)
                

class TrigonometricExpressionWindow(object):
    WINDOW_NAME = "Trigonometric_Expression"
    DEFAULT_TEXT = "// Generated expression preview\n"

    def __init__(self, expression_text="", script_name="", main_controller="", target_nodes=None, settings=None):
        self.window = None
        self.main_form = None
        self.script_name_title = None
        self.script_name_tf = None
        self.preview_form = None
        self.generate_btn = None

        self.qt_parent = None
        self.qt_container = None
        self.qt_layout = None
        self.code_editor = None
        self.highlighter = None
        self.resize_filter = None

        self.expression_text = expression_text or self.DEFAULT_TEXT
        self.script_name = script_name

        self.main_controller = main_controller
        self.target_nodes = target_nodes or []
        self.settings = settings or {}

        self.show()
    
    def openExpressCmdExtra(self):
        mel.eval('ExpressionEditor;')
        mel.eval('EEselectFilterCB expression;')
        
    def show(self):
        self._delete_existing_window()
        self._build_ui()
        cmds.showWindow(self.window)
        self.set_inputs(self.expression_text, self.script_name)
        self._store_references()
        self.resize_filter.resize_child()
        return self

    def _delete_existing_window(self):
        if cmds.window(self.WINDOW_NAME, q=True, exists=True):
            cmds.deleteUI(self.WINDOW_NAME)

    def _build_ui(self):
        self.window = cmds.window(self.WINDOW_NAME,title=self.WINDOW_NAME,menuBar=True,widthHeight=(300, 200),sizeable=True)

        cmds.menu(l='Help')
        cmds.menuItem(dl='Expression Editor',divider=True)
        cmds.menuItem(l='Expression_Filter',c=lambda *_:self.openExpressCmdExtra())
        
        self.main_form = cmds.formLayout()
        self.script_name_title = cmds.text(l="Script Node Name :")
        self.script_name_tf = cmds.textField(p=self.main_form, text="")
        self.preview_form = cmds.formLayout(p=self.main_form)
        self.generate_btn = cmds.button(label="Create", p=self.main_form, height=30, c=lambda *_: self.create_expression_node())

        cmds.formLayout(
            self.main_form,
            e=True,
            attachForm=[
                (self.script_name_title, "top", 8),
                (self.script_name_title, "left", 5),
                (self.script_name_tf, "top", 5),
                (self.script_name_tf, "right", 5),
                (self.preview_form, "left", 5),
                (self.preview_form, "right", 5),
                (self.generate_btn, "left", 5),
                (self.generate_btn, "right", 5),
                (self.generate_btn, "bottom", 5),
            ],
            attachControl=[
                (self.script_name_tf, "left", 10, self.script_name_title),
                (self.preview_form, "top", 5, self.script_name_tf),
                (self.preview_form, "bottom", 5, self.generate_btn),
            ],
        )

        self.qt_parent = maya_to_qt(self.preview_form)
        self.qt_container = QtWidgets.QWidget(self.qt_parent)
        self.qt_container.setObjectName("TrigoCodeEditorContainer")

        self.qt_layout = QtWidgets.QVBoxLayout(self.qt_container)
        self.qt_layout.setContentsMargins(0, 0, 0, 0)
        self.qt_layout.setSpacing(0)

        self.code_editor = CodeViewer()
        self.code_editor.setParent(self.qt_container)
        self.code_editor.setPlainText(self.DEFAULT_TEXT)
        self.code_editor.setStyleSheet("""
QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: Consolas;
    font-size: 12px;
    border: 1px solid #3c3c3c;
    selection-background-color: #264f78;
    selection-color: #ffffff;
}
QScrollBar:vertical {
    background: #2d2d30;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #686868;
    min-height: 20px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #2d2d30;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: #686868;
    min-width: 20px;
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}
""")
        self.code_editor.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

        self.qt_layout.addWidget(self.code_editor)

        self.highlighter = ExpressionHighlighter(self.code_editor.document())
        self.resize_filter = ResizeFilter(self.qt_parent, self.qt_container)

    def set_script_name(self, script_name):
        self.script_name = script_name or ""
        cmds.textField(self.script_name_tf, e=True, text=self.script_name)
        return self.script_name

    def set_expression_text(self, expression_text):
        self.expression_text = expression_text or self.DEFAULT_TEXT
        self.code_editor.setPlainText(self.expression_text)
        return self.expression_text

    def set_inputs(self, expression_text="", script_name=""):
        self.set_script_name(script_name)
        self.set_expression_text(expression_text)

    def _store_references(self):
        TRIGO_QT_REFS.clear()
        TRIGO_QT_REFS["qt_parent"] = self.qt_parent
        TRIGO_QT_REFS["qt_container"] = self.qt_container
        TRIGO_QT_REFS["qt_layout"] = self.qt_layout
        TRIGO_QT_REFS["code_editor"] = self.code_editor
        TRIGO_QT_REFS["highlighter"] = self.highlighter
        TRIGO_QT_REFS["resize_filter"] = self.resize_filter
        TRIGO_QT_REFS["window_name"] = self.WINDOW_NAME
        TRIGO_QT_REFS["instance"] = self

    def create_expression_node(self):
        expression_name = cmds.textField(self.script_name_tf, q=True, text=True).strip()
        expression_text = self.code_editor.toPlainText()

        try:
            from . import Trigonometric_Expression_Create as creator
        except ImportError:
            import Trigonometric_Expression_Create as creator

        reload(creator)

        result = creator.create_trigonometric_expression(
            main_controller=self.main_controller,
            target_nodes=self.target_nodes,
            expression_name=expression_name,
            expression_text=expression_text,
            settings=self.settings,
            add_blend_expression=self.settings.get("target", False),
        )

        if result:
            cmds.inViewMessage(
                amg='Expression Created: <hl>{}</hl>'.format(result["expressionNode"]),
                pos='midCenter',
                fade=True
            )

        return result

def Trigonometric_UI_Expression(
    expression_text="",
    script_name="",
    main_controller="",
    target_nodes=None,
    settings=None,
):
    global TRIGONOMETRIC_EXPRESSION_UI_INSTANCE

    TRIGONOMETRIC_EXPRESSION_UI_INSTANCE = TrigonometricExpressionWindow(
        expression_text=expression_text,
        script_name=script_name,
        main_controller=main_controller,
        target_nodes=target_nodes,
        settings=settings,
    )

    return TRIGONOMETRIC_EXPRESSION_UI_INSTANCE


if __name__ == "__main__":
    Trigonometric_UI_Expression()

