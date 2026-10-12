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
| **Faz 8** | Gelişmiş İzin Yönetimi (Flatseal Benzeri) & ODRS Oylama | 🔄 Planlanıyor |

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
- [x] **Arch Linux & Pars Linux Uyumluluğu:** `python3-apt` zorunluluğunun kaldırılarak sistem bağımsız hale getirilmesi.
- [x] **Dinamik Kategori Gezintisi:** Sol menüdeki kategorilere tıklandığında anlık Flathub yüklemesi.
- [x] **Gelişmiş Detay Sayfası:** Ekran görüntüleri, geliştirici bilgisi, lisans, temizlenmiş açıklamalar ve eylem butonları.
- [x] **Otomatik Test Paketi:** Mixin doğrulama (`verify_mixins.py`), FlowBox kararlılık testi (`test_flowbox_stability.py`) ve başsız GTK testi (`test_mainwindow_headless.py`).

---

## 🎯 Gelecek Yol Haritası (Faz 8 ve Sonrası)

1. **Gelişmiş İzin Düzenleyici (Permission Editor):**
   - Flatseal benzeri, kurulu Flatpak uygulamalarının izinlerini (Ağ, Dosya Sistemi, Kamera, Mikrofon vb.) kullanıcı arayüzünden doğrudan açıp kapatabilme.
2. **Kullanıcı Yorumları ve Değerlendirmeler:**
   - ODRS (Open Desktop Rating Service) veya Flathub topluluk oylamalarının detay sayfasına entegrasyonu.
3. **Sistem ve Flatpak Güncellemeleri Sekmesi:**
   - Bekleyen Flatpak güncellemelerinin tek tıkla topluca güncellenmesini sağlayan arayüz paneli.
4. **Mimarî Rozetleri:**
   - Uygulamanın `x86_64`, `aarch64` (ARM) ve RISC-V desteğinin detay sayfasında rozet olarak belirtilmesi.

