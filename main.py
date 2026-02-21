import sys, json, os
import yaml
import theme
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox,
    QComboBox, QSplitter, QTextEdit, QSpinBox, QScrollArea, QStackedWidget,
    QSizePolicy, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

CMD_COLORS = {
    "sequences":"#3d8bc4","sequence":"#7090a8","title":"#9090a0",
    "description":"#9090a0","background":"#6abf96","characters":"#9090a0",
    "char":"#5a9fd4","emotion":"#9bc48a","say":"#c8c4b0","animate":"#d4a84a",
    "choice":"#d47a4a","option":"#c4906a","music":"#8a7abf","sound":"#b4a040",
    "wait":"#708090","jump":"#a07090","set":"#70a090",
}
EMOTIONS   = ["happy","sad","angry","excited","serious","thinking","laugh",
              "surprised","nervous","neutral","cry","smug"]
ANIMATIONS = ["jump","shake","bounce","spin","flash","slide_in","slide_out",
              "fade_in","fade_out","nod","tremble"]
CMDS       = ["char","emotion","say","background","animate","choice",
              "music","sound","wait"]
CHARS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "characters.json")

FONT_SIZE = 15
TREE_FONT = LABEL_FONT = BTN_FONT = INPUT_FONT = None

def init_fonts():
    global TREE_FONT, LABEL_FONT, BTN_FONT, INPUT_FONT
    for name in ["TREE_FONT","LABEL_FONT","BTN_FONT","INPUT_FONT"]:
        f = QFont(); f.setPointSize(FONT_SIZE)
        globals()[name] = f

def color(key): return CMD_COLORS.get(key, "#c8cdd4")

def make_item(col0, col1="", key=None):
    item = QTreeWidgetItem([col0, col1])
    k = key or col0
    item.setForeground(0, QColor(color(k)))
    item.setForeground(1, QColor("#a0a8b0"))
    item.setData(0, Qt.UserRole, k)
    item.setFont(0, TREE_FONT); item.setFont(1, TREE_FONT)
    return item

def is_seq_container(item):
    if item is None: return False
    k = item.data(0, Qt.UserRole) or item.text(0)
    return k == "sequence" and item.data(0, Qt.UserRole) != "__seq__"

# ── Gendered Insert Widget ────────────────────────────────────────────────────
class GenderedInsertWidget(QWidget):
    def __init__(self, target_textedit, parent=None):
        super().__init__(parent)
        self.target = target_textedit
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 4, 0, 0); lay.setSpacing(4)
        self.toggle_btn = QPushButton("⚥  Gendered variants  ▸")
        self.toggle_btn.setFont(BTN_FONT); self.toggle_btn.setObjectName("btn_io")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(lambda c: (self.body.setVisible(c),
            self.toggle_btn.setText("⚥  Gendered variants  ▾" if c else "⚥  Gendered variants  ▸")))
        lay.addWidget(self.toggle_btn)
        self.body = QWidget(); body_l = QVBoxLayout(self.body)
        body_l.setContentsMargins(0, 2, 0, 2); body_l.setSpacing(4)
        lf = QFont(); lf.setPointSize(FONT_SIZE - 1)
        self.inputs = {}
        for pronoun, icon in [("he", "♂"), ("she", "♀"), ("they", "⚧")]:
            row = QHBoxLayout(); row.setSpacing(6)
            lbl = QLabel(f"{icon} {pronoun}:"); lbl.setFont(lf); lbl.setFixedWidth(52)
            inp = QLineEdit(); inp.setFont(INPUT_FONT); inp.setMinimumHeight(32)
            inp.setPlaceholderText(f"{pronoun} form…")
            row.addWidget(lbl); row.addWidget(inp); body_l.addLayout(row)
            self.inputs[pronoun] = inp
        insert_btn = QPushButton("↩  Insert (he/she/they)")
        insert_btn.setFont(BTN_FONT); insert_btn.setObjectName("btn_primary")
        insert_btn.clicked.connect(self._insert); body_l.addWidget(insert_btn)
        self.body.setVisible(False); lay.addWidget(self.body)

    def _insert(self):
        vals = [self.inputs[p].text().strip() for p in ("he", "she", "they")]
        if not any(vals): return
        cursor = self.target.textCursor()
        cursor.insertText(f"({'/'.join(vals)})")
        self.target.setTextCursor(cursor); self.target.setFocus()
        for inp in self.inputs.values(): inp.clear()


# ── YAML serializer ──────────────────────────────────────────────────────────

# Custom string subclass used to flag values that must be double-quoted in YAML
class DoubleQuotedStr(str):
    pass

