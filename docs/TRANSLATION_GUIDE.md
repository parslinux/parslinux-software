# Çeviri ve Yerelleştirme Kılavuzu (TRANSLATION_GUIDE.md)

Pars Linux Yazılım Merkezi, GNU `gettext` standardını kullanarak çoklu dil desteği sunar. Bu kılavuz, var olan çevirileri güncellemeyi ve projeye yeni bir dil eklemeyi açıklar.

---

## 1. Dizin ve Dosya Yapısı

Çeviri dosyaları projenin `po/` dizininde yer alır:
- `po/parslinux-software.pot`: Kaynak kodlardan taranan ana çeviri şablon dosyası.
- `po/tr.po`: Türkçe çeviriler.
- `po/es.po`: İspanyolca çeviriler.
- `po/pt.po`: Portekizce çeviriler.
- `po/files`: Taranacak kaynak dosyaların listesi.

---

## 2. Gerekli Araçlar

Çeviri şablonlarını güncellemek ve derlemek için `gettext` paketine ihtiyaç vardır:

- **Arch Linux & Pars Linux:** `sudo pacman -S gettext`
- **Debian & Ubuntu:** `sudo apt install gettext`
- **Fedora:** `sudo dnf install gettext`

Grafik arayüz üzerinden çeviri yapmak için **Poedit** yazılımı önerilir (`sudo pacman -S poedit` veya Flathub üzerinden `net.poedit.Poedit`).

---

## 3. Çevirileri Güncelleme Adımları

Kaynak koda yeni bir metin eklendiğinde şablonu ve mevcut dilleri güncellemek için:

```bash
# Proje kök dizininde çeviri betiğini çalıştırın
./update-translations.sh
```

Bu betik:
1. Kaynak kodlardaki `_("metin")` ifadelerini tarar ve `po/parslinux-software.pot` dosyasını günceller.
2. `msgmerge` aracı ile `po/tr.po`, `po/es.po`, `po/pt.po` dosyalarındaki mevcut çevirileri koruyarak yeni satırları ekler.

---

## 4. Yeni Bir Dil Ekleme

Projeye yeni bir dil eklemek için (örneğin Almanca - `de` veya Azerbaycanca - `az`):

1. Ana şablonu kopyalayın:
   ```bash
   cp po/parslinux-software.pot po/az.po
   ```
2. `po/az.po` dosyasını Poedit veya favori metin düzenleyicinizle açarak çevirileri tamamlayın.
3. `update-translations.sh` dosyasındaki `langs` dizisine dili ekleyin:
   ```bash
   langs=("tr" "pt" "es" "az")
   ```

---

## 5. Çevirileri Yerel Olarak Test Etme

Uygulamayı belirli bir dilde çalıştırmak için `LANGUAGE` veya `LANG` ortam değişkenini kullanabilirsiniz:

```bash
# İngilizce olarak çalıştırma
LANGUAGE=en ./parslinux-software

# Türkçe olarak çalıştırma
LANGUAGE=tr ./parslinux-software

# İspanyolca olarak çalıştırma
LANGUAGE=es ./parslinux-software
```
