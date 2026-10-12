# Pars Linux Yazılım Merkezi (Pars Linux Software Center)

Pars Linux Yazılım Merkezi, modern Linux dağıtımları için geliştirilmiş, **Flathub REST API v2** ve **Flatpak** tabanlı, zengin ve modern bir GTK+ 3 grafik uygulama mağazasıdır.

Pars Linux Yazılım Merkezi, modern Flatpak ekosistemini temel alarak evrensel ve hızlı bir uygulama deneyimi sunar.

---

## 🌟 Öne Çıkan Özellikler

- **Flathub REST API v2 & Meilisearch:** Binlerce güncel uygulamayı popüler, trend, kategori ve canlı arama desteğiyle sunar.
- **Evrensel Flatpak Yönetimi:** Tek tıkla kurma, kaldırma, güncelleme ve doğrudan masaüstünde bağımsız süreçte başlatma.
- **Gelişmiş İzin Düzenleyici (Permission Editor):** Flatseal benzeri, kurulu Flatpak uygulamalarının izinlerini (Ağ, Dosya Sistemi, Ekran, Ses, Donanım) arayüzden doğrudan açıp kapatabilme (`flatpak override --user`) ve sıfırlama.
- **Canlı ODRS Yorumları & Puan Gönderme:** Open Desktop Rating Service (`odrs.gnome.org`) üzerinden topluluk incelemeleri ve doğrudan detay sayfasından yıldızlı puan/yorum gönderebilme.
- **Flatpak Depo (Remote) Yönetimi:** Ayarlar ekranından sistem ve kullanıcı depolarını listeleme, Flathub Beta, GNOME Nightly veya özel adresle yeni depo ekleme ve yönetme.
- **Gelişmiş Çevrimdışı Mod (Offline Mode):** İnternet olmadığında önbellek ile kesintisiz açılış, yerel arama fallback'i, bilgi çubuğu bildirimi ve yüklü uygulamalara tam erişim.
- **Çoklu Kriter Sıralama:** Kategori ve arama ekranlarında Ada Göre (A-Z), En Çok İndirilenler, Popülerlik ve Son Eklenenlere göre 0ms GTK sıralaması.
- **Masaüstü Bildirim Eylemleri:** İndirme veya güncelleme tamamlandığında bildirimden tek tıkla uygulamayı başlatma butonu.
- **Wayland & Touchpad Jestleri:** Vitrin afişlerinde dokunmatik parmakla kaydırma (`Gtk.GestureSwipe`) ve touchpad iki parmak yatay kaydırma desteği.
- **Sistem ve Flatpak Güncellemeleri:** Bekleyen güncellemeleri anlık tespit edip tek tıkla topluca güncelleyen "Tümünü Güncelle" paneli.
- **Mimarî Rozetleri:** Uygulamanın `x86_64`, `aarch64` (ARM64) ve `riscv64` CPU desteği ile donanım uyumluluk rozetleri.
- **Modüler Denetleyici Mimarisi (`src/controllers/`):** Bakımı kolaylaştıran 6 bağımsız mixin yapısı (Slider, Galeri, Arama & Kategori, Detay, Kuyruk ve Yüklü Uygulamalar).
- **0ms Sıfır Titreme (Zero-Flicker) FlowBox:** Senkron kart inşası, kalıcı kayıt defteri ve yerel GTK filtreleme/sıralama mekanizmasıyla akıcı ve anlık sayfa geçişleri.
- **Yüksek Performans & Çift Katmanlı Önbellek:** Bellek içi ve kalıcı disk TTL önbelleği (4s/24s), 250ms debounced arama ve asenkron ikon ön yükleme.
- **Çift Erişimli Ayarlar:** Hem sol gezinme çubuğundan hem de başlık çubuğundaki menüden (☰) kolayca erişilebilen ayarlar paneli.
- **20 Özel Vektör Kategori İkonu:** FreeDesktop standartlarında hazırlanan modern SVG kategori ikonları ve SVG yıldız derecelendirme sistemi.
- **Dağıtım Bağımsız:** Pars Linux başta olmak üzere Arch Linux, Debian, Ubuntu ve Fedora dahil tüm Linux dağıtımlarında sorunsuz çalışır.

---

## 🚀 Hızlı Başlangıç

### Bağımlılıkları Yükleyin:

