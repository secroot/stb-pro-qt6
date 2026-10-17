"""
Obsidian Cyber-Cinema Design System & Qt6 Stylesheet (QSS).
Provides color tokens, font families, and global dark stylesheet for PySide6.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication


class ThemeColors:
    """Design tokens matching and refining the Obsidian Cyber-Cinema palette."""
    BG_PRIMARY = "#070A10"       # Deepest space background
    BG_SECONDARY = "#0C111C"     # Sidebar & structural panels
    BG_CARD = "#121928"          # Elevated card surface
    BG_CARD_HOVER = "#192338"    # Card hover surface
    BG_CARD_SELECTED = "#1E2B48" # Active/selected card
    BG_INPUT = "#0A0E17"         # Input fields & code boxes

    ACCENT = "#4F46E5"           # Electric Indigo primary
    ACCENT_HOVER = "#6366F1"     # Bright Indigo hover
    ACCENT_GLOW = "#818CF8"      # Soft Indigo highlight

    CYAN = "#06B6D4"             # Cyber Cyan (telemetries, badges)
    CYAN_DIM = "#0E7490"

    SUCCESS = "#10B981"          # Emerald green (online, hot hit)
    SUCCESS_BG = "#064E3B"

    WARNING = "#F59E0B"          # Amber gold (favorites, warnings, buffering)
    WARNING_BG = "#78350F"

    DANGER = "#EF4444"           # Crimson red (REC, offline, errors)
    DANGER_BG = "#7F1D1D"

    PURPLE = "#8B5CF6"           # Royal Purple (4K/UHD badges, inspector)

    TEXT_PRIMARY = "#F8FAFC"     # Crisp white
    TEXT_SECONDARY = "#94A3B8"   # Muted slate
    TEXT_MUTED = "#64748B"       # Dim slate

    BORDER = "#1E293B"           # Subtle hairline border
    BORDER_FOCUS = "#4F46E5"     # Focused input border


GLOBAL_QSS = f"""
/* Global Window & Widget Defaults */
QMainWindow, QDialog {{
    background-color: {ThemeColors.BG_PRIMARY};
    color: {ThemeColors.TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}}

QWidget {{
    color: {ThemeColors.TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", sans-serif;
    selection-background-color: {ThemeColors.ACCENT};
    selection-color: #FFFFFF;
}}

/* Frames & Cards */
QFrame#TopBar {{
    background-color: {ThemeColors.BG_SECONDARY};
    border-bottom: 1px solid {ThemeColors.BORDER};
}}

QFrame#Sidebar {{
    background-color: {ThemeColors.BG_SECONDARY};
    border-right: 1px solid {ThemeColors.BORDER};
}}

QFrame#CardFrame {{
    background-color: {ThemeColors.BG_CARD};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 10px;
}}

QFrame#HeroCard {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #111827, stop:0.6 #151E32, stop:1 #1A233A);
    border: 1px solid #263554;
    border-radius: 10px;
}}

QFrame#SubtlePanel {{
    background-color: {ThemeColors.BG_SECONDARY};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 8px;
}}

/* Buttons */
QPushButton {{
    background-color: {ThemeColors.BG_CARD};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 600;
}}

QPushButton#IconButton, QPushButton[compact="true"] {{
    padding: 2px 4px;
    min-width: 24px;
}}

QPushButton#SidebarToggle {{
    background-color: #0F172A;
    color: #CBD5E1;
    border: 1px solid #1E293B;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
}}

QPushButton#SidebarToggle:hover {{
    background-color: #1E293B;
    color: #F8FAFC;
    border-color: #818CF8;
}}

QPushButton#SidebarToggle:pressed {{
    background-color: #4F46E5;
    color: #FFFFFF;
}}

QPushButton#SidebarToggle[active="true"] {{
    background-color: #1E1B4B;
    color: #A5B4FC;
    border-color: #6366F1;
}}

QPushButton:hover {{
    background-color: {ThemeColors.BG_CARD_HOVER};
    border-color: #334155;
}}

