# Katkıda Bulunma Rehberi (CONTRIBUTING.md)

Pars Linux Yazılım Merkezi'ne (Pars Linux Software Center) katkıda bulunmak istediğiniz için teşekkür ederiz! Açık kaynak topluluğunun katkıları bu projeyi daha güçlü, kararlı ve kullanıcı dostu kılmaktadır.

---

## 1. Katkı Sağlama Yolları

Projeye farklı şekillerde katkıda bulunabilirsiniz:
- 🐛 **Hata Bildirimi:** Karşılaştığınız çökmeleri, eksiklikleri veya tutarsızlıkları detaylı olarak bildirebilirsiniz.
- 💡 **Özellik Önerisi:** Arayüz, performans veya Flatpak yönetimi için yeni fikirler sunabilirsiniz.
- 💻 **Kod Katkısı:** Hata düzeltmeleri, yeni özellikler veya mimari optimizasyonlar geliştirebilirsiniz.
- 🌍 **Çeviri:** Uygulamanın farklı dillerdeki çevirilerini iyileştirebilir veya yeni diller ekleyebilirsiniz.
- 📖 **Dokümantasyon:** Kılavuzları ve açıklamaları güncelleyebilir veya genişletebilirsiniz.

---

## 2. Geliştirme ve PR Süreci

1. **Depoyu Çatallayın (Fork):** Projeyi kendi GitHub/GitLab hesabınıza çatallayın.
2. **Dal Oluşturun (Branch):** Anlamlı bir dal adı belirleyin:
   ```bash
   git checkout -b ozellik/flathub-izin-denetleyici
   # veya
   git checkout -b duzeltme/pango-markup-escape
   ```
3. **Geliştirme Yapın:** Değişikliklerinizi kod standartlarına uygun olarak uygulayın.
4. **Testleri Çalıştırın:**
   ```bash
   python3 -m py_compile src/*.py
   ./parslinux-software
   ```
5. **İşleyin (Commit):** Açık ve anlaşılır commit mesajları yazın:
   ```bash
   git commit -m "feat(ui): add permission badges to app details page"
   ```
6. **Pull Request Açın:** Değişikliklerinizi ve neyi çözdüğünü açıklayan bir PR oluşturun.

---

## 3. Kod Standartları ve Kuralları

- **Python & PEP 8:** Kodlar genel Python 3 standartlarına ve PEP 8 kurallarına uygun olmalıdır.
- **İş Parçacığı Güvenliği:** Asla arka plan iş parçacığından GTK bileşenlerini doğrudan değiştirmeyin; daima `GLib.idle_add` kullanın.
- **Markup Güvenliği:** Pango etiketlerine aktarılan dinamik metinleri `GLib.markup_escape_text(text, -1)` ile süzün.
- **Bağımlılık İzolasyonu:** Debian dışı sistemlerde (Arch Linux, Fedora) çökmeye yol açacak kütüphaneleri zorunlu kılmayın.
- **Günlükleme (Logging):** Doğrudan `print()` yerine projenin `Logger` modülünü kullanın (`self.Logger.info`, `self.Logger.warning`).
