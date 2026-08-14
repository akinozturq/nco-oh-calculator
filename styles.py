import os
import json
from typing import Dict, Any

USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".nco_oh_calculator")
SETTINGS_FILE = os.path.join(USER_DATA_DIR, "settings.json")

# ─── Laboratory Design Tokens ──────────────────────────────────────────

DARK_THEME: Dict[str, str] = {
    "name": "dark",
    "bg_primary":     "#0B1120",  # Dark laboratory slate
    "bg_secondary":   "#162238",  # Lab panel container
    "bg_card":        "#162238",  # Card surface
    "bg_input":       "#0F172A",  # Deep input background
    "bg_dialog":      "#0B1120",  # Dialog background
    "border":         "#263852",  # Crisp lab container border
    "border_focus":   "#06B6D4",  # Neon lab cyan focus
    "text_primary":   "#F8FAFC",  # High contrast crisp white
    "text_secondary": "#94A3B8",  # Subtitle slate
    "text_muted":     "#64748B",  # Muted label slate
    "accent_blue":    "#2563EB",  # Primary R&D blue
    "accent_blue_h":  "#1D4ED8",  # Hover R&D blue
    "accent_cyan":    "#06B6D4",  # Chemical reactivity cyan
    "accent_cyan_h":  "#0891B2",
    "accent_green":   "#10B981",  # Stoichiometric ratio emerald
    "accent_green_h": "#059669",
    "accent_orange":  "#F97316",  # Isocyanate warning coral
    "accent_orange_h":"#EA580C",
    "accent_purple":  "#8B5CF6",  # Database portal purple
    "accent_purple_h": "#7C3AED",
    "danger":         "#EF4444",  # Error / Delete red
    "danger_bg":      "#450A0A",
    "cell_error":     "#7F1D1D",  # Table cell invalid entry highlight
    "badge_lab_bg":   "#0E3A47",  # Lab R&D badge fill
    "badge_lab_border":"#155E75",
    "badge_lab_fg":   "#22D3EE",  # Lab R&D badge text
}

LIGHT_THEME: Dict[str, str] = {
    "name": "light",
    "bg_primary":     "#F1F5F9",  # Clean clinical lab slate
    "bg_secondary":   "#FFFFFF",  # Pure white card container
    "bg_card":        "#FFFFFF",  # Card surface
    "bg_input":       "#F8FAFC",  # Subtle light input background
    "bg_dialog":      "#FFFFFF",  # Dialog white background
    "border":         "#CBD5E1",  # Crisp light gray border
    "border_focus":   "#0284C7",  # Royal cyan focus
    "text_primary":   "#0F172A",  # Deep slate text
    "text_secondary": "#475569",  # Slate subtitle
    "text_muted":     "#64748B",  # Muted label slate
    "accent_blue":    "#1D4ED8",  # Primary R&D blue
    "accent_blue_h":  "#1E40AF",  # Hover R&D blue
    "accent_cyan":    "#0284C7",  # Chemical reactivity cyan
    "accent_cyan_h":  "#0369A1",
    "accent_green":   "#059669",  # Stoichiometric ratio emerald
    "accent_green_h": "#047857",
    "accent_orange":  "#D97706",  # Isocyanate warning amber
    "accent_orange_h":"#B45309",
    "accent_purple":  "#6D28D9",  # Database portal purple
    "accent_purple_h": "#5B21B6",
    "danger":         "#DC2626",  # Error / Delete red
    "danger_bg":      "#FEE2E2",
    "cell_error":     "#FCA5A5",  # Table cell invalid entry highlight
    "badge_lab_bg":   "#E0F2FE",  # Lab R&D badge fill
    "badge_lab_border":"#BAE6FD",
    "badge_lab_fg":   "#0369A1",  # Lab R&D badge text
}

FONT_FAMILY = "Segoe UI"


class ThemeManager:
    """Laboratuvar Tasarım ve Tema Yöneticisi (Dark / Light Mode)."""
    
    _instance = None

    def __init__(self):
        self.current_mode = self.load_theme_preference()

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_theme_preference(self) -> str:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("theme", "dark")
            except Exception:
                pass
        return "dark"

    def save_theme_preference(self, mode: str):
        try:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"theme": mode}, f, indent=2)
        except Exception:
            pass

    def get_colors(self) -> Dict[str, str]:
        return DARK_THEME if self.current_mode == "dark" else LIGHT_THEME

    def is_dark(self) -> bool:
        return self.current_mode == "dark"

    def toggle_theme(self) -> str:
        self.current_mode = "light" if self.current_mode == "dark" else "dark"
        self.save_theme_preference(self.current_mode)
        return self.current_mode