def _yaml_escape(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')

def _yaml_scalar(v):
    if isinstance(v, DoubleQuotedStr):
        return f'"{_yaml_escape(v)}"'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if any(c in s for c in ':{}[]|>&*!,#?\'"\\%@`') or s == "" or s.startswith(" "):
        return f'"{_yaml_escape(s)}"'
    return s

def _dump_node(node, indent):
    sp = " " * indent
    lines = []
    if isinstance(node, list):
        for item in node:
            if isinstance(item, dict):
                pairs = list(item.items())
                k0, v0 = pairs[0]
                if isinstance(v0, list):
                    lines.append(f"{sp}- {k0}:")
                    lines.append(_dump_node(v0, indent + 2))
                    for k, v in pairs[1:]:
                        if isinstance(v, list):
                            lines.append(f"{sp}  {k}:")
                            lines.append(_dump_node(v, indent + 4))
                        else:
                            lines.append(f"{sp}  {k}: {_yaml_scalar(v)}")
                else:
                    lines.append(f"{sp}- {k0}: {_yaml_scalar(v0)}")
                    for k, v in pairs[1:]:
                        if isinstance(v, list):
                            lines.append(f"{sp}  {k}:")
                            lines.append(_dump_node(v, indent + 4))
                        else:
                            lines.append(f"{sp}  {k}: {_yaml_scalar(v)}")
            else:
                lines.append(f"{sp}- {_yaml_scalar(item)}")
    elif isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}{k}:")
                lines.append(_dump_node(v, indent + 2))
            else:
                lines.append(f"{sp}{k}: {_yaml_scalar(v)}")
    else:
        lines.append(f"{sp}{_yaml_scalar(node)}")
    return "\n".join(l for l in lines if l)

def dump_yaml(data):
    return _dump_node(data, 0) + "\n"


