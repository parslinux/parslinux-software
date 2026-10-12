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
| **Faz 9** | Çevrimdışı Mod İyileştirmeleri, ODRS Yorum Gönderme & Flatpak Depo Yönetimi | ✅ Tamamlandı (%100) |
| **Faz 10** | Çoklu Sıralama, Masaüstü Bildirim Eylemleri & Dokunmatik Jestler | ✅ Tamamlandı (%100) |

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
- [x] **ODRS İnceleme & Puan Gönderme:** Kullanıcıların detay sayfasından doğrudan puan (1-5 yıldız), başlık ve yorum yazıp ODRS sunucusuna anonim donanım hash'i ile gönderebilmesi (`ODRSClient.submit_review_async`).
- [x] **Sistem ve Flatpak Güncellemeleri:** Bekleyen Flatpak güncellemelerinin anlık algılanması (`flatpak remote-ls --updates`) ve tek tıkla topluca güncellenmesini sağlayan "Tümünü Güncelle" arayüz butonu.
- [x] **Mimarî Uyumluluk Rozetleri:** Uygulamanın `x86_64`, `aarch64` (ARM64) ve `riscv64` CPU mimari desteğinin detay sayfasında rozet olarak gösterilmesi ve "Donanımınızla Tam Uyumlu" doğrulama rozeti.
- [x] **Gelişmiş Çevrimdışı Mod (Offline Mode):** Ağ bağlantısı kesildiğinde diskteki `api_cache/` verileriyle sorunsuz çalışma, yerel arama fallback'i, ana ekranda `Gtk.InfoBar` çevrimdışı uyarı çubuğu ve kurulu uygulamalara kesintisiz erişim.
- [x] **Flatpak Depo (Remote) Yönetimi:** Ayarlar ekranında sistem ve kullanıcı Flatpak depolarının listelenmesi, hazır şablonlar (Flathub Beta, GNOME Nightly, Resmi Flathub) veya özel adresle yeni depo ekleme ve güvenli depo kaldırma/devre dışı bırakma.
- [x] **Çoklu Kriter Sıralama Seçicisi:** Kategori ve arama ekranlarında "Ada Göre (A-Z)", "En Çok İndirilenler", "Popülerliğe Göre" ve "Son Eklenenler" seçenekleriyle anlık GTK FlowBox sıralaması.
- [x] **Masaüstü Bildirim Eylemleri:** Uygulama kurulumu veya güncellemesi bittiğinde masaüstü bildiriminde çıkan interaktif "Uygulamayı Başlat" (Launch) butonu.
- [x] **Wayland Dokunmatik ve Touchpad Jestleri:** Vitrin slider alanında parmakla kaydırma (`Gtk.GestureSwipe`) ve touchpad iki parmak yatay kaydırma (`scroll-event`) ile akıcı geçişler.
- [x] **Arch Linux & Pars Linux Uyumluluğu:** `python3-apt` zorunluluğunun kaldırılarak sistem bağımsız hale getirilmesi.
- [x] **Dinamik Kategori Gezintisi:** Sol menüdeki kategorilere tıklandığında anlık Flathub yüklemesi.
- [x] **Gelişmiş Detay Sayfası:** Ekran görüntüleri, geliştirici bilgisi, lisans, temizlenmiş açıklamalar ve eylem butonları.
- [x] **Kapsamlı Test Paketi:** Mixin doğrulama (`verify_mixins.py`), FlowBox kararlılık testi (`test_flowbox_stability.py`), başsız GTK testi (`test_mainwindow_headless.py`), ileri düzey özellikler testi (`test_advanced_features.py`), Faz 9 testleri (`test_phase9_features.py`) ve Faz 10 testleri (`test_phase10_features.py`).

---

## 🎯 Gelecek Vizyonu & Bakım

Tüm 10 geliştirme fazı %100 başarıyla tamamlanmış olup kod tabanı modern, kararlı, yüksek performanslı ve geleceğe hazır durumdadır. İlerleyen süreçte Flathub API güncellemeleri ve yeni GNOME/Wayland standartları periyodik olarak takip edilecektir.

