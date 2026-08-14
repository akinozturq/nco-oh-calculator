import urllib.request
import urllib.parse
import json
import re
from PyQt6.QtCore import QThread, pyqtSignal


class ChemicalDataFetcher:
    """PubChem PUG REST API üzerinden kimyasal moleküler veri ve KOH değeri çekici."""

    TURKISH_TO_ENGLISH = {
        "diaseton alkol": "diacetone alcohol",
        "diasetonalkol": "diacetone alcohol",
        "daa": "diacetone alcohol",
        "propilen glikol": "propylene glycol",
        "etil glikol": "ethylene glycol",
        "monoetilen glikol": "ethylene glycol",
        "meg": "ethylene glycol",
        "gliserin": "glycerol",
        "izopropanol": "isopropanol",
        "butil asetat": "butyl acetate",
        "ksilen": "xylene",
        "toluen": "toluene",
        "bütandiol": "1,4-butanediol",
        "butandiol": "1,4-butanediol",
        "bdo": "1,4-butanediol",
        "bütanol": "butanol",
        "metanol": "methanol",
        "etanol": "ethanol",
        "pma": "propylene glycol monomethyl ether acetate",
        "mek": "methyl ethyl ketone",
    }

    @staticmethod
    def fetch_compound_info(query_name: str) -> dict:
        """
        Verilen hammadde/solvent adı ile PubChem REST API'sinden moleküler ağırlık,
        formül ve hesaplanan KOH değerini çeker.
        """
        raw_name = query_name.strip().lower()
        if not raw_name:
            return {"success": False, "error": "Lütfen bir kimyasal adı girin."}

        search_term = ChemicalDataFetcher.TURKISH_TO_ENGLISH.get(raw_name, query_name)
        encoded_term = urllib.parse.quote(search_term)
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_term}/property/MolecularWeight,MolecularFormula,IUPACName,Title,CanonicalSMILES/JSON"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                props = data['PropertyTable']['Properties'][0]
                
                mw = float(props.get('MolecularWeight', 0))
                formula = props.get('MolecularFormula', '')
                title = props.get('Title', query_name)
                iupac = props.get('IUPACName', '')
                smiles = props.get('CanonicalSMILES', '')

                # OH Grubu Fonksiyonalite ($f$) Tespiti
                f = 1
                combined_text = (search_term + " " + title + " " + iupac + " " + smiles).lower()
                if 'tetrol' in combined_text or 'pentaerythritol' in combined_text:
                    f = 4
                elif 'triol' in combined_text or 'glycer' in combined_text:
                    f = 3
                elif 'diol' in combined_text or 'glycol' in combined_text or 'glikol' in combined_text:
                    f = 2
                
                # KOH Değeri Hesabı: (56110 * f) / MW
                koh_value = (56110.0 * f) / mw if mw > 0 else 0.0

                return {
                    "success": True,
                    "name": title,
                    "mw": mw,
                    "formula": formula,
                    "f": f,
                    "koh_value": round(koh_value, 2),
                    "iupac": iupac
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"'{query_name}' için internetten kimyasal veri bulunamadı."
            }


class ChemFetchThread(QThread):
    """PubChem REST API'sinden asenkron (arka planda) veri çeken QThread."""
    result_ready = pyqtSignal(dict)

    def __init__(self, query_name: str, parent=None):
        super().__init__(parent)
        self.query_name = query_name

    def run(self):
        res = ChemicalDataFetcher.fetch_compound_info(self.query_name)
        self.result_ready.emit(res)

