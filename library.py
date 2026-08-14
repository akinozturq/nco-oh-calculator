import json
import os
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".nco_oh_calculator")
USER_LIBRARY_FILE = os.path.join(USER_DATA_DIR, "user_library.json")

# Kategori Kodları ve İsimleri
CATEGORIES = {
    "polyol":         "Polyol / Reçine (OH)",
    "isocyanate":     "İzosiyanat / Sertleştirici (NCO)",
    "pigment_filler": "Pigment & Dolgu (İnert)",
    "solvent":        "Solvent / Çözücü",
    "additive":       "Katkı Maddesi / Ajan"
}


@dataclass
class RawMaterial:
    """Hammadde veritabanı öğesi."""
    name: str
    category: str         # "polyol", "isocyanate", "pigment_filler", "solvent", "additive"
    value: float          # Polyol veya Reaktif Solvent için OH Değeri (mg KOH/g), İzosiyanat için % NCO
    solid_content: float    # Katı Madde Oranı (%)
    supplier: str = ""    # Üretici / Tedarikçi (Opsiyonel)
    notes: str = ""       # Notlar

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RawMaterial":
        return cls(
            name=data.get("name", ""),
            category=data.get("category", "polyol"),
            value=float(data.get("value", 0.0)),
            solid_content=float(data.get("solid_content", 100.0)),
            supplier=data.get("supplier", ""),
            notes=data.get("notes", "")
        )


