# Gelişim ve Yol Haritası (progress.md)

Pars Linux Yazılım Merkezi'nin güncel gelişim durumu, tamamlanan aşamalar ve gelecek sürümler için planlanan özellikler aşağıda listelenmiştir.

---

## 📊 Güncel Durum Özeti

| Faz | Açıklama | Durum |
| :--- | :--- | :--- |
| **Faz 1** | Eski Sunucudan Ayrıştırma & Flathub REST API v2 | ✅ Tamamlandı (%100) |
| **Faz 2** | Flatpak Paket Yönetim Motoru & Yerel Algılama | ✅ Tamamlandı (%100) |
| **Faz 3** | Çoklu Dağıtım Uyumluluğu (Arch / Debian / Pars) | ✅ Tamamlandı (%100) |
| **Faz 4** | Arayüz Entegrasyonu (Arama, Kategoriler, Vitrin, Detay) | ✅ Tamamlandı (%100) |
| **Faz 5** | Modüler Mimari & Denetleyici Ayrıştırması (`src/controllers/`) | ✅ Tamamlandı (%100) |
| **Faz 6** | Performans & 0ms Sıfır Titreme (Zero-Flicker) FlowBox | ✅ Tamamlandı (%100) |
| **Faz 7** | Özel FreeDesktop Kategori İkonları & Çift Erişimli Ayarlar | ✅ Tamamlandı (%100) |
| **Faz 8** | Gelişmiş İzin Yönetimi (Flatseal Benzeri), Canlı ODRS & Mimari Rozetleri | ✅ Tamamlandı (%100) |

---

## ✅ Tamamlanan Özellikler

- [x] **Flathub REST API v2 İstemcisi:** Popüler, trend, kategori listeleri ve Meilisearch anlık arama desteği.
- [x] **Çift Katmanlı Önbellekleme (2-Tier Cache):** Bellek içi + 4s/24s disk TTL önbelleği (`api_cache/`) ile mikro-saniyelik yanıtlar.
- [x] **250ms Arama Debouncing:** Meilisearch uç noktasına gereksiz sorgu yükünü engelleyen akıllı zamanlayıcı.
- [x] **Modüler Denetleyici Mimarisi:** `MainWindow.py` 6 bağımsız mixin'e ayrıştırıldı (`SliderMixin`, `ImageGalleryMixin`, `SearchMixin`, `DetailMixin`, `QueueMixin`, `InstalledMixin`).
- [x] **0ms Sıfır Titreme FlowBox:** Senkron kart inşası, kalıcı kart kayıt defteri (`_flowbox_app_ids`), artımlı kart ekleme (`_append_apps_to_flowbox`) ve yerel GTK filtreleme/sıralama.
- [x] **Çift Erişimli Ayarlar:** Hem sol kenar çubuğundan hem de sağ üst hamburger menüsünden (☰) güvenle açılan ayarlar görünümü.
- [x] **Özel FreeDesktop Vektör İkonları:** 20 adet özgün SVG kategori ikonu (`ps-cat-*.svg`) ve 3 adet SVG yıldız simgesi.
- [x] **Asenkron İkon İndirici:** `ThreadPoolExecutor` ile simgelerin arka planda indirilip yerel diskte önbelleğe alınması.
- [x] **Flatpak Paket Yönetimi:** Kurulu uygulamaları listeleme, kurma, kaldırma, güncelleme ve bağımsız süreçte başlatma.
- [x] **Gelişmiş İzin Düzenleyici (Permission Editor):** Flatseal benzeri, kurulu Flatpak uygulamalarının izinlerini (Ağ, Dosya Sistemi, Ekran, Ses, Kamera vb.) kullanıcı arayüzünden doğrudan açıp kapatabilme (`flatpak override --user`) ve varsayılana sıfırlama.
- [x] **Canlı ODRS (Open Desktop Rating Service) Yorumları & Puanlama:** `odrs.gnome.org` üzerinden 1-5 yıldızlı topluluk oylamaları, ortalama puanlar ve yerel kullanıcı yorumlarının detay sayfasında asenkron listelenmesi (`ODRSClient.py`).
- [x] **Sistem ve Flatpak Güncellemeleri:** Bekleyen Flatpak güncellemelerinin anlık algılanması (`flatpak remote-ls --updates`) ve tek tıkla topluca güncellenmesini sağlayan "Tümünü Güncelle" arayüz butonu.
- [x] **Mimarî Uyumluluk Rozetleri:** Uygulamanın `x86_64`, `aarch64` (ARM64) ve `riscv64` CPU mimari desteğinin detay sayfasında rozet olarak gösterilmesi ve "Donanımınızla Tam Uyumlu" doğrulama rozeti.
- [x] **Arch Linux & Pars Linux Uyumluluğu:** `python3-apt` zorunluluğunun kaldırılarak sistem bağımsız hale getirilmesi.
- [x] **Dinamik Kategori Gezintisi:** Sol menüdeki kategorilere tıklandığında anlık Flathub yüklemesi.
- [x] **Gelişmiş Detay Sayfası:** Ekran görüntüleri, geliştirici bilgisi, lisans, temizlenmiş açıklamalar ve eylem butonları.
- [x] **Otomatik Test Paketi:** Mixin doğrulama (`verify_mixins.py`), FlowBox kararlılık testi (`test_flowbox_stability.py`), başsız GTK testi (`test_mainwindow_headless.py`) ve ileri düzey özellikler testi (`test_advanced_features.py`).

---

## 🎯 Gelecek Yol Haritası (Faz 9 ve Sonrası)

1. **Çevrimdışı Mod İyileştirmeleri:**
   - İnternet bağlantısı kesildiğinde önbelleğe alınmış Flathub verileriyle gezinmeye devam edebilme.
2. **Kullanıcı İncelemesi Gönderme:**
   - ODRS API üzerinden doğrudan yazılım merkezi içinden yeni yorum ve puan gönderebilme.
3. **Flatpak Depo (Remote) Yönetimi:**
   - Kullanıcıların özel Flatpak repolarını (Flathub Beta, yerel depolar) arayüzden ekleyip kaldırabilmesi.

