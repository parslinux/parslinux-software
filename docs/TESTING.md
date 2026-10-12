# Test ve Doğrulama Kılavuzu (TESTING.md)

Bu kılavuz, Pars Linux Yazılım Merkezi'nde birim testlerin, API entegrasyon testlerinin ve grafik arayüz doğrulamasının nasıl çalıştırılacağını açıklar.

---

## 1. Test Seviyeleri

1. **Sözdizimi ve Derleme Testi:** Tüm Python kaynak dosyalarının ve denetleyicilerin hatasız derlenmesi.
2. **Denetleyici & Mixin Doğrulama Testi:** `src/controllers/` mixin yapısının ve metot sözleşmelerinin doğrulanması.
3. **FlowBox Sıfır Titreme & Kararlılık Testi:** Hızlı kategori/arama geçişlerinde kartların kaybolmadığının ve FlowBox'ın çökmediğinin doğrulanması.
4. **Birim & API Entegrasyon Testi:** `FlathubClient` (önbellek, TTL, arama) ve `FlatpakManager` modüllerinin işlevsellik kontrolü.
5. **Grafik Arayüz (GTK3) Doğrulama Testi:** Pencerenin çökme olmadan açılması, sinyallerin bağlanması ve temiz kapanması.

---

## 2. Test Komutları

### A. Python Derleme Testi
Tüm ana modüllerde ve denetleyici mixin'lerinde sözdizimi hatalarını denetler:
```bash
python3 -m py_compile setup.py src/*.py src/controllers/*.py
```
*Beklenen Çıktı:* Komut hatasız ve 0 çıkış koduyla tamamlanmalıdır.

---

### B. Mixin Denetleyici Doğrulama Testi
`MainWindow` sınıfının tüm mixin'lerden (`SliderMixin`, `ImageGalleryMixin`, `SearchMixin`, `DetailMixin`, `QueueMixin`, `InstalledMixin`) beklenen metotları eksiksiz devraldığını denetler:

```bash
python3 scratch/verify_mixins.py
```
*Beklenen Çıktı:* `All mixin checks passed!`

---

### C. FlowBox Sıfır Titreme & Kararlılık Testi
FlowBox bileşeninde hızlı kategori değişimlerini simüle eder; widget silme (`remove`) yerine artımlı ekleme (`_append_apps_to_flowbox`) ve yerel filtreleme (`invalidate_filter`) yapıldığını, hiçbir uygulamanın ekrandan kaybolmadığını doğrular:

```bash
python3 scratch/test_flowbox_stability.py
```
*Beklenen Çıktı:* `Ran 5 tests ... OK`

---

### D. Flathub API, Önbellek ve Flatpak Entegrasyon Testi
Flathub sunucusuna erişimi, disk TTL önbelleğini (`api_cache/`) ve yerel Flatpak uygulamalarını test eder:

```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from FlathubClient import FlathubClient
from FlatpakManager import FlatpakManager

client = FlathubClient()
manager = FlatpakManager()

print('[TEST] Flathub Bağlantısı:', client.check_connection())
popular = client.get_popular(limit=5)
print(f'[TEST] Popüler Uygulamalar: {len(popular)} adet alındı.')

search_res = client.search('vlc', limit=3)
print(f'[TEST] VLC Arama Sonucu: {len(search_res)} adet bulundu.')

installed = manager.get_installed_apps()
print(f'[TEST] Yerel Kurulu Flatpak Sayısı: {len(installed)}')
assert client.check_connection() is True, 'Flathub erişilemez!'
assert len(popular) > 0, 'Popüler listesi boş!'
print('TÜM BİRİM TESTLERİ BAŞARIYLA GEÇTİ!')
"
```

---

### E. Başsız (Headless) GTK3 Arayüz Testi
Ekran sunucusuna bağlanarak arayüzün kilitlenmeden, çökmeden açıldığını ve temiz şekilde kapandığını doğrular:

```bash
python3 scratch/test_mainwindow_headless.py
```

---

## 3. GitHub Actions CI Örneği

Proje için önerilen `.github/workflows/test.yml` yapılandırması:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install System Dependencies
        run: |
          sudo apt update
          sudo apt install -y python3-gi gir1.2-gtk-3.0 flatpak xvfb
      - name: Compile Check
        run: python3 -m py_compile setup.py src/*.py src/controllers/*.py
      - name: Mixin Contract Verification
        run: python3 scratch/verify_mixins.py
      - name: FlowBox Stability Test
        run: xvfb-run python3 scratch/test_flowbox_stability.py
      - name: Headless GUI Test
        run: xvfb-run python3 scratch/test_mainwindow_headless.py
```

