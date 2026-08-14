# NCO / OH Calculator — Poliüretan Stokiyometri & Reçete Portalı

🔬 **NCO / OH Calculator**, 2-Bileşenli Poliüretan (2K PU) kaplama, ahşap verniği, oto tamir boyası, zemin sistemleri ve elastomer formülasyonlarında A Komponenti (Polyol / Reçine) ile B Komponenti (İzosiyanat / Sertleştirici) arasındaki stokiyometrik reaksiyon oranlarını hesaplayan profesyonel bir masaüstü yazılımıdır.

---

## 🌟 Öne Çıkan Özellikler

- **🧪 Hassas Stokiyometri Motoru:** NCO/OH indeksine göre gerekli sertleştirici gramajını ve $100\text{g } A : B$ karışım oranını anında hesaplar.
- **📋 Çoklu Sertleştirici (Part B Blend) Desteği:** Sertleştiricinin kendisi de bir reçete ise (örneğin TDI Trimer + Çözücüler) net $\%NCO$ ve katı madde oranını otomatik hesaplar.
- **☀️ / 🌙 Dark & Light Mode:** Modern laboratuvar tasarımı ve tek tıkla Açık/Koyu tema geçişi (Tercih kalıcı olarak saklanır).
- **⚠️ Reaktif Solvent Hesabı:** Diaseton Alkol (DAA), Monoetilen Glikol (MEG), Propilen Glikol (PG) gibi $NCO$ tüketen reaktif solventlerin OH değerlerini otomatik hesaba katar.
- **🌐 PubChem REST API Entegrasyonu:** Kimyasalların molekül ağırlığı ($MW$) ve fonksiyonalitesinden ($f$) teorik KOH değerlerini arka planda (asenkron `QThread`) çeker.
- **🗄️ Hammadde Veritabanı Portalı:** Özel reçineler ve sertleştiriciler tanımlama, düzenleme ve silme.
- **📊 Dışa Aktarma & Raporlama:** Reçeteyi JSON kaydetme, Microsoft Excel uyumlu CSV (UTF-8 BOM) aktarımı ve resmi baskı HTML raporları üretme.

---

## 📐 Kimyasal Formüller ve Hesaplama Mantığı

Poliüretan (2K PU) reaksiyonunda 1 mol hidroksil grubu (-OH), 1 mol izosiyanat grubu (-NCO) ile reaksiyona girerek üretan bağını oluşturur:

```
R-N=C=O + R'-OH  --->  R-NH-COO-R'  (Üretan Bağı)
```

### 1. Hydroxyl (OH) Eşdeğer Molü (Eq_OH)
```
Eq_OH = (Miktar [g] × OH Değeri [mg KOH/g]) / 56110.0
```
*Not: 56110 = KOH moleküler ağırlığı (56.11 g/mol) × 1000 mg/g*

### 2. Isocyanate (NCO) Eşdeğer Molü (Eq_NCO)
```
Eq_NCO = (Miktar [g] × (Serbest % NCO / 100)) / 42.02
```
*Not: 42.02 = -NCO grubu moleküler ağırlığı (42.02 g/mol)*

### 3. İndeks ve Gereken Sertleştirici (B) Gramajı
```
Gereken Eq_NCO = Toplam Eq_OH × NCO/OH İndeksi

Gereken Sertleştirici Kütlesi (B) [g] = (Gereken Eq_NCO × 4202.0) / Net % NCO
```

### 4. Karışım Oranı (100g A : B)
```
Karışım Oranı (B [g]) = (Gereken Sertleştirici [g] / Toplam Polyol Kütlesi [g]) × 100.0
```

### 5. Saf Moleküller İçin Teorik OH Değeri (MW ve f)
```
OH Değeri (mg KOH/g) = (56110.0 × f) / MW [g/mol]
```
*(burada f: moleküldeki -OH grubu sayısı, MW: molekül ağırlığıdır)*

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.8 veya üzeri
- PyQt6

### Kurulum

```bash
# Depoyu klonlayın
git clone https://github.com/akinozturq/nco-oh-calculator.git
cd nco-oh-calculator

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
python main.py
```

---

## 📁 Proje Yapısı

```
nco-oh-calculator/
├── main.py              # Uygulama giriş noktası (QApplication)
├── main_window.py       # Ana pencere (MainWindow) ve arayüz mantığı
├── dialogs.py           # Diyalog pencereleri (Veritabanı, Web Arama vb.)
├── styles.py            # Laboratuvar tasarım sistemi ve Dark/Light Theme Manager
├── chemistry.py         # Pure-Python stokiyometri hesaplama motoru
├── library.py           # Hammadde veritabanı yönetimi ve JSON depolama
├── chem_fetcher.py      # PubChem REST API asenkron istemcisi (QThread)
├── exporter.py          # JSON, CSV ve HTML rapor üreticileri
├── requirements.txt     # Bağımlılıklar
└── README.md            # Proje dokümantasyonu
```

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