# Yerleşik (Standart) Hammadde Kütüphanesi
BUILTIN_MATERIALS: List[RawMaterial] = [
    # ── POLYOL & REÇİNELER ──
    RawMaterial("Akrilik Polyol %4.2 OH (Solventli)", "polyol", 138.0, 70.0, "Standart", "Genel amaçlı 2K Oto/Sanayi boyaları"),
    RawMaterial("Akrilik Polyol %3.0 OH", "polyol", 99.0, 60.0, "Standart", "Esnek / Ahşap Kaplama"),
    RawMaterial("Akrilik Polyol %4.5 OH (Yüksek Katılı)", "polyol", 148.0, 75.0, "Standart", "High-Solid Vernik"),
    RawMaterial("AK-022 / ALK-022 Reçine (%60 Katı)", "polyol", 120.0, 60.0, "Standart", "2K PU Son Kat Boya & Astar"),
    RawMaterial("Polyester Polyol 165 OH", "polyol", 165.0, 100.0, "Standart", "Solventsiz / Elastomer"),
    RawMaterial("Polyester Polyol 210 OH", "polyol", 210.0, 75.0, "Standart", "Zemin Kaplama / Astar"),
    RawMaterial("Polyether Polyol 280 OH (Triol)", "polyol", 280.0, 100.0, "Standart", "Köpük / Yapıştırıcı"),
    RawMaterial("Doymuş Polyester Reçine", "polyol", 140.0, 65.0, "Standart", "Bobin Kaplama (Coil Coating)"),

    # ── İZOSİYANAT & SERTLEŞTİRİCİLER ──
    RawMaterial("Desmodur N 75 (HDI Biuret)", "isocyanate", 16.5, 75.0, "Covestro", "Standart 2K PU sertleştirici"),
    RawMaterial("Desmodur N 3300 (HDI Trimer %100)", "isocyanate", 21.8, 100.0, "Covestro", "Solventsiz / Yüksek UV direnci"),
    RawMaterial("Desmodur L 75 (TDI Adduct)", "isocyanate", 13.3, 75.0, "Covestro", "Hızlı kuruyan ahşap / vernik"),
    RawMaterial("WANNATE TT-350B (TDI Trimer)", "isocyanate", 12.0, 50.0, "Wanhua", "2K PU Ahşap & Sanayi Sertleştiricisi"),
    RawMaterial("WANNATE TT-150B (TDI Trimer)", "isocyanate", 15.0, 50.0, "Wanhua", "Hızlı Sertleştirici"),
    RawMaterial("WANNATE TL-75E (TDI Adduct)", "isocyanate", 13.3, 75.0, "Wanhua", "2K PU Vernik Sertleştiricisi"),
    RawMaterial("Tolonate HDB 75 MX (HDI Biuret)", "isocyanate", 16.5, 75.0, "Vencorex", "Otomotiv ve sanayi boyaları"),
    RawMaterial("Tolonate HDT 90 (HDI Trimer)", "isocyanate", 19.6, 90.0, "Vencorex", "Düşük VOC kaplamalar"),
    RawMaterial("Vestabond IPDI Trimer T1890", "isocyanate", 11.5, 70.0, "Evonik", "Dış mekan sararmasız vernik"),
    RawMaterial("MDI İzosiyanat (Saf MDI)", "isocyanate", 33.6, 100.0, "Standart", "Yapıştırıcı / Elastomer"),

    # ── PİGMENT & DOLGULAR ──
    RawMaterial("Titanium Dioxide (Titan TiO2)", "pigment_filler", 0.0, 100.0, "Kronos/Venator", "Örtücü beyaz pigment"),
    RawMaterial("Talk (Magnezyum Silikat)", "pigment_filler", 0.0, 100.0, "Standart", "Zımpara ve matlık dolgusu"),
    RawMaterial("Kalsit (Kalsiyum Karbonat CaCO3)", "pigment_filler", 0.0, 100.0, "Omya", "Ekonomik hacim dolgusu"),
    RawMaterial("TSA 260 L (Matlaştırıcı Silika)", "pigment_filler", 0.0, 100.0, "Evonik Grace", "Film matlaştırıcı ajan"),
    RawMaterial("Baryum Sülfat (Baryt)", "pigment_filler", 0.0, 100.0, "Standart", "Yüksek yoğunluklu astar dolgusu"),

    # ── SOLVENTLER (İnert & Reaktif Solventler) ──
    RawMaterial("Butil Asetat (İnert)", "solvent", 0.0, 0.0, "Standart", "İnert Çözücü - OH İçermez"),
    RawMaterial("Metil Etil Keton MEK (İnert)", "solvent", 0.0, 0.0, "Standart", "İnert Çözücü - OH İçermez"),
    RawMaterial("P.M.A. (İnert)", "solvent", 0.0, 0.0, "Standart", "İnert Çözücü - OH İçermez"),
    RawMaterial("Toluene (İnert)", "solvent", 0.0, 0.0, "Standart", "İnert Çözücü - OH İçermez"),
    RawMaterial("Etil Asetat (İnert)", "solvent", 0.0, 0.0, "Standart", "İnert Çözücü - OH İçermez"),
    RawMaterial("Xylene Ksilen (İnert)", "solvent", 0.0, 0.0, "Standart", "İnert Çözücü - OH İçermez"),
    
    # 🧪 REAKTİF SOLVENTLER / ZİNCİR UZATICALAR (OH İçeren Solventler)
    RawMaterial("Diaseton Alkol (DAA - Reaktif Solvent)", "solvent", 483.0, 0.0, "Standart", "⚠️ REAKTİF SOLVENT! OH Değeri: 483 mg KOH/g, NCO tüketir"),
    RawMaterial("Monoetilen Glikol (MEG - Reaktif Diol)", "solvent", 1807.9, 0.0, "Standart", "⚠️ REAKTİF SOLVENT/DİOL! OH Değeri: 1808 mg KOH/g"),
    RawMaterial("Propilen Glikol (PG - Reaktif Solvent)", "solvent", 1474.6, 0.0, "Standart", "⚠️ REAKTİF SOLVENT! OH Değeri: 1475 mg KOH/g"),
    RawMaterial("1,4-Butanediol (BDO - Zincir Uzatıcı)", "polyol", 1245.2, 100.0, "Standart", "Reaktif Diol Zincir Uzatıcı"),

    # ── KATKI MADDELERİ / AJANLAR ──
    RawMaterial("DBTDL Katalizör Çözeltisi %10", "additive", 0.0, 10.0, "Standart", "Dibutiltin dilaurat üretan katalizörü"),
    RawMaterial("Borchi Gen 911", "additive", 0.0, 100.0, "Borchers", "Pigment ve dolgu dispersiyon ajanı"),
    RawMaterial("Claytone HY (Organokil)", "additive", 0.0, 100.0, "BYK", "Çökme önleyici & reoloji düzenleyici"),
    RawMaterial("Afcona 3033", "additive", 0.0, 100.0, "Afcona", "Yüzey düzleştirici & slip ajanı"),
    RawMaterial("Afcona 2040", "additive", 0.0, 100.0, "Afcona", "Köpük kesici (Defoamer)"),
    RawMaterial("MJU Wax 2301", "additive", 0.0, 100.0, "Standart", "Sentetik vaks zımpara ajanı"),
    RawMaterial("Nem / Eser Su Katkısı (H2O Düzeltme)", "additive", 6229.0, 0.0, "Standart", "⚠️ Nem Reaksiyon Düzeltmesi (1g Su = 6229 OH)"),
]


