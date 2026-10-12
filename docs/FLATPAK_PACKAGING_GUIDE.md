# Flatpak Paketleme ve Geliştirici Kılavuzu (FLATPAK_PACKAGING_GUIDE.md)

Bu kılavuz; bir uygulamanın **Flatpak** formatında nasıl paketleneceğini, hangi resmi araçların kullanıldığını, araçların kaynak kod depolarını ve oluşturulan paketlerin Flathub / Pars Linux Yazılım Merkezi ekosistemine nasıl dahil edildiğini adım adım açıklar.

---

## 1. Flatpak Ekosistemi Nasıl Çalışır?

Flatpak uygulamaları üç temel yapıtaşından oluşur:

1. **Çalışma Zamanı (Runtime / Platform):** Uygulamanın çalışması için gereken temel kütüphaneleri sağlar (örn. GNOME Platform, KDE Platform veya FreeDesktop Platform).
2. **Geliştirme Kiti (SDK):** Derleyicileri, başlık dosyalarını (headers) ve araçları içerir. Sadece derleme aşamasında kullanılır.
3. **Uygulama Katmanı (Application):** Uygulamanızın kendi ikili dosyaları, veri dosyaları ve manifestosu.

```
+-------------------------------------------------------------+
|        Uygulamanız (org.parslinux.OrnekUygulama)            |
+-------------------------------------------------------------+
|    Çalışma Zamanı (org.gnome.Platform / org.kde.Platform)   |
+-------------------------------------------------------------+
|              Linux Çekirdeği & Bubblewrap Sandbox            |
+-------------------------------------------------------------+
```

---

## 2. Paket Yapmak İçin Hangi Araçlar Kullanılır?

Flatpak paketi hazırlamak için kullanılan tüm resmi ve topluluk araçları açık kaynaklıdır:

