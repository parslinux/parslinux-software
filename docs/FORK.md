# Çatallanma ve Yeniden Yapılandırma Belgesi (FORK.md)

Bu belge, **Pars Linux Yazılım Merkezi** projesinin kökenini, çatallanma (fork) gerekçelerini, orijinal depodan devralınan temel mirası ve Pars Linux ekibi tarafından gerçekleştirilen kapsamlı mimari dönüşümü açıklar.

---

## 1. Köken ve Açık Kaynak Mirası (Upstream Heritage)

- **Orijinal Proje:** Pardus Yazılım Merkezi (`pardus-software`)
- **Orijinal Geliştirici:** TÜBİTAK ULAKBİM & Fatih Altun (ve açık kaynak topluluk katkıcıları)
- **Orijinal Lisans:** GNU Genel Kamu Lisansı sürüm 3 (GPLv3)
- **Çatallanma Tarihi:** Ekim 2026

> [!NOTE]
> **GPLv3 Lisans Uyumluluğu (Madde 5a):**
> GNU GPLv3 lisansının gereklilikleri doğrultusunda, orijinal projenin telif ve emek sahiplerine saygı duyulmakta; kod tabanında yapılan tüm değişiklikler, yeniden yapılandırmalar ve eklenen yeni özellikler bu belgede açıkça beyan edilmektedir.

---

## 2. Neden Çatallandı? (Çatallanma Motivasyonu)

Orijinal yazılım merkezi, belirli bir dağıtıma (Debian/Pardus) ve kurumun kendi barındırdığı statik metadata arşivine (`apps.pardus.org.tr`) sıkı sıkıya bağlı olarak tasarlanmıştı. 

Pars Linux projesinin ihtiyaçları doğrultusunda şu temel sınırlamalar ortaya çıkmıştır:

1. **Dağıtım Bağımlılığı:** Eski yapı yalnızca `apt`, `dpkg` ve Debian depolarıyla çalışabiliyordu. Pars Linux, Arch Linux ve diğer bağımsız dağıtımlarda çalışamaz durumdaydı.
2. **Merkezi ve Statik Sunucu Modeli:** Uygulama meta verileri her açılışta sunucudan büyük `.tar.gz` paketleri halinde indirilip açılıyordu; arama ve listeleme statik paket dosyalarıyla sınırlıydı.
3. **Monolitik Kod Tabanı:** Arayüz mantığı, indirme işlemleri, arama, ayarlar ve vitrin akışı 2500+ satırlık tek bir monolitik dosya (`MainWindow.py`) içinde toplanmıştı.
4. **Arayüz Titremesi (Flickering):** Kategori veya arama değişimlerinde FlowBox içindeki tüm bileşenler yok edilip yeniden üretildiği için ciddi titremeler ve donmalar yaşanıyordu.
5. **Modern Evrensel Paket Desteğinin Eksikliği:** Flatpak, yalıtımlı çalıştırma (sandboxing), izin yönetimi ve modern paket ekosistemi entegrasyonu bulunmuyordu.

Bu nedenlerle Pars Linux ekibi, projeyi çatallayarak baştan aşağı yeniden yapılandırma ve modernleştirme kararı almıştır.

---

## 3. Neler Değişti? (Karşılaştırmalı Özet)

| Alan | Orijinal Depo (`pardus-software`) | Pars Linux Yazılım Merkezi (`parslinux-software`) |
| :--- | :--- | :--- |
| **Paket Yönetim Motoru** | Sadece Debian APT / dpkg | **Evrensel Flatpak CLI** (Tüm Linux dağıtımlarıyla tam uyumlu) |
| **Uygulama Kataloğu** | `apps.pardus.org.tr` (Statik tar.gz) | **Flathub REST API v2** (Binlerce güncel evrensel uygulama) |
| **Arama Motoru** | Yerel paket adı eşleştirmesi | **Flathub Meilisearch** (250ms debounced anlık canlı arama) |
| **Kod Mimarisi** | Monolitik tek dosya (`MainWindow.py`) | **6 Modüler Mixin Denetleyicisi** (`src/controllers/`) |
| **FlowBox Performansı** | Kartları silip baştan kurma (titreme) | **0ms Sıfır Titreme (Zero-Flicker)** (Senkron inşaa, kalıcı ID kaydı, yerel filtre) |
| **Önbellek Stratejisi** | Tek seferlik arşiv indirme | **2-Tier TTL Önbellek** (Bellek içi + 4s/24s disk JSON TTL) |
| **İzin Yönetimi** | Yok (Sistem geneli kök yetkisi) | **Gelişmiş İzin Düzenleyici** (Flatseal benzeri kullanıcı override yönetimi) |
| **Topluluk Yorumları** | Yerel sunucu yorum sistemi | **Canlı ODRS (GNOME)** (Topluluk incelemeleri ve oylama gönderme) |
| **Depo Yönetimi** | Sabit APT kaynakları | **Flatpak Remote Yöneticisi** (Flathub Beta, GNOME Nightly, özel repo ekleme) |
| **Çevrimdışı Çalışma** | Ağ yoksa çökme veya boş ekran | **Gelişmiş Çevrimdışı Mod** (Yerel önbellek araması, InfoBar uyarısı) |
| **Sıralama Yeteneği** | Sabit liste | **4 Modlu Çoklu Kriter Sıralaması** (A-Z, İndirme, Trend, Tarih) |
| **Masaüstü Bildirimleri** | Pasif bilgilendirme metni | **İnteraktif Eylemler** (Bildirimden tek tıkla "Uygulamayı Başlat") |
| **Girdi / Jest Desteği** | Yalnızca fare tıklaması | **Wayland & Touchpad Jestleri** (Dokunmatik ekran swipe & 2 parmak kaydırma) |
| **İkon Teması** | Karışık bitmap/harici simgeler | **20 Özel FreeDesktop SVG Simgesi** ve SVG yıldız puanları |
| **Mimarî Uyumluluk** | Debian arch tespiti | **Detay Sayfasında x86_64, aarch64, riscv64 Rozetleri** |