QPushButton:pressed {{
    background-color: {ThemeColors.ACCENT};
    border-color: {ThemeColors.ACCENT_GLOW};
}}

QPushButton:disabled {{
    background-color: #0B0F17;
    color: #475569;
    border-color: #161F30;
}}

QPushButton#PrimaryButton {{
    background-color: {ThemeColors.ACCENT};
    color: #FFFFFF;
    border: 1px solid {ThemeColors.ACCENT_HOVER};
}}

QPushButton#PrimaryButton:hover {{
    background-color: {ThemeColors.ACCENT_HOVER};
    border-color: {ThemeColors.ACCENT_GLOW};
}}

QPushButton#SuccessButton {{
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid {ThemeColors.SUCCESS};
}}

QPushButton#SuccessButton:hover {{
    background-color: {ThemeColors.SUCCESS};
}}

QPushButton#DangerButton {{
    background-color: #B91C1C;
    color: #FFFFFF;
    border: 1px solid {ThemeColors.DANGER};
}}

QPushButton#DangerButton:hover {{
    background-color: {ThemeColors.DANGER};
}}

QPushButton#WarningButton {{
    background-color: #B45309;
    color: #FFFFFF;
    border: 1px solid {ThemeColors.WARNING};
}}

QPushButton#WarningButton:hover {{
    background-color: {ThemeColors.WARNING};
}}

QPushButton#NavPill {{
    background-color: transparent;
    color: {ThemeColors.TEXT_SECONDARY};
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 5px 11px;
    font-weight: 600;
}}

QPushButton#NavPill:hover {{
    background-color: {ThemeColors.BG_CARD};
    color: {ThemeColors.TEXT_PRIMARY};
}}

QPushButton#NavPill[active="true"] {{
    background-color: {ThemeColors.ACCENT};
    color: #FFFFFF;
    border: 1px solid {ThemeColors.ACCENT_GLOW};
}}

QPushButton#FilterPill {{
    background-color: {ThemeColors.BG_INPUT};
    color: {ThemeColors.TEXT_SECONDARY};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    font-weight: 600;
}}

QPushButton#FilterPill:hover {{
    background-color: {ThemeColors.BG_CARD_HOVER};
    color: {ThemeColors.TEXT_PRIMARY};
}}

QPushButton#FilterPill:checked {{
    background-color: {ThemeColors.ACCENT};
    color: #FFFFFF;
    border-color: {ThemeColors.ACCENT_GLOW};
}}

/* Inputs */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {ThemeColors.BG_INPUT};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 6px;
    padding: 4px 8px;
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus {{
    border: 1px solid {ThemeColors.ACCENT_HOVER};
    background-color: #0D1320;
}}

QComboBox {{
    background-color: {ThemeColors.BG_INPUT};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 20px;
}}

QComboBox:hover {{
    border-color: #334155;
}}

QComboBox:focus {{
    border-color: {ThemeColors.ACCENT_HOVER};
}}

QComboBox::drop-down {{
    border: none;
    width: 18px;
}}

QComboBox QAbstractItemView {{
    background-color: {ThemeColors.BG_CARD};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER_FOCUS};
    selection-background-color: {ThemeColors.ACCENT};
    selection-color: #FFFFFF;
    outline: 0;
}}

/* Lists, Tables, Trees */
QListView, QTableView, QTreeView, QTreeWidget, QTableWidget {{
    background-color: {ThemeColors.BG_SECONDARY};
    alternate-background-color: #0E1525;
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 8px;
    gridline-color: #162033;
    outline: 0;
}}

QHeaderView::section {{
    background-color: #101726;
    color: {ThemeColors.TEXT_SECONDARY};
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {ThemeColors.BORDER};
    border-right: 1px solid #162033;
}}

QTableView::item, QTreeView::item {{
    padding: 4px 6px;
}}