# ── Right Panel ──────────────────────────────────────────────────────────────
class RightPanel(QWidget):
    def __init__(self, editor):
        super().__init__()
        self.editor = editor
        self.current_item = None
        self.current_seq  = None
        self.field_widgets = {}
        self._block_instant = False

        self.chars_list = QListWidget()  # init early

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(8)

        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        self.stack.addWidget(self._build_empty())   # 0
        self.stack.addWidget(self._build_seq())     # 1
        self.stack.addWidget(self._build_cmd())     # 2
        self.stack.addWidget(self._build_chars())   # 3

        self.import_btn = self._btn("⬆  Import YAML");   self.import_btn.setObjectName("btn_io")
        self.export_btn = self._btn("⬇  Export YAML");   self.export_btn.setObjectName("btn_io")
        self.chars_btn  = self._btn("✦  Characters");    self.chars_btn.setObjectName("btn_io")
        self.chars_btn.clicked.connect(lambda: self.stack.setCurrentIndex(3))

    # helpers
    def _lbl(self, txt, obj=None):
        l = QLabel(txt); l.setFont(LABEL_FONT)
        if obj: l.setObjectName(obj)
        return l

    def _btn(self, txt, obj=None):
        b = QPushButton(txt); b.setFont(BTN_FONT)
        if obj: b.setObjectName(obj)
        return b

    def _inp(self, val=""):
        w = QLineEdit(val); w.setFont(INPUT_FONT); w.setMinimumHeight(36); return w

    # ── pages ────────────────────────────────────────────────────────────────

    def _build_empty(self):
        w = QWidget(); l = QVBoxLayout(w)
        lbl = self._lbl("Select a sequence\nor command to edit.")
        lbl.setAlignment(Qt.AlignCenter); lbl.setWordWrap(True)
        l.addStretch(); l.addWidget(lbl); l.addStretch()
        return w

    def _build_seq(self):
        w = QWidget(); l = QVBoxLayout(w); l.setSpacing(8); l.setContentsMargins(0,0,0,0)
        l.addWidget(self._lbl("SEQUENCE", "lbl_section"))
        self.s_id    = self._inp(); l.addWidget(self._lbl("ID:", "lbl_field"));          l.addWidget(self.s_id)
        self.s_title = self._inp(); l.addWidget(self._lbl("title:", "lbl_field"));       l.addWidget(self.s_title)
        self.s_desc  = self._inp(); l.addWidget(self._lbl("description:", "lbl_field")); l.addWidget(self.s_desc)
        self.s_bg    = self._inp(); l.addWidget(self._lbl("background:", "lbl_field"));  l.addWidget(self.s_bg)
        l.addWidget(self._lbl("characters (name: pos):", "lbl_field"))
        self.s_chars = QTextEdit(); self.s_chars.setFont(INPUT_FONT); self.s_chars.setFixedHeight(80)
        l.addWidget(self.s_chars)
        b1 = self._btn("Apply",            "btn_primary"); b1.clicked.connect(self._apply_seq); l.addWidget(b1)
        b2 = self._btn("Delete sequence",  "btn_danger");  b2.clicked.connect(self.editor.del_sequence); l.addWidget(b2)
        b3 = self._btn("+ New sequence",   "btn_new");     b3.clicked.connect(self.editor.add_sequence); l.addWidget(b3)
        l.addStretch(); return w

    def _build_cmd(self):
        w = QWidget(); l = QVBoxLayout(w); l.setSpacing(8); l.setContentsMargins(0,0,0,0)
        hdr_row = QHBoxLayout()
        hdr_row.addWidget(self._lbl("COMMAND", "lbl_section"))
        hdr_row.addStretch()
        self.new_cmd_btn = self._btn("+ New", "btn_new")
        self.new_cmd_btn.setFixedHeight(28)
        self.new_cmd_btn.clicked.connect(self._switch_to_new_mode)
        hdr_row.addWidget(self.new_cmd_btn)
        l.addLayout(hdr_row)
        self.cmd_combo = QComboBox(); self.cmd_combo.setFont(INPUT_FONT); self.cmd_combo.setMinimumHeight(36)
        self.cmd_combo.addItems(CMDS)
        self.cmd_combo.currentTextChanged.connect(self._on_cmd_combo_changed)
        l.addWidget(self.cmd_combo)
        l.addWidget(self._lbl("─────", "lbl_field"))
        self.cmd_type_lbl = self._lbl("", "lbl_cmd_type")
        l.addWidget(self.cmd_type_lbl)
        self.fields_w = QWidget()
        self.fields_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.fields_l = QVBoxLayout(self.fields_w)
        self.fields_l.setContentsMargins(0,0,0,0); self.fields_l.setSpacing(6)
        l.addWidget(self.fields_w)
        self.apply_btn  = self._btn("Apply",  "btn_primary"); self.apply_btn.clicked.connect(self._apply_cmd)
        self.delete_btn = self._btn("Delete", "btn_danger");  self.delete_btn.clicked.connect(self.editor._delete)
        self.delete_btn.hide()
        l.addWidget(self.apply_btn); l.addWidget(self.delete_btn)
        l.addStretch()
        self._load_fields_for_cmd(CMDS[0])
        return w

    def _build_chars(self):
        w = QWidget(); l = QVBoxLayout(w); l.setSpacing(8); l.setContentsMargins(0,0,0,0)
        l.addWidget(self._lbl("CHARACTERS", "lbl_section"))
        self.chars_list.setFont(TREE_FONT); l.addWidget(self.chars_list)
        row = QHBoxLayout()
        self.char_input = QLineEdit(); self.char_input.setFont(INPUT_FONT)
        self.char_input.setPlaceholderText("name"); self.char_input.setMinimumHeight(36)
        self.char_input.returnPressed.connect(self._add_char); row.addWidget(self.char_input)
        b_add = QPushButton("+"); b_add.setFont(BTN_FONT); b_add.setFixedWidth(40)
        b_add.clicked.connect(self._add_char); row.addWidget(b_add); l.addLayout(row)
        b_del  = self._btn("Delete selected", "btn_danger"); b_del.clicked.connect(self._del_char); l.addWidget(b_del)
        b_back = self._btn("← Back",          "btn_io");     b_back.clicked.connect(lambda: self.stack.setCurrentIndex(2)); l.addWidget(b_back)
        l.addStretch(); return w

    # ── characters ───────────────────────────────────────────────────────────

    def _add_char(self):
        name = self.char_input.text().strip()
        if not name: return
        self.chars_list.addItem(QListWidgetItem(name))
        self.char_input.clear(); self._refresh_char_combo(); self._autosave_chars()

    def _del_char(self):
        for item in self.chars_list.selectedItems():
            self.chars_list.takeItem(self.chars_list.row(item))
        self._refresh_char_combo(); self._autosave_chars()

    def _autosave_chars(self):
        try:
            with open(CHARS_FILE,"w",encoding="utf-8") as f: json.dump(self.get_chars(), f)
        except: pass

    def autoload_chars(self):
        if not os.path.exists(CHARS_FILE): return
        try:
            with open(CHARS_FILE,"r",encoding="utf-8") as f: chars = json.load(f)
            self.chars_list.clear()
            for c in chars: self.chars_list.addItem(QListWidgetItem(c))
            self._refresh_char_combo()
        except: pass

    def get_chars(self):
        return [self.chars_list.item(i).text() for i in range(self.chars_list.count())]

    def _refresh_char_combo(self):
        for attr in ("_char_field_combo", "_say_char_combo"):
            if not hasattr(self, attr): continue
            c = getattr(self, attr)
            prev = c.currentText()
            self._block_instant = True
            c.clear(); c.addItems([""] + self.get_chars())
            idx = c.findText(prev)
            if idx >= 0: c.setCurrentIndex(idx)
            self._block_instant = False

    # ── sequence panel ───────────────────────────────────────────────────────

    def show_seq(self, item):
        self.current_seq = item
        d = item.data(0, Qt.UserRole+1) or {}
        self.s_id.setText(d.get("id",""))
        self.s_title.setText(d.get("title",""))
        self.s_desc.setText(d.get("desc",""))
        self.s_bg.setText(d.get("bg",""))
        self.s_chars.setPlainText(d.get("chars",""))
        self.stack.setCurrentIndex(1)

    def _apply_seq(self):
        item = self.current_seq
        if not item: return
        d = {"id": self.s_id.text().strip(), "title": self.s_title.text().strip(),
             "desc": self.s_desc.text().strip(), "bg": self.s_bg.text().strip(),
             "chars": self.s_chars.toPlainText().strip()}
        item.setData(0, Qt.UserRole+1, d)
        item.setText(0, d["id"]); item.setText(1, d["title"])
        self.editor._refresh_seq_children(item, d)

    # ── cmd panel ────────────────────────────────────────────────────────────

    def _switch_to_new_mode(self):
        self.current_item = None
        self.delete_btn.hide()
        self._load_fields_for_cmd(self.cmd_combo.currentText(), value="")

    def show_add_cmd(self, target_seq=None):
        self.current_item = None
        self.current_seq = target_seq
        self.delete_btn.hide()
        idx = self.cmd_combo.findText("char")
        if idx >= 0: self.cmd_combo.setCurrentIndex(idx)
        self._load_fields_for_cmd("char", value="")
        self.stack.setCurrentIndex(2)

    def show_cmd(self, item):
        self.current_item = item
        cmd   = item.data(0, Qt.UserRole) or item.text(0)
        value = item.text(1)
        self._block_instant = True
        idx = self.cmd_combo.findText(cmd)
        if idx >= 0: self.cmd_combo.setCurrentIndex(idx)
        self._block_instant = False
        self._load_fields_for_cmd(cmd, value)
        self.delete_btn.show()
        self.stack.setCurrentIndex(2)

    def _on_cmd_combo_changed(self, cmd):
        if self._block_instant: return
        self.current_item = None
        self.delete_btn.hide()
        self._load_fields_for_cmd(cmd, value="")

    def _clear_fields(self):
        self.field_widgets.clear()
        for attr in ("_char_field_combo","_say_char_combo"):
            if hasattr(self, attr): delattr(self, attr)
        self._clear_layout(self.fields_l)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
                item.layout().deleteLater()

    def _load_fields_for_cmd(self, cmd, value=""):
        self._clear_fields()
        self.cmd_type_lbl.setText(cmd.upper())
        chars = self.get_chars()

        if cmd in ("say", "option"):
            w = QTextEdit(); w.setFont(INPUT_FONT)
            w.setPlainText(value.strip('"'))
            w.setFixedHeight(100 if cmd == "say" else 80)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._row("text", w)
            self.fields_l.addWidget(self._lbl("Insert character mention:", "lbl_field"))
            row = QHBoxLayout()
            self._say_char_combo = QComboBox(); self._say_char_combo.setFont(INPUT_FONT)
            self._say_char_combo.setMinimumHeight(34)
            self._say_char_combo.addItems([""] + chars)
            row.addWidget(self._say_char_combo)
            b = QPushButton("Insert {name}"); b.setFont(BTN_FONT)
            b.setObjectName("btn_io")
            b.clicked.connect(lambda checked=False, te=w, cb=self._say_char_combo: self._insert_char_tag(te, cb))
            row.addWidget(b)
            self.fields_l.addLayout(row)
            gw = GenderedInsertWidget(w); self.fields_l.addWidget(gw)

        elif cmd == "char":
            c = QComboBox(); c.setFont(INPUT_FONT); c.setMinimumHeight(36); c.setEditable(True)
            c.addItems([""] + chars)
            idx = c.findText(value); c.setCurrentIndex(idx) if idx >= 0 else c.setCurrentText(value)
            self._char_field_combo = c
            c.currentTextChanged.connect(self._instant_update)
            self._row("character", c)

        elif cmd == "emotion":
            c = QComboBox(); c.setFont(INPUT_FONT); c.setMinimumHeight(36); c.setEditable(True)
            c.addItems(EMOTIONS)
            idx = c.findText(value); c.setCurrentIndex(idx) if idx >= 0 else c.setCurrentText(value)
            c.currentTextChanged.connect(self._instant_update)
            self._row("emotion", c)

        elif cmd == "animate":
            c = QComboBox(); c.setFont(INPUT_FONT); c.setMinimumHeight(36); c.setEditable(True)
            c.addItems(ANIMATIONS)
            idx = c.findText(value); c.setCurrentIndex(idx) if idx >= 0 else c.setCurrentText(value)
            c.currentTextChanged.connect(self._instant_update)
            self._row("animation", c)

        elif cmd == "background":
            bg_val, fade_val = value, ""
            if ", fadeout:" in value:
                p = value.split(", fadeout:"); bg_val, fade_val = p[0].strip(), p[1].strip()
            self._row("background", self._inp(bg_val))
            self._row("fadeout",    self._inp(fade_val))

        elif cmd == "choice":
            spin = QSpinBox(); spin.setFont(INPUT_FONT); spin.setMinimumHeight(36)
            spin.setRange(1, 20)
            spin.setValue(self.current_item.childCount() if self.current_item else 2)
            self._row("options", spin)

        elif cmd == "set":
            var_v = value.split("=")[0].strip() if "=" in value else value
            val_v = value.split("=")[1].strip() if "=" in value else ""
            self._row("variable", self._inp(var_v)); self._row("value", self._inp(val_v))

        else:
            self._row("value", self._inp(value))

    def _insert_char_tag(self, text_edit, combo):
        name = combo.currentText().strip()
        if not name: return
        cursor = text_edit.textCursor()
        cursor.insertText(f"{{{name}}}")
        text_edit.setTextCursor(cursor)
        text_edit.setFocus()

    def _instant_update(self, value):
        if self._block_instant: return
        if self.current_item is None:
            self.editor._add_cmd_with_value(value)
        else:
            self.current_item.setText(1, value)

    def _row(self, key, widget):
        lbl = QLabel(key + ":"); lbl.setFont(LABEL_FONT); lbl.setObjectName("lbl_field")
        self.fields_l.addWidget(lbl); self.fields_l.addWidget(widget)
        self.field_widgets[key] = widget

    def get_cmd_value(self, force_cmd=None):
        cmd = force_cmd or self.cmd_combo.currentText()

        def t(k):
            w = self.field_widgets.get(k)
            if not w: return ""
            if isinstance(w, QTextEdit):  return w.toPlainText().strip()
            if isinstance(w, QLineEdit):  return w.text().strip()
            if isinstance(w, QComboBox):  return w.currentText().strip()
            if isinstance(w, QSpinBox):   return str(w.value())
            return ""

        if cmd == "say":        return f'"{t("text")}"'
        if cmd == "option":     return f'"{t("text")}"'
        if cmd == "emotion":    return t("emotion")
        if cmd == "animate":    return t("animation")
        if cmd == "char":       return t("character")
        if cmd == "set":        return f"{t('variable')} = {t('value')}"
        if cmd == "background":
            bg, fade = t("background"), t("fadeout")
            return f"{bg}, fadeout: {fade}" if fade else bg
        return t("value")

    def get_num_options(self):
        w = self.field_widgets.get("options")
        return w.value() if isinstance(w, QSpinBox) else 2

    def _apply_cmd(self):
        if self.current_item:
            item = self.current_item
            real_cmd = item.data(0, Qt.UserRole) or item.text(0)

            if real_cmd == "choice":
                num = self.get_num_options()
                cur = item.childCount()
                if num > cur:
                    for i in range(cur, num): self.editor._add_option_to_choice(item, f"Option {i+1}")
                elif num < cur:
                    for _ in range(cur - num): item.removeChild(item.child(item.childCount()-1))
            else:
                new_value = self.get_cmd_value(force_cmd=real_cmd)
                item.setText(1, new_value)
        else:
            self.editor._add_cmd()

