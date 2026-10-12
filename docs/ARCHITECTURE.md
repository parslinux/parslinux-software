# Pars Linux Yazılım Merkezi Mimarisi (ARCHITECTURE.md)

Bu belge, Pars Linux Yazılım Merkezi'nin (Pars Linux Software Center) iç mimarisini, bileşenler arasındaki veri akışını ve Flathub/Flatpak entegrasyon modelini detaylandırır.

---

## 1. Genel Mimari Bakış

Uygulama, eski ve hantal `.tar.gz` metadata sunucu modeli yerine, modern ve dağıtımdan bağımsız **Flathub v2 REST API**, yerel **Flatpak CLI** motoru ve **Modüler Mixin Denetleyici** mimarisi üzerine kurgulanmıştır.

```
+-----------------------------------------------------------------------------------+
|                             GTK+ 3 / Glade Arayüz Katmanı                         |
|                                    (MainWindow.py)                                |
|  +-----------------------+------------------------+----------------------------+  |
|  |     SliderMixin       |   ImageGalleryMixin    |        SearchMixin         |  |
|  |  (Vitrin & Geçişler)  | (Ekran Görüntüleri)    | (Meilisearch, Kategori/Ayar)| |
|  +-----------------------+------------------------+----------------------------+  |
|  |     DetailMixin       |       QueueMixin       |       InstalledMixin       |  |
|  | (Uygulama Detay Sayfası|  (İşlem Kuyruğu/Durum) | (Yüklü Flatpak & Sistem)   |  |
|  +-----------------------+------------------------+----------------------------+  |
+--------------------------+------------------------+-------------------------------+
                           |                        |
                           v                        v
+------------------------------------------+   +------------------------------------+
|          Katalog ve Ağ Katmanı           |   |     Paket ve Çalıştırma Katmanı    |
|   - Server.py (Flathub Router)           |   |   - FlatpakManager.py              |
|   - FlathubClient.py (REST API & Cache)  |   |   - Package.py (Flatpak/APT Bridge)|
|   - AppImage.py (Asenkron Görsel Akışı)  |   |   - Actions.py (pkexec / CLI Alt İş)|
+--------------------------+---------------+   +-----------------+------------------+
                           |                                     |
                           v                                     v
+------------------------------------------+   +------------------------------------+
|         Harici Flathub v2 API            |   |        Yerel Sistem Flatpak        |
|       https://flathub.org/api/v2         |   |     /usr/bin/flatpak & Remotes     |
|   - /collection/popular (TTL: 4s)        |   |   - flatpak list --app             |
|   - /collection/category/{cat} (TTL: 24s)|   |   - flatpak install -y             |
|   - /search (Meilisearch, 250ms Debounce)|   |   - flatpak uninstall -y           |
|   - /appstream/{app_id}                  |   |   - flatpak run {app_id}           |
+------------------------------------------+   +------------------------------------+
```

---

## 2. Temel Modüller ve Sorumlulukları

### A. Katalog ve Ağ Katmanı

1. **`src/FlathubClient.py`**:
   - Flathub REST API v2 (`https://flathub.org/api/v2`) ile HTTP/JSON haberleşmesini yürütür.
   - **Çift Katmanlı Önbellek (2-Tier Cache):**
     - *Bellek İçi Önbellek:* Tek oturum içinde aynı uç noktalara tekrarlanan çağrıları mikro-saniyeler içinde karşılar.
     - *Kalıcı Disk TTL Önbelleği:* `~/.cache/parslinux/parslinux-software/api_cache/` dizininde JSON yanıtlarını TTL süresiyle saklar. Popüler/trend yayınları için 4 saat, statik kategoriler için 24 saat geçerlilik süresi (TTL) uygulanır.
   - **Canlı Arama ve Debouncing:** Arama girdisindeki her harfte API boğulmasını önlemek için 250 milisaniyelik zamanlayıcı (`search_timeout_id`) kullanılarak sorgular Meilisearch'e iletilir.
   - **Paralel İkon Ön İndirme:** `ThreadPoolExecutor` havuzu (8 iş parçacığı) kullanarak uygulama simgelerini yerel dosya sistemine (`~/.cache/parslinux/parslinux-software/icons/app-icons`) asenkron olarak indirir.

2. **`src/Server.py`**:
   - Sunucu soyutlama ve veri köprüsü katmanıdır.
   - Flathub modunda (`backend = flathub`), `FlathubClient` verilerini arayüzün beklediği `apps.json`, `cats.json` ve `home.json` veri yapılarına dönüştürerek yerel önbelleğe yazar.