**Pars Linux & Arch Linux:**
```bash
sudo pacman -S --needed python-gobject gtk3 flatpak vte3 libsoup libnotify
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

**Debian & Ubuntu:**
```bash
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-soup-2.4 gir1.2-vte-2.91 flatpak
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

### Uygulamayı Çalıştırın:
```bash
git clone https://github.com/parslinux/parslinux-software.git
cd parslinux-software
./parslinux-software
```

### Hızlı Test Komutları:
```bash
# Kod Derleme ve Denetleyici Doğrulaması
python3 -m py_compile setup.py src/*.py src/controllers/*.py
python3 scratch/verify_mixins.py

# FlowBox Kararlılık ve Sıfır Titreme Testi
python3 scratch/test_flowbox_stability.py

# İleri Düzey Özellikler Testi (İzinler, ODRS, Güncellemeler, Mimari)
python3 scratch/test_advanced_features.py
```

---

## 📚 Kapsamlı Dokümantasyon (`docs/`)

Tüm teknik, mimari ve kullanıcı rehberleri **[docs/](docs/)** dizini altında toplanmıştır:

| Doküman | İçerik |
| :--- | :--- |
| **[Mimari (ARCHITECTURE.md)](docs/ARCHITECTURE.md)** | Modüler mixin yapısı, FlowBox mimarisi, Flathub/Flatpak motoru |
| **[Kurulum Rehberi (INSTALL.md)](docs/INSTALL.md)** | Detaylı dağıtım kurulumları, masaüstü entegrasyonu ve dizinler |
| **[Özel Sunucu Kılavuzu (SELF_HOSTING_GUIDE.md)](docs/SELF_HOSTING_GUIDE.md)** | Kurumsal ağlarda kendi Flathub/Flatpak aynanızı barındırma |
| **[Değişiklik Günlüğü (CHANGELOG.md)](docs/CHANGELOG.md)** | Sürüm geçmişi, modüler refactor ve performans geliştirmeleri |
| **[Ödeme ve Bağış (PAYMENT_INTEGRATION.md)](docs/PAYMENT_INTEGRATION.md)** | Geliştirici destekleme ve bağış modelleri |
| **[Şartlar (TERMS.md)](docs/TERMS.md) / [SARTLAR.md](docs/SARTLAR.md)** | Kullanım koşulları ve sorumluluk reddi |
| **[AI Asistan Rehberi (CLAUDE.md)](docs/CLAUDE.md)** | Claude ve AI ajanları için kod tabanı kuralları ve standartlar |
| **[Yol Haritası (progress.md)](docs/progress.md)** | Gelişim aşamaları, tamamlanan fazlar ve gelecek hedefler |
| **[Test Kılavuzu (TESTING.md)](docs/TESTING.md)** | Birim, API, mixin ve başsız (headless) arayüz testleri |
| **[Komut Satırı Rehberi (CLI_REFERENCE.md)](docs/CLI_REFERENCE.md)** | Parametreler ve Flatpak hata ayıklama komutları |
| **[Çeviri Rehberi (TRANSLATION_GUIDE.md)](docs/TRANSLATION_GUIDE.md)** | Yeni diller ekleme ve gettext kullanımı |
| **[Katkıda Bulunma (CONTRIBUTING.md)](docs/CONTRIBUTING.md)** | Katkı süreci ve PR kuralları |
| **[Uygulama Bağlama (UYGULAMA_BAGLAMA.md)](docs/UYGULAMA_BAGLAMA.md)** | Flathub'da uygulama yayınlama ve AppStream hazırlama |
| **[Veri Tasarrufu (DATA_SAVING_GUIDE.md)](docs/DATA_SAVING_GUIDE.md)** | 2-tier disk önbelleği, TTL yönetimi ve bant genişliği tasarrufu |
| **[Güvenlik (SECURITY.md)](docs/SECURITY.md)** | Polkit, Bubblewrap sandbox ve açık bildirim süreci |
| **[Çatallanma ve Yeniden Yapılandırma (FORK.md)](docs/FORK.md)** | Orijinal proje kökeni, çatallanma gerekçeleri ve mimari dönüşüm |
| **[Sürüm Politikası (VERSION.md)](docs/VERSION.md)** | SemVer sürümleme ilkeleri |

---

## 📄 Lisans

Pars Linux Yazılım Merkezi, [GNU General Public License v3.0 (GPLv3)](LICENSE) kapsamında lisanslanmıştır.