### A. Temel Derleme Aracı: `flatpak-builder`
Flatpak paketlerini derlemek, kaynak kodları indirmek, bağımlılıkları çözmek ve sanal alanda inşa etmek için kullanılan resmi komut satırı aracıdır.
* **GitHub Deposu:** [https://github.com/flatpak/flatpak-builder](https://github.com/flatpak/flatpak-builder)
* **Lisans:** LGPL-2.1

### B. Bağımlılık ve Paket Üreticileri (Generators)
Modern dillerin paket yöneticilerini (pip, cargo, npm) Flatpak manifestolarına dönüştüren yardımcı araçlar:
* **Python (PyPI):** [flatpak-pip-generator](https://github.com/flatpak/flatpak-builder-tools/tree/master/pip) - `requirements.txt` dosyasını Flatpak JSON/YAML modüllerine çevirir.
* **Rust (Cargo):** [flatpak-cargo-generator](https://github.com/flatpak/flatpak-builder-tools/tree/master/cargo) - `Cargo.lock` dosyasındaki tüm crate bağımlılıklarını indirilebilir kaynaklara dönüştürür.
* **Node.js / Electron:** [flatpak-node-generator](https://github.com/flatpak/flatpak-builder-tools/tree/master/node) - `package-lock.json` dosyalarını paketler.
* **Go:** [flatpak-go-mod-generator](https://github.com/flatpak/flatpak-builder-tools/tree/master/go-get) - `go.mod` bağımlılıklarını dönüştürür.
* **Tüm Araçların Ana Deposu:** [https://github.com/flatpak/flatpak-builder-tools](https://github.com/flatpak/flatpak-builder-tools)

### C. Grafik Arayüzlü Geliştirme Ortamları (IDE)
* **GNOME Builder:** Flatpak derleme ve hata ayıklama yetenekleri doğrudan içine entegre edilmiş resmi GNOME IDE'si.
  * **GitLab Deposu:** [https://gitlab.gnome.org/GNOME/gnome-builder](https://gitlab.gnome.org/GNOME/gnome-builder)

---

## 3. Flathub Depoları Nerede? (Kod Tabanı & Yapı)

Flathub üzerindeki her bir uygulama bağımsız bir Git deposudur:

* **Flathub GitHub Organizasyonu:** [https://github.com/flathub](https://github.com/flathub)
* **Örnek Depo İsimleri:**
  * VLC: `https://github.com/flathub/org.videolan.VLC`
  * GIMP: `https://github.com/flathub/org.gimp.GIMP`
  * Blender: `https://github.com/flathub/org.blender.Blender`
* **Flathub Resmi Dokümantasyonu:** [https://docs.flathub.org](https://docs.flathub.org)
* **Flathub Derleme Sistemi (Buildbot / CI):** [https://github.com/flathub-infra](https://github.com/flathub-infra)

---

## 4. Adım Adım Flatpak Paketi Nasıl Yapılır?

### Adım 1: Gerekli Araçları Yükleyin

**Pars Linux & Arch Linux:**
```bash
sudo pacman -S flatpak flatpak-builder
```

**Debian & Ubuntu:**
```bash
sudo apt install flatpak flatpak-builder
```

### Adım 2: SDK ve Çalışma Zamanını (Runtime) Kurun

Uygulamanız GTK tabanlıysa GNOME SDK, Qt tabanlıysa KDE SDK seçebilirsiniz:

```bash
# GNOME SDK ve Platformu
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46

# veya FreeDesktop Temel Platformu
flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
```

### Adım 3: Manifest Dosyası Hazırlayın (`org.parslinux.Notlar.yaml`)

Manifest, uygulamanızın hangi kaynaklardan nasıl derleneceğini ve hangi izinlere sahip olacağını tanımlar:

```yaml
app-id: org.parslinux.Notlar
runtime: org.gnome.Platform
runtime-version: '46'
sdk: org.gnome.Sdk
command: parslinux-notlar

finish-args:
  # Sandbox İzinleri
  - --share=ipc             # İşlemler arası iletişim
  - --socket=fallback-x11   # X11 ekran sunucusu
  - --socket=wayland        # Wayland ekran sunucusu
  - --share=network         # İnternet erişimi (gerekliyse)
  - --filesystem=home:ro    # Kullanıcı ev dizini (sadece okuma)

modules:
  - name: parslinux-notlar
    buildsystem: meson      # veya cmake, autotools, simple
    sources:
      - type: git
        url: https://github.com/parslinux/notlar.git
        tag: v1.0.0
```

### Adım 4: AppStream Üstveri (`metainfo.xml`) ve Masaüstü Dosyası

Pars Linux Yazılım Merkezi'nin uygulamanızın adını, simgesini, ekran görüntülerini ve lisansını gösterebilmesi için şu iki dosya projenizin içinde yer almalıdır:

1. **`org.parslinux.Notlar.desktop`:**
```ini
[Desktop Entry]
Name=Pars Notlar
Comment=Hızlı ve güvenli not alma aracı
Exec=parslinux-notlar
Icon=org.parslinux.Notlar
Type=Application
Categories=Office;Utility;
```

2. **`org.parslinux.Notlar.metainfo.xml`:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>org.parslinux.Notlar</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-or-later</project_license>
  <name>Pars Notlar</name>
  <summary>Modern ve sade not defteri</summary>
  <description>
    <p>Pars Notlar, günlük işlerinizi organize etmenize yardımcı olur.</p>
  </description>
  <developer_name>Pars Linux Topluluğu</developer_name>
  <url type="homepage">https://parslinux.org</url>
  <screenshots>
    <screenshot type="default">
      <image>https://parslinux.org/screenshots/notlar.png</image>
    </screenshot>
  </screenshots>
</component>
```

### Adım 5: Yerel Olarak Derleyin ve Test Edin

Tek bir komutla uygulamanızı yalıtılmış ortamda derleyip sisteme kurabilirsiniz:

```bash
# Derleyin ve kullanıcı alanına yükleyin
flatpak-builder --user --install --force-clean build-dir org.parslinux.Notlar.yaml

# Test etmek için çalıştırın
flatpak run org.parslinux.Notlar
```

---

## 5. Paketi Yayınlama ve Dağıtma

Paketinizi hazırladıktan sonra iki farklı şekilde kullanıcılarınıza ulaştırabilirsiniz:

### Seçenek A: Flathub'a Gönderme (Tüm Linux Dünyasına Ulaşma)
1. [https://github.com/flathub/flathub](https://github.com/flathub/flathub) deposunu fork edin.
2. `new-pr` dalı açarak uygulamanızın YAML manifestosunu ekleyin ve Pull Request açın.
3. Flathub botları kodunuzu `x86_64` ve `aarch64` (ARM) mimarilerinde otomatik olarak derleyecektir.
4. Onaylandığında uygulamanız Flathub'a yüklenir; **Pars Linux Yazılım Merkezi dahil tüm dünyadaki Flatpak mağazalarında anında yayınlanır!**

### Seçenek B: Kendi Özel Flatpak Deponuzu Kurma
Harici bir sunucuya bağımlı olmadan kendi kurumunuzda veya sunucunuzda yayınlamak isterseniz:
1. `ostree init --mode=archive-z2 --repo=/var/www/repo` ile yerel depo açın.
2. `flatpak-builder --repo=/var/www/repo ...` ile derlediğiniz paketi deponuza aktarın.
3. Pars Linux Yazılım Merkezi'nin "Ayarlar > Yeni Depo Ekle" ekranından deponuzun URL'sini girerek tek tıkla entegre edin! (Detaylar için: [SELF_HOSTING_GUIDE.md](SELF_HOSTING_GUIDE.md)).

---

## 6. Pars Linux Yazılım Merkezi Paketinizi Nasıl Görür?

Uygulamanız Flathub'a yüklendiği anda:
1. Flathub'ın REST API'si (`https://flathub.org/api/v2/appstream/<app-id>`) uygulamanızın AppStream meta verilerini JSON formatında yayınlar.
2. Pars Linux Yazılım Merkezi'ndeki `FlathubClient` motoru bu API'den simgenizi, açıklamalarınızı, ekran görüntülerinizi ve CPU mimarilerinizi otomatik çeker.
3. Kullanıcılar arama çubuğuna uygulamanızın adını yazdığında Meilisearch sayesinde milisaniyeler içinde bulur ve "Kur" butonuna basarak tek tıkla yükler.
