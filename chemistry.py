from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PolyolItem:
    """Polyol / Reçine bileşeni veri sınıfı (A Komponenti)."""
    name: str
    amount: float          # Miktar (gram)
    oh_value: float        # OH Değeri (mg KOH/g)
    solid_content: float   # Katı Madde Oranı (%)

    @property
    def eq_oh(self) -> float:
        """Bileşenin sağladığı OH eşdeğer molü."""
        if self.oh_value <= 0 or self.amount <= 0:
            return 0.0
        return (self.amount * self.oh_value) / 56110.0

    @property
    def solid_mass(self) -> float:
        """Bileşendeki net katı madde kütlesi (g). Reaktif solventler (OH>0) reaksiyonda polimerleşerek kürülen filmde kalır."""
        if self.oh_value > 0 and self.solid_content == 0.0:
            return self.amount  # Reaktif solvent (DAA, MEG, PG) reaksiyon sonucu polimer katı film kütlesine katılır
        sc = max(0.0, min(100.0, self.solid_content))
        return self.amount * (sc / 100.0)


@dataclass
class IsocyanateItem:
    """İzosiyanat / Sertleştirici bileşeni veri sınıfı (B Komponenti)."""
    name: str
    amount: float          # Miktar (gram veya %)
    nco_percent: float     # Serbest NCO (%)
    solid_content: float   # Katı Madde Oranı (%)

    @property
    def eq_nco(self) -> float:
        """Bileşenin sağladığı NCO eşdeğer molü (100g kütle esasına göre)."""
        if self.nco_percent <= 0 or self.amount <= 0:
            return 0.0
        return (self.amount * (self.nco_percent / 100.0)) / 42.02

    @property
    def solid_mass(self) -> float:
        """Bileşendeki net katı madde kütlesi (g). Aktif izosiyanat bileşenleri polimerleşerek kürülen filmde kalır."""
        if self.nco_percent > 0 and self.solid_content == 0.0:
            return self.amount  # Aktif izosiyanat polimer katı film kütlesine katılır
        sc = max(0.0, min(100.0, self.solid_content))
        return self.amount * (sc / 100.0)


@dataclass
class CalculationResult:
    """Hesaplama sonuç paketi."""
    total_polyol_mass: float
    total_eq_oh: float
    req_iso_mass: float
    req_eq_nco: float
    mixing_ratio_b: float          # 100g A Komponentine karşılık gelen B gramı
    total_mixture_mass: float
    mixture_solid_content: float
    blend_oh_value: float           # Ağırlıklı ortalama OH değeri (mg KOH/g)
    iso_nco_percent: float          # Kullanılan veya blend net %NCO değeri
    iso_solid_content: float        # Kullanılan veya blend net katı madde % değeri
    is_iso_blend: bool = False       # B komponenti çoklu reçete mi?


class ChemistryEngine:
    """NCO/OH Stokiyometri ve Karışım Hesaplama Motoru."""

    @staticmethod
    def calculate_blend(
        polyols: List[PolyolItem],
        nco_percent: float,
        iso_solid_content: float,
        index: float,
        isocyanates: Optional[List[IsocyanateItem]] = None
    ) -> CalculationResult:

        total_polyol_mass = sum(p.amount for p in polyols)
        total_polyol_solid = sum(p.solid_mass for p in polyols)
        total_eq_oh = sum(p.eq_oh for p in polyols)

        # Ağırlıklı ortalama OH değeri
        if total_polyol_mass > 0:
            blend_oh_value = sum(p.amount * p.oh_value for p in polyols) / total_polyol_mass
        else:
            blend_oh_value = 0.0

        # Hedeflenen NCO eşdeğeri
        req_eq_nco = total_eq_oh * index

        is_iso_blend = False
        eff_nco_percent = nco_percent
        eff_iso_solid = iso_solid_content

        # Eğer B komponenti çoklu bileşen (IsocyanateItem listesi) olarak verilmişse:
        if isocyanates and len(isocyanates) > 0:
            total_iso_recipe_mass = sum(i.amount for i in isocyanates)
            if total_iso_recipe_mass > 0:
                is_iso_blend = True
                # Ağırlıklı ortalama %NCO ve Katı Madde Oranı
                eff_nco_percent = sum(i.amount * i.nco_percent for i in isocyanates) / total_iso_recipe_mass
                total_iso_solid_mass = sum(i.solid_mass for i in isocyanates)
                eff_iso_solid = (total_iso_solid_mass / total_iso_recipe_mass) * 100.0

        # Gereken Sertleştirici (İzosiyanat) Gramajı: m = (Eq_NCO * 4202) / %NCO
        if eff_nco_percent > 0:
            req_iso_mass = (req_eq_nco * 4202.0) / eff_nco_percent
        else:
            req_iso_mass = 0.0

        iso_solid_mass = req_iso_mass * (eff_iso_solid / 100.0)

        # A:B Karışım Oranı (100 gram Polyol karışımına göre)
        if total_polyol_mass > 0:
            mixing_ratio_b = (req_iso_mass / total_polyol_mass) * 100.0
        else:
            mixing_ratio_b = 0.0

        total_mixture_mass = total_polyol_mass + req_iso_mass
        total_solid_mass = total_polyol_solid + iso_solid_mass

        mixture_solid_content = (
            (total_solid_mass / total_mixture_mass * 100.0)
            if total_mixture_mass > 0 else 0.0
        )

        return CalculationResult(
            total_polyol_mass=total_polyol_mass,
            total_eq_oh=total_eq_oh,
            req_iso_mass=req_iso_mass,
            req_eq_nco=req_eq_nco,
            mixing_ratio_b=mixing_ratio_b,
            total_mixture_mass=total_mixture_mass,
            mixture_solid_content=mixture_solid_content,
            blend_oh_value=blend_oh_value,
            iso_nco_percent=eff_nco_percent,
            iso_solid_content=eff_iso_solid,
            is_iso_blend=is_iso_blend
        )