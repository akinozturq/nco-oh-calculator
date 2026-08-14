from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QFormLayout, QDoubleSpinBox,
    QMessageBox, QGroupBox, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from library import RawMaterial, LibraryManager, CATEGORIES
from chem_fetcher import ChemicalDataFetcher, ChemFetchThread
from styles import get_dialog_stylesheet, ThemeManager


class MolecularOhCalculatorDialog(QDialog):
    """Küçük moleküller ve reaktif solventler için Moleküler OH Değeri Hesaplayıcı."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧪 Moleküler OH Değeri Hesaplayıcı & Web Arama")
        self.setMinimumWidth(420)
        self.calculated_oh: float = 0.0

        self.setStyleSheet(get_dialog_stylesheet())

        layout = QVBoxLayout(self)

        # Web Search Quick Bar
        web_box = QHBoxLayout()
        self.txt_web_search = QLineEdit()
        self.txt_web_search.setPlaceholderText("Kimyasal ara... (Örn: Diaseton alkol, MEG, PG)")
        self.btn_web_search = QPushButton("🌐 Web'den Ara")
        self.btn_web_search.setStyleSheet("background-color: #059669; padding: 6px 12px;")
        self.btn_web_search.clicked.connect(self._fetch_web_data)

        web_box.addWidget(self.txt_web_search, 1)
        web_box.addWidget(self.btn_web_search)
        layout.addLayout(web_box)

        form = QFormLayout()

        self.spin_mw = QDoubleSpinBox()
        self.spin_mw.setRange(1.0, 10000.0)
        self.spin_mw.setValue(116.16)  # DAA Molar Kütlesi
        self.spin_mw.setDecimals(2)
        self.spin_mw.setSuffix(" g/mol")
        self.spin_mw.valueChanged.connect(self._recalc)

        self.spin_func = QDoubleSpinBox()
        self.spin_func.setRange(1.0, 10.0)
        self.spin_func.setValue(1.0)
        self.spin_func.setDecimals(0)
        self.spin_func.valueChanged.connect(self._recalc)

        self.lbl_ew = QLabel("Eşdeğer Ağırlık (EW): 116.16 g/eq")
        self.lbl_ew.setStyleSheet("color: #94A3B8; font-size: 11px;")

        self.lbl_res_oh = QLabel("483.04 mg KOH/g")
        self.lbl_res_oh.setStyleSheet("color: #06B6D4; font-size: 18px; font-weight: bold;")

        form.addRow("Molekül Ağırlığı (MW):", self.spin_mw)
        form.addRow("OH Grubu Sayısı (f):", self.spin_func)
        form.addRow("", self.lbl_ew)
        form.addRow("Teorik OH Değeri:", self.lbl_res_oh)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("background-color: #475569;")
        btn_cancel.clicked.connect(self.reject)

        btn_use = QPushButton("Değeri Aktar")
        btn_use.clicked.connect(self.accept)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_use)

        layout.addLayout(btn_box)
        self._recalc()

    def _fetch_web_data(self):
        query = self.txt_web_search.text().strip()
        if not query:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir kimyasal adı girin.")
            return

        self.btn_web_search.setEnabled(False)
        self.btn_web_search.setText("⏳ Aranıyor...")

        self.fetch_thread = ChemFetchThread(query, parent=self)
        self.fetch_thread.result_ready.connect(self._on_web_data_received)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        self.fetch_thread.start()

    def _on_web_data_received(self, res: dict):
        self.btn_web_search.setEnabled(True)
        self.btn_web_search.setText("🌐 Web'den Ara")

        if res.get("success"):
            self.spin_mw.setValue(res["mw"])
            self.spin_func.setValue(res["f"])
            self._recalc()
            QMessageBox.information(
                self, "Başarılı",
                f"Web Verisi Çekildi:\n• İsim: {res['name']}\n• Formül: {res['formula']}\n• MW: {res['mw']} g/mol\n• Hesaplanan KOH Değeri: {res['koh_value']} mg KOH/g"
            )
        else:
            QMessageBox.warning(self, "Bulunamadı", res.get("error", "Veri çekilemedi."))

    def _recalc(self):
        mw = self.spin_mw.value()
        f = self.spin_func.value()
        if mw > 0 and f > 0:
            ew = mw / f
            self.calculated_oh = 56110.0 / ew
            self.lbl_ew.setText(f"Eşdeğer Ağırlık (EW): {ew:.2f} g/eq")
            self.lbl_res_oh.setText(f"{self.calculated_oh:.2f} mg KOH/g")


class LibrarySelectorDialog(QDialog):
    """Hammadde Kütüphanesinden Seçim Diyaloğu (Tüm Kategoriler Destekli)."""

    def __init__(self, category: str = "all", library_mgr: LibraryManager = None, parent=None):
        super().__init__(parent)
        self.category_filter = category
        self.library_mgr = library_mgr or LibraryManager()
        self.selected_material: RawMaterial = None

        self.setWindowTitle("Hammadde Veritabanı — Seçim Penceresi")
        self.setMinimumSize(720, 480)
        self.setStyleSheet(get_dialog_stylesheet())

        self._build_ui()
        self._load_materials()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Search bar & Filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Arama:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Hammadde adı, üretici veya kategori ara...")
        self.txt_search.textChanged.connect(self._filter_materials)
        search_layout.addWidget(self.txt_search, 2)

        search_layout.addWidget(QLabel("Kategori:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("Tüm Kategoriler", "all")
        self.cmb_filter.addItem("Polyol / Reçine (OH)", "polyol")
        self.cmb_filter.addItem("İzosiyanat / Sertleştirici (NCO)", "isocyanate")
        self.cmb_filter.addItem("Pigment & Dolgu", "pigment_filler")
        self.cmb_filter.addItem("Solvent / Çözücü", "solvent")
        self.cmb_filter.addItem("Katkı Maddesi / Ajan", "additive")

        idx = self.cmb_filter.findData(self.category_filter)
        if idx >= 0:
            self.cmb_filter.setCurrentIndex(idx)
        self.cmb_filter.currentIndexChanged.connect(self._filter_materials)

        search_layout.addWidget(self.cmb_filter, 1)
        layout.addLayout(search_layout)

        # List & Details splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.list_widget)

        # Detail panel
        detail_group = QGroupBox("Bileşen Detayları")
        detail_layout = QVBoxLayout(detail_group)
        self.lbl_detail_name = QLabel("—")
        self.lbl_detail_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #3B82F6;")
        self.lbl_detail_cat = QLabel("Kategori: —")
        self.lbl_detail_val = QLabel("Değer: —")
        self.lbl_detail_solid = QLabel("Katı Madde: —")
        self.lbl_detail_supplier = QLabel("Tedarikçi: —")
        self.lbl_detail_notes = QLabel("Notlar: —")
        self.lbl_detail_notes.setWordWrap(True)

        detail_layout.addWidget(self.lbl_detail_name)
        detail_layout.addWidget(self.lbl_detail_cat)
        detail_layout.addWidget(self.lbl_detail_val)
        detail_layout.addWidget(self.lbl_detail_solid)
        detail_layout.addWidget(self.lbl_detail_supplier)
        detail_layout.addWidget(self.lbl_detail_notes)
        detail_layout.addStretch()

        splitter.addWidget(detail_group)
        splitter.setSizes([400, 300])
        layout.addWidget(splitter)

        # Action buttons
        btn_box = QHBoxLayout()
        btn_add_new = QPushButton("＋ Veritabanına Yeni Ekle")
        btn_add_new.setStyleSheet("background-color: #10B981;")
        btn_add_new.clicked.connect(self._open_add_custom)
        btn_box.addWidget(btn_add_new)

        btn_box.addStretch()

        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("background-color: #475569;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_select = QPushButton("Seç ve Ekle")
        btn_select.clicked.connect(self._on_accept)
        btn_box.addWidget(btn_select)

        layout.addLayout(btn_box)

    def _load_materials(self):
        self.all_materials = self.library_mgr.get_all_materials(category_filter="all")
        self._filter_materials()

    def _filter_materials(self):
        query = self.txt_search.text().lower().strip()
        cat_key = self.cmb_filter.currentData()
        self.list_widget.clear()

        for mat in self.all_materials:
            if cat_key != "all" and mat.category != cat_key:
                continue

            if query in mat.name.lower() or query in mat.supplier.lower() or query in mat.notes.lower():
                if mat.value > 0:
                    val_unit = f"OH: {mat.value}" if mat.category != "isocyanate" else f"%NCO: {mat.value}"
                else:
                    val_unit = "İnert (OH: 0)"

                cat_title = CATEGORIES.get(mat.category, mat.category)
                item_text = f"{mat.name}  [{cat_title} | {val_unit} | Katı: %{mat.solid_content}]"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, mat)
                self.list_widget.addItem(item)

    def _on_selection_changed(self, current: QListWidgetItem, previous):
        if not current:
            return
        mat: RawMaterial = current.data(Qt.ItemDataRole.UserRole)
        self.selected_material = mat

        self.lbl_detail_name.setText(mat.name)
        self.lbl_detail_cat.setText(f"Kategori: {CATEGORIES.get(mat.category, mat.category)}")

        if mat.category == "polyol":
            val_label = f"OH Değeri: {mat.value} mg KOH/g"
        elif mat.category == "isocyanate":
            val_label = f"Serbest NCO: % {mat.value}"
        elif mat.value > 0:
            val_label = f"Reaktif OH Değeri: {mat.value} mg KOH/g (⚠️ NCO Tüketir)"
        else:
            val_label = "Reaktif Değer: İnert (OH/NCO = 0.0)"

        self.lbl_detail_val.setText(val_label)
        self.lbl_detail_solid.setText(f"Katı Madde Oranı: % {mat.solid_content}")
        self.lbl_detail_supplier.setText(f"Tedarikçi / Marka: {mat.supplier or 'Bilinmiyor'}")
        self.lbl_detail_notes.setText(f"Açıklama: {mat.notes or '—'}")

    def _open_add_custom(self):
        dlg = AddCustomMaterialDialog(default_category=self.cmb_filter.currentData(), parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.new_material:
            self.library_mgr.add_custom_material(dlg.new_material)
            self._load_materials()

    def _on_accept(self):
        if not self.selected_material:
            QMessageBox.warning(self, "Uyarı", "Lütfen listeden bir hammadde seçin.")
            return
        self.accept()


class AddCustomMaterialDialog(QDialog):
    """Yeni Özel Hammadde Tanımlama ve Düzenleme Diyaloğu."""

    def __init__(self, default_category="polyol", edit_material: RawMaterial = None, parent=None):
        super().__init__(parent)
        self.edit_material = edit_material
        self.setWindowTitle("Hammadde Düzenle" if edit_material else "Veritabanına Yeni Hammadde Ekle")
        self.setMinimumWidth(480)
        self.new_material: RawMaterial = None

        self.setStyleSheet(get_dialog_stylesheet())

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Name field with Web Fetch Button
        name_layout = QHBoxLayout()
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Örn: Diaseton alkol, Propilen glikol, Titan")
        name_layout.addWidget(self.txt_name, 1)

        self.btn_fetch_web = QPushButton("🌐 Web'den KOH Çek")
        self.btn_fetch_web.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_fetch_web.setStyleSheet("background-color: #059669; padding: 5px 10px; font-size: 11px;")
        self.btn_fetch_web.clicked.connect(self._fetch_from_web)
        name_layout.addWidget(self.btn_fetch_web)

        self.cmb_cat = QComboBox()
        self.cmb_cat.addItem("Polyol / Reçine (OH)", "polyol")
        self.cmb_cat.addItem("İzosiyanat / Sertleştirici (NCO)", "isocyanate")
        self.cmb_cat.addItem("Pigment & Dolgu (İnert)", "pigment_filler")
        self.cmb_cat.addItem("Solvent / Çözücü", "solvent")
        self.cmb_cat.addItem("Katkı Maddesi / Ajan", "additive")

        target_cat = edit_material.category if edit_material else default_category
        idx = self.cmb_cat.findData(target_cat)
        if idx >= 0:
            self.cmb_cat.setCurrentIndex(idx)
        self.cmb_cat.currentIndexChanged.connect(self._on_cat_changed)

        val_layout = QHBoxLayout()
        self.lbl_value = QLabel("OH Değeri (mg KOH/g):")
        self.spin_value = QDoubleSpinBox()
        self.spin_value.setRange(0.0, 7000.0)
        self.spin_value.setValue(140.0)
        val_layout.addWidget(self.spin_value, 1)

        self.btn_calc_mol = QPushButton("🧪 MW -> OH Hesabı")
        self.btn_calc_mol.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_calc_mol.setStyleSheet("background-color: #06B6D4; padding: 5px 10px; font-size: 11px;")
        self.btn_calc_mol.clicked.connect(self._open_mol_calculator)
        val_layout.addWidget(self.btn_calc_mol)

        self.spin_solid = QDoubleSpinBox()
        self.spin_solid.setRange(0.0, 100.0)
        self.spin_solid.setValue(70.0)
        self.spin_solid.setSuffix(" %")

        self.txt_supplier = QLineEdit()
        self.txt_supplier.setPlaceholderText("Tedarikçi firma veya marka")

        self.txt_notes = QLineEdit()
        self.txt_notes.setPlaceholderText("Kullanım amacı veya açıklamalar")

        form.addRow("Hammadde Adı:", name_layout)
        form.addRow("Kategori:", self.cmb_cat)
        form.addRow(self.lbl_value, val_layout)
        form.addRow("Katı Madde Oranı:", self.spin_solid)
        form.addRow("Tedarikçi:", self.txt_supplier)
        form.addRow("Notlar:", self.txt_notes)

        layout.addLayout(form)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("İptal")
        btn_cancel.setStyleSheet("background-color: #475569;")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Kaydet")
        btn_save.clicked.connect(self._on_save)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

        # Pre-fill if editing existing material
        if edit_material:
            self.txt_name.setText(edit_material.name)
            self.spin_value.setValue(edit_material.value)
            self.spin_solid.setValue(edit_material.solid_content)
            self.txt_supplier.setText(edit_material.supplier)
            self.txt_notes.setText(edit_material.notes)

        self._on_cat_changed(self.cmb_cat.currentIndex())

    def _fetch_from_web(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce aratılacak hammadde veya solvent adını girin.")
            return

        self.btn_fetch_web.setEnabled(False)
        self.btn_fetch_web.setText("⏳ Aranıyor...")

        self.fetch_thread = ChemFetchThread(name, parent=self)
        self.fetch_thread.result_ready.connect(self._on_fetch_web_received)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        self.fetch_thread.start()

    def _on_fetch_web_received(self, res: dict):
        self.btn_fetch_web.setEnabled(True)
        self.btn_fetch_web.setText("🌐 Web'den KOH Çek")

        if res.get("success"):
            self.spin_value.setValue(res["koh_value"])
            note_str = f"Formül: {res['formula']} | MW: {res['mw']} g/mol (PubChem Verisi)"
            self.txt_notes.setText(note_str)
            if not self.txt_supplier.text().strip():
                self.txt_supplier.setText("PubChem / Standart Kimyasal")

            QMessageBox.information(
                self, "Web Verisi Alındı",
                f"PubChem Verisi Başarıyla Çekildi:\n\n• Kimyasal: {res['name']}\n• Formül: {res['formula']}\n• Molekül Ağırlığı: {res['mw']} g/mol\n• OH Grubu (f): {res['f']}\n• KOH / OH Değeri: {res['koh_value']} mg KOH/g"
            )
        else:
            QMessageBox.warning(self, "Bulunamadı", res.get("error", "Veri çekilemedi."))

    def _open_mol_calculator(self):
        dlg = MolecularOhCalculatorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.spin_value.setValue(dlg.calculated_oh)

    def _on_cat_changed(self, idx):
        cat = self.cmb_cat.itemData(idx)
        if cat == "polyol":
            self.lbl_value.setText("OH Değeri (mg KOH/g):")
            self.spin_value.setEnabled(True)
            self.btn_calc_mol.setVisible(True)
            if not self.edit_material and self.spin_value.value() == 0.0:
                self.spin_value.setValue(140.0)
            if not self.edit_material:
                self.spin_solid.setValue(70.0)
        elif cat == "isocyanate":
            self.lbl_value.setText("Serbest NCO (%):")
            self.spin_value.setEnabled(True)
            self.btn_calc_mol.setVisible(False)
            if not self.edit_material and self.spin_value.value() == 0.0:
                self.spin_value.setValue(13.3)
            if not self.edit_material:
                self.spin_solid.setValue(75.0)
        elif cat == "solvent":
            self.lbl_value.setText("OH Değeri (Reaktif Solvent ise >0):")
            self.spin_value.setEnabled(True)
            self.btn_calc_mol.setVisible(True)
            if not self.edit_material:
                self.spin_solid.setValue(0.0)
        elif cat == "pigment_filler":
            self.lbl_value.setText("Reaktif Değer (OH/NCO):")
            self.spin_value.setValue(0.0)
            self.spin_value.setEnabled(False)
            self.btn_calc_mol.setVisible(False)
            if not self.edit_material:
                self.spin_solid.setValue(100.0)
        elif cat == "additive":
            self.lbl_value.setText("Reaktif Değer (Su/OH var ise >0):")
            self.spin_value.setEnabled(True)
            self.btn_calc_mol.setVisible(True)
            if not self.edit_material:
                self.spin_solid.setValue(100.0)

    def _on_save(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Lütfen hammadde adını girin.")
            return

        cat = self.cmb_cat.currentData()
        self.new_material = RawMaterial(
            name=name,
            category=cat,
            value=self.spin_value.value(),
            solid_content=self.spin_solid.value(),
            supplier=self.txt_supplier.text().strip(),
            notes=self.txt_notes.text().strip()
        )
        self.accept()


class DatabaseManagerDialog(QDialog):
    """Veritabanı Yönetimi Diyaloğu (Ekleme, Düzenleme, Silme, Listeleme)."""

    def __init__(self, library_mgr: LibraryManager, parent=None):
        super().__init__(parent)
        self.library_mgr = library_mgr
        self.setWindowTitle("🗄️ Hammadde Veritabanı Yönetimi")
        self.setMinimumSize(850, 520)

        self.setStyleSheet(get_dialog_stylesheet())

        self._build_ui()
        self._load_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Header Title
        title = QLabel("Hammadde Veritabanı Portalı")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3B82F6;")
        layout.addWidget(title)

        # Search bar & Filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Arama:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Veritabanında hammadde, tedarikçi veya not ara...")
        self.txt_search.textChanged.connect(self._filter_table)
        search_layout.addWidget(self.txt_search, 2)

        search_layout.addWidget(QLabel("Kategori:"))
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("Tüm Kategoriler", "all")
        self.cmb_filter.addItem("Polyol / Reçine (OH)", "polyol")
        self.cmb_filter.addItem("İzosiyanat / Sertleştirici (NCO)", "isocyanate")
        self.cmb_filter.addItem("Pigment & Dolgu", "pigment_filler")
        self.cmb_filter.addItem("Solvent / Çözücü", "solvent")
        self.cmb_filter.addItem("Katkı Maddesi / Ajan", "additive")
        self.cmb_filter.currentIndexChanged.connect(self._filter_table)

        search_layout.addWidget(self.cmb_filter, 1)
        layout.addLayout(search_layout)

        # Main Database Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "HAMMADDE ADI", "KATEGORİ", "DEĞER (OH / %NCO)", "KATI MADDE (%)", "TEDARİKÇİ", "NOTLAR"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        h.resizeSection(1, 160)
        h.resizeSection(2, 140)
        h.resizeSection(3, 110)
        h.resizeSection(4, 130)

        layout.addWidget(self.table)

        # Action Buttons
        btn_box = QHBoxLayout()

        btn_add = QPushButton("＋ Veritabanına Yeni Ekle")
        btn_add.setStyleSheet("background-color: #10B981;")
        btn_add.clicked.connect(self._on_add)

        btn_edit = QPushButton("✏️ Düzenle")
        btn_edit.setStyleSheet("background-color: #F59E0B; color: #0F172A;")
        btn_edit.clicked.connect(self._on_edit)

        btn_del = QPushButton("🗑️ Veritabanından Sil")
        btn_del.setStyleSheet("background-color: #EF4444;")
        btn_del.clicked.connect(self._on_delete)

        btn_close = QPushButton("Kapat")
        btn_close.setStyleSheet("background-color: #475569;")
        btn_close.clicked.connect(self.accept)

        btn_box.addWidget(btn_add)
        btn_box.addWidget(btn_edit)
        btn_box.addWidget(btn_del)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)

        layout.addLayout(btn_box)

    def _load_table(self):
        self.all_materials = self.library_mgr.get_all_materials(category_filter="all")
        self._filter_table()

    def _filter_table(self):
        query = self.txt_search.text().lower().strip()
        cat_key = self.cmb_filter.currentData()
        self.table.setRowCount(0)

        for mat in self.all_materials:
            if cat_key != "all" and mat.category != cat_key:
                continue

            if query in mat.name.lower() or query in mat.supplier.lower() or query in mat.notes.lower():
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setRowHeight(r, 32)

                cat_name = CATEGORIES.get(mat.category, mat.category)
                val_str = f"{mat.value:.1f} mg KOH/g" if mat.category == "polyol" else (f"% {mat.value:.1f} NCO" if mat.category == "isocyanate" else (f"{mat.value:.1f} OH" if mat.value > 0 else "0.0 (İnert)"))

                items = [
                    QTableWidgetItem(mat.name),
                    QTableWidgetItem(cat_name),
                    QTableWidgetItem(val_str),
                    QTableWidgetItem(f"% {mat.solid_content:.1f}"),
                    QTableWidgetItem(mat.supplier or "—"),
                    QTableWidgetItem(mat.notes or "—")
                ]

                for col, item in enumerate(items):
                    item.setData(Qt.ItemDataRole.UserRole, mat)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if col in [1, 2, 3] else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    self.table.setItem(r, col, item)

    def _get_selected_material(self) -> RawMaterial:
        r = self.table.currentRow()
        if r < 0:
            return None
        item = self.table.item(r, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_add(self):
        dlg = AddCustomMaterialDialog(default_category=self.cmb_filter.currentData(), parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.new_material:
            self.library_mgr.add_custom_material(dlg.new_material)
            self._load_table()

    def _on_edit(self):
        mat = self._get_selected_material()
        if not mat:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için tablodan bir hammadde seçin.")
            return

        dlg = AddCustomMaterialDialog(edit_material=mat, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.new_material:
            self.library_mgr.update_material(mat, dlg.new_material)
            self._load_table()

    def _on_delete(self):
        mat = self._get_selected_material()
        if not mat:
            QMessageBox.warning(self, "Uyarı", "Lütfen silmek için tablodan bir hammadde seçin.")
            return

        reply = QMessageBox.question(
            self, "Silme Onayı",
            f"'{mat.name}' hammaddesini veritabanından kalıcı olarak silmek istediğinizden emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.library_mgr.delete_material(mat)
            self._load_table()
