import json
import csv
import html
from typing import List, Dict, Any, Optional
from chemistry import PolyolItem, IsocyanateItem, CalculationResult


class RecipeExporter:
    """Reçete kaydetme/yükleme ve rapor dışa aktarma araçları."""

    @staticmethod
    def save_recipe_to_json(
        filepath: str,
        recipe_name: str,
        polyols: List[PolyolItem],
        nco_percent: float,
        iso_solid: float,
        index: float,
        notes: str = "",
        isocyanates: Optional[List[IsocyanateItem]] = None,
        is_iso_blend_mode: bool = False
    ):
        data = {
            "recipe_name": recipe_name,
            "notes": notes,
            "polyols": [
                {
                    "name": p.name,
                    "amount": p.amount,
                    "oh_value": p.oh_value,
                    "solid_content": p.solid_content
                }
                for p in polyols
            ],
            "isocyanate": {
                "nco_percent": nco_percent,
                "solid_content": iso_solid,
                "index": index,
                "is_blend_mode": is_iso_blend_mode,
                "isocyanates": [
                    {
                        "name": i.name,
                        "amount": i.amount,
                        "nco_percent": i.nco_percent,
                        "solid_content": i.solid_content
                    }
                    for i in (isocyanates or [])
                ]
            }
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_recipe_from_json(filepath: str) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def export_to_csv(
        filepath: str,
        recipe_name: str,
        polyols: List[PolyolItem],
        nco_percent: float,
        iso_solid: float,
        index: float,
        res: CalculationResult,
        isocyanates: Optional[List[IsocyanateItem]] = None
    ):
        """Excel ile doğrudan açılabilen UTF-8 BOM CSV formatında dışa aktarma."""
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["REÇETE ADI", recipe_name])
            writer.writerow([])
            writer.writerow(["--- A KOMPONENTİ (POLYOL / REÇİNE BLEND) ---"])
            writer.writerow(["Hammadde Adı", "Miktar (g)", "OH Değeri (mg KOH/g)", "Katı Madde (%)", "Eq OH"])
            
            for p in polyols:
                writer.writerow([
                    p.name,
                    f"{p.amount:.2f}",
                    f"{p.oh_value:.2f}",
                    f"{p.solid_content:.2f}",
                    f"{p.eq_oh:.6f}"
                ])
            
            writer.writerow([])
            writer.writerow(["--- B KOMPONENTİ (İZOSİYANAT / SERTLEŞTİRİCİ) ---"])
            
            if res.is_iso_blend and isocyanates and len(isocyanates) > 0:
                writer.writerow(["Hammadde Adı", "Miktar (g/%)", "Serbest NCO (%)", "Katı Madde (%)", "Eq NCO"])
                for i in isocyanates:
                    writer.writerow([
                        i.name,
                        f"{i.amount:.2f}",
                        f"{i.nco_percent:.2f}",
                        f"{i.solid_content:.2f}",
                        f"{i.eq_nco:.6f}"
                    ])
                writer.writerow(["Harman Net Serbest NCO (%)", f"{res.iso_nco_percent:.2f}"])
                writer.writerow(["Harman Net Katı Madde (%)", f"{res.iso_solid_content:.2f}"])
            else:
                writer.writerow(["Serbest NCO (%)", f"{nco_percent:.2f}"])
                writer.writerow(["Katı Madde (%)", f"{iso_solid:.2f}"])
            
            writer.writerow(["NCO / OH İndeksi", f"{index:.2f}"])
            
            writer.writerow([])
            writer.writerow(["--- HESAPLAMA SONUÇLARI ---"])
            writer.writerow(["Gerekli Sertleştirici (B)", f"{res.req_iso_mass:.2f} g"])
            writer.writerow(["Karışım Oranı (100g A : B)", f"100 : {res.mixing_ratio_b:.2f}"])
            writer.writerow(["Toplam Polyol Kütlesi", f"{res.total_polyol_mass:.2f} g"])
            writer.writerow(["Blend Ağırlıklı OH Değeri", f"{res.blend_oh_value:.2f} mg KOH/g"])
            writer.writerow(["Toplam Eq OH", f"{res.total_eq_oh:.6f}"])
            writer.writerow(["Gereken Eq NCO", f"{res.req_eq_nco:.6f}"])
            writer.writerow(["Toplam Karışım Kütlesi", f"{res.total_mixture_mass:.2f} g"])
            writer.writerow(["Nihai Karışım Katı Madde Oranı", f"% {res.mixture_solid_content:.2f}"])

    @staticmethod
    def generate_html_report(
        recipe_name: str,
        polyols: List[PolyolItem],
        nco_percent: float,
        iso_solid: float,
        index: float,
        res: CalculationResult,
        isocyanates: Optional[List[IsocyanateItem]] = None
    ) -> str:
        """Yazdırılabilir veya kaydedilebilir HTML rapor çıktısı."""
        safe_recipe_name = html.escape(recipe_name)
        polyol_rows_html = "".join([
            f"<tr><td>{html.escape(p.name)}</td><td>{p.amount:.2f} g</td><td>{p.oh_value:.2f}</td><td>%{p.solid_content:.1f}</td><td>{p.eq_oh:.6f}</td></tr>"
            for p in polyols
        ])

        if res.is_iso_blend and isocyanates and len(isocyanates) > 0:
            iso_rows_html = "".join([
                f"<tr><td>{html.escape(i.name)}</td><td>{i.amount:.2f} g/%</td><td>%{i.nco_percent:.2f}</td><td>%{i.solid_content:.1f}</td><td>{i.eq_nco:.6f}</td></tr>"
                for i in isocyanates
            ])
            iso_section_html = f"""
            <table>
                <thead>
                    <tr><th>Hammadde Adı</th><th>Miktar</th><th>Serbest NCO %</th><th>Katı %</th><th>Eq NCO</th></tr>
                </thead>
                <tbody>
                    {iso_rows_html}
                </tbody>
            </table>
            <table class="summary-table" style="margin-top: 10px;">
                <tr><td><strong>Harman Net Serbest NCO (%):</strong></td><td>%{res.iso_nco_percent:.2f}</td></tr>
                <tr><td><strong>Harman Net Katı Madde (%):</strong></td><td>%{res.iso_solid_content:.2f}</td></tr>
                <tr><td><strong>NCO / OH İndeksi:</strong></td><td>{index:.2f}</td></tr>
            </table>
            """
        else:
            iso_section_html = f"""
            <table class="summary-table">
                <tr><td><strong>Serbest NCO (%):</strong></td><td>{nco_percent:.2f} %</td></tr>
                <tr><td><strong>Katı Madde Oranı (%):</strong></td><td>{iso_solid:.2f} %</td></tr>
                <tr><td><strong>NCO / OH İndeksi:</strong></td><td>{index:.2f}</td></tr>
            </table>
            """

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>NCO/OH Stokiyometri Raporu - {safe_recipe_name}</title>
<style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f8fafc; color: #0f172a; padding: 30px; }}
    .card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto; }}
    h1 {{ color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; margin-top: 0; }}
    h3 {{ color: #3b82f6; margin-top: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ background: #f1f5f9; color: #475569; text-transform: uppercase; font-size: 12px; }}
    .res-box {{ display: flex; gap: 15px; margin-top: 15px; }}
    .res-card {{ flex: 1; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 15px; text-align: center; }}
    .res-val {{ font-size: 22px; font-weight: bold; color: #1d4ed8; margin-top: 5px; }}
    .summary-table td {{ border: none; padding: 6px 0; }}
</style>
</head>
<body>
<div class="card">
    <h1>Poliüretan Stokiyometri Raporu</h1>
    <p><strong>Reçete Adı:</strong> {safe_recipe_name}</p>
    
    <h3>A Komponenti (Polyol / Reçine Blend)</h3>
    <table>
        <thead>
            <tr><th>Hammadde Adı</th><th>Miktar</th><th>OH Değeri</th><th>Katı %</th><th>Eq OH</th></tr>
        </thead>
        <tbody>
            {polyol_rows_html}
        </tbody>
    </table>

    <h3>B Komponenti (İzosiyanat / Sertleştirici)</h3>
    {iso_section_html}

    <h3>Hesaplama Sonuçları</h3>
    <div class="res-box">
        <div class="res-card">
            <div>GEREKLİ SERTLEŞTİRİCİ (B)</div>
            <div class="res-val">{res.req_iso_mass:.2f} g</div>
        </div>
        <div class="res-card">
            <div>KARIŞIM ORANI (A : B)</div>
            <div class="res-val">100 : {res.mixing_ratio_b:.2f}</div>
        </div>
    </div>

    <table class="summary-table" style="margin-top: 20px;">
        <tr><td><strong>Toplam Polyol Kütlesi:</strong></td><td>{res.total_polyol_mass:.2f} g</td></tr>
        <tr><td><strong>Blend OH Değeri:</strong></td><td>{res.blend_oh_value:.2f} mg KOH/g</td></tr>
        <tr><td><strong>Toplam Eq OH:</strong></td><td>{res.total_eq_oh:.6f}</td></tr>
        <tr><td><strong>Gereken Eq NCO:</strong></td><td>{res.req_eq_nco:.6f}</td></tr>
        <tr><td><strong>Toplam Karışım Kütlesi:</strong></td><td>{res.total_mixture_mass:.2f} g</td></tr>
        <tr><td><strong>Nihai Karışım Katı Madde Oranı:</strong></td><td>%{res.mixture_solid_content:.2f}</td></tr>
    </table>
</div>
</body>
</html>"""

