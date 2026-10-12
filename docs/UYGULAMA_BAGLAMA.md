# Uygulama Bağlama ve Yayınlama Rehberi (UYGULAMA_BAGLAMA.md)

Bu rehber, bağımsız bir yazılım geliştiricisinin kendi uygulamasını Pars Linux Yazılım Merkezi'nde nasıl yayınlayabileceğini, Flathub entegrasyonunu ve gerekli AppStream standartlarını açıklar.

---

## 1. Genel Yayınlama Mantığı

Pars Linux Yazılım Merkezi, uygulamaları doğrudan **Flathub** kataloğundan çeker. Dolayısıyla uygulamanızı Flathub'da yayınladığınız anda, Pars Linux kullanıcıları uygulamanızı mağazada görebilir, arayabilir ve tek tıkla kurabilir.

---

## 2. Gerekli Temel Dosyalar

Uygulamanızın mağazada eksiksiz ve profesyonel görünmesi için 3 temel dosyaya ihtiyacı vardır:

### A. Masaüstü Başlatıcı (`<app-id>.desktop`)
Uygulamanın menüde ve mağazada nasıl başlatılacağını tanımlar.
```ini
[Desktop Entry]
Name=Pars Not Defteri
Comment=Hızlı ve sade not alma uygulaması
Exec=pars-notes
Icon=org.parslinux.Notes
Terminal=false
Type=Application
Categories=Utility;TextEditor;
```

### B. AppStream Üstveri Dosyası (`<app-id>.metainfo.xml`)
Mağazadaki detay sayfası, açıklamalar, ekran görüntüleri ve lisans buradan okunur:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>org.parslinux.Notes</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-or-later</project_license>
  <name>Pars Not Defteri</name>
  <summary>Hızlı ve sade not alma uygulaması</summary>
  <description>
    <p>Pars Not Defteri, günlük notlarınızı güvenle saklamanızı sağlayan hafif ve modern bir not alma aracıdır.</p>
  </description>
  <developer_name>Pars Linux Topluluğu</developer_name>
  <url type="homepage">https://parslinux.org</url>
  <url type="bugtracker">https://github.com/parslinux/notes/issues</url>
  <url type="donation">https://opencollective.com/parslinux</url>
  <screenshots>
    <screenshot type="default">
      <image>https://parslinux.org/screenshots/notes-main.png</image>
    </screenshot>
  </screenshots>
  <releases>
    <release version="1.0.0" date="2026-10-12">
      <description>
        <p>İlk kararlı sürüm yayınlandı.</p>
      </description>
    </release>
  </releases>
</component>
```

### C. Yüksek Çözünürlüklü Simge
- `128x128` veya `256x256` piksel PNG veya ölçeklenebilir SVG formatında simge.
- Adı tam olarak `<app-id>.png` veya `<app-id>.svg` olmalıdır.

---

## 3. Flathub Üzerinden Yayınlama Adımları

1. **Flatpak Manifesti Hazırlayın (`org.parslinux.Notes.yaml`):**
   ```yaml
   app-id: org.parslinux.Notes
   runtime: org.gnome.Platform
   runtime-version: '46'
   sdk: org.gnome.Sdk
   command: pars-notes
   finish-args:
     - --share=ipc
     - --socket=fallback-x11
     - --socket=wayland
   modules:
     - name: pars-notes
       buildsystem: meson
       sources:
         - type: git
           url: https://github.com/parslinux/notes.git
           tag: v1.0.0
   ```
2. **Yerel Olarak Derleyin ve Test Edin:**
   ```bash
   flatpak-builder --user --install --force-clean build-dir org.parslinux.Notes.yaml
   flatpak run org.parslinux.Notes
   ```
3. **Flathub'a Başvurun:**
   - [flathub/flathub](https://github.com/flathub/flathub) deposunu fork edin.
   - Yeni bir dal oluşturup manifestinizi ekleyin ve Pull Request açın.
   - Flathub botları manifestinizi otomatik derleyip test edecektir.
4. **Yayınlanma:**
   - PR onaylandığında uygulamanız Flathub'da derlenir ve birkaç saat içinde Pars Linux Yazılım Merkezi vitrininde ve arama sonuçlarında yerini alır!
