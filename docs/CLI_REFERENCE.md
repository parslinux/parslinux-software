# Komut Satırı Başvuru Kılavuzu (CLI_REFERENCE.md)

Bu belge, Pars Linux Yazılım Merkezi'nin komut satırı argümanlarını, dahili işlem betiklerini ve Flatpak hata ayıklama komutlarını içerir.

---

## 1. Ana Başlatıcı Komut Satırı Kullanımı

Yazılım merkezini terminalden çalıştırırken aşağıdaki parametreleri kullanabilirsiniz:

```bash
./parslinux-software [SEÇENEKLER]
```

### Genel Seçenekler:
| Parametre | Kısa Yol | Açıklama |
| :--- | :--- | :--- |
| `--help` | `-h` | Genel yardım seçeneklerini görüntüler |
| `--help-all` | | Tüm GTK ve GApplication seçeneklerini listeler |
| `--help-gtk` | | GTK+ kütüphanesine özel parametreleri listeler |
| `--display=DISPLAY` | | Kullanılacak X11 veya Wayland ekran sunucusunu belirtir |

### Uygulama Seçenekleri:
| Parametre | Kısa Yol | Açıklama |
| :--- | :--- | :--- |
| `--details=<UYGULAMA_ID>` | `-d` | Yazılım merkezini doğrudan belirtilen uygulamanın detay sayfasında açar |

#### Örnek:
VLC Media Player'ın detay sayfasını doğrudan açmak için:
```bash
./parslinux-software -d org.videolan.VLC
```

---

## 2. Dahili İşlem Betiği (`src/Actions.py`)

`Actions.py`, paket kurulumu, kaldırılması ve güncellenmesi işlemlerini yürüten yardımcı motordur. Genellikle `MainWindow.py` tarafından arka planda çağrılır, ancak geliştirme ve test amacıyla doğrudan da çalıştırılabilir:

```bash
# Flatpak paketini kurma
python3 src/Actions.py install org.videolan.VLC

# Flatpak paketini kaldırma
python3 src/Actions.py remove org.videolan.VLC

# Flatpak paketini güncelleme
python3 src/Actions.py upgrade org.videolan.VLC

# İndirme veya işlem sürecini sonlandırma
python3 src/Actions.py kill <PID>
```

---

## 3. Flatpak Hata Ayıklama Komutları

Yazılım merkezinde bir paketle ilgili sorun yaşandığında kullanabileceğiniz yardımcı terminal komutları:

- **Kurulu Paketleri Listeleme:**
  ```bash
  flatpak list --app
  ```
- **Paket Bilgisini İnceleme:**
  ```bash
  flatpak info org.videolan.VLC
  ```
- **Uygulamayı Terminal Çıktısıyla Çalıştırma:**
  ```bash
  flatpak run -v org.videolan.VLC
  ```
- **Tanımlı Depoları (Remotes) Görme:**
  ```bash
  flatpak remotes
  ```
- **Kullanılmayan Bağımlılıkları Temizleme:**
  ```bash
  flatpak uninstall --unused -y
  ```