class VNTreeWidget(QTreeWidget):
    def _is_drop_valid(self, event):
        target_item = self.itemAt(event.position().toPoint())
        dragged_item = self.currentItem()

        if not dragged_item: return False

        drag_key = dragged_item.data(0, Qt.UserRole) or dragged_item.text(0)
        if drag_key == "sequence":
            p = dragged_item.parent()
            if p:
                pk = p.data(0, Qt.UserRole) or p.text(0)
                if pk == "__seq__" or pk == "option":
                    return False

        meta_tags = ["title", "description", "characters"]
        if drag_key in meta_tags: return False

        if drag_key == "background":
            p = dragged_item.parent()
            if p and (p.data(0, Qt.UserRole) or p.text(0)) == "__seq__":
                return False

        if not target_item:
            return drag_key == "__seq__"

        drop_pos = self.dropIndicatorPosition()

        if drop_pos == QTreeWidget.DropIndicatorPosition.OnItem:
            parent_item = target_item
        else:
            parent_item = target_item.parent()

        if not parent_item:
            return drag_key == "__seq__"

        parent_key = parent_item.data(0, Qt.UserRole) or parent_item.text(0)

        if parent_key == "__seq__":
            if drag_key == "sequence":
                return False
            allowed_meta = ["title", "description", "background", "characters"]
            return drag_key in allowed_meta

        valid_containers = ["characters", "choice", "sequence"]
        if parent_key not in valid_containers:
            return False

        if parent_key == "choice":
            return drag_key == "option"

        if parent_key == "option":
            return False

        if parent_key == "sequence":
            forbidden = ["option", "title", "description", "__seq__"]
            return drag_key not in forbidden

        return True

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        if not self._is_drop_valid(event):
            event.ignore()

    def dropEvent(self, event):
        if self._is_drop_valid(event):
            super().dropEvent(event)
        else:
            event.ignore()

