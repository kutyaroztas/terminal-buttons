#!/usr/bin/env python3
"""SecureCRT/WindTerm-style window: tabbed VTE terminals (the same widget
gnome-terminal uses) with split panes, search, and grouped, colored, editable
buttons that send commands or keystrokes to the focused terminal."""
import json
import math
import os
import re

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango, Vte  # noqa: E402

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(APP_DIR, "config")
BUTTONS_FILE = os.path.join(CONFIG_DIR, "buttons.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
APP_NAME = "Smart Terminal"
APP_VERSION = "1.0"
ICON_FILE = os.path.join(APP_DIR, "terminal-buttons.svg")
TAB_ICON_FILE = os.path.join(APP_DIR, "assets", "tab-icon.svg")
TAB_ICON_SIZE = 18
FONT = "Ubuntu Sans Mono 13"
DEFAULT_GROUP = "General"

DEFAULT_BUTTONS = [
    {"label": "ls -larth", "cmd": "ls -larth", "enter": True, "group": "Files", "color": "#729fcf"},
    {"label": "pwd", "cmd": "pwd", "enter": True, "group": "Files", "color": "#8ae234"},
    {"label": "clear", "cmd": "clear", "enter": True, "group": "Files", "color": "#fce94f"},
    {"label": "Ctrl+C", "cmd": "\\x03", "enter": False, "group": "Keys", "color": "#ef2929"},
    {"label": "Ctrl+D", "cmd": "\\x04", "enter": False, "group": "Keys", "color": "#ad7fa8"},
    {"label": "Esc", "cmd": "\\x1b", "enter": False, "group": "Keys", "color": "#fcaf3e"},
    {"label": "Tab", "cmd": "\\t", "enter": False, "group": "Keys", "color": "#34e2e2"},
]

# Shortcut actions, in the order they appear in Settings. Values are GTK accelerator strings.
DEFAULT_SHORTCUTS = {
    "new_tab": "<Ctrl><Shift>t",
    "close_tab": "<Ctrl>w",
    "next_tab": "<Ctrl>Tab",
    "prev_tab": "<Ctrl><Shift>Tab",
    "split_v": "<Ctrl><Shift>e",
    "split_h": "<Ctrl><Shift>o",
    "close_pane": "<Ctrl><Shift>w",
    "find": "<Ctrl>f",
    "copy": "<Ctrl><Shift>c",
    "paste": "<Ctrl><Shift>v",
}
DEFAULT_SETTINGS = {
    "theme": "aubergine",
    "lang": "en",
    "rightclick_action": "menu",   # "menu" = context menu, "putty" = copy selection / paste
    "copy_on_select": False,
    "middle_paste": True,
    "paste_warning": True,
    "tab_hover_delay": 2.0,        # seconds of hovering before a tab is activated; 0 = off
    "group_order": [],             # button-group names, first = top of the drop-down and shown at start
    "shortcuts": DEFAULT_SHORTCUTS,
}

# --- themes -----------------------------------------------------------------
LIGHT_PALETTE = ("#171421", "#c01c28", "#26a269", "#a2734c", "#12488b", "#a347ba",
                 "#2aa1b3", "#d0cfcc", "#5e5c64", "#f66151", "#33da7a", "#e9ad0c",
                 "#2a7bde", "#c061cb", "#33c7de", "#ffffff")
TANGO_PALETTE = ("#2e3436", "#cc0000", "#4e9a06", "#c4a000", "#3465a4", "#75507b",
                 "#06989a", "#d3d7cf", "#555753", "#ef2929", "#8ae234", "#fce94f",
                 "#729fcf", "#ad7fa8", "#34e2e2", "#eeeeec")
# bg/fg/palette: terminal colors; chrome/btn: window and button-bar colors (None = system theme)
THEMES = {
    "light": {"dark": False, "bg": "#ffffff", "fg": "#171421", "palette": LIGHT_PALETTE,
              "chrome": None, "btn": None},
    "dark": {"dark": True, "bg": "#1e1e1e", "fg": "#d4d4d4", "palette": TANGO_PALETTE,
             "chrome": "#2b2b2b", "btn": "#3a3a3a"},
    "blue": {"dark": True, "bg": "#012456", "fg": "#eeedf0", "palette": TANGO_PALETTE,
             "chrome": "#0a3170", "btn": "#1c4a94"},
    "aubergine": {"dark": True, "bg": "#300a24", "fg": "#eeeeec", "palette": TANGO_PALETTE,
                  "chrome": "#3e1132", "btn": "#5c2a4e"},
}

# --- translations -----------------------------------------------------------
LANGS = {"en": "English", "de": "Deutsch", "fr": "Français", "tr": "Türkçe", "ru": "Русский"}
STRINGS = {
    "en": {
        "new_tab": "New tab", "edit_buttons": "Edit buttons", "group_order": "Group order",
        "settings": "Settings", "cancel": "Cancel", "save": "Save", "close": "Close",
        "col_label": "Label", "col_command": "Command (\\x03=Ctrl+C, \\t, \\e)",
        "col_enter": "Enter", "col_color": "Color", "col_group": "Group",
        "add": "Add", "delete": "Delete", "up": "Up", "down": "Down",
        "clear_color": "Clear color", "pick_color": "Button color",
        "theme": "Theme", "language": "Language",
        "theme_light": "Light", "theme_dark": "Dark", "theme_blue": "Blue",
        "theme_aubergine": "Aubergine", "new_label": "new", "terminal": "Terminal",
        "rename_tab": "Rename tab", "close_tab": "Close tab", "close_pane": "Close pane",
        "copy": "Copy", "paste": "Paste", "select_all": "Select all",
        "split_v": "Split vertically", "split_h": "Split horizontally",
        "find": "Find", "search_placeholder": "Search…",
        "find_next": "Next match", "find_prev": "Previous match",
        "tab_general": "General", "tab_shortcuts": "Shortcuts",
        "rightclick_action": "Right-click action", "rc_menu": "Context menu",
        "rc_putty": "Copy / paste (PuTTY style)",
        "copy_on_select": "Copy on select", "middle_paste": "Middle-click pastes",
        "paste_warning": "Warn before pasting multiple lines",
        "paste_lines": "Paste {n} lines into terminal?",
        "press_shortcut": "Press the new shortcut… (Esc cancels, Backspace clears)",
        "reset_shortcuts": "Reset to defaults",
        "next_tab": "Next tab", "prev_tab": "Previous tab", "clone_tab": "Clone tab",
        "edit_button": "Edit…", "tab_hover_delay": "Switch tab on hover (seconds, 0 = off)",
        "export_settings": "Export settings…", "import_settings": "Import settings…",
        "import_bad": "This is not a valid settings file.",
        "json_files": "Settings files (*.json)",
    },
    "de": {
        "new_tab": "Neuer Tab", "edit_buttons": "Schaltflächen bearbeiten", "group_order": "Gruppenreihenfolge",
        "settings": "Einstellungen", "cancel": "Abbrechen", "save": "Speichern",
        "close": "Schließen", "col_label": "Beschriftung",
        "col_command": "Befehl (\\x03=Strg+C, \\t, \\e)", "col_enter": "Enter",
        "col_color": "Farbe", "col_group": "Gruppe",
        "add": "Hinzufügen", "delete": "Löschen", "up": "Nach oben", "down": "Nach unten",
        "clear_color": "Farbe entfernen", "pick_color": "Schaltflächenfarbe",
        "theme": "Design", "language": "Sprache",
        "theme_light": "Hell", "theme_dark": "Dunkel", "theme_blue": "Blau",
        "theme_aubergine": "Aubergine", "new_label": "neu", "terminal": "Terminal",
        "rename_tab": "Tab umbenennen", "close_tab": "Tab schließen",
        "close_pane": "Bereich schließen",
        "copy": "Kopieren", "paste": "Einfügen", "select_all": "Alles auswählen",
        "split_v": "Vertikal teilen", "split_h": "Horizontal teilen",
        "find": "Suchen", "search_placeholder": "Suchen…",
        "find_next": "Nächster Treffer", "find_prev": "Vorheriger Treffer",
        "tab_general": "Allgemein", "tab_shortcuts": "Tastenkürzel",
        "rightclick_action": "Rechtsklick-Aktion", "rc_menu": "Kontextmenü",
        "rc_putty": "Kopieren / Einfügen (PuTTY-Stil)",
        "copy_on_select": "Beim Auswählen kopieren", "middle_paste": "Mittelklick fügt ein",
        "paste_warning": "Vor dem Einfügen mehrerer Zeilen warnen",
        "paste_lines": "{n} Zeilen in das Terminal einfügen?",
        "press_shortcut": "Neues Tastenkürzel drücken … (Esc bricht ab, Rücktaste löscht)",
        "reset_shortcuts": "Standard wiederherstellen",
        "next_tab": "Nächster Tab", "prev_tab": "Vorheriger Tab", "clone_tab": "Tab duplizieren",
        "edit_button": "Bearbeiten…",
        "tab_hover_delay": "Tab beim Überfahren wechseln (Sekunden, 0 = aus)",
        "export_settings": "Einstellungen exportieren…", "import_settings": "Einstellungen importieren…",
        "import_bad": "Das ist keine gültige Einstellungsdatei.",
        "json_files": "Einstellungsdateien (*.json)",
    },
    "fr": {
        "new_tab": "Nouvel onglet", "edit_buttons": "Modifier les boutons", "group_order": "Ordre des groupes",
        "settings": "Paramètres", "cancel": "Annuler", "save": "Enregistrer",
        "close": "Fermer", "col_label": "Libellé",
        "col_command": "Commande (\\x03=Ctrl+C, \\t, \\e)", "col_enter": "Entrée",
        "col_color": "Couleur", "col_group": "Groupe",
        "add": "Ajouter", "delete": "Supprimer", "up": "Monter", "down": "Descendre",
        "clear_color": "Effacer la couleur", "pick_color": "Couleur du bouton",
        "theme": "Thème", "language": "Langue",
        "theme_light": "Clair", "theme_dark": "Sombre", "theme_blue": "Bleu",
        "theme_aubergine": "Aubergine", "new_label": "nouveau", "terminal": "Terminal",
        "rename_tab": "Renommer l'onglet", "close_tab": "Fermer l'onglet",
        "close_pane": "Fermer le volet",
        "copy": "Copier", "paste": "Coller", "select_all": "Tout sélectionner",
        "split_v": "Diviser verticalement", "split_h": "Diviser horizontalement",
        "find": "Rechercher", "search_placeholder": "Rechercher…",
        "find_next": "Occurrence suivante", "find_prev": "Occurrence précédente",
        "tab_general": "Général", "tab_shortcuts": "Raccourcis",
        "rightclick_action": "Action du clic droit", "rc_menu": "Menu contextuel",
        "rc_putty": "Copier / coller (style PuTTY)",
        "copy_on_select": "Copier à la sélection", "middle_paste": "Le clic milieu colle",
        "paste_warning": "Avertir avant de coller plusieurs lignes",
        "paste_lines": "Coller {n} lignes dans le terminal ?",
        "press_shortcut": "Appuyez sur le nouveau raccourci… (Échap annule, Retour arrière efface)",
        "reset_shortcuts": "Rétablir les valeurs par défaut",
        "next_tab": "Onglet suivant", "prev_tab": "Onglet précédent", "clone_tab": "Dupliquer l'onglet",
        "edit_button": "Modifier…",
        "tab_hover_delay": "Changer d'onglet au survol (secondes, 0 = désactivé)",
        "export_settings": "Exporter les paramètres…", "import_settings": "Importer les paramètres…",
        "import_bad": "Ce n'est pas un fichier de paramètres valide.",
        "json_files": "Fichiers de paramètres (*.json)",
    },
    "tr": {
        "new_tab": "Yeni sekme", "edit_buttons": "Düğmeleri düzenle", "group_order": "Grup sırası",
        "settings": "Ayarlar", "cancel": "İptal", "save": "Kaydet", "close": "Kapat",
        "col_label": "Etiket", "col_command": "Komut (\\x03=Ctrl+C, \\t, \\e)",
        "col_enter": "Enter", "col_color": "Renk", "col_group": "Grup",
        "add": "Ekle", "delete": "Sil", "up": "Yukarı", "down": "Aşağı",
        "clear_color": "Rengi kaldır", "pick_color": "Düğme rengi",
        "theme": "Tema", "language": "Dil",
        "theme_light": "Açık", "theme_dark": "Koyu", "theme_blue": "Mavi",
        "theme_aubergine": "Aubergine", "new_label": "yeni", "terminal": "Terminal",
        "rename_tab": "Sekmeyi yeniden adlandır", "close_tab": "Sekmeyi kapat",
        "close_pane": "Bölmeyi kapat",
        "copy": "Kopyala", "paste": "Yapıştır", "select_all": "Tümünü seç",
        "split_v": "Dikey böl", "split_h": "Yatay böl",
        "find": "Ara", "search_placeholder": "Ara…",
        "find_next": "Sonraki eşleşme", "find_prev": "Önceki eşleşme",
        "tab_general": "Genel", "tab_shortcuts": "Kısayollar",
        "rightclick_action": "Sağ tık eylemi", "rc_menu": "Bağlam menüsü",
        "rc_putty": "Kopyala / yapıştır (PuTTY tarzı)",
        "copy_on_select": "Seçince kopyala", "middle_paste": "Orta tık yapıştırır",
        "paste_warning": "Çok satırlı yapıştırmadan önce uyar",
        "paste_lines": "Terminale {n} satır yapıştırılsın mı?",
        "press_shortcut": "Yeni kısayola bas… (Esc iptal, Backspace siler)",
        "reset_shortcuts": "Varsayılanlara dön",
        "next_tab": "Sonraki sekme", "prev_tab": "Önceki sekme", "clone_tab": "Sekmeyi klonla",
        "edit_button": "Düzenle…",
        "tab_hover_delay": "Üzerinde bekleyince sekmeye geç (saniye, 0 = kapalı)",
        "export_settings": "Ayarları dışa aktar…", "import_settings": "Ayarları içe aktar…",
        "import_bad": "Bu geçerli bir ayar dosyası değil.",
        "json_files": "Ayar dosyaları (*.json)",
    },
    "ru": {
        "new_tab": "Новая вкладка", "edit_buttons": "Изменить кнопки", "group_order": "Порядок групп",
        "settings": "Настройки", "cancel": "Отмена", "save": "Сохранить",
        "close": "Закрыть", "col_label": "Название",
        "col_command": "Команда (\\x03=Ctrl+C, \\t, \\e)", "col_enter": "Enter",
        "col_color": "Цвет", "col_group": "Группа",
        "add": "Добавить", "delete": "Удалить", "up": "Вверх", "down": "Вниз",
        "clear_color": "Убрать цвет", "pick_color": "Цвет кнопки",
        "theme": "Тема", "language": "Язык",
        "theme_light": "Светлая", "theme_dark": "Тёмная", "theme_blue": "Синяя",
        "theme_aubergine": "Баклажан", "new_label": "новая", "terminal": "Terminal",
        "rename_tab": "Переименовать вкладку", "close_tab": "Закрыть вкладку",
        "close_pane": "Закрыть панель",
        "copy": "Копировать", "paste": "Вставить", "select_all": "Выделить всё",
        "split_v": "Разделить по вертикали", "split_h": "Разделить по горизонтали",
        "find": "Найти", "search_placeholder": "Поиск…",
        "find_next": "Следующее совпадение", "find_prev": "Предыдущее совпадение",
        "tab_general": "Общие", "tab_shortcuts": "Горячие клавиши",
        "rightclick_action": "Действие правой кнопки", "rc_menu": "Контекстное меню",
        "rc_putty": "Копировать / вставлять (как в PuTTY)",
        "copy_on_select": "Копировать при выделении", "middle_paste": "Средняя кнопка вставляет",
        "paste_warning": "Предупреждать при вставке нескольких строк",
        "paste_lines": "Вставить {n} строк в терминал?",
        "press_shortcut": "Нажмите новую комбинацию… (Esc — отмена, Backspace — очистить)",
        "reset_shortcuts": "Сбросить по умолчанию",
        "next_tab": "Следующая вкладка", "prev_tab": "Предыдущая вкладка",
        "clone_tab": "Клонировать вкладку", "edit_button": "Изменить…",
        "tab_hover_delay": "Переключать вкладку при наведении (секунды, 0 = выкл.)",
        "export_settings": "Экспорт настроек…", "import_settings": "Импорт настроек…",
        "import_bad": "Это не файл настроек.",
        "json_files": "Файлы настроек (*.json)",
    },
}

ESCAPES = {"n": "\n", "t": "\t", "e": "\x1b", "r": "\r", "\\": "\\"}
PCRE2_CASELESS = 0x00000008
PCRE2_MULTILINE = 0x00000400
MODIFIER_KEY_NAME = re.compile(r"(Shift|Control|Alt|Super|Meta|Hyper|Caps|Num|ISO_Level3)_")
COMMAND_MODS = (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK
                | Gdk.ModifierType.SUPER_MASK | Gdk.ModifierType.META_MASK)


def rgba(hex_color):
    color = Gdk.RGBA()
    color.parse(hex_color)
    return color


def rgba_to_hex(color):
    return "#%02x%02x%02x" % tuple(int(v * 255 + 0.5) for v in (color.red, color.green, color.blue))


def decode(text):
    """Turn \\xHH, \\n, \\t, \\e, \\r and \\\\ sequences into the real characters."""
    def replace(m):
        s = m.group(1)
        return chr(int(s[1:], 16)) if s[0] == "x" else ESCAPES[s]
    return re.sub(r"\\(x[0-9a-fA-F]{2}|[ntre\\])", replace, text)


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_buttons():
    data = read_json(BUTTONS_FILE, None)
    if not isinstance(data, list):
        return [dict(b) for b in DEFAULT_BUTTONS]
    default_groups = {b["label"]: b["group"] for b in DEFAULT_BUTTONS}
    for b in data:
        # Older configs had no group, or used the Turkish name "Genel"
        if not b.get("group") or b["group"] == "Genel":
            b["group"] = default_groups.get(b.get("label"), DEFAULT_GROUP)
        b.setdefault("color", "")
    return data


def load_settings():
    return normalize_settings(read_json(SETTINGS_FILE, {}))


def normalize_settings(saved):
    """Merge a saved/imported settings dict over the defaults and validate it."""
    if not isinstance(saved, dict):
        saved = {}
    if saved.pop("rightclick_copy", False) and "rightclick_action" not in saved:
        saved["rightclick_action"] = "putty"  # migrate the old checkbox
    settings = dict(DEFAULT_SETTINGS)
    settings.update(saved)
    shortcuts = saved.get("shortcuts")
    settings["shortcuts"] = {**DEFAULT_SHORTCUTS, **(shortcuts if isinstance(shortcuts, dict) else {})}
    try:
        settings["tab_hover_delay"] = max(0.0, float(settings["tab_hover_delay"]))
    except (TypeError, ValueError):
        settings["tab_hover_delay"] = DEFAULT_SETTINGS["tab_hover_delay"]
    if settings["theme"] not in THEMES:
        settings["theme"] = DEFAULT_SETTINGS["theme"]
    if settings["lang"] not in LANGS:
        settings["lang"] = DEFAULT_SETTINGS["lang"]
    if settings["rightclick_action"] not in ("menu", "putty"):
        settings["rightclick_action"] = "menu"
    order = settings["group_order"]
    settings["group_order"] = [g for g in order if isinstance(g, str)] if isinstance(order, list) else []
    return settings


def ordered_groups(names, order):
    """Unique group names: those listed in `order` first (in that order), the rest as they appear."""
    present = list(dict.fromkeys(names))
    return [g for g in order if g in present] + [g for g in present if g not in order]


def first_terminal(widget):
    """Leftmost/topmost terminal inside a pane tree."""
    if isinstance(widget, Vte.Terminal):
        return widget
    if isinstance(widget, Gtk.Paned):
        return first_terminal(widget.get_child1())
    return None


def replace_child(parent, old, new):
    """Put `new` where `old` was inside a Box (a tab page) or a Paned."""
    if isinstance(parent, Gtk.Paned):
        first = parent.get_child1() is old
        pos = parent.get_position()
        parent.remove(old)
        (parent.pack1 if first else parent.pack2)(new, True, False)
        parent.set_position(pos)
    else:
        parent.remove(old)
        parent.pack_start(new, True, True, 0)


def accel_label(accel):
    """'<Ctrl><Shift>t' -> 'Ctrl+Shift+T' ('' if unset)."""
    if not accel:
        return ""
    keyval, mods = Gtk.accelerator_parse(accel)
    return Gtk.accelerator_get_label(keyval, mods) if keyval else ""


class Page(Gtk.Box):
    """One notebook tab: a tree of terminals (Paned splits), a search bar, a tab label."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.last_term = None       # most recently focused terminal in this tab
        self.custom_title = None    # user-chosen name; None = follow the terminal title
        self.title_label = Gtk.Label()
        self.search_bar = None
        self.search_entry = None

    def root(self):
        """The pane tree (every child except the search bar)."""
        for child in self.get_children():
            if child is not self.search_bar:
                return child
        return None


class App(Gtk.Window):
    def __init__(self):
        super().__init__(title=f"{APP_NAME} v{APP_VERSION}")
        self.set_default_size(1000, 650)
        self.buttons = load_buttons()
        self.settings = load_settings()
        self.menu = None
        self.css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Own header bar so it can be dark gray like GNOME Terminal's, whatever the GTK theme
        header = Gtk.HeaderBar(show_close_button=True, title=f"{APP_NAME} v{APP_VERSION}")
        header.get_style_context().add_class("tb-titlebar")
        self.set_titlebar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.get_style_context().add_class("tb-root")
        self.add(root)

        # Terminal tabs; new-tab and split buttons sit in the tab strip
        self.nb = Gtk.Notebook(scrollable=True)
        tools = Gtk.Box(spacing=2)
        self.action_buttons = {
            "new_tab": self.icon_button(("tab-new-symbolic",), "+"),
            "split_v": self.icon_button(("view-dual-symbolic",), "|"),
            "split_h": self.icon_button(("view-continuous-symbolic",), "-"),
        }
        for action, button in self.action_buttons.items():
            button.set_relief(Gtk.ReliefStyle.NONE)
            button.connect("clicked", lambda _b, a=action: self.perform(a))
            tools.pack_start(button, False, False, 0)
        tools.show_all()
        self.nb.set_action_widget(tools, Gtk.PackType.END)
        self.nb.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.nb.connect("button-press-event", self.strip_click)
        root.pack_start(self.nb, True, True, 0)

        # Bottom bar: group drop-down, buttons of that group, edit, settings
        bar = Gtk.Box(spacing=6, margin=4)
        bar.get_style_context().add_class("tb-bar")
        # A popover (drawn inside the window) instead of a ComboBox: the combo popup is a separate
        # window that gets clipped near the screen edge, so not every group was always visible.
        self.group = None
        self.group_label = Gtk.Label(xalign=0)
        group_box = Gtk.Box(spacing=8)
        group_box.pack_start(self.group_label, True, True, 0)
        group_box.pack_start(Gtk.Image.new_from_icon_name("pan-up-symbolic", Gtk.IconSize.BUTTON),
                             False, False, 0)
        self.group_btn = Gtk.MenuButton(direction=Gtk.ArrowType.UP)
        self.group_btn.add(group_box)
        self.group_popover = Gtk.Popover(position=Gtk.PositionType.TOP)
        self.group_btn.set_popover(self.group_popover)
        bar.pack_start(self.group_btn, False, False, 0)
        self.btnbox = Gtk.Box(spacing=2)
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.AUTOMATIC,
                                      vscrollbar_policy=Gtk.PolicyType.NEVER)
        scroller.add(self.btnbox)
        bar.pack_start(scroller, True, True, 0)
        self.settings_btn = self.icon_button(("emblem-system-symbolic",), "S")
        self.settings_btn.connect("clicked", lambda *_: self.settings_dialog())
        bar.pack_end(self.settings_btn, False, False, 0)
        self.edit_btn = self.icon_button(("document-edit-symbolic",), "E")
        self.edit_btn.connect("clicked", lambda *_: self.edit_dialog())
        bar.pack_end(self.edit_btn, False, False, 0)
        root.pack_start(bar, False, False, 0)

        self.connect("key-press-event", self.on_key)
        self.connect("destroy", Gtk.main_quit)

        self.apply_language()
        self.rebuild_buttons()
        self.new_tab()
        self.apply_theme()

    @staticmethod
    def icon_button(icon_names, fallback_label):
        theme = Gtk.IconTheme.get_default()
        for name in icon_names:
            if theme.has_icon(name):
                return Gtk.Button.new_from_icon_name(name, Gtk.IconSize.BUTTON)
        return Gtk.Button(label=fallback_label)

    # --- i18n / settings ---
    def tr(self, key):
        return STRINGS[self.settings["lang"]][key]

    def save_settings(self):
        write_json(SETTINGS_FILE, self.settings)

    def tip(self, action):
        """Tooltip text for an action: its name plus the current shortcut."""
        keys = accel_label(self.settings["shortcuts"].get(action))
        return self.tr(action) + (f" ({keys})" if keys else "")

    def apply_language(self):
        for action, button in self.action_buttons.items():
            button.set_tooltip_text(self.tip(action))
        self.edit_btn.set_tooltip_text(self.tr("edit_buttons"))
        self.settings_btn.set_tooltip_text(self.tr("settings"))

    def apply_theme(self):
        theme = THEMES[self.settings["theme"]]
        Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", theme["dark"])
        if theme["chrome"]:
            css = (
                ".tb-root, .tb-bar, .tb-root notebook > header {{ background-color: {chrome}; }}"
                ".tb-root notebook > header tab {{ background-color: {chrome}; }}"
                ".tb-root notebook > header tab:checked {{ background-color: {btn}; }}"
                ".tb-root notebook > header tab label {{ color: {fg}; }}"
                ".tb-bar scrolledwindow, .tb-bar viewport {{ background-color: {chrome}; }}"
                ".tb-root button {{ background-image: none; background-color: {btn};"
                " color: {fg}; border: 1px solid alpha({fg}, 0.25); }}"
                ".tb-root button:hover {{ background-color: alpha({fg}, 0.25); }}"
                ".tb-bar label {{ color: {fg}; }}"
            ).format(**theme)
        else:
            css = ""
        # Dark gray title bar in every theme; the tab close button stays flat and small
        css += ("headerbar.tb-titlebar { background-image: none; background-color: #2b2b2b;"
                " color: #eeeeec; border-bottom: 1px solid #1a1a1a; box-shadow: none; }"
                "headerbar.tb-titlebar label, headerbar.tb-titlebar button { color: #eeeeec; }"
                "headerbar.tb-titlebar button { background-image: none; background-color: transparent;"
                " border-color: transparent; box-shadow: none; }"
                "headerbar.tb-titlebar button:hover { background-color: rgba(255, 255, 255, 0.14); }")
        css += (".tb-root button.tb-tabclose { background-image: none; background-color: transparent;"
                " border: none; box-shadow: none; padding: 0 2px; min-width: 0; min-height: 0; }"
                ".tb-root button.tb-tabclose:hover { background-color: alpha(#e95420, 0.6); }")
        self.css.load_from_data(css.encode("utf-8"))
        for i in range(self.nb.get_n_pages()):
            self.restyle_terminals(self.nb.get_nth_page(i))

    def restyle_terminals(self, widget):
        if isinstance(widget, Vte.Terminal):
            self.style_terminal(widget)
        elif isinstance(widget, Gtk.Paned):
            self.restyle_terminals(widget.get_child1())
            self.restyle_terminals(widget.get_child2())
        elif isinstance(widget, Gtk.Box):
            for child in widget.get_children():
                self.restyle_terminals(child)

    def style_terminal(self, term):
        theme = THEMES[self.settings["theme"]]
        term.set_colors(rgba(theme["fg"]), rgba(theme["bg"]),
                        [rgba(c) for c in theme["palette"]])

    # --- tabs and panes ---
    def new_terminal(self, cwd=None):
        term = Vte.Terminal()
        term.set_scrollback_lines(20000)
        term.set_font(Pango.FontDescription(FONT))
        term.set_mouse_autohide(True)
        self.style_terminal(term)
        shell = os.environ.get("SHELL", "/bin/bash")
        if not cwd or not os.path.isdir(cwd):
            cwd = os.path.expanduser("~")
        term.spawn_async(Vte.PtyFlags.DEFAULT, cwd, [shell],
                         None, GLib.SpawnFlags.DEFAULT, None, None, -1, None,
                         lambda t, pid, _err, *_: setattr(t, "shell_pid", pid))
        term.connect("window-title-changed", self.on_terminal_title)
        term.connect("child-exited", lambda t, _status: self.close_pane(t))
        term.connect("focus-in-event", self.on_terminal_focus)
        term.connect("key-press-event", lambda t, ev: self.handle_shortcut(ev, t))
        term.connect("button-press-event", self.term_click)
        term.connect("button-release-event", self.term_release)
        return term

    def new_tab(self, cwd=None, position=-1, title=None):
        page = Page()
        term = self.new_terminal(cwd)
        page.last_term = term
        page.pack_start(term, True, True, 0)
        self.build_search_bar(page)
        page.custom_title = title
        page.title_label.set_text(title or self.tr("terminal"))
        page.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        page.title_label.set_width_chars(12)
        page.title_label.set_max_width_chars(28)
        close = Gtk.Button(relief=Gtk.ReliefStyle.NONE, focus_on_click=False)
        close.add(Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU))
        close.get_style_context().add_class("tb-tabclose")
        close.set_tooltip_text(self.tr("close_tab"))
        close.connect("clicked", lambda _b: self.close_page(page))
        tab = Gtk.EventBox(visible_window=False)  # receives double/right clicks and hover
        box = Gtk.Box(spacing=6)
        icon = self.tab_icon()
        if icon is not None:
            box.pack_start(icon, False, False, 0)
        box.pack_start(page.title_label, True, True, 0)
        box.pack_start(close, False, False, 0)
        tab.add(box)
        tab.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        tab.connect("button-press-event", self.tab_click, page)
        tab.connect("enter-notify-event", self.tab_enter, page)
        tab.connect("leave-notify-event", self.tab_leave)
        tab.show_all()
        page.show_all()
        self.nb.insert_page(page, tab, position)
        self.nb.set_tab_reorderable(page, True)
        self.nb.set_current_page(self.nb.page_num(page))
        term.grab_focus()

    def tab_icon(self):
        """The small penguin at the left of each tab, rendered sharp on HiDPI screens."""
        scale = self.get_scale_factor()
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(
                TAB_ICON_FILE, TAB_ICON_SIZE * scale, TAB_ICON_SIZE * scale)
        except GLib.Error:
            return None  # icon file missing: tabs simply have no icon
        surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, scale, None)
        return Gtk.Image.new_from_surface(surface)

    def clone_tab(self, page):
        """Open a new tab next to `page`, in the same working directory."""
        term = page.last_term or first_terminal(page.root())
        cwd = None
        uri = term.get_current_directory_uri() if term is not None else None
        if uri:
            cwd = GLib.filename_from_uri(uri)[0]
        elif term is not None and getattr(term, "shell_pid", None):
            try:  # the shell did not report its directory: ask the kernel
                cwd = os.readlink(f"/proc/{term.shell_pid}/cwd")
            except OSError:
                pass
        self.new_tab(cwd, self.nb.page_num(page) + 1, page.custom_title)

    # Hovering a tab for `tab_hover_delay` seconds activates it
    def tab_enter(self, _tab, _ev, page):
        self.tab_leave()
        delay = self.settings["tab_hover_delay"]
        if delay > 0 and self.nb.get_current_page() != self.nb.page_num(page):
            self.hover_timer = GLib.timeout_add(int(delay * 1000), self.hover_switch, page)
        return False

    def tab_leave(self, _tab=None, ev=None):
        if ev is not None and ev.detail == Gdk.NotifyType.INFERIOR:
            return False  # moved onto the close button, still on the tab
        timer = getattr(self, "hover_timer", 0)
        if timer:
            GLib.source_remove(timer)
            self.hover_timer = 0
        return False

    def hover_switch(self, page):
        self.hover_timer = 0
        n = self.nb.page_num(page)
        if n >= 0:
            self.nb.set_current_page(n)
            term = page.last_term
            if term is not None and term.get_parent() is not None:
                term.grab_focus()
        return False

    def page_of(self, widget):
        while widget is not None and not isinstance(widget, Page):
            widget = widget.get_parent()
        return widget

    def current(self):
        n = self.nb.get_current_page()
        return self.nb.get_nth_page(n) if n >= 0 else None

    def focused_terminal(self):
        page = self.current()
        if page is None:
            return None
        term = page.last_term
        if term is not None and term.get_parent() is not None:
            return term
        return first_terminal(page.root())

    def on_terminal_focus(self, term, _event):
        page = self.page_of(term)
        if page is not None:
            page.last_term = term
            self.update_title(page, term)
        return False

    def on_terminal_title(self, term):
        page = self.page_of(term)
        if page is not None and page.last_term in (None, term):
            self.update_title(page, term)

    def update_title(self, page, term):
        if page.custom_title is None:
            page.title_label.set_text(term.get_window_title() or self.tr("terminal"))

    def close_page(self, page):
        if page is None:
            return
        self.tab_leave()  # drop a pending hover switch
        self.nb.remove_page(self.nb.page_num(page))
        if self.nb.get_n_pages() == 0:
            Gtk.main_quit()

    def split(self, term, orientation):
        """HORIZONTAL = side by side (vertical divider), VERTICAL = stacked."""
        parent = term.get_parent()
        new = self.new_terminal()
        paned = Gtk.Paned(orientation=orientation)
        paned.set_wide_handle(True)
        replace_child(parent, term, paned)
        paned.pack1(term, True, False)
        paned.pack2(new, True, False)
        paned.show_all()

        def halve():
            horizontal = orientation == Gtk.Orientation.HORIZONTAL
            size = paned.get_allocated_width() if horizontal else paned.get_allocated_height()
            paned.set_position(size // 2)
            return False
        GLib.timeout_add(60, halve)
        new.grab_focus()

    def close_pane(self, term):
        page = self.page_of(term)
        parent = term.get_parent()
        if page is None or parent is None:  # already closed
            return
        if isinstance(parent, Gtk.Paned):
            sibling = parent.get_child2() if parent.get_child1() is term else parent.get_child1()
            parent.remove(term)
            parent.remove(sibling)
            replace_child(parent.get_parent(), parent, sibling)
            survivor = first_terminal(sibling)
            page.last_term = survivor
            if survivor is not None:
                survivor.grab_focus()
        else:
            self.close_page(page)

    # --- shortcuts ---
    def match_shortcut(self, ev):
        state = ev.state & Gtk.accelerator_get_default_mod_mask()
        keyval = Gdk.keyval_to_lower(ev.keyval)
        if keyval == Gdk.KEY_ISO_Left_Tab:  # Shift+Tab arrives as its own keyval
            keyval = Gdk.KEY_Tab
        for action, accel in self.settings["shortcuts"].items():
            if not accel:
                continue
            want_key, want_mods = Gtk.accelerator_parse(accel)
            if want_key and want_key == keyval and want_mods == state:
                return action
        return None

    def handle_shortcut(self, ev, term=None):
        action = self.match_shortcut(ev)
        if action is None:
            return False
        if isinstance(self.get_focus(), Gtk.Editable) and action in ("copy", "paste"):
            return False  # let text entries (search box) keep their own clipboard keys
        self.perform(action, term)
        return True

    def perform(self, action, term=None):
        term = term or self.focused_terminal()
        if action == "new_tab":
            self.new_tab()
        elif action == "close_tab":
            self.close_page(self.current())
        elif action in ("next_tab", "prev_tab"):
            count = self.nb.get_n_pages()
            step = 1 if action == "next_tab" else -1
            self.nb.set_current_page((self.nb.get_current_page() + step) % count)
            focused = self.focused_terminal()
            if focused is not None:
                focused.grab_focus()
        elif term is None:
            return
        elif action == "split_v":
            self.split(term, Gtk.Orientation.HORIZONTAL)
        elif action == "split_h":
            self.split(term, Gtk.Orientation.VERTICAL)
        elif action == "close_pane":
            self.close_pane(term)
        elif action == "find":
            self.open_search(self.page_of(term))
        elif action == "copy":
            term.copy_clipboard_format(Vte.Format.TEXT)
        elif action == "paste":
            self.paste(term)

    def on_key(self, _widget, ev):
        return self.handle_shortcut(ev)

    # --- mouse ---
    def term_click(self, term, ev):
        if ev.button == 2:  # middle click: paste the primary selection, or swallow it
            if self.settings["middle_paste"]:
                self.paste(term, primary=True)
            return True
        if ev.button != 3:
            return False
        if self.settings["rightclick_action"] == "putty":  # copy the selection, else paste
            if term.get_has_selection():
                term.copy_clipboard_format(Vte.Format.TEXT)
                term.unselect_all()
            else:
                self.paste(term)
            return True
        self.show_terminal_menu(term, ev)
        return True

    def term_release(self, term, ev):
        if ev.button == 1 and self.settings["copy_on_select"] and term.get_has_selection():
            term.copy_clipboard_format(Vte.Format.TEXT)
        return False

    def show_terminal_menu(self, term, ev):
        page = self.page_of(term)
        menu = Gtk.Menu()

        def add(key, callback, sensitive=True):
            item = Gtk.MenuItem(label=self.tr(key))
            item.set_sensitive(sensitive)
            item.connect("activate", lambda *_: callback())
            menu.append(item)

        add("copy", lambda: term.copy_clipboard_format(Vte.Format.TEXT), term.get_has_selection())
        add("paste", lambda: self.paste(term))
        add("select_all", term.select_all)
        add("find", lambda: self.open_search(page))
        menu.append(Gtk.SeparatorMenuItem())
        add("split_v", lambda: self.split(term, Gtk.Orientation.HORIZONTAL))
        add("split_h", lambda: self.split(term, Gtk.Orientation.VERTICAL))
        menu.append(Gtk.SeparatorMenuItem())
        add("rename_tab", lambda: self.rename_tab(page))
        add("close_pane", lambda: self.close_pane(term))
        menu.show_all()
        self.menu = menu  # keep a reference while it is open
        menu.popup_at_pointer(ev)

    def strip_click(self, nb, ev):
        """Double-click on the empty part of the tab strip opens a new tab."""
        if ev.type != Gdk.EventType._2BUTTON_PRESS or ev.button != 1:
            return False
        page = nb.get_nth_page(nb.get_current_page())
        if page is None or ev.y >= page.translate_coordinates(nb, 0, 0)[1]:
            return False  # not in the strip (the strip is above the page content)
        for i in range(nb.get_n_pages()):
            label = nb.get_tab_label(nb.get_nth_page(i))
            x, y = label.translate_coordinates(nb, 0, 0)
            a = label.get_allocation()
            if x <= ev.x < x + a.width and y <= ev.y < y + a.height:
                return False  # on a tab: that has its own double-click (clone)
        self.perform("new_tab")
        return True

    def tab_click(self, _tab, ev, page):
        if ev.type == Gdk.EventType._2BUTTON_PRESS and ev.button == 1:
            self.clone_tab(page)
            return True
        if ev.button == 3:
            menu = Gtk.Menu()
            for key, callback in (("clone_tab", lambda: self.clone_tab(page)),
                                  ("rename_tab", lambda: self.rename_tab(page)),
                                  ("close_tab", lambda: self.close_page(page))):
                item = Gtk.MenuItem(label=self.tr(key))
                item.connect("activate", lambda *_, cb=callback: cb())
                menu.append(item)
            menu.show_all()
            self.menu = menu
            menu.popup_at_pointer(ev)
            return True
        return False

    def rename_tab(self, page):
        dlg = Gtk.Dialog(title=self.tr("rename_tab"), transient_for=self, modal=True)
        dlg.add_buttons(self.tr("cancel"), Gtk.ResponseType.CANCEL,
                        self.tr("save"), Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.OK)
        entry = Gtk.Entry(text=page.title_label.get_text(), margin=16, activates_default=True)
        dlg.get_content_area().pack_start(entry, True, True, 0)
        dlg.show_all()
        if dlg.run() == Gtk.ResponseType.OK:
            name = entry.get_text().strip()
            page.custom_title = name or None  # empty name = follow the terminal title again
            term = self.focused_terminal() or page.last_term
            if name:
                page.title_label.set_text(name)
            elif term is not None:
                self.update_title(page, term)
        dlg.destroy()

    # --- paste ---
    def paste(self, term, primary=False):
        """Paste the clipboard (or the primary selection), warning on multi-line text."""
        which = Gdk.SELECTION_PRIMARY if primary else Gdk.SELECTION_CLIPBOARD
        Gtk.Clipboard.get(which).request_text(lambda _clip, text: self.paste_text(term, text))

    def paste_text(self, term, text):
        if not text:
            return
        lines = len(text.splitlines())
        if self.settings["paste_warning"] and lines > 1 and not self.confirm_paste(lines):
            return
        term.paste_text(text)
        term.grab_focus()

    def build_paste_dialog(self, lines):
        dlg = Gtk.Dialog(title=self.tr("paste"), transient_for=self, modal=True)
        dlg.add_button(self.tr("cancel"), Gtk.ResponseType.CANCEL)
        dlg.add_button(self.tr("paste"), Gtk.ResponseType.OK)
        dlg.set_default_response(Gtk.ResponseType.CANCEL)  # Enter cancels: safe default
        dlg.get_content_area().pack_start(
            Gtk.Label(label=self.tr("paste_lines").format(n=lines), margin=24), True, True, 0)
        return dlg

    def confirm_paste(self, lines):
        dlg = self.build_paste_dialog(lines)
        dlg.show_all()
        ok = dlg.run() == Gtk.ResponseType.OK
        dlg.destroy()
        return ok

    # --- search ---
    def build_search_bar(self, page):
        bar = Gtk.Box(spacing=4, margin=4)
        entry = Gtk.SearchEntry(placeholder_text=self.tr("search_placeholder"))
        entry.connect("search-changed", lambda e: self.run_search(page, e.get_text()))
        entry.connect("activate", lambda _e: self.find(page, forward=True))
        entry.connect("stop-search", lambda _e: self.close_search(page))
        entry.connect("key-press-event", self.search_key, page)
        bar.pack_start(entry, True, True, 0)
        for icons, fallback, tip, handler in (
            (("go-up-symbolic",), "▲", "find_prev", lambda *_: self.find(page, forward=False)),
            (("go-down-symbolic",), "▼", "find_next", lambda *_: self.find(page, forward=True)),
            (("window-close-symbolic",), "x", "close", lambda *_: self.close_search(page)),
        ):
            button = self.icon_button(icons, fallback)
            button.set_tooltip_text(self.tr(tip))
            button.connect("clicked", handler)
            bar.pack_start(button, False, False, 0)
        page.search_bar, page.search_entry = bar, entry
        page.pack_end(bar, False, False, 0)
        bar.show_all()
        bar.set_no_show_all(True)  # window.show_all() must not reveal it
        bar.hide()

    def search_key(self, _entry, ev, page):
        shift_enter = (ev.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter)
                       and ev.state & Gdk.ModifierType.SHIFT_MASK)
        if shift_enter:
            self.find(page, forward=False)
            return True
        return False

    def search_term(self, page):
        term = page.last_term
        return term if term is not None and term.get_parent() is not None else first_terminal(page.root())

    def open_search(self, page):
        if page is None:
            return
        page.search_bar.show()
        page.search_entry.grab_focus()
        page.search_entry.select_region(0, -1)

    def close_search(self, page):
        term = self.search_term(page)
        if term is not None:
            term.search_set_regex(None, 0)
            term.grab_focus()
        page.search_bar.hide()

    def run_search(self, page, text):
        term = self.search_term(page)
        if term is None:
            return
        if not text:
            term.search_set_regex(None, 0)
            return
        # Literal text; case-insensitive unless the query contains an uppercase letter
        flags = PCRE2_MULTILINE | (0 if text != text.lower() else PCRE2_CASELESS)
        pattern = re.sub(r"([^\w\s])", r"\\\1", text)
        term.search_set_regex(Vte.Regex.new_for_search(pattern, -1, flags), 0)
        term.search_set_wrap_around(True)
        term.search_find_next()

    def find(self, page, forward):
        term = self.search_term(page)
        if term is not None:
            (term.search_find_next if forward else term.search_find_previous)()

    # --- buttons ---
    def send(self, btn):
        term = self.focused_terminal()
        if not term:
            return
        text = decode(btn["cmd"]) + ("\n" if btn.get("enter") else "")
        term.feed_child(text.encode("utf-8"))
        term.grab_focus()

    def rebuild_buttons(self):
        groups = ordered_groups((b.get("group") or DEFAULT_GROUP for b in self.buttons),
                                self.settings["group_order"])
        if self.group not in groups:
            self.group = groups[0] if groups else None

        # Rebuild the popover list; it scrolls when there are many groups
        old = self.group_popover.get_child()
        if old is not None:
            self.group_popover.remove(old)
        items = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin=6)
        for name in groups:
            item = Gtk.ModelButton(text=name, halign=Gtk.Align.FILL)
            item.connect("clicked", self.select_group, name)
            items.pack_start(item, False, False, 0)
        scroller = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER,
                                      propagate_natural_height=True,
                                      propagate_natural_width=True,
                                      max_content_height=360)
        scroller.add(items)
        scroller.show_all()
        self.group_popover.add(scroller)
        self.fill_buttons()

    def select_group(self, _item, name):
        self.group = name
        self.group_popover.popdown()
        self.fill_buttons()

    def fill_buttons(self, *_):
        for child in self.btnbox.get_children():
            self.btnbox.remove(child)
        group = self.group
        self.group_label.set_text(group or "")
        for b in self.buttons:
            if (b.get("group") or DEFAULT_GROUP) == group:
                self.btnbox.pack_start(self.make_button(b), False, False, 0)
        self.btnbox.show_all()

    def make_button(self, b):
        btn = Gtk.Button(relief=Gtk.ReliefStyle.NONE)
        btn.set_tooltip_text(b["cmd"] + ("  ⏎" if b.get("enter") else ""))
        box = Gtk.Box(spacing=6)
        if b.get("color"):
            dot = Gtk.DrawingArea(valign=Gtk.Align.CENTER)
            dot.set_size_request(14, 14)
            dot.connect("draw", self.draw_dot, b["color"])
            box.pack_start(dot, False, False, 0)
        box.pack_start(Gtk.Label(label=b["label"]), False, False, 0)
        btn.add(box)
        btn.connect("clicked", lambda _w: self.send(b))
        btn.connect("button-press-event", self.button_click, b)
        return btn

    def button_click(self, _btn, ev, b):
        """Right-click on a button: offer to edit it."""
        if ev.button != 3:
            return False
        menu = Gtk.Menu()
        item = Gtk.MenuItem(label=self.tr("edit_button"))
        item.connect("activate", lambda *_: self.edit_dialog(select=b))
        menu.append(item)
        menu.show_all()
        self.menu = menu
        menu.popup_at_pointer(ev)
        return True

    @staticmethod
    def draw_dot(widget, cr, color):
        c = rgba(color)
        w, h = widget.get_allocated_width(), widget.get_allocated_height()
        cr.set_source_rgba(c.red, c.green, c.blue, 1)
        cr.arc(w / 2, h / 2, min(w, h) / 2, 0, 2 * math.pi)
        cr.fill()
        return False

    # --- dialogs: button editor ---
    def pick_color(self, parent, current):
        dlg = Gtk.ColorChooserDialog(title=self.tr("pick_color"), transient_for=parent)
        dlg.set_use_alpha(False)
        if current:
            dlg.set_rgba(rgba(current))
        result = rgba_to_hex(dlg.get_rgba()) if dlg.run() == Gtk.ResponseType.OK else None
        dlg.destroy()
        return result

    def build_edit_dialog(self, select=None):
        dlg = Gtk.Dialog(title=self.tr("edit_buttons"), transient_for=self, modal=True)
        dlg.set_default_size(760, 440)
        dlg.add_buttons(self.tr("cancel"), Gtk.ResponseType.CANCEL,
                        self.tr("save"), Gtk.ResponseType.OK)
        # model columns: 0 label, 1 command, 2 enter, 3 group, 4 color (#rrggbb or "")
        store = Gtk.ListStore(str, str, bool, str, str)
        for b in self.buttons:
            store.append([b["label"], b["cmd"], bool(b.get("enter")),
                          b.get("group") or DEFAULT_GROUP, b.get("color") or ""])
        tv = Gtk.TreeView(model=store)
        if select in self.buttons:  # preselect the button that was right-clicked
            tv.set_cursor(Gtk.TreePath.new_from_indices([self.buttons.index(select)]))

        def text_column(title, col, expand=False):
            renderer = Gtk.CellRendererText(editable=True)
            renderer.connect("edited", lambda _r, path, text: store.set_value(
                store.get_iter(path), col, text))
            column = Gtk.TreeViewColumn(title, renderer, text=col)
            column.set_expand(expand)
            column.set_resizable(True)
            tv.append_column(column)

        text_column(self.tr("col_label"), 0)
        text_column(self.tr("col_command"), 1, expand=True)
        toggle = Gtk.CellRendererToggle()
        toggle.connect("toggled", lambda _r, path: store.set_value(
            store.get_iter(path), 2, not store[path][2]))
        tv.append_column(Gtk.TreeViewColumn(self.tr("col_enter"), toggle, active=2))

        # Color column: a colored dot; click it to open the color chooser
        dot = Gtk.CellRendererText(xalign=0.5)

        def color_data(_col, cell, model, it, _data):
            hex_color = model[it][4]
            cell.set_property("text", "●" if hex_color else "○")
            cell.set_property("foreground-rgba", rgba(hex_color or "#888888"))
        color_col = Gtk.TreeViewColumn(self.tr("col_color"), dot)
        color_col.set_cell_data_func(dot, color_data)
        tv.append_column(color_col)
        text_column(self.tr("col_group"), 3)

        def on_press(_tv, ev):
            hit = tv.get_path_at_pos(int(ev.x), int(ev.y))
            if ev.button == 1 and hit and hit[1] is color_col:
                tv.set_cursor(hit[0])
                chosen = self.pick_color(dlg, store[hit[0]][4])
                if chosen:
                    store[hit[0]][4] = chosen
                return True
            return False
        tv.connect("button-press-event", on_press)

        scroller = Gtk.ScrolledWindow()
        scroller.add(tv)
        area = dlg.get_content_area()
        area.set_spacing(6)
        area.pack_start(scroller, True, True, 0)

        def selected_row():
            return tv.get_selection().get_selected()[1]

        def clear_color(*_):
            it = selected_row()
            if it:
                store[it][4] = ""

        def add_row(*_):
            it = selected_row()
            group = store[it][3] if it else DEFAULT_GROUP
            store.append([self.tr("new_label"), "echo hello", True, group, ""])

        row = Gtk.Box(spacing=4)
        actions = (
            ("add", add_row),
            ("delete", lambda *_: self._delete_row(tv, store)),
            ("up", lambda *_: self._move_row(tv, store, -1)),
            ("down", lambda *_: self._move_row(tv, store, 1)),
            ("clear_color", clear_color),
        )
        for key, handler in actions:
            b = Gtk.Button(label=self.tr(key))
            b.connect("clicked", handler)
            row.pack_start(b, False, False, 0)
        order_btn = Gtk.Button(label=self.tr("group_order") + "…")
        order_btn.connect("clicked", lambda *_: self.order_dialog(dlg, store))
        row.pack_end(order_btn, False, False, 0)
        area.pack_start(row, False, False, 0)
        dlg.group_order = None  # set by the order dialog, applied on Save
        return dlg, store

    def order_dialog(self, parent, store):
        """Reorder the button groups with Up/Down; the result is kept on the editor dialog."""
        current = parent.group_order if parent.group_order is not None else self.settings["group_order"]
        groups = ordered_groups((r[3].strip() or DEFAULT_GROUP for r in store), current)
        dlg = Gtk.Dialog(title=self.tr("group_order"), transient_for=parent, modal=True)
        dlg.set_default_size(280, 320)
        dlg.add_buttons(self.tr("cancel"), Gtk.ResponseType.CANCEL, self.tr("save"), Gtk.ResponseType.OK)
        order = Gtk.ListStore(str)
        for g in groups:
            order.append([g])
        tv = Gtk.TreeView(model=order, headers_visible=False)
        tv.append_column(Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=0))
        tv.set_cursor(Gtk.TreePath.new_from_indices([0]))
        scroller = Gtk.ScrolledWindow()
        scroller.add(tv)
        area = dlg.get_content_area()
        area.set_spacing(6)
        area.pack_start(scroller, True, True, 0)

        def move(delta):
            it = tv.get_selection().get_selected()[1]
            if not it:
                return
            other = order.iter_previous(it) if delta < 0 else order.iter_next(it)
            if other:
                order.swap(it, other)
        row = Gtk.Box(spacing=4)
        for key, delta in (("up", -1), ("down", 1)):
            b = Gtk.Button(label=self.tr(key))
            b.connect("clicked", lambda _b, d=delta: move(d))
            row.pack_start(b, False, False, 0)
        area.pack_start(row, False, False, 0)
        dlg.show_all()
        if dlg.run() == Gtk.ResponseType.OK:
            parent.group_order = [r[0] for r in order]
        dlg.destroy()

    def edit_dialog(self, select=None):
        dlg, store = self.build_edit_dialog(select)
        dlg.show_all()
        if dlg.run() == Gtk.ResponseType.OK:
            self.buttons = [{"label": r[0], "cmd": r[1], "enter": r[2],
                             "group": r[3].strip() or DEFAULT_GROUP, "color": r[4]}
                            for r in store]
            write_json(BUTTONS_FILE, self.buttons)
            if dlg.group_order is not None:
                self.settings["group_order"] = dlg.group_order
                self.save_settings()
            self.rebuild_buttons()
        dlg.destroy()

    # --- dialogs: settings ---
    def build_settings_dialog(self, page=0):
        dlg = Gtk.Dialog(title=self.tr("settings"), transient_for=self, modal=True)
        dlg.add_button(self.tr("close"), Gtk.ResponseType.CLOSE)
        tabs = Gtk.Notebook()
        dlg.get_content_area().pack_start(tabs, True, True, 0)
        tabs.append_page(self.build_general_page(dlg), Gtk.Label(label=self.tr("tab_general")))
        tabs.append_page(self.build_shortcuts_page(dlg), Gtk.Label(label=self.tr("tab_shortcuts")))
        dlg.show_all()
        tabs.set_current_page(page)
        dlg.settings_tabs = tabs
        return dlg

    def build_general_page(self, dlg):
        grid = Gtk.Grid(row_spacing=10, column_spacing=12, margin=16)

        theme_combo = Gtk.ComboBoxText()
        for key in THEMES:
            theme_combo.append(key, self.tr("theme_" + key))
        theme_combo.set_active_id(self.settings["theme"])
        theme_combo.connect("changed", self.on_theme_changed)

        lang_combo = Gtk.ComboBoxText()
        for code, name in LANGS.items():
            lang_combo.append(code, name)
        lang_combo.set_active_id(self.settings["lang"])
        lang_combo.connect("changed", self.on_language_changed, dlg)

        rc_combo = Gtk.ComboBoxText()
        rc_combo.append("menu", self.tr("rc_menu"))
        rc_combo.append("putty", self.tr("rc_putty"))
        rc_combo.set_active_id(self.settings["rightclick_action"])
        rc_combo.connect("changed", lambda c: self.set_setting("rightclick_action", c.get_active_id()))

        rows = (("theme", theme_combo), ("language", lang_combo), ("rightclick_action", rc_combo))
        for i, (key, widget) in enumerate(rows):
            grid.attach(Gtk.Label(label=self.tr(key), xalign=0), 0, i, 1, 1)
            grid.attach(widget, 1, i, 1, 1)

        row = len(rows)
        for key in ("copy_on_select", "middle_paste", "paste_warning"):
            check = Gtk.CheckButton(label=self.tr(key))
            check.set_active(self.settings[key])
            check.connect("toggled", lambda c, k=key: self.set_setting(k, c.get_active()))
            grid.attach(check, 0, row, 2, 1)
            row += 1

        hover = Gtk.SpinButton.new_with_range(0, 30, 0.5)
        hover.set_value(self.settings["tab_hover_delay"])
        hover.connect("value-changed", lambda s: self.set_setting("tab_hover_delay", s.get_value()))
        grid.attach(Gtk.Label(label=self.tr("tab_hover_delay"), xalign=0), 0, row, 1, 1)
        grid.attach(hover, 1, row, 1, 1)
        row += 1

        edit = Gtk.Button(label=self.tr("edit_buttons") + "…")  # button colors live there
        edit.connect("clicked", lambda *_: self.edit_dialog())
        grid.attach(edit, 0, row, 2, 1)
        row += 1
        backup = Gtk.Box(spacing=6)
        for key, handler in (("export_settings", self.export_settings),
                             ("import_settings", self.import_settings)):
            b = Gtk.Button(label=self.tr(key))
            b.connect("clicked", lambda _b, h=handler: h(dlg))
            backup.pack_start(b, True, True, 0)
        grid.attach(backup, 0, row, 2, 1)
        return grid

    def json_chooser(self, parent, title, action):
        save = action == Gtk.FileChooserAction.SAVE
        chooser = Gtk.FileChooserDialog(title=title, transient_for=parent, action=action)
        chooser.add_buttons(self.tr("cancel"), Gtk.ResponseType.CANCEL,
                            self.tr("save") if save else Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        flt = Gtk.FileFilter()
        flt.set_name(self.tr("json_files"))
        flt.add_pattern("*.json")
        chooser.add_filter(flt)
        if save:
            chooser.set_current_name("terminal-buttons-settings.json")
            chooser.set_do_overwrite_confirmation(True)
        return chooser

    def export_settings(self, parent):
        """Write settings and all button bars into one JSON file."""
        chooser = self.json_chooser(parent, self.tr("export_settings"), Gtk.FileChooserAction.SAVE)
        if chooser.run() == Gtk.ResponseType.OK:
            write_json(chooser.get_filename(), {"settings": self.settings, "buttons": self.buttons})
        chooser.destroy()

    def import_settings(self, parent):
        chooser = self.json_chooser(parent, self.tr("import_settings"), Gtk.FileChooserAction.OPEN)
        path = chooser.get_filename() if chooser.run() == Gtk.ResponseType.OK else None
        chooser.destroy()
        if not path:
            return
        data = read_json(path, None)
        buttons = data.get("buttons") if isinstance(data, dict) else None
        if not isinstance(data, dict) or not isinstance(data.get("settings"), dict) or (
                buttons is not None and not (isinstance(buttons, list) and all(
                    isinstance(b, dict) and "label" in b and "cmd" in b for b in buttons))):
            err = Gtk.MessageDialog(transient_for=parent, modal=True, message_type=Gtk.MessageType.ERROR,
                                    buttons=Gtk.ButtonsType.CLOSE, text=self.tr("import_bad"))
            err.run()
            err.destroy()
            return
        self.settings = normalize_settings(data["settings"])
        self.save_settings()
        if buttons is not None:
            for b in buttons:
                b.setdefault("enter", False)
                b["group"] = b.get("group") or DEFAULT_GROUP
                b.setdefault("color", "")
            self.buttons = buttons
            write_json(BUTTONS_FILE, self.buttons)
        self.apply_language()
        self.apply_theme()
        self.rebuild_buttons()
        # Reopen the dialog so its widgets show the imported values
        parent.response(Gtk.ResponseType.CLOSE)
        GLib.idle_add(self.settings_dialog, 0)

    def build_shortcuts_page(self, dlg):
        grid = Gtk.Grid(row_spacing=8, column_spacing=12, margin=16)
        buttons = {}

        def refresh():
            for action, button in buttons.items():
                button.set_label(accel_label(self.settings["shortcuts"].get(action)) or "—")

        def change(action):
            accel = self.capture_shortcut(dlg, action)
            if accel is None:
                return
            for other, value in self.settings["shortcuts"].items():
                if accel and other != action and value == accel:
                    self.settings["shortcuts"][other] = ""  # one accelerator, one action
            self.settings["shortcuts"][action] = accel
            self.save_settings()
            self.apply_language()  # tooltips show the shortcuts
            refresh()

        def reset(*_):
            self.settings["shortcuts"] = dict(DEFAULT_SHORTCUTS)
            self.save_settings()
            self.apply_language()
            refresh()

        for i, action in enumerate(DEFAULT_SHORTCUTS):
            grid.attach(Gtk.Label(label=self.tr(action), xalign=0), 0, i, 1, 1)
            button = Gtk.Button()
            button.set_size_request(180, -1)
            button.connect("clicked", lambda _b, a=action: change(a))
            buttons[action] = button
            grid.attach(button, 1, i, 1, 1)
        reset_btn = Gtk.Button(label=self.tr("reset_shortcuts"))
        reset_btn.connect("clicked", reset)
        grid.attach(reset_btn, 0, len(DEFAULT_SHORTCUTS), 2, 1)
        refresh()
        return grid

    def capture_shortcut(self, parent, action):
        """Ask for a key combination. Returns an accelerator string, '' (clear) or None (cancel)."""
        dlg = Gtk.Dialog(title=self.tr(action), transient_for=parent, modal=True)
        dlg.add_button(self.tr("cancel"), Gtk.ResponseType.CANCEL)
        dlg.get_content_area().pack_start(
            Gtk.Label(label=self.tr("press_shortcut"), margin=24), True, True, 0)
        result = {}

        def on_key(_w, ev):
            keyval = Gdk.keyval_to_lower(ev.keyval)
            state = ev.state & Gtk.accelerator_get_default_mod_mask()
            if keyval == Gdk.KEY_ISO_Left_Tab:
                keyval = Gdk.KEY_Tab
            if keyval == Gdk.KEY_Escape:
                dlg.response(Gtk.ResponseType.CANCEL)
            elif keyval == Gdk.KEY_BackSpace and not state:
                result["accel"] = ""
                dlg.response(Gtk.ResponseType.OK)
            elif MODIFIER_KEY_NAME.match(Gdk.keyval_name(keyval) or ""):
                pass  # wait for the real key
            elif Gdk.KEY_F1 <= keyval <= Gdk.KEY_F12 or state & COMMAND_MODS:
                result["accel"] = Gtk.accelerator_name(keyval, state)
                dlg.response(Gtk.ResponseType.OK)
            return True  # a bare letter is not a valid shortcut; keep waiting
        dlg.connect("key-press-event", on_key)
        dlg.show_all()
        ok = dlg.run() == Gtk.ResponseType.OK
        dlg.destroy()
        return result.get("accel") if ok else None

    def settings_dialog(self, page=0):
        dlg = self.build_settings_dialog(page)
        dlg.run()
        dlg.destroy()

    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def on_theme_changed(self, combo):
        self.set_setting("theme", combo.get_active_id())
        self.apply_theme()

    def on_language_changed(self, combo, dlg):
        self.set_setting("lang", combo.get_active_id())
        self.apply_language()
        # Reopen the dialog so its own labels switch language too
        dlg.response(Gtk.ResponseType.CLOSE)
        GLib.idle_add(self.settings_dialog, dlg.settings_tabs.get_current_page())

    @staticmethod
    def _delete_row(tv, store):
        _, it = tv.get_selection().get_selected()
        if it:
            store.remove(it)

    @staticmethod
    def _move_row(tv, store, delta):
        _, it = tv.get_selection().get_selected()
        if not it:
            return
        i = store.get_path(it).get_indices()[0]
        j = i + delta
        if 0 <= j < len(store):
            store.swap(it, store.get_iter(j))


def main():
    GLib.set_prgname("terminal-buttons")  # matches the .desktop file (Wayland app id)
    GLib.set_application_name(APP_NAME)
    try:
        Gtk.Window.set_default_icon_from_file(ICON_FILE)
    except GLib.Error:
        pass
    if not os.path.exists(BUTTONS_FILE):
        write_json(BUTTONS_FILE, DEFAULT_BUTTONS)
    App().show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