---

## 4. Gerçekleştirilen Başlıca Yenilikler ve İyileştirmeler

### A. Modüler Mimari Dönüşümü (`src/controllers/`)
2500+ satırlık monolitik yapı şu odaklanmış denetleyici sınıflarına ayrılmıştır:
- `SliderMixin.py`: Hero afiş vitrini, zamanlayıcılar ve jest algılama.
- `ImageGalleryMixin.py`: Ekran görüntüleri, asenkron görsel yükleme ve modal önizleme.
- `SearchMixin.py`: Debounced arama, kategori gezintisi ve kenar çubuğu ayarları.
- `DetailMixin.py`: AppStream detayları, izin düzenleyici ve mimari rozetleri.
- `QueueMixin.py`: Asenkron kurulum kuyruğu, işlem çubukları ve bildirimler.
- `InstalledMixin.py`: Yüklü uygulamalar, güncelleme taraması ve toplu güncelleme paneli.

### B. Orijinal Depoda Hiç Olmayan İleri Seviye Özellikler
1. **İzin Düzenleyici (Permission Editor):** Kurulu uygulamaların dosya sistemi, ağ, ses, Wayland/X11 ve donanım izinlerini GUI üzerinden değiştirme (`flatpak override --user`) ve sıfırlama.
2. **Canlı ODRS (Open Desktop Rating Service) & İnceleme Gönderme:** `odrs.gnome.org` REST API entegrasyonu ile oylama dağılımı, yorumlar ve donanım hash'li güvenli inceleme formu.
3. **Flatpak Depo (Remote) Yönetimi:** Ayarlar ekranında depo ekleme (Flathub Beta, GNOME Nightly, Custom), kaldırma ve etkinleştirme.
4. **Çevrimdışı Mod (Offline Mode):** İnternet yokken diskteki önbellekle başlama, yerel arama ve durum bildiren `Gtk.InfoBar`.
5. **Çoklu Sıralama:** Kategori ve arama ekranlarında 0ms gecikmeli dinamik FlowBox sıralaması.
6. **Masaüstü Bildirim Eylemleri:** Kurulum tamamlandığında bildirim üzerinden doğrudan uygulamayı başlatma butonu.
7. **Wayland & Touchpad Jestleri:** `Gtk.GestureSwipe` ve `scroll-event` ile pürüzsüz dokunmatik vitrin geçişleri.
8. **Modern Sistem Koruması:** `Soup 2.4` / `Soup 3` ayrışma koruması, Pango etiket kaçırma (`GLib.markup_escape_text`) ve HTML sanitize mekanizmaları ile sıfır çökme garantisi.

---

## 5. Teşekkür ve İletişim

Pars Linux Yazılım Merkezi, açık kaynak yazılımın ve GNU felsefesinin sunduğu özgürlük sayesinde hayata geçmiştir. Projenin ilk temellerini atan orijinal Pardus Yazılım Merkezi ekibine ve Fatih Altun'a teşekkür ederiz.

Proje hakkındaki soru, öneri ve katkılarınız için:
- **Web Sitesi:** [https://parslinux.org](https://parslinux.org)
- **Kaynak Kod Deposu:** [https://github.com/parslinux/parslinux-software](https://github.com/parslinux/parslinux-software)
- **İletişim:** `dev@parslinux.org`
