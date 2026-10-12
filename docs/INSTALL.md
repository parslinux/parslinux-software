# Pars Linux Yazılım Merkezi Kurulum Kılavuzu (INSTALL.md)

Bu kılavuz, Pars Linux Yazılım Merkezi'nin farklı Linux dağıtımlarında nasıl kurulacağını, gerekli sistem bağımlılıklarını ve ilk çalıştırma adımlarını açıklar.

---

## 1. Sistem Gereksinimleri

- **Python:** Python 3.8 veya üzeri
- **Arayüz Kütüphanesi:** GTK+ 3.24+ ve GObject Introspection (`PyGObject`)
- **Paket Yöneticisi:** `flatpak` (v1.10 veya üzeri)
- **Ek Kütüphaneler:** Libsoup, GdkPixbuf, Pango, Polkit (`pkexec`)

---

## 2. Dağıtımlara Göre Bağımlılıkların Kurulumu

### A. Pars Linux & Arch Linux
Arch Linux veya Pars Linux tabanlı sistemlerde:

```bash
# Sistem paketlerini yükleyin
sudo pacman -S --needed python-gobject gtk3 flatpak vte3 libsoup libnotify

# Flathub deposunu ekleyin (ekli değilse)
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

### B. Debian ve Ubuntu
Debian tabanlı sistemlerde:

```bash
# Sistem paketlerini yükleyin
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    gir1.2-notify-0.7 gir1.2-soup-2.4 gir1.2-vte-2.91 flatpak

# Flathub deposunu ekleyin
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

### C. Fedora & Red Hat Ailesi
```bash
sudo dnf install -y python3-gobject gtk3 flatpak vte291 libsoup libnotify
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
```

---

## 3. Kaynak Koddan Çalıştırma

Projeyi klonlayıp derlemeye gerek kalmadan doğrudan çalıştırabilirsiniz:

```bash
# Depoyu klonlayın
git clone https://github.com/parslinux/parslinux-software.git
cd parslinux-software

# Giriş betiğine çalıştırma yetkisi verin
chmod +x parslinux-software

# Uygulamayı başlatın
./parslinux-software
```

Veya doğrudan Python ile:
```bash
python3 src/Main.py
```

---

## 4. Sisteme Yükleme ve Masaüstü Entegrasyonu

Uygulamayı sistem genelinde `/usr` dizinine yüklemek için:

```bash
# Seçenek A: setup.py ile otomatik kurulum
sudo python3 setup.py install

# Seçenek B: Dosyaları elle kopyalama
sudo cp -r src /usr/share/parslinux-software/
sudo cp -r ui /usr/share/parslinux-software/
sudo cp -r css /usr/share/parslinux-software/
sudo cp -r images /usr/share/parslinux-software/
sudo cp -r icons /usr/share/parslinux-software/
sudo cp parslinux-software.conf /etc/parslinux/parslinux-software.conf
sudo cp parslinux-software /usr/bin/parslinux-software

# Masaüstü başlatıcı ve simgeyi yükleyin
sudo cp org.parslinux.software.desktop /usr/share/applications/parslinux-software.desktop
sudo cp images/parslinux-software.svg /usr/share/icons/hicolor/scalable/apps/parslinux-software.svg
sudo update-desktop-database
```

---

## 5. Sorun Giderme

- **Hata: `ModuleNotFoundError: No module named 'gi'`**
  - Çözüm: Dağıtımınızın `python-gobject` veya `python3-gi` paketini yüklediğinizden emin olun.
- **Hata: `flatpak: command not found`**
  - Çözüm: `flatpak` paketini sisteminize kurun ve terminali yeniden başlatın.
- **Simgeler Görünmüyor:**
  - Uygulama ilk açılışta simgeleri arka planda `~/.cache/parslinux/parslinux-software/icons/app-icons` dizinine indirir. İnternet bağlantınızı kontrol edin.