# ── Main Window ──────────────────────────────────────────────────────────────
class DialogueTreeEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VN Editor")
        self.resize(1400, 820)
        self._build()
        self.panel.autoload_chars()

    def _build(self):
        root_lay = QHBoxLayout(self); root_lay.setContentsMargins(4,4,4,4)
        self.splitter = QSplitter(Qt.Horizontal); root_lay.addWidget(self.splitter)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(320)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.panel = RightPanel(self)
        self.panel.import_btn.clicked.connect(self._import)
        self.panel.export_btn.clicked.connect(self._export)

        left = QWidget(); ll = QVBoxLayout(left); ll.setContentsMargins(6,6,6,6); ll.setSpacing(6)
        hdr = QLabel("✦  VN EDITOR"); hdr.setObjectName("lbl_header"); hdr.setFont(TREE_FONT)
        ll.addWidget(hdr)
        b_new = QPushButton("+ New Sequence"); b_new.setFont(BTN_FONT)
        b_new.setObjectName("btn_new"); b_new.clicked.connect(self.add_sequence)
        row = QHBoxLayout()
        row.addWidget(b_new)
        row.addWidget(self.panel.import_btn)
        row.addWidget(self.panel.export_btn)
        row.addWidget(self.panel.chars_btn)
        row.addStretch(); ll.addLayout(row)

        self.tree = VNTreeWidget()
        self.tree.setFont(TREE_FONT); self.tree.setHeaderLabels(["key","value"])
        self.tree.setColumnWidth(0, 220); self.tree.header().setFont(TREE_FONT)
        self.tree.setDragEnabled(True); self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.itemClicked.connect(self._on_click)
        self.tree.itemSelectionChanged.connect(self._on_sel)
        ll.addWidget(self.tree); self.splitter.addWidget(left)

        scroll.setWidget(self.panel); self.splitter.addWidget(scroll)
        self.splitter.setStretchFactor(0, 1); self.splitter.setStretchFactor(1, 0)
        self.splitter.setCollapsible(0, False); self.splitter.setCollapsible(1, False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        total = self.splitter.width()
        sizes = self.splitter.sizes()
        if len(sizes) == 2 and sizes[1] < 320:
            self.splitter.setSizes([total - 320, 320])

    # ── node factories ───────────────────────────────────────────────────────

    def _make_cmd_node(self, cmd, value=""):
        item = make_item(cmd, value, cmd)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def _make_seq_node(self, d):
        item = QTreeWidgetItem([d["id"], d["title"]])
        item.setFont(0, TREE_FONT); item.setFont(1, TREE_FONT)
        item.setForeground(0, QColor(color("sequences")))
        item.setForeground(1, QColor("#7090a0"))
        item.setData(0, Qt.UserRole, "__seq__")
        item.setData(0, Qt.UserRole+1, d)
        item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        return item

    def _make_seq_container(self):
        sn = make_item("sequence", "", "sequence")
        sn.setFlags(sn.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        return sn

    # ── tree helpers ─────────────────────────────────────────────────────────

    def _is_seq(self, item): return item and item.data(0, Qt.UserRole) == "__seq__"

    def _seq_of(self, item):
        cur = item
        while cur:
            if self._is_seq(cur): return cur
            cur = cur.parent()
        return None

    def _cur(self):
        sel = self.tree.selectedItems(); return sel[0] if sel else None

    def _find_seq_container(self, seq_node):
        for i in range(seq_node.childCount()):
            ch = seq_node.child(i)
            if is_seq_container(ch): return ch
        return None

    def _on_click(self, item, _):
        key = item.data(0, Qt.UserRole) or item.text(0)
        parent = item.parent()
        parent_key = parent.data(0, Qt.UserRole) if parent else None

        header_keys = ["title", "description", "characters"]
        is_header_bg = (key == "background" and parent_key == "__seq__")

        if key == "__seq__" or key in header_keys or parent_key == "characters" or is_header_bg:
            self.panel.show_seq(self._seq_of(item))
            return

        if key == "sequence":
            self.panel.show_add_cmd(target_seq=item)
            return

        if key in CMDS or key == "option" or key == "choice":
            self.panel.show_cmd(item)

    def _on_sel(self):
        sel = self.tree.selectedItems()
        if sel: self._on_click(sel[0], 0)

    # ── seq metadata ─────────────────────────────────────────────────────────

    def _refresh_seq_children(self, seq_node, d):
        meta_keys = {"title", "description", "background", "characters"}
        for i in range(seq_node.childCount()-1, -1, -1):
            if seq_node.child(i).text(0) in meta_keys:
                seq_node.removeChild(seq_node.child(i))

        inserts = []
        if d["title"]: inserts.append(make_item("title",       d["title"]))
        if d["desc"]:  inserts.append(make_item("description", d["desc"]))
        if d["bg"]:    inserts.append(make_item("background",  d["bg"]))
        if d["chars"]:
            cn = make_item("characters", "")
            for part in d["chars"].split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    cn.addChild(make_item(k.strip(), v.strip()))
            cn.setExpanded(True)
            inserts.append(cn)
        for i, node in enumerate(inserts):
            seq_node.insertChild(i, node)

    # ── sequences ────────────────────────────────────────────────────────────

    def add_sequence(self):
        n = self.tree.invisibleRootItem().childCount() + 1
        d = {"id": f"sequence_{n}", "title": "", "desc": "", "bg": "", "chars": ""}
        node = self._make_seq_node(d)
        self.tree.invisibleRootItem().addChild(node)
        sc = self._make_seq_container()
        node.addChild(sc)
        node.setExpanded(True); sc.setExpanded(True)
        self.tree.setCurrentItem(sc)
        self.panel.show_seq(node)

    def del_sequence(self):
        item = self.panel.current_seq
        seq = item if self._is_seq(item) else self._seq_of(item)
        if not seq: return
        if QMessageBox.question(self, "Delete", f"Delete {seq.text(0)}?") == QMessageBox.Yes:
            self.tree.invisibleRootItem().removeChild(seq)
            self.panel.stack.setCurrentIndex(0)

    # ── insertion ────────────────────────────────────────────────────────────

    def _insert_after(self, new_node):
        cur = self._cur()
        if not cur: return
        if self._is_seq(cur):
            sc = self._find_seq_container(cur)
            if sc: sc.addChild(new_node)
            return
        if is_seq_container(cur):
            cur.addChild(new_node); return
        parent = cur.parent() or self.tree.invisibleRootItem()
        if parent and (parent.data(0, Qt.UserRole) or parent.text(0)) == "choice":
            return
        parent.insertChild(parent.indexOfChild(cur) + 1, new_node)

    def _add_option_to_choice(self, choice_node, label):
        opt = self._make_cmd_node("option", f'"{label}"')
        sn = self._make_seq_container()
        opt.addChild(sn); opt.setExpanded(True); choice_node.addChild(opt)

    def _add_cmd(self):
        cmd = self.panel.cmd_combo.currentText()
        value = self.panel.get_cmd_value()

        if cmd == "choice":
            node = self._make_cmd_node("choice", "")
            num = self.panel.get_num_options()
            for i in range(num): self._add_option_to_choice(node, f"Option {i+1}")
        else:
            node = self._make_cmd_node(cmd, value)

        cur = self._cur()
        inserted = False

        if cur:
            key = cur.data(0, Qt.UserRole) or cur.text(0)

            if is_seq_container(cur):
                cur.addChild(node)
                inserted = True
            elif self._is_seq(cur):
                sc = self._find_seq_container(cur)
                if sc: sc.addChild(node); inserted = True
            elif key == "choice":
                parent = cur.parent()
                if parent:
                    idx = parent.indexOfChild(cur)
                    parent.insertChild(idx + 1, node)
                    inserted = True
            else:
                parent = cur.parent()
                if parent:
                    pkey = parent.data(0, Qt.UserRole) or parent.text(0)
                    if pkey != "choice":
                        idx = parent.indexOfChild(cur)
                        parent.insertChild(idx + 1, node)
                        inserted = True

        if not inserted:
            target = self.panel.current_seq
            if not target or (target.data(0, Qt.UserRole) != "sequence" and target.text(0) != "sequence"):
                node_walk = cur
                while node_walk:
                    if is_seq_container(node_walk):
                        target = node_walk; break
                    node_walk = node_walk.parent() if node_walk else None
            if not target:
                QMessageBox.warning(self, "Aviso", "Selecciona un nodo dentro de una secuencia primero.")
                return
            target.addChild(node)

        node.setExpanded(True)
        self.tree.setCurrentItem(node)
        self.panel.show_cmd(node)

    def _add_cmd_with_value(self, value):
        cur = self._cur()
        if not cur or (not self._seq_of(cur) and not self._is_seq(cur) and not is_seq_container(cur)):
            return
        cmd  = self.panel.cmd_combo.currentText()
        node = self._make_cmd_node(cmd, value)
        self._insert_after(node)
        self.tree.setCurrentItem(node); self.panel.show_cmd(node)

    def _delete(self):
        item = self._cur()
        if not item or self._is_seq(item) or is_seq_container(item): return
        parent = item.parent()
        if parent and (parent.data(0, Qt.UserRole) or parent.text(0)) == "option":
            QMessageBox.warning(self, "Warning", "Option must have exactly one sequence."); return
        (parent or self.tree.invisibleRootItem()).removeChild(item)
        self.panel.show_add_cmd()

    # ── import ───────────────────────────────────────────────────────────────

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import YAML", "", "YAML Files (*.yaml *.yml)")
        if not path: return
        try:
            with open(path, "r", encoding="utf-8") as f: data = yaml.safe_load(f)
            self.tree.clear()
            for seq_id, sd in data.get("sequences", {}).items():
                chars_raw = sd.get("characters", {})
                chars_str = ", ".join(f"{k}: {v}" for k,v in chars_raw.items()) if isinstance(chars_raw, dict) else ""
                d = {"id": seq_id, "title": sd.get("title",""), "desc": sd.get("description",""),
                     "bg": sd.get("background",""), "chars": chars_str}
                node = self._make_seq_node(d)
                self.tree.invisibleRootItem().addChild(node)
                self._refresh_seq_children(node, d)
                sc = self._make_seq_container()
                node.addChild(sc)
                self._load_seq(sd.get("sequence", []), sc)
                sc.setExpanded(True); node.setExpanded(True)
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _load_seq(self, seq, parent):
        for entry in seq:
            if not isinstance(entry, dict): continue
            if "background" in entry and "fadeout" in entry:
                parent.addChild(self._make_cmd_node("background",
                    f"{entry['background']}, fadeout: {entry['fadeout']}")); continue
            for key, val in entry.items():
                if key == "choice":
                    cn = self._make_cmd_node("choice", ""); parent.addChild(cn)
                    for opt in (val or []):
                        on = self._make_cmd_node("option", f'"{opt.get("option","")}"')
                        sn = self._make_seq_container()
                        on.addChild(sn)
                        self._load_seq(opt.get("sequence", []), sn)
                        sn.setExpanded(True); on.setExpanded(True); cn.addChild(on)
                    cn.setExpanded(True)
                else:
                    v = f'"{val}"' if key == "say" and val is not None else (str(val) if val is not None else "")
                    parent.addChild(self._make_cmd_node(key, v))

    # ── export ───────────────────────────────────────────────────────────────

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export YAML", "", "YAML Files (*.yaml)")
        if not path: return
        try:
            sequences = {}; root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                sn = root.child(i)
                if not self._is_seq(sn): continue
                d = sn.data(0, Qt.UserRole+1) or {}
                seq_id = d.get("id", f"seq_{i}")
                chars = {}
                for part in d.get("chars","").split(","):
                    if ":" in part:
                        k, v = part.split(":", 1); chars[k.strip()] = v.strip()
                sc = self._find_seq_container(sn)
                sequences[seq_id] = {
                    "title":       d.get("title",""),
                    "description": d.get("desc",""),
                    "background":  d.get("bg",""),
                    "characters":  chars,
                    "sequence":    self._build_seq(sc if sc else sn)
                }
            with open(path, "w", encoding="utf-8") as f:
                f.write(dump_yaml({"sequences": sequences}))
            QMessageBox.information(self, "Exported", "File saved successfully.")
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def _build_seq(self, parent):
        if parent is None: return []
        seq = []
        skip = {"title", "description", "characters", "__seq__"}
        for i in range(parent.childCount()):
            child = parent.child(i)
            key   = child.data(0, Qt.UserRole) or child.text(0)
            value = child.text(1)
            if key in skip or self._is_seq(child) or key == "option": continue
            if is_seq_container(child):
                seq.extend(self._build_seq(child)); continue
            if key == "choice":
                opts = []
                for j in range(child.childCount()):
                    oc = child.child(j); opt_text = oc.text(1).strip('"')
                    sc = next((oc.child(k) for k in range(oc.childCount()) if is_seq_container(oc.child(k))), None)
                    opts.append({"option": DoubleQuotedStr(opt_text), "sequence": self._build_seq(sc) if sc else []})
                seq.append({"choice": opts})
            elif key == "background":
                p = child.parent()
                if p and (p.data(0, Qt.UserRole) or p.text(0)) == "__seq__":
                    continue
                entry = {"background": value}
                if ", fadeout:" in value:
                    p_parts = value.split(", fadeout:")
                    try: fade = int(p_parts[1].strip()) if "." not in p_parts[1] else float(p_parts[1].strip())
                    except: fade = p_parts[1].strip()
                    entry = {"background": p_parts[0].strip(), "fadeout": fade}
                seq.append(entry)
            elif key == "say":
                seq.append({"say": DoubleQuotedStr(value.strip('"'))})
            elif key == "wait":
                try: seq.append({"wait": int(value) if "." not in value else float(value)})
                except: seq.append({"wait": value})
            else:
                seq.append({key: value})
        return seq

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete: self._delete()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    init_fonts()
    theme.apply(app)
    w = DialogueTreeEditor(); w.show()
    sys.exit(app.exec())