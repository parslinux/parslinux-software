# Sürüm Politikası ve Yaşam Döngüsü (VERSION.md)

Pars Linux Yazılım Merkezi, [Semantik Sürümleme 2.0.0 (SemVer)](https://semver.org/) ilkelerini benimser.

---

## 1. Güncel Sürüm

- **Sürüm:** `2.0.0`
- **Kod Adı:** `Flathub Core`
- **Yayın Tarihi:** 12 Ekim 2026
- **Durum:** Kararlı (Stable)

---

## 2. Sürüm Numaralandırma Şeması: `MAJOR.MINOR.PATCH`

1. **MAJOR (Ana Sürüm - örn. 2.0.0):**
   - Temel mimari ve arka uç değişikliklerinde artırılır (örn. Eski arşiv mimarisinden evrensel Flathub/Flatpak mimarisine geçiş).
   - Geriye dönük uyumsuzluklar veya köklü arayüz yenilikleri içerir.
2. **MINOR (Alt Sürüm - örn. 2.1.0):**
   - Yeni özellikler (örn. izin görüntüleyici, çevrimdışı önbellek modu, yeni arama filtreleri) eklendiğinde artırılır.
   - Geriye dönük uyumluluk korunur.
3. **PATCH (Yama Sürümü - örn. 2.0.1):**
   - Hata düzeltmeleri, Pango etiket iyileştirmeleri, çeviri güncellemeleri ve güvenlik yamaları için artırılır.

---

## 3. Kod Tabanında Sürüm Senkronizasyonu

Bir sürüm yayınlanırken aşağıdaki dosyalar eşzamanlı olarak güncellenir:

- `setup.py` (`version='2.0.0'`)
- `debian/changelog`
- `docs/CHANGELOG.md`
- `docs/VERSION.md`
- Git Etiketi: `git tag -a v2.0.0 -m "Release v2.0.0"`