4. **`src/ODRSClient.py`**:
   - `https://odrs.gnome.org` REST API'si üzerinden Open Desktop Rating Service oylama ve kullanıcı yorumlarını çeker.
   - 1-5 yıldız oylama dağılımını, ağırlıklı ortalama puanı ve toplam oy sayısını hesaplar.
   - Kullanıcının sistem diline (`user_locale`) göre filtrelenmiş ve sıralanmış gerçek topluluk incelemelerini asenkron (`fetch_feedback_async`) olarak sunar.
   - Puanlar için 2 saat, yorumlar için 1 saat yerel TTL disk önbelleği uygular.

---

### B. Paket Yönetim ve Çalıştırma Katmanı

1. **`src/FlatpakManager.py`**:
   - Sistemdeki `/usr/bin/flatpak` motorunu yönetir.
   - Sistem veya kullanıcı alanında kurulu Flatpak uygulamalarını (`flatpak list --app`) tarar ve `_installed_cache` sözlüğünde tutar.
   - **Gelişmiş İzin Yönetimi (Flatseal Benzeri):** `~/.local/share/flatpak/overrides/<app_id>` dosyasını okuyup ayrıştırarak ağ, ev dizini, dosya sistemi, ekran sunucusu, ses ve donanım izinlerini raporlar; `flatpak override --user` ile değiştirir veya sıfırlar.
   - **Güncelleme Motoru:** `flatpak remote-ls --updates` ile bekleyen güncellemeleri tespit eder; `update_all` ile tüm uygulamaları topluca günceller.
   - Kurulu uygulamaları masaüstü ortamında `start_new_session=True` ile bağımsız bir süreç olarak başlatır (`launch`).

2. **`src/Package.py`**:
   - Uygulamanın kurulu olup olmadığını (`isinstalled`), sürümünü, boyutunu ve güncellenebilirliğini sorgulayan soyutlama katmanıdır.
   - `FlatpakManager` ile entegre çalışarak bekleyen güncellemeleri (`get_upgradable_apps`, `is_upgradable`) köprüler.
   - Dağıtımdan bağımsız olarak Arch Linux, Pars Linux ve Debian'da kesintisiz çalışma sağlar.

3. **`src/Actions.py`**:
   - Polkit ayrıcalıklı işlemlerini ve paket kurma/kaldırma alt süreçlerini koordine eder.

---

### C. Modüler Arayüz Denetleyicileri (`src/controllers/`)

Monolitik `MainWindow.py` karmaşıklığını engellemek için tüm arayüz mantığı 6 odaklanmış mixin denetleyicisine bölünmüştür:

1. **`SliderMixin.py`**:
   - Ana sayfa hero slider vitrinini yönetir.
   - 6 saniyelik otomatik kayma döngüsü (`GLib.timeout_add`), sol/sağ buton navigasyonu ve aktif nokta göstergelerini (dot indicators) günceller.

2. **`ImageGalleryMixin.py`**:
   - Uygulama detay sayfasındaki ekran görüntüsü galerisini yönetir.
   - Küçük resimlerin arka planda asenkron akışla yüklenmesi, seçilen görselin tam boyutta gösterilmesi ve tam ekran modal önizleme penceresini yönetir.

3. **`SearchMixin.py`**:
   - Arama çubuğu girdisini 250ms debouncing ile Flathub Meilisearch'e iletir.
   - Sol menü kategori geçişlerini, kategori ikon eşlemelerini ve GTK yerel filtre/sıralama işlemlerini yürütür.
   - Sol kenar çubuğundaki "Ayarlar" satırı tıklandığında ayarlar iletişim kutusunu güvenle açar.

4. **`DetailMixin.py`**:
   - Bir uygulama kartına tıklandığında açılan detay sayfasını yönetir.
   - **Mimarî Rozetleri:** `FlathubClient.get_app_summary` ile `x86_64`, `aarch64` ve `riscv64` donanım desteği rozetlerini ve sistem uyumluluk bildirimini gösterir.
   - **Gelişmiş İzin Düzenleyici:** Kurulu uygulamalar için açılır-kapanır Flatseal benzeri interaktif izin düzenleyici panelini oluşturur.
   - **Canlı ODRS Yorumları:** Yıldız dağılımlarını, ortalama puanı ve topluluk incelemelerini asenkron olarak yerleştirir.
   - AppStream açıklamalarını Pango uyumlu temiz metne dönüştürür; geliştirici, lisans, boyut ve indirme bilgilerini yerleştirir.

