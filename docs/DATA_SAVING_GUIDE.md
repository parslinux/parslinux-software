# Veri ve Önbellek Yönetimi Rehberi (DATA_SAVING_GUIDE.md)

Bu kılavuz, Pars Linux Yazılım Merkezi'nin internet bant genişliğini nasıl optimize ettiğini, yerel disk alanını nasıl kullandığını ve önbellek temizleme yöntemlerini açıklar.

---

## 1. Veri ve Dosya Konumları

Uygulama, XDG Temel Dizin Standartlarına (XDG Base Directory Specification) tam uyumludur:

| Dizin | Konum | İçerik |
| :--- | :--- | :--- |
| **Önbellek (Cache)** | `~/.cache/parslinux/parslinux-software/` | İndirilen uygulama simgeleri, `apps.json`, `cats.json`, `home.json` |
| **API Yanıt Önbelleği** | `~/.cache/parslinux/parslinux-software/api_cache/` | Flathub koleksiyon ve kategori JSON yanıtları (TTL'li) |
| **Simgeler** | `~/.cache/parslinux/parslinux-software/icons/app-icons/` | Flathub'dan önbelleğe alınan PNG ve SVG simgeleri |
| **Kullanıcı Ayarları** | `~/.config/parslinux/parslinux-software/settings.ini` | Animasyon tercihleri, tema, son güncelleme zamanı |
| **Sistem Ayarları** | `/etc/parslinux/parslinux-software.conf` | Sunucu URL'si, arka uç tipi, zaman aşımları |

---

## 2. Bant Genişliği ve Veri Tasarrufu Stratejileri

### A. Çift Katmanlı API Önbelleği ve TTL Yönetimi
- **Bellek İçi Önbellek:** Uygulama açık olduğu sürece aynı API istekleri anında bellekten döner.
- **Kalıcı Disk Önbelleği (`api_cache/`):** API yanıtları diskte saklanır:
  - *Dinamik Listeler:* Popüler, trend ve son güncellenen akışlar için 4 saatlik TTL (Time-To-Live).
  - *Kategori Listeleri:* Statik kategori koleksiyonları için 24 saatlik TTL.
- TTL süresi dolana kadar Flathub sunucusuna yeni HTTP isteği gönderilmez; bu sayede veri tüketimi sıfıra indirilir.

### B. Canlı Arama Debouncing (250ms)
- Arama çubuğuna yazılan her karakterde anında istek atmak yerine 250 milisaniyelik gecikme sayacı (`search_timeout_id`) kullanılır.
- Kullanıcı yazmayı bitirene kadar sorgu bekletilir; gereksiz onlarca arama isteği engellenir.

### C. Kalıcı Simge Önbelleği
- Uygulama simgeleri ilk kez çekildiğinde diske kaydedilir (`get_icon_local_path`).
- Sonraki açılışlarda veya sayfa geçişlerinde simge tekrar internetten indirilmez; doğrudan yerel diskten yüklenir. Bu sayede yüzlerce uygulamanın simgesi için tekrar tekrar ağ trafiği harcanmaz.

### D. Flatpak OSTree Katman Paylaşımı
- Flatpak, OSTree tabanlı bir içerik adreslemeli dosya sistemi kullanır.
- Örneğin iki farklı uygulama aynı GNOME veya KDE çalışma zamanını (runtime) kullanıyorsa, paylaşılan dosyalar diskte tek bir kez saklanır; tekrarlı indirme ve disk tüketimi önlenir.

---

## 3. Önbellek ve Disk Alanı Temizleme

Zamanla biriken geçici verileri temizlemek veya sıfırdan taze bir katalog indirmek için:

### A. Yazılım Merkezi Önbelleğini Temizleme:
```bash
# Simge, API ve katalog önbelleğini silin
rm -rf ~/.cache/parslinux/parslinux-software/
```
*Not:* Uygulama bir sonraki açılışında ihtiyaç duyduğu güncel katalog ve simgeleri otomatik olarak yeniden oluşturacaktır.

### B. Kullanılmayan Flatpak Bağımlılıklarını Temizleme:
Kaldırılan uygulamalardan arta kalan gereksiz runtime paketlerini temizleyerek gigabaytlarca disk alanı kazanabilirsiniz:
```bash
flatpak uninstall --unused -y
```

