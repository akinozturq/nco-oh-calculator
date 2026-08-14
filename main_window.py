import os
import webbrowser
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QDoubleSpinBox, QLabel, QGroupBox,
    QHeaderView, QFormLayout, QFrame, QAbstractItemView, QFileDialog,
    QMessageBox, QInputDialog, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon

from chemistry import PolyolItem, IsocyanateItem, ChemistryEngine
from library import LibraryManager, RawMaterial
from exporter import RecipeExporter
from dialogs import LibrarySelectorDialog, AddCustomMaterialDialog, DatabaseManagerDialog
from styles import ThemeManager, get_global_stylesheet, get_dialog_stylesheet


class _SeparatorLine(QFrame):
    """Laboratuvar ayırıcı çizgi."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.update_theme()

    def update_theme(self):
        colors = ThemeManager.instance().get_colors()
        self.setStyleSheet(f"color: {colors['border']}; max-height: 1px;")


class _ResultCard(QFrame):
    """Laboratuvar metrik sonuç kartı (Metrik + Değer)."""
    def __init__(self, label: str, value: str = "—", accent_key: str = "text_primary", parent=None):
        super().__init__(parent)
        self.accent_key = accent_key

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        self._lbl_label = QLabel(label)
        self._lbl_value = QLabel(value)

        layout.addWidget(self._lbl_label)
        layout.addWidget(self._lbl_value)
        self.update_theme()

    def update_theme(self):
        colors = ThemeManager.instance().get_colors()
        accent_color = colors.get(self.accent_key, colors["text_primary"])

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg_primary']};
                border: 1px solid {colors['border']};
                border-radius: 8px;
            }}
        """)
        self._lbl_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_muted']};
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.8px;
                border: none;
                background: transparent;
            }}
        """)
        self._lbl_value.setStyleSheet(f"""
            QLabel {{
                color: {accent_color};
                font-size: 18px;
                font-weight: 800;
                border: none;
                background: transparent;
            }}
        """)

    def set_value(self, text: str):
        self._lbl_value.setText(text)


class _ResultRow(QFrame):
    """İkincil veri satırı (Metrik : Değer)."""
    def __init__(self, label: str, value: str = "—", accent_key: str = "text_primary", parent=None):
        super().__init__(parent)
        self.accent_key = accent_key

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(8)

        self._lbl_label = QLabel(label)
        self._lbl_value = QLabel(value)
        self._lbl_value.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(self._lbl_label, 1)
        layout.addWidget(self._lbl_value, 0)
        self.update_theme()

    def update_theme(self):
        colors = ThemeManager.instance().get_colors()
        accent_color = colors.get(self.accent_key, colors["text_primary"])

        self.setStyleSheet("QFrame { background: transparent; border: none; }")
        self._lbl_label.setStyleSheet(f"""
            QLabel {{ color: {colors['text_secondary']}; font-size: 11px; font-weight: 500; }}
        """)
        self._lbl_value.setStyleSheet(f"""
            QLabel {{ color: {accent_color}; font-size: 11px; font-weight: 700; }}
        """)

    def set_value(self, text: str):
        self._lbl_value.setText(text)


class MainWindow(QMainWindow):
    """Modern Laboratuvar Tasarımlı NCO / OH Calculator (Dark / Light Mode Destekli)."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NCO / OH Calculator  —  Poliüretan Stokiyometri & Laboratuvar Portalı")
        self.setMinimumSize(1240, 800)
        self.resize(1300, 840)

        self.library_mgr = LibraryManager()
        self.current_recipe_name = "Yeni Reçete"
        self.current_result = None
        self.current_polyols = []
        self.current_isocyanates = []

        self._build_ui()
        self._apply_theme()
        self._add_default_polyols()
        self._add_default_isocyanates()
        self._recalculate()

    # ─── UI Construction ────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(20, 14, 20, 16)
        root_layout.setSpacing(0)

        # ── Top Header & Action Bar ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        # Lab Badge & Title Group
        title_group = QVBoxLayout()
        title_group.setSpacing(2)

        header_title_box = QHBoxLayout()
        header_title_box.setSpacing(10)

        self.lbl_title = QLabel("NCO / OH Calculator")
        self.lbl_title.setStyleSheet("font-size: 22px; font-weight: 800; letter-spacing: -0.5px;")

        self.lbl_badge = QLabel("🔬 R&D LAB PORTAL")
        header_title_box.addWidget(self.lbl_title)
        header_title_box.addWidget(self.lbl_badge)
        header_title_box.addStretch()

        self.lbl_subtitle = QLabel("Poliüretan Stokiyometri & Reçete Portalı")
        self.lbl_subtitle.setStyleSheet("font-size: 11px; font-weight: 500;")

        title_group.addLayout(header_title_box)
        title_group.addWidget(self.lbl_subtitle)

        top_bar.addLayout(title_group)
        top_bar.addStretch()

        # Modern Action Buttons
        self.btn_theme_toggle = QPushButton()
        self.btn_theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme_toggle.clicked.connect(self._toggle_theme)

        self.btn_db_mgr = QPushButton("🗄️ Veritabanı Portal")
        self.btn_db_mgr.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_db_mgr.clicked.connect(self._open_database_manager)

        self.btn_load = QPushButton("📂 Reçete Yükle")
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.clicked.connect(self._on_load_recipe_clicked)

        self.btn_save = QPushButton("💾 Reçete Kaydet")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self._on_save_recipe_clicked)

        self.btn_excel = QPushButton("📊 Excel CSV")
        self.btn_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_excel.clicked.connect(self._on_export_csv_clicked)

        self.btn_report = QPushButton("🌐 HTML Rapor")
        self.btn_report.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_report.clicked.connect(self._on_export_html_clicked)

        top_bar.addWidget(self.btn_theme_toggle)
        top_bar.addWidget(self.btn_db_mgr)
        top_bar.addWidget(self.btn_load)
        top_bar.addWidget(self.btn_save)
        top_bar.addWidget(self.btn_excel)
        top_bar.addWidget(self.btn_report)

        root_layout.addLayout(top_bar)
        root_layout.addSpacing(12)

        # ── Body (Two-Column) ──
        body = QHBoxLayout()
        body.setSpacing(16)

        # ▸ LEFT: Polyol Table (Part A)
        left = QVBoxLayout()
        left.setSpacing(10)

        self.table_group = QGroupBox("A Komponenti  ·  Polyol / Reçine Blend")
        tg_layout = QVBoxLayout(self.table_group)
        tg_layout.setContentsMargins(12, 18, 12, 12)
        tg_layout.setSpacing(8)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "HAMMADDE ADI", "MİKTAR (g)", "OH DEĞERİ (mg KOH/g)", "KATI MADDE (%)", ""
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.resizeSection(1, 105)
        h.resizeSection(2, 155)
        h.resizeSection(3, 115)
        h.resizeSection(4, 42)

        self.table.itemChanged.connect(self._on_polyol_cell_changed)
        tg_layout.addWidget(self.table)

        # Polyol action buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        self.btn_lib_polyol = QPushButton("📚 Veritabanından Yükle")
        self.btn_lib_polyol.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lib_polyol.clicked.connect(self._on_select_polyol_from_library)

        btn_bar.addWidget(self.btn_lib_polyol)
        tg_layout.addLayout(btn_bar)

        left.addWidget(self.table_group)

        # ▸ RIGHT: Part B Hardener (Single or Blend) + Results
        right = QVBoxLayout()
        right.setSpacing(10)

        # ── B Komponenti Group Box ──
        self.iso_group = QGroupBox("B Komponenti  ·  İzosiyanat / Sertleştirici")
        iso_layout = QVBoxLayout(self.iso_group)
        iso_layout.setContentsMargins(12, 16, 12, 12)
        iso_layout.setSpacing(8)

        # Tab widget for Part B: Blend Mode vs Single Mode
        self.iso_tabs = QTabWidget()
        self.iso_tabs.currentChanged.connect(self._on_iso_tab_changed)

        # ── TAB 1: Sertleştirici Reçetesi (Blend Tablosu) ──
        tab_blend = QWidget()
        blend_layout = QVBoxLayout(tab_blend)
        blend_layout.setContentsMargins(8, 8, 8, 8)
        blend_layout.setSpacing(6)

        self.iso_table = QTableWidget()
        self.iso_table.setColumnCount(5)
        self.iso_table.setHorizontalHeaderLabels([
            "HAMMADDE / SOLVENT ADI", "MİKTAR (g/%)", "NCO (%)", "KATI MADDE (%)", ""
        ])
        self.iso_table.setAlternatingRowColors(True)
        self.iso_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.iso_table.verticalHeader().setVisible(False)
        self.iso_table.setShowGrid(False)

        h2 = self.iso_table.horizontalHeader()
        h2.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h2.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h2.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h2.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h2.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h2.resizeSection(1, 95)
        h2.resizeSection(2, 85)
        h2.resizeSection(3, 105)
        h2.resizeSection(4, 40)

        self.iso_table.itemChanged.connect(self._on_iso_cell_changed)
        blend_layout.addWidget(self.iso_table)

        # Status badge for Part B Blend
        self.lbl_iso_blend_status = QLabel("Harman Net Serbest NCO: %0.00  |  Net Katı Madde: %0.00")
        blend_layout.addWidget(self.lbl_iso_blend_status)

        # Blend buttons
        iso_btn_bar = QHBoxLayout()
        iso_btn_bar.setSpacing(6)

        self.btn_lib_iso_row = QPushButton("📚 Veritabanından Yükle")
        self.btn_lib_iso_row.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_lib_iso_row.clicked.connect(self._on_select_iso_from_library)

        iso_btn_bar.addWidget(self.btn_lib_iso_row)
        blend_layout.addLayout(iso_btn_bar)

        self.iso_tabs.addTab(tab_blend, "📋 Sertleştirici Reçetesi (Blend)")

        # ── TAB 2: Tekli / Manuel İzosiyanat ──
        tab_single = QWidget()
        single_layout = QVBoxLayout(tab_single)
        single_layout.setContentsMargins(12, 12, 12, 12)

        iso_form = QFormLayout()
        iso_form.setSpacing(8)
        iso_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.spin_nco = self._make_spin(0.1, 100.0, 31.5, " %", 2)
        self.spin_iso_solid = self._make_spin(1.0, 100.0, 100.0, " %", 1)

        iso_form.addRow("Serbest NCO (%):", self.spin_nco)
        iso_form.addRow("Katı Madde (%):", self.spin_iso_solid)
        single_layout.addLayout(iso_form)

        self.lbl_selected_iso = QLabel("Seçilen Sertleştirici: Özel (Manuel Giriş)")
        single_layout.addWidget(self.lbl_selected_iso)
        single_layout.addStretch()

        self.iso_tabs.addTab(tab_single, "⚙️ Tekli / Manuel İzosiyanat")

        iso_layout.addWidget(self.iso_tabs)

        # Index control (Common to both modes)
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("NCO / OH İndeksi:"))
        self.spin_index = self._make_spin(0.5, 5.0, 1.05, "", 2, step=0.01)
        index_layout.addWidget(self.spin_index)
        iso_layout.addLayout(index_layout)

        right.addWidget(self.iso_group)

        # ── Sonuçlar Group Box ──
        self.res_group = QGroupBox("Hesaplama Sonuçları")
        res_layout = QVBoxLayout(self.res_group)
        res_layout.setContentsMargins(12, 18, 12, 12)
        res_layout.setSpacing(6)

        # Primary cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(10)
        self.card_iso = _ResultCard("GEREKLİ SERTLEŞTİRİCİ (B)", "0.00 g", "accent_orange")
        self.card_ratio = _ResultCard("KARIŞIM ORANI (A : B)", "100 : 0.00", "accent_green")
        cards_row.addWidget(self.card_iso)
        cards_row.addWidget(self.card_ratio)
        res_layout.addLayout(cards_row)

        self.sep_line = _SeparatorLine()
        res_layout.addWidget(self.sep_line)

        # Secondary rows
        self.row_polyol_mass = _ResultRow("Toplam Polyol Kütlesi", "0.00 g")
        self.row_blend_oh    = _ResultRow("Blend OH Değeri", "0.00 mg KOH/g", "accent_cyan")
        self.row_eq_oh       = _ResultRow("Toplam Eq OH", "0.000000")
        self.row_eq_nco      = _ResultRow("Gereken Eq NCO", "0.000000")
        self.row_iso_nco     = _ResultRow("Kullanılan Net NCO", "% 0.00", "accent_purple")
        self.row_total_mass  = _ResultRow("Toplam Karışım Kütlesi", "0.00 g")
        self.row_solid       = _ResultRow("Nihai Katı Madde Oranı", "% 0.00")

        for w in [self.row_polyol_mass, self.row_blend_oh,
                  self.row_eq_oh, self.row_eq_nco, self.row_iso_nco,
                  self.row_total_mass, self.row_solid]:
            res_layout.addWidget(w)

        right.addWidget(self.res_group)
        right.addStretch()

        body.addLayout(left, 3)
        body.addLayout(right, 2)
        root_layout.addLayout(body, 1)

    # ─── Theme Management ───────────────────────────────────────────
    def _toggle_theme(self):
        ThemeManager.instance().toggle_theme()
        self._apply_theme()

    def _apply_theme(self):
        colors = ThemeManager.instance().get_colors()
        self.setStyleSheet(get_global_stylesheet(colors))

        # Title & Subtitle
        self.lbl_title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {colors['text_primary']}; letter-spacing: -0.5px;")
        self.lbl_badge.setStyleSheet(f"""
            QLabel {{
                background-color: {colors['badge_lab_bg']};
                color: {colors['badge_lab_fg']};
                border: 1px solid {colors['badge_lab_border']};
                border-radius: 12px;
                padding: 4px 10px;
                font-weight: 700;
                font-size: 10px;
                letter-spacing: 0.5px;
            }}
        """)
        self.lbl_subtitle.setStyleSheet(f"font-size: 11px; color: {colors['text_muted']}; font-weight: 500;")

        # Toggle Button
        if ThemeManager.instance().is_dark():
            self.btn_theme_toggle.setText("☀️ Açık Tema")
            self.btn_theme_toggle.setStyleSheet(f"background-color: {colors['bg_card']}; color: {colors['text_primary']}; border: 1px solid {colors['border']}; font-weight: 600;")
        else:
            self.btn_theme_toggle.setText("🌙 Koyu Tema")
            self.btn_theme_toggle.setStyleSheet(f"background-color: {colors['bg_card']}; color: {colors['text_primary']}; border: 1px solid {colors['border']}; font-weight: 600;")

        # Action Buttons
        self.btn_db_mgr.setStyleSheet(f"background-color: {colors['accent_purple']}; font-weight: bold;")
        self.btn_load.setStyleSheet(f"background-color: {colors['accent_cyan']}; font-weight: bold;")
        self.btn_save.setStyleSheet(f"background-color: {colors['accent_green']}; font-weight: bold;")
        self.btn_excel.setStyleSheet(f"background-color: {colors['accent_orange']}; font-weight: bold;")
        self.btn_report.setStyleSheet(f"background-color: {colors['accent_blue']}; font-weight: bold;")
        self.btn_lib_polyol.setStyleSheet(f"background-color: {colors['accent_purple']}; font-size: 12px; font-weight: bold; padding: 8px;")
        self.btn_lib_iso_row.setStyleSheet(f"background-color: {colors['accent_purple']}; font-size: 12px; font-weight: bold; padding: 8px;")

        # Blend status badge
        self.lbl_iso_blend_status.setStyleSheet(f"""
            QLabel {{
                color: {colors['accent_cyan']};
                font-size: 11px;
                font-weight: 700;
                background-color: {colors['bg_input']};
                border: 1px solid {colors['border']};
                padding: 5px 10px;
                border-radius: 4px;
            }}
        """)
        self.lbl_selected_iso.setStyleSheet(f"color: {colors['text_muted']}; font-size: 11px; font-style: italic;")

        # Subcomponents
        self.sep_line.update_theme()
        self.card_iso.update_theme()
        self.card_ratio.update_theme()
        for w in [self.row_polyol_mass, self.row_blend_oh, self.row_eq_oh,
                  self.row_eq_nco, self.row_iso_nco, self.row_total_mass, self.row_solid]:
            w.update_theme()

        self._recalculate()

    # ─── Helpers ────────────────────────────────────────────────────
    def _make_spin(self, lo, hi, val, suffix, decimals, step=None):
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setValue(val)
        sb.setDecimals(decimals)
        if suffix:
            sb.setSuffix(suffix)
        if step:
            sb.setSingleStep(step)
        sb.valueChanged.connect(self._recalculate)
        return sb

    # ─── Polyol (Part A) Table Management ─────────────────────────────
    def _add_polyol_row(self, name="Polyol", amount=100.0, oh_val=150.0, solid=100.0):
        self.table.blockSignals(True)
        r = self.table.rowCount()
        self.table.insertRow(r)
        self.table.setRowHeight(r, 34)

        colors = ThemeManager.instance().get_colors()

        for col, text in enumerate([name, str(amount), str(oh_val), str(solid)]):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col > 0 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if col != 1:  # Miktar haricindeki hücreler veritabanından çekilir (düzenlenemez)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(r, col, item)

        btn_del = QPushButton("✕")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setFixedSize(28, 24)
        btn_del.setToolTip("Bileşeni Sil")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['bg_input']};
                color: {colors['danger']};
                font-size: 13px;
                font-weight: 800;
                border: 1px solid {colors['border']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors['danger']};
                color: #FFFFFF;
                border-color: {colors['danger']};
            }}
        """)
        btn_del.clicked.connect(self._on_delete_polyol_clicked)
        self.table.setCellWidget(r, 4, btn_del)

        self.table.blockSignals(False)
        self._recalculate()

    def _on_delete_polyol_clicked(self):
        btn = self.sender()
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 4) is btn:
                self.table.removeRow(r)
                break
        self._recalculate()

    def _add_default_polyols(self):
        mats = {m.name: m for m in self.library_mgr.get_all_materials()}
        defaults = [
            ("AK-022 / ALK-022 Reçine (%60 Katı)", 43.0),
            ("Titanium Dioxide (Titan TiO2)", 24.0),
            ("Talk (Magnezyum Silikat)", 10.0),
            ("Kalsit (Kalsiyum Karbonat CaCO3)", 10.0),
            ("Butil Asetat (İnert)", 2.0),
            ("Metil Etil Keton MEK (İnert)", 3.55)
        ]
        for name, amt in defaults:
            if name in mats:
                m = mats[name]
                oh_val = m.value if m.category != "isocyanate" else 0.0
                self._add_polyol_row(m.name, amt, oh_val, m.solid_content)

    def _on_polyol_cell_changed(self, item):
        self._recalculate()

    # ─── Isocyanate (Part B) Table Management ─────────────────────────
    def _add_iso_row(self, name="İzosiyanat / Solvent", amount=20.0, nco_pct=12.0, solid=75.0):
        self.iso_table.blockSignals(True)
        r = self.iso_table.rowCount()
        self.iso_table.insertRow(r)
        self.iso_table.setRowHeight(r, 34)

        colors = ThemeManager.instance().get_colors()

        for col, text in enumerate([name, str(amount), str(nco_pct), str(solid)]):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col > 0 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if col != 1:  # Miktar haricindeki hücreler veritabanından çekilir (düzenlenemez)
                item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self.iso_table.setItem(r, col, item)

        btn_del = QPushButton("✕")
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.setFixedSize(28, 24)
        btn_del.setToolTip("Bileşeni Sil")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['bg_input']};
                color: {colors['danger']};
                font-size: 13px;
                font-weight: 800;
                border: 1px solid {colors['border']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {colors['danger']};
                color: #FFFFFF;
                border-color: {colors['danger']};
            }}
        """)
        btn_del.clicked.connect(self._on_delete_iso_clicked)
        self.iso_table.setCellWidget(r, 4, btn_del)

        self.iso_table.blockSignals(False)
        self._recalculate()

    def _on_delete_iso_clicked(self):
        btn = self.sender()
        for r in range(self.iso_table.rowCount()):
            if self.iso_table.cellWidget(r, 4) is btn:
                self.iso_table.removeRow(r)
                break
        self._recalculate()

    def _add_default_isocyanates(self):
        mats = {m.name: m for m in self.library_mgr.get_all_materials()}
        defaults = [
            ("WANNATE TT-350B (TDI Trimer)", 24.0),
            ("WANNATE TT-150B (TDI Trimer)", 8.0),
            ("WANNATE TL-75E (TDI Adduct)", 12.0),
            ("Butil Asetat (İnert)", 26.0),
            ("Toluene (İnert)", 20.0),
            ("Etil Asetat (İnert)", 10.0)
        ]
        for name, amt in defaults:
            if name in mats:
                m = mats[name]
                nco = m.value if m.category == "isocyanate" else 0.0
                self._add_iso_row(m.name, amt, nco, m.solid_content)

    def _on_iso_cell_changed(self, item):
        self._recalculate()

    def _on_iso_tab_changed(self, index):
        self._recalculate()

    # ─── Cell Validation ────────────────────────────────────────────
    def _validate_table_cell(self, table: QTableWidget, row: int, col: int):
        item = table.item(row, col)
        if item is None:
            return None
        text = item.text().strip()
        colors = ThemeManager.instance().get_colors()

        try:
            val = float(text)
            if val < 0:
                item.setBackground(QColor(colors["cell_error"]))
                return None
            item.setBackground(QColor(colors["bg_primary"]))
            return val
        except ValueError:
            item.setBackground(QColor(colors["cell_error"]))
            return None

    # ─── Recalculate ────────────────────────────────────────────────
    def _recalculate(self):
        if not hasattr(self, "spin_nco") or not hasattr(self, "spin_iso_solid") or not hasattr(self, "spin_index"):
            return

        # Polyol (Part A) tablosunu oku
        self.table.blockSignals(True)
        polyols = []
        for r in range(self.table.rowCount()):
            name = self.table.item(r, 0).text() if self.table.item(r, 0) else f"Polyol {r+1}"
            amount = self._validate_table_cell(self.table, r, 1)
            oh_val = self._validate_table_cell(self.table, r, 2)
            solid  = self._validate_table_cell(self.table, r, 3)
            if amount is None or oh_val is None or solid is None:
                continue
            polyols.append(PolyolItem(name, amount, oh_val, solid))
        self.table.blockSignals(False)

        # İzosiyanat (Part B) modunu incele
        isocyanates = []
        is_blend_mode = (self.iso_tabs.currentIndex() == 0)

        if is_blend_mode:
            self.iso_table.blockSignals(True)
            for r in range(self.iso_table.rowCount()):
                name = self.iso_table.item(r, 0).text() if self.iso_table.item(r, 0) else f"Bileşen {r+1}"
                amount = self._validate_table_cell(self.iso_table, r, 1)
                nco_pct = self._validate_table_cell(self.iso_table, r, 2)
                solid  = self._validate_table_cell(self.iso_table, r, 3)
                if amount is None or nco_pct is None or solid is None:
                    continue
                isocyanates.append(IsocyanateItem(name, amount, nco_pct, solid))
            self.iso_table.blockSignals(False)

        # Hesaplamayı çalıştır
        res = ChemistryEngine.calculate_blend(
            polyols=polyols,
            nco_percent=self.spin_nco.value(),
            iso_solid_content=self.spin_iso_solid.value(),
            index=self.spin_index.value(),
            isocyanates=isocyanates if is_blend_mode else None
        )
        self.current_result = res
        self.current_polyols = polyols
        self.current_isocyanates = isocyanates if is_blend_mode else []

        # UI güncelleme
        if is_blend_mode:
            self.lbl_iso_blend_status.setText(
                f"Harman Net Serbest NCO: %{res.iso_nco_percent:.2f}  |  Net Katı Madde: %{res.iso_solid_content:.2f}"
            )

        self.card_iso.set_value(f"{res.req_iso_mass:.2f} g")
        self.card_ratio.set_value(f"100 : {res.mixing_ratio_b:.2f}")
        self.row_polyol_mass.set_value(f"{res.total_polyol_mass:.2f} g")
        self.row_blend_oh.set_value(f"{res.blend_oh_value:.2f} mg KOH/g")
        self.row_eq_oh.set_value(f"{res.total_eq_oh:.6f}")
        self.row_eq_nco.set_value(f"{res.req_eq_nco:.6f}")
        self.row_iso_nco.set_value(f"% {res.iso_nco_percent:.2f}")
        self.row_total_mass.set_value(f"{res.total_mixture_mass:.2f} g")
        self.row_solid.set_value(f"% {res.mixture_solid_content:.2f}")

    # ─── Library Selection Actions ──────────────────────────────────
    def _on_select_polyol_from_library(self):
        dlg = LibrarySelectorDialog(category="all", library_mgr=self.library_mgr, parent=self)
        if dlg.exec() == LibrarySelectorDialog.DialogCode.Accepted and dlg.selected_material:
            mat = dlg.selected_material
            oh_val = mat.value if mat.category != "isocyanate" else 0.0
            self._add_polyol_row(name=mat.name, amount=10.0, oh_val=oh_val, solid=mat.solid_content)

    def _on_select_iso_from_library(self):
        dlg = LibrarySelectorDialog(category="all", library_mgr=self.library_mgr, parent=self)
        if dlg.exec() == LibrarySelectorDialog.DialogCode.Accepted and dlg.selected_material:
            mat = dlg.selected_material
            nco_pct = mat.value if mat.category == "isocyanate" else 0.0
            if self.iso_tabs.currentIndex() == 0:  # Blend tablosuna ekle
                self._add_iso_row(name=mat.name, amount=10.0, nco_pct=nco_pct, solid=mat.solid_content)
            else:  # Tekli moda yaz
                self.spin_nco.setValue(nco_pct)
                self.spin_iso_solid.setValue(mat.solid_content)
                self.lbl_selected_iso.setText(f"Seçilen Sertleştirici: {mat.name}")

    # ─── Recipe & Report Actions ────────────────────────────────────
    def _on_load_recipe_clicked(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "JSON Reçete Yükle", "", "JSON Dosyaları (*.json)")
        if not filepath:
            return

        try:
            data = RecipeExporter.load_recipe_from_json(filepath)
            self.current_recipe_name = data.get("recipe_name", "Yüklenen Reçete")

            # Polyol (A Komponenti) tablosunu yükle
            polyols_data = data.get("polyols", [])
            self.table.blockSignals(True)
            self.table.setRowCount(0)
            self.table.blockSignals(False)

            for p in polyols_data:
                self._add_polyol_row(
                    name=p.get("name", "Polyol"),
                    amount=float(p.get("amount", 0.0)),
                    oh_val=float(p.get("oh_value", 0.0)),
                    solid=float(p.get("solid_content", 100.0))
                )

            # İzosiyanat (B Komponenti) ayarlarını yükle
            iso_data = data.get("isocyanate", {})
            self.spin_nco.setValue(float(iso_data.get("nco_percent", 31.5)))
            self.spin_iso_solid.setValue(float(iso_data.get("solid_content", 100.0)))
            self.spin_index.setValue(float(iso_data.get("index", 1.05)))

            is_blend_mode = iso_data.get("is_blend_mode", True)
            self.iso_tabs.setCurrentIndex(0 if is_blend_mode else 1)

            if is_blend_mode:
                isocyanates_data = iso_data.get("isocyanates", [])
                self.iso_table.blockSignals(True)
                self.iso_table.setRowCount(0)
                self.iso_table.blockSignals(False)

                for i in isocyanates_data:
                    self._add_iso_row(
                        name=i.get("name", "İzosiyanat"),
                        amount=float(i.get("amount", 0.0)),
                        nco_pct=float(i.get("nco_percent", 0.0)),
                        solid=float(i.get("solid_content", 100.0))
                    )

            self._recalculate()
            QMessageBox.information(self, "Başarılı", f"Reçete başarıyla yüklendi:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Reçete yüklenirken hata oluştu:\n{e}")

    def _on_save_recipe_clicked(self):
        name, ok = QInputDialog.getText(self, "Reçete Kaydet", "Reçete Adı:", text=self.current_recipe_name)
        if not ok or not name.strip():
            return
        self.current_recipe_name = name.strip()

        filepath, _ = QFileDialog.getSaveFileName(self, "Reçeteyi JSON Olarak Kaydet", f"{self.current_recipe_name}.json", "JSON Dosyaları (*.json)")
        if not filepath:
            return

        try:
            is_blend_mode = (self.iso_tabs.currentIndex() == 0)
            RecipeExporter.save_recipe_to_json(
                filepath=filepath,
                recipe_name=self.current_recipe_name,
                polyols=self.current_polyols,
                nco_percent=self.spin_nco.value(),
                iso_solid=self.spin_iso_solid.value(),
                index=self.spin_index.value(),
                isocyanates=self.current_isocyanates if is_blend_mode else None,
                is_iso_blend_mode=is_blend_mode
            )
            QMessageBox.information(self, "Başarılı", f"Reçete başarıyla kaydedildi:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Reçete kaydedilirken hata oluştu:\n{e}")

    def _open_database_manager(self):
        """Veritabanı yönetimi portalını (ekleme, düzenleme, silme) açar."""
        dlg = DatabaseManagerDialog(library_mgr=self.library_mgr, parent=self)
        dlg.exec()

    def _on_export_csv_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Excel CSV Olarak Dışa Aktar", f"{self.current_recipe_name}_Stokiyometri.csv", "CSV Dosyaları (*.csv)")
        if not filepath:
            return

        try:
            is_blend_mode = (self.iso_tabs.currentIndex() == 0)
            RecipeExporter.export_to_csv(
                filepath,
                self.current_recipe_name,
                self.current_polyols,
                self.spin_nco.value(),
                self.spin_iso_solid.value(),
                self.spin_index.value(),
                self.current_result,
                isocyanates=self.current_isocyanates if is_blend_mode else None
            )
            QMessageBox.information(self, "Başarılı", f"Excel uyumlu CSV dosyası oluşturuldu:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"CSV dışa aktarılırken hata oluştu:\n{e}")

    def _on_export_html_clicked(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "HTML Raporu Oluştur", f"{self.current_recipe_name}_Rapor.html", "HTML Dosyaları (*.html)")
        if not filepath:
            return

        try:
            is_blend_mode = (self.iso_tabs.currentIndex() == 0)
            html_content = RecipeExporter.generate_html_report(
                self.current_recipe_name,
                self.current_polyols,
                self.spin_nco.value(),
                self.spin_iso_solid.value(),
                self.spin_index.value(),
                self.current_result,
                isocyanates=self.current_isocyanates if is_blend_mode else None
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            webbrowser.open(f"file:///{os.path.abspath(filepath)}")
            QMessageBox.information(self, "Başarılı", f"HTML Raporu oluşturuldu ve tarayıcıda açıldı:\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"HTML Raporu oluşturulurken hata oluştu:\n{e}")