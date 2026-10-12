# Güvenlik Politikası ve Mimarisi (SECURITY.md)

Pars Linux projesi, kullanıcıların ve sistemlerinin güvenliğini en üst düzeyde tutmayı taahhüt eder. Bu belge, yazılım merkezinin güvenlik mimarisini ve güvenlik açıklarını bildirme sürecini açıklar.

---

## 1. Desteklenen Sürümler

| Sürüm | Durum | Güvenlik Güncellemeleri |
| :--- | :--- | :--- |
| **2.x (Pars Linux / Flathub)** | Aktif | ✅ Tam Destek |
| 1.0.x (Legacy) | Emekli | ❌ Desteklenmiyor |

---

## 2. Güvenlik Mimarisi ve Koruma Mekanizmaları

### A. Girdi Doğrulama ve Komut Enjeksiyonu Koruması
- `Actions.py` ve `MainWindow.py` içerisindeki tüm paket adları ve kullanıcı girdileri düzenli ifadeler (`regex`) ve katı parametre denetimlerinden geçirilir.
- Kabuk karakterleri (`&`, `;`, `|`, `` ` ``, `$`) doğrudan kabuğa (`shell=True`) aktarılmaz; tüm komutlar güvenli liste argümanı dizisi olarak (`subprocess.Popen(["flatpak", ...])`) çalıştırılır.

### B. Polkit ve En Az Ayrıcalık İlkesi (Least Privilege)
- Arayüz (`MainWindow.py`) asla `root` olarak çalıştırılmaz; tamamen standart kullanıcı haklarıyla çalışır.
- Sistem seviyesinde ayrıcalık gerektiren nadir durumlarda (APT veya sistem genelinde Flatpak kurulumu), Polkit (`pkexec`) yetkilendirmesi tetiklenir.
- Kullanıcı bazlı Flatpak kurulumlarında `root` şifresi dahi talep edilmeyerek saldırı yüzeyi minimuma indirilir.

### C. Flatpak ve Sandbox İzolasyonu
- Flathub üzerinden indirilen uygulamalar, `bubblewrap` ve Linux çekirdeğinin `cgroups`, `seccomp` filtreleri ile sistemden yalıtılmış olarak çalışır.
- Kötü amaçlı bir yazılım sisteme sızmaya çalışsa bile ana işletim sistemi çekirdeğine ve hassas sistem dosyalarına (`/etc`, `/boot`, `/usr`) doğrudan erişemez.

### D. Arayüz ve Pango Güvenliği
- Harici Flathub API'sinden gelen tüm metinler (uygulama adı, özet, geliştirici) `GLib.markup_escape_text()` ile süzülür. Arayüzün çökmesine veya sahte bildirimlerin gösterilmesine yönelik etiket enjeksiyonları engellenir.

---

## 3. Güvenlik Açığı Bildirimi

Bir güvenlik açığı keşfettiyseniz, lütfen bunu halka açık bir sorun (public issue) olarak açmak yerine sorumlu ifşa (responsible disclosure) ilkelerine uygun şekilde iletiniz:

- **E-Posta:** `guvenlik@parslinux.org`
- **Geri Dönüş Süresi:** 48 saat içinde ilk değerlendirme yapılır ve doğrulanan açıklar için en geç 7 iş günü içinde güvenlik yaması yayınlanır.
