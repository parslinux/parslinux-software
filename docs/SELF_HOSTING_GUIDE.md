# Pars Linux Yazılım Merkezi Özel Sunucu ve Barındırma Kılavuzu (SELF_HOSTING_GUIDE.md)

Bu kılavuz, Pars Linux Yazılım Merkezi'ni kurumsal ağlarda, internet erişimi kısıtlı (air-gapped) ortamlarda, okullarda veya özel bir Flatpak deposuyla kendi sunucunuz üzerinden nasıl çalıştırabileceğinizi açıklar.

---

## 1. Neden Kendi Sunucunuzu Barındırmalısınız?

- **Kurumsal İhtiyaçlar:** Şirket içi geliştirilen özel yazılımların merkezi bir mağazadan dağıtılması.
- **Güvenlik ve İzolasyon:** Dış internete kapalı ağlarda yerel ağ üzerinden Flatpak dağıtımı.
- **Küratörlük:** Sadece onaylanmış, test edilmiş belirli uygulamaların kullanıcılara sunulması.
- **Bant Genişliği Tasarrufu:** Kurum ağında tek bir sunucu üzerinden yerel önbellek/ayna (mirror) sunulması.

---

## 2. Yazılım Merkezi Yapılandırması (`parslinux-software.conf`)

Uygulamanın bağlandığı sunucu adresi ve çalışma modu `parslinux-software.conf` üzerinden kontrol edilir:

```ini
[DEFAULT]
server = https://yazilim.kurumunuz.local/api/v2
backend = flathub
connectiontimeout = 5
repo = 1
myapps = 1
```

- `server`: Kendi REST API sunucunuzun veya ayna adresinizin kök URL'si.
- `backend`: `flathub` (Flathub v2 REST uyumlu) veya `custom`.

---

## 3. Basit Bir Katalog Sunucusu Kurulumu (Nginx & Statik JSON)

Flathub API v2 yapısı statik JSON dosyalarıyla kolayca taklit edilebilir.

### Dizin Yapısı:
```
/var/www/software-center/
├── api/
│   └── v2/
│       ├── collection/
│       │   ├── popular.json
│       │   ├── trending.json
│       │   └── category/
│       │       ├── development.json
│       │       ├── office.json
│       │       └── utility.json
│       └── appstream/
│           ├── org.kurum.uygulama1.json
│           └── org.kurum.uygulama2.json
```

### Örnek `popular.json` Yapısı:
```json
{
  "hits": [
    {
      "app_id": "com.kurum.muhasebe",
      "name": "Kurumsal Muhasebe",
      "summary": "İç ağ muhasebe yönetim yazılımı",
      "icon": "https://yazilim.kurumunuz.local/icons/muhasebe.png",
      "main_categories": "office",
      "project_license": "Proprietary",
      "developer_name": "Kurum Bilgi İşlem"
    }
  ]
}
```

### Nginx Yapılandırması:
```nginx
server {
    listen 80;
    server_name yazilim.kurumunuz.local;
    root /var/www/software-center;

    location /api/v2/collection/popular {
        try_files $uri /api/v2/collection/popular.json;
    }

    location /api/v2/collection/category/ {
        try_files $uri.json =404;
    }

    location /api/v2/appstream/ {
        try_files $uri.json =404;
    }
}
```

---

## 4. Özel Flatpak OSTree Deposu Oluşturma

Uygulamaların yerel ağdan kurulabilmesi için standart bir Flatpak deposu kurulabilir:

```bash
# 1. Yeni bir OSTree deposu başlatın
ostree init --mode=archive-z2 --repo=/var/www/flatpak-repo

# 2. Paketi depoya aktarın
flatpak build-export /var/www/flatpak-repo /path/to/build-dir

# 3. Depo özetini (summary) güncelleyin
flatpak build-update-repo /var/www/flatpak-repo

# 4. İstemci istemcide depoyu tanımlayın
flatpak remote-add --if-not-exists kurum-repo http://yazilim.kurumunuz.local/flatpak-repo
```

İstemci bilgisayarlar `flatpak install kurum-repo com.kurum.muhasebe` komutuyla veya Pars Linux Yazılım Merkezi üzerinden tek tıkla uygulamayı kurabilir.
