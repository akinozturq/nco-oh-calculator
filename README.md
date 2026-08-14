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

Poliüretan (2K PU) tepkimesinde 1 mol hidroksil grubu ($-OH$), 1 mol izosiyanat grubu ($-NCO$) ile tepkimeye girerek üretan bağını oluşturur:

$$\text{R-N=C=O} + \text{R'-OH} \longrightarrow \text{R-NH-COO-R'}$$

### 1. Hydroxyl (OH) Eşdeğer Molü ($\text{Eq}_{OH}$)
$$\text{Eq}_{OH} = \frac{\text{Miktar (g)} \times \text{OH Değeri (mg KOH/g)}}{56110.0}$$
*($56110 = M_{KOH} \text{ [56.11 g/mol]} \times 1000 \text{ [mg/g]}$)*

### 2. Isocyanate (NCO) Eşdeğer Molü ($\text{Eq}_{NCO}$)
$$\text{Eq}_{NCO} = \frac{\text{Miktar (g)} \times \left(\frac{\%NCO}{100}\right)}{42.02}$$
*($42.02 = M_{NCO} \text{ [g/mol]}$)*

### 3. İndeks ve Gereken Sertleştirici (B) Gramajı
$$\text{Gereken Eq}_{NCO} = \text{Toplam Eq}_{OH} \times \text{NCO/OH İndeksi}$$

$$\text{Gereken Sertleştirici Kütlesi (B) [g]} = \frac{\text{Gereken Eq}_{NCO} \times 4202.0}{\text{Net } \%NCO}$$

### 4. Karışım Oranı ($100\text{g } A : B$)
$$\text{Karışım Oranı (B [g])} = \left(\frac{\text{Gereken Sertleştirici (B)}}{\text{Toplam Polyol Kütlesi (A)}}\right) \times 100.0$$

### 5. Saf Moleküller İçin Teorik OH Değeri ($MW$ ve $f$)
$$\text{OH Değeri (mg KOH/g)} = \frac{56110.0 \times f}{MW \text{ (g/mol)}}$$
*(burada $f$ moleküldeki $-OH$ grubu sayısı, $MW$ ise molekül ağırlığıdır)*

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