5. **`QueueMixin.py`**:
   - Eşzamanlı veya ardışık indirme/kurulum görevlerini yönetir.
   - İşlem çubukları (progress bar), dönen yükleme göstergeleri (spinner) ve masaüstü bildirimlerini (`notify-send` / `Notify.Notification`) kontrol eder.

6. **`InstalledMixin.py`**:
   - Sistemde kurulu olan Flatpak ve yerel paketlerin listelendiği görünümü yönetir.
   - Bekleyen güncellemeleri algılar ve "Tümünü Güncelle" (Update All) butonu ile tek tıkla toplu güncelleme sürecini başlatır.
   - Tek tıkla kaldırma veya çalıştırma işlemlerini listeler.

---

## 3. Sıfır Titreme (Zero-Flicker) ve Artımlı FlowBox Mimarisi

Uygulama listelerinin gösterildiği `ui_parslinuxapps_flowbox` bileşeninde kartların anlık kaybolması ve titremesi sorununu çözmek için şu mimari uygulanmıştır:

1. **Kalıcı Kart Kayıt Defteri (`_flowbox_app_ids`):**
   - Kategori veya arama değiştiğinde mevcut widget'lar `remove()` ile yok edilmez.
   - `self._flowbox_app_ids = set()` kümesi ile FlowBox'a daha önce eklenmiş tüm uygulama kimlikleri hafızada tutulur.

2. **Senkron Kart İnşası (`_create_app_card_sync`):**
   - Her bir kart widget'ı (ikon, başlık, özet ve buton) ana döngüde senkron olarak oluşturulur.
   - Böylece asenkron `GLib.idle_add` gecikmelerinden kaynaklanan yarış durumları (race conditions) ve kartların sonradan parça parça belirmesi tamamen engellenir.

3. **Artımlı Ekleme (`_append_apps_to_flowbox`):**
   - Yeni bir kategori veya arama sonucu geldiğinde, yalnızca daha önce FlowBox'a eklenmemiş olan yeni uygulamalar için widget üretilir ve eklenir.

4. **Yerel GTK Filtreleme ve Sıralama:**
   - FlowBox için tanımlı `parslinuxapps_filter_function` ve `parslinuxapps_sort_func` fonksiyonları kullanılır.
   - Kategori veya arama metni değiştiğinde sadece `ui_parslinuxapps_flowbox.invalidate_filter()` ve `invalidate_sort()` çağrılır.
   - GTK, C düzeyinde milisaniyeler içinde görünürlüğü günceller; sıfır titreme ve anlık geçiş sağlanır.

---

## 4. Çift Erişimli Ayarlar ve İkon Sistemi

### A. Çift Erişimli Ayarlar Paneli
Kullanıcı deneyimini maksimize etmek amacıyla ayarlar penceresi iki farklı noktadan erişilebilir kılınmıştır:
- **Sağ Üst Başlık Çubuğu Menüsü:** Hamburger butonu (☰) menüsündeki "Ayarlar" seçeneği (`on_menu_settings_clicked`).
- **Sol Gezinme Çubuğu:** "Yüklü Uygulamalar" grubunun altındaki etkileşimli "Ayarlar" satırı (`SearchMixin.py` -> `on_ui_leftinstalled_listbox_row_activated`).
- *Güvenlik Koruması:* Ayarlar penceresi çağrıldığında sunucu veya paket katmanı henüz ilklendirilmemişse çökmeyi önleyen güvenli null-kontrolü uygulanır.

### B. FreeDesktop Vektör Kategori İkonları
Pars Linux Yazılım Merkezi için 20 adet özel SVG kategori simgesi ve 3 adet SVG derecelendirme yıldızı tasarlanmıştır:
- Simgeler `icons/hicolor/scalable/categories/ps-cat-*.svg` ve `icons/hicolor/scalable/status/ps-rating-star-*.svg` altında yer alır.
- Yüksek DPI ekranlarda keskin ve modern bir görünüm sunar.

---

## 5. Eşzamanlılık ve Güvenlik İlkeleri

- **Ana Döngü Güvenliği:** GTK iş parçacığı güvenli değildir. Arka plandan yapılan tüm arayüz çağrıları `GLib.idle_add` ile iletilir.
- **Pango Markup Koruması:** Webden gelen tüm metinler Pango çökmelerine karşı `GLib.markup_escape_text()` ile sanitize edilir.
- **Güvenli Paket Başlatma:** Flatpak uygulamaları ana yazılım merkezinin sürecinden bağımsız (`start_new_session=True`) başlatılır.