class LibraryManager:
    """Hammadde veritabanı yönetimi (Ekleme, Düzenleme, Silme ve Saklama)."""

    def __init__(self):
        self.user_materials: List[RawMaterial] = []
        self.deleted_builtins: List[str] = []
        self.load_user_library()

    def get_all_materials(self, category_filter: str = "all") -> List[RawMaterial]:
        active_builtins = [m for m in BUILTIN_MATERIALS if m.name not in self.deleted_builtins]
        all_mats = active_builtins + self.user_materials
        if category_filter == "all" or not category_filter:
            return all_mats
        return [m for m in all_mats if m.category == category_filter]

    def get_all_polyols(self) -> List[RawMaterial]:
        return self.get_all_materials("polyol")

    def get_all_isocyanates(self) -> List[RawMaterial]:
        return self.get_all_materials("isocyanate")

    def add_custom_material(self, mat: RawMaterial):
        self.user_materials.append(mat)
        self.save_user_library()

    def delete_material(self, mat: RawMaterial):
        """Veritabanından maddeyi siler."""
        found = False
        for i, u_mat in enumerate(self.user_materials):
            if u_mat.name == mat.name and u_mat.category == mat.category:
                self.user_materials.pop(i)
                found = True
                break
        if not found:
            # Built-in maddelerden siliniyorsa silinenler listesine kaydet
            if mat.name not in self.deleted_builtins:
                self.deleted_builtins.append(mat.name)
        self.save_user_library()

    def update_material(self, old_mat: RawMaterial, new_mat: RawMaterial):
        """Var olan maddeyi günceller."""
        updated = False
        for i, u_mat in enumerate(self.user_materials):
            if u_mat.name == old_mat.name and u_mat.category == old_mat.category:
                self.user_materials[i] = new_mat
                updated = True
                break
        if not updated:
            # Eğer built-in bir madde düzenleniyorsa, eskisini gizle ve yenisini ekle
            if old_mat.name not in self.deleted_builtins:
                self.deleted_builtins.append(old_mat.name)
            self.user_materials.append(new_mat)
        self.save_user_library()

    def load_user_library(self):
        if not os.path.exists(USER_LIBRARY_FILE):
            self.user_materials = []
            self.deleted_builtins = []
            return
        try:
            with open(USER_LIBRARY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.user_materials = [RawMaterial.from_dict(item) for item in data.get("materials", [])]
                    self.deleted_builtins = data.get("deleted_builtins", [])
                else:
                    self.user_materials = [RawMaterial.from_dict(item) for item in data]
                    self.deleted_builtins = []
        except Exception as e:
            logger.error(f"Kullanıcı kütüphanesi yüklenirken hata: {e}")
            self.user_materials = []
            self.deleted_builtins = []

    def save_user_library(self):
        try:
            os.makedirs(USER_DATA_DIR, exist_ok=True)
            with open(USER_LIBRARY_FILE, "w", encoding="utf-8") as f:
                payload = {
                    "materials": [m.to_dict() for m in self.user_materials],
                    "deleted_builtins": self.deleted_builtins
                }
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Kullanıcı kütüphanesi kaydedilirken hata: {e}")