def get_global_stylesheet(colors: Dict[str, str] = None) -> str:
    """Genel Laboratuvar QSS Teması."""
    if colors is None:
        colors = ThemeManager.instance().get_colors()

    return f"""
        QMainWindow, QDialog, QMessageBox, QInputDialog {{
            background-color: {colors['bg_primary']};
            color: {colors['text_primary']};
        }}
        QWidget {{
            font-family: '{FONT_FAMILY}', system-ui, -apple-system, sans-serif;
            font-size: 12px;
            color: {colors['text_primary']};
        }}
        QGroupBox {{
            background-color: {colors['bg_card']};
            border: 1px solid {colors['border']};
            border-radius: 8px;
            margin-top: 14px;
            padding: 16px;
            font-size: 14px;
            font-weight: 600;
            color: {colors['text_primary']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 12px;
            background-color: {colors['bg_card']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            color: {colors['accent_cyan']};
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        QTableWidget {{
            background-color: {colors['bg_secondary']};
            alternate-background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            gridline-color: {colors['border']};
            color: {colors['text_primary']};
            selection-background-color: {colors['accent_cyan']};
            selection-color: #FFFFFF;
            font-size: 11px;
        }}
        QTableWidget::item {{
            padding: 6px 8px;
            border-bottom: 1px solid {colors['border']};
            color: {colors['text_primary']};
        }}
        QTableWidget::item:selected {{
            background-color: {colors['accent_cyan_h']};
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            background-color: {colors['bg_input']};
            color: {colors['text_secondary']};
            border: none;
            border-bottom: 2px solid {colors['accent_cyan']};
            padding: 6px 8px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
        }}
        QPushButton {{
            border: none;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: 600;
            font-size: 12px;
            color: #FFFFFF;
            background-color: {colors['accent_blue']};
        }}
        QPushButton:hover {{
            background-color: {colors['accent_blue_h']};
        }}
        QDoubleSpinBox, QSpinBox, QLineEdit {{
            background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {colors['text_primary']};
            font-size: 12px;
            font-weight: 500;
            min-height: 28px;
            selection-background-color: {colors['accent_cyan']};
            selection-color: #FFFFFF;
        }}
        QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus {{
            border-color: {colors['border_focus']};
        }}
        QComboBox {{
            background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 6px 10px;
            color: {colors['text_primary']};
            font-size: 12px;
            min-height: 28px;
        }}
        QComboBox:hover {{
            border-color: {colors['border_focus']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            color: {colors['text_primary']};
            selection-background-color: {colors['accent_cyan']};
            selection-color: #FFFFFF;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 28px;
            padding: 4px 8px;
            color: {colors['text_primary']};
            background-color: {colors['bg_secondary']};
        }}
        QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {{
            background-color: {colors['accent_cyan']};
            color: #FFFFFF;
        }}
        QMenu {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            color: {colors['text_primary']};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 20px;
            color: {colors['text_primary']};
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {colors['accent_cyan']};
            color: #FFFFFF;
        }}
        QToolTip {{
            background-color: {colors['bg_secondary']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            padding: 4px 8px;
            border-radius: 4px;
        }}
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
            border-radius: 6px;
            background-color: {colors['bg_card']};
        }}
        QTabBar::tab {{
            background-color: {colors['bg_input']};
            color: {colors['text_secondary']};
            border: 1px solid {colors['border']};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 6px 14px;
            font-weight: 600;
            font-size: 11px;
        }}
        QTabBar::tab:selected {{
            background-color: {colors['accent_cyan']};
            color: #FFFFFF;
        }}
        QListWidget {{
            background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            color: {colors['text_primary']};
            padding: 6px;
        }}
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors['border']};
            border-radius: 4px;
            color: {colors['text_primary']};
            background-color: {colors['bg_input']};
        }}
        QListWidget::item:selected {{
            background-color: {colors['accent_cyan']};
            color: #FFFFFF;
        }}
        QLabel {{
            color: {colors['text_primary']};
            font-size: 12px;
        }}
        QFormLayout QLabel {{
            color: {colors['text_secondary']};
            font-size: 11px;
            font-weight: 500;
        }}
    """


def get_dialog_stylesheet(colors: Dict[str, str] = None) -> str:
    """Diyalog pencereleri için özel laboratuvar QSS teması."""
    if colors is None:
        colors = ThemeManager.instance().get_colors()

    return f"""
        QDialog {{
            background-color: {colors['bg_dialog']};
            color: {colors['text_primary']};
        }}
        QLabel {{
            color: {colors['text_primary']};
            font-size: 12px;
        }}
        QFormLayout QLabel {{
            color: {colors['text_secondary']};
            font-size: 11px;
            font-weight: 500;
        }}
        QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
            background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            padding: 6px;
            color: {colors['text_primary']};
            font-size: 12px;
        }}
        QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
            border-color: {colors['border_focus']};
        }}
        QComboBox QAbstractItemView {{
            background-color: {colors['bg_secondary']};
            border: 1px solid {colors['border']};
            color: {colors['text_primary']};
            selection-background-color: {colors['accent_cyan']};
            selection-color: #FFFFFF;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 28px;
            padding: 4px 8px;
            color: {colors['text_primary']};
            background-color: {colors['bg_secondary']};
        }}
        QListWidget {{
            background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            color: {colors['text_primary']};
            padding: 6px;
        }}
        QListWidget::item {{
            padding: 8px;
            border-bottom: 1px solid {colors['border']};
            border-radius: 4px;
            color: {colors['text_primary']};
            background-color: {colors['bg_input']};
        }}
        QListWidget::item:selected {{
            background-color: {colors['accent_cyan']};
            color: #FFFFFF;
        }}
        QGroupBox {{
            background-color: {colors['bg_card']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            margin-top: 10px;
            color: {colors['text_primary']};
            font-weight: bold;
            padding: 15px;
        }}
        QTableWidget {{
            background-color: {colors['bg_secondary']};
            alternate-background-color: {colors['bg_input']};
            border: 1px solid {colors['border']};
            border-radius: 6px;
            color: {colors['text_primary']};
            gridline-color: {colors['border']};
        }}
        QHeaderView::section {{
            background-color: {colors['bg_input']};
            color: {colors['accent_cyan']};
            padding: 6px;
            font-weight: bold;
            border: 1px solid {colors['border']};
        }}
        QPushButton {{
            background-color: {colors['accent_blue']};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            color: white;
        }}
        QPushButton:hover {{
            background-color: {colors['accent_blue_h']};
        }}
    """
