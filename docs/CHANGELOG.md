# Değişiklik Günlüğü (CHANGELOG.md)

Pars Linux Yazılım Merkezi projesindeki tüm önemli değişiklikler, yenilikler ve hata düzeltmeleri bu dosyada belgelenmektedir.

Format, [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standardını temel alır ve [Semantik Sürümleme](https://semver.org/spec/v2.0.0.html) ilkelerine uyar.

---

## [2.1.0] - 2026-10-12 (İzin Düzenleyici, ODRS Oylama, Flatpak Güncellemeleri & Mimari Rozetleri)

### 🚀 Yeni Özellikler
- **Gelişmiş İzin Düzenleyici (Permission Editor):**
  - Flatseal benzeri, kurulu Flatpak uygulamalarının izinlerini (İnternet, Ev Dizini, Kök Dizin, Wayland, X11, PulseAudio/Ses, Donanım/Kamera) arayüzdeki `Gtk.Switch` düğmeleriyle anlık olarak değiştirme (`flatpak override --user`).
  - Uygulama bazlı geçersiz kılmaları algılama, değiştirme ve tek tıkla varsayılan sandbox izinlerine geri döndürme (`reset_permissions`).
- **Canlı ODRS (Open Desktop Rating Service) Yorumları & Puanlama (`src/ODRSClient.py`):**
  - `https://odrs.gnome.org` REST API entegrasyonu ile binlerce gerçek topluluk incelemesi ve 1-5 yıldızlı puan dağılımı.
  - Ortalama yıldız puanı, toplam oy sayısı ve kullanıcının sistem diline (`user_locale`) göre önceliklendirilmiş kullanıcı yorumları.
  - Çift katmanlı TTL disk önbelleği (puanlar 2 saat, yorumlar 1 saat).
- **Sistem ve Flatpak Güncellemeleri Sekmesi:**
  - `flatpak remote-ls --updates` motoru ile bekleyen tüm Flatpak güncellemelerini anında tarama.
  - Güncelleme başlığına eklenen "Tümünü Güncelle" (Update All) butonu ile tüm bekleyen paketleri tek tıkla indirme ve kurma kuyruğuna alma.
- **Mimarî Uyumluluk Rozetleri:**
  - `FlathubClient.get_app_summary` üzerinden uygulamanın derlendiği mimarileri (`x86_64`, `aarch64`, `riscv64`) çekme ve detay sayfasında rozet olarak gösterme.
  - Sistemin mevcut mimarisiyle eşleşen uygulamalarda "✓ Donanımınızla Tam Uyumlu" rozeti sunma.

---

## [2.0.0] - 2026-10-12 (Pars Linux Fork & Flathub Entegrasyonu)

### 🚀 Yeni Özellikler & Modüler Mimari
- **Modüler Denetleyici Mimarisi (`src/controllers/`):**
  - Monolitik `MainWindow.py` yapısı 6 bağımsız mixin sınıfına bölündü:
    - `SliderMixin.py`: Hero banner vitrini, zamanlayıcı ve slayt geçişleri.
    - `ImageGalleryMixin.py`: Ekran görüntüsü galerisi, asenkron yükleme ve modal önizleme.
    - `SearchMixin.py`: Debounced Meilisearch, kategori gezintisi ve kenar çubuğu ayarlar entegrasyonu.
    - `DetailMixin.py`: AppStream detay görünümü, izin rozetleri ve eylem butonları.
    - `QueueMixin.py`: Asenkron kurulum/kaldırma kuyruğu, işlem çubukları ve bildirimler.
    - `InstalledMixin.py`: Kurulu Flatpak ve sistem uygulamaları listesi.
- **Flathub REST API v2 & Meilisearch İstemcisi (`src/FlathubClient.py`):**
  - Popüler, trend, kategori ve son güncellenen koleksiyonlar.
  - Flathub Meilisearch motoru üzerinden 250ms debounced canlı arama desteği (`/search`).
  - Çift katmanlı önbellek: Bellek içi ve kalıcı disk TTL önbelleği (`api_cache/`, dinamik listeler için 4 saat, kategoriler için 24 saat).
  - `ThreadPoolExecutor` ile simgelerin asenkron indirilmesi ve yerel önbellek (`~/.cache/parslinux/parslinux-software/icons/app-icons`).
- **Sıfır Titreme (Zero-Flicker) FlowBox Arayüzü:**
  - Kategori ve arama geçişlerinde kartların anlık kaybolması ve titremesi kökten çözüldü.
  - Kalıcı `_flowbox_app_ids` kayıt defteri ve artımlı `_append_apps_to_flowbox` ekleme mekanizması.
  - Senkron `_create_app_card_sync` kart inşası ile yarış durumları (race conditions) engellendi.
  - GTK yerel `set_filter_func` ve `set_sort_func` ile 0ms gecikmesiz filtreleme/sıralama.
- **Çift Erişimli Ayarlar Paneli:**
  - Sağ üst HeaderBar menüsüne (☰) ek olarak sol kenar çubuğunda "Yüklü Uygulamalar" altına etkileşimli "Ayarlar" satırı eklendi.
  - Erken çağrılarda ve çevrimdışı modda çökmeleri önleyen güvenli nesne koruması getirildi.
- **20 Özel FreeDesktop Vektör Kategori İkonu & Yıldız Derecelendirmeleri:**
  - FreeDesktop standartlarında 20 adet özel SVG kategori simgesi (`ps-cat-*.svg`) ve 3 adet SVG yıldız simgesi (`ps-rating-star-*.svg`) eklendi.
- **Flatpak Yönetim Motoru (`src/FlatpakManager.py`):**
  - Sistemde kurulu Flatpak uygulamalarını listeleme (`flatpak list --app`).
  - Kurma, kaldırma, güncelleme ve bağımsız oturumda başlatma (`launch`) yeteneği.
- **Otomatik Test Paketi:**
  - `scratch/verify_mixins.py`: Mixin sınıflarının metot sözleşmelerini ve kalıtım doğruluğunu denetler.
  - `scratch/test_flowbox_stability.py`: Hızlı kategori geçişlerinde kart kaybolması olmadığını doğrular.
  - `scratch/test_mainwindow_headless.py`: Başsız GTK ortamında tam pencere döngüsünü test eder.

### 🔄 İyileştirmeler ve Hata Düzeltmeleri
- **Dağıtım Bağımsızlığı:** `python3-apt` zorunluluğu kaldırılarak Arch Linux, Pars Linux ve Debian'da Flatpak arka ucu ile kesintisiz çalışma sağlandı.
- **Pango Markup Güvenliği:** Özel karakterlerin (`&`, `<`) arayüzü çökertmesi `GLib.markup_escape_text` ile engellendi.
- **HTML Temizliği:** Flathub'dan gelen zengin HTML etiketleri düzgün GTK etiket metnine dönüştürüldü.
- **Ayrıcalıklı İşlemler (`src/Actions.py`):** Flatpak işlemleri için gereksiz APT kilit beklemesi kaldırıldı.


---

## [1.0.0] - 2021-09-18 (Pardus Orijinal Sürümü)
- Pardus için geliştirilen ilk GTK+ 3 tabanlı yazılım merkezi sürümü.
- Debian APT paket arşivi ve `apps.pardus.org.tr` tar.gz metadata sunucu yapısı.
- Pardus yorum ve oylama sistemi entegrasyonu.