QTableView::item:selected, QTreeView::item:selected {{
    background-color: {ThemeColors.BG_CARD_SELECTED};
    color: #FFFFFF;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background: #26334D;
    min-height: 28px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {ThemeColors.ACCENT_HOVER};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background: #26334D;
    min-width: 28px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {ThemeColors.ACCENT_HOVER};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Sliders & Progress Bars */
QSlider::groove:horizontal {{
    height: 5px;
    background: #1E293B;
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {ThemeColors.ACCENT_HOVER};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: #F8FAFC;
    border: 2px solid {ThemeColors.ACCENT};
    width: 13px;
    height: 13px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {ThemeColors.CYAN};
    border-color: #FFFFFF;
}}

QProgressBar {{
    background-color: #162033;
    border: 1px solid {ThemeColors.BORDER};
    border-radius: 4px;
    text-align: center;
    color: {ThemeColors.TEXT_PRIMARY};
    font-size: 10px;
    font-weight: 700;
}}

QProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ThemeColors.ACCENT}, stop:1 {ThemeColors.CYAN});
    border-radius: 3px;
}}

QProgressBar#ValidationProgressBar {{
    background-color: #0F172A;
    border: 1px solid #1E293B;
    border-radius: 5px;
    text-align: center;
    color: #F8FAFC;
    font-size: 10px;
    font-weight: 700;
    min-height: 18px;
    max-height: 18px;
}}

QProgressBar#ValidationProgressBar::chunk {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4F46E5, stop:0.5 #06B6D4, stop:1 #10B981);
    border-radius: 4px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {ThemeColors.BORDER};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QSplitter::handle:hover {{
    background-color: {ThemeColors.ACCENT_HOVER};
}}

/* TabWidget */
QTabWidget::pane {{
    border: 1px solid {ThemeColors.BORDER};
    background-color: {ThemeColors.BG_SECONDARY};
    border-radius: 6px;
}}

QTabBar::tab {{
    background-color: {ThemeColors.BG_INPUT};
    color: {ThemeColors.TEXT_SECONDARY};
    border: 1px solid {ThemeColors.BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 6px 14px;
    margin-right: 3px;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background-color: {ThemeColors.ACCENT};
    color: #FFFFFF;
    border-color: {ThemeColors.ACCENT_GLOW};
}}

QTabBar::tab:hover:!selected {{
    background-color: {ThemeColors.BG_CARD_HOVER};
    color: {ThemeColors.TEXT_PRIMARY};
}}

/* CheckBox */
QCheckBox {{
    spacing: 6px;
    color: {ThemeColors.TEXT_SECONDARY};
    font-weight: 600;
}}

QCheckBox:hover {{
    color: {ThemeColors.TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #334155;
    background-color: {ThemeColors.BG_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {ThemeColors.ACCENT};
    border-color: {ThemeColors.ACCENT_GLOW};
}}

/* ToolTip */
QToolTip {{
    background-color: {ThemeColors.BG_CARD};
    color: {ThemeColors.TEXT_PRIMARY};
    border: 1px solid {ThemeColors.ACCENT_HOVER};
    padding: 5px 8px;
    border-radius: 4px;
}}
"""


def apply_obsidian_theme(app: QApplication, scale_factor: float = 1.0):
    """Apply dark QPalette and Obsidian Cyber-Cinema QSS stylesheet with dynamic UI scaling."""
    from PySide6.QtGui import QFont

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(ThemeColors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(ThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(ThemeColors.BG_INPUT))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(ThemeColors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(ThemeColors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(ThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(ThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(ThemeColors.BG_CARD))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(ThemeColors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ThemeColors.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    sf = max(0.85, min(1.35, float(scale_factor)))
    base_px = max(11, min(18, int(round(13 * sf))))
    med_px = max(10, min(16, int(round(12 * sf))))
    sm_px = max(9, min(15, int(round(11 * sf))))

    font = QFont("Segoe UI")
    font.setPixelSize(base_px)
    app.setFont(font)

    qss = (
        GLOBAL_QSS.replace("font-size: 13px;", f"font-size: {base_px}px;")
        .replace("font-size: 12px;", f"font-size: {med_px}px;")
        .replace("font-size: 11px;", f"font-size: {sm_px}px;")
    )
    app.setStyleSheet(qss)
