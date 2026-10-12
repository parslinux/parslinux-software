# Pars Linux Yazılım Merkezi Dokümantasyonu

Pars Linux Yazılım Merkezi (Pars Linux Software Center) için hazırlanmış kapsamlı teknik, kullanıcı ve geliştirici kılavuzlarına hoş geldiniz.

---

## 📚 Dokümantasyon Rehberi

| Doküman | Açıklama |
| :--- | :--- |
| **[MİMARİ (ARCHITECTURE.md)](ARCHITECTURE.md)** | Sistem mimarisi, modüler mixin yapısı, sıfır titreme FlowBox ve önbellek motoru |
| **[KURULUM (INSTALL.md)](INSTALL.md)** | Dağıtımlar arası kurulum, bağımlılıklar, setup.py ve masaüstü entegrasyonu |
| **[ÖZEL SUNUCU / AYNA KILAVUZU (SELF_HOSTING_GUIDE.md)](SELF_HOSTING_GUIDE.md)** | Özel Flathub aynası veya özel Flatpak deposu barındırma rehberi |
| **[DEĞİŞİKLİK GÜNLÜĞÜ (CHANGELOG.md)](CHANGELOG.md)** | Sürüm geçmişi, modüler refactor, sıfır titreme UI ve performans geliştirmeleri |
| **[ÖDEME VE BAĞIŞ ENTEGRASYONU (PAYMENT_INTEGRATION.md)](PAYMENT_INTEGRATION.md)** | Flathub bağış modeli, geliştirici destekleme ve mağaza vizyonu |
| **[ŞARTLAR VE KOŞULLAR (TERMS.md)](TERMS.md)** | Terms of Service, lisans hakları ve sorumluluk reddi (İngilizce) |
| **[ŞARTLAR VE SORUMLULUK REDDİ (SARTLAR.md)](SARTLAR.md)** | Kullanım şartları ve feragatname (Türkçe) |
| **[YAPAY ZEKA ASİSTAN REHBERİ (CLAUDE.md)](CLAUDE.md)** | Claude ve AI ajanları için kod tabanı kuralları ve test komutları |
| **[GELİŞİM VE YOL HARİTASI (progress.md)](progress.md)** | Tamamlanan aşamalar (modülerlik, kararlılık, ikonlar) ve gelecek hedefler |
| **[TEST KILAVUZU (TESTING.md)](TESTING.md)** | Mixin doğrulama, FlowBox kararlılık testi ve başsız GTK testleri |
| **[KOMUT SATIRI REHBERİ (CLI_REFERENCE.md)](CLI_REFERENCE.md)** | Parametreler, yardımcı betikler ve Flatpak hata ayıklama komutları |
| **[ÇEVİRİ REHBERİ (TRANSLATION_GUIDE.md)](TRANSLATION_GUIDE.md)** | Çoklu dil desteği, `.po`/`.pot` gettext dosyalarının güncellenmesi |
| **[KATKIDA BULUNMA (CONTRIBUTING.md)](CONTRIBUTING.md)** | Katkı sağlama ilkeleri, Pull Request ve kod standartları |
| **[UYGULAMA BAĞLAMA VE YAYINLAMA (UYGULAMA_BAGLAMA.md)](UYGULAMA_BAGLAMA.md)** | Flathub veya Pars Linux deposuna uygulama ekleme ve paketleme rehberi |
| **[VERİ VE ÖNBELLEK REHBERİ (DATA_SAVING_GUIDE.md)](DATA_SAVING_GUIDE.md)** | Çift katmanlı disk TTL önbelleği, 250ms debouncing ve bant genişliği optimizasyonu |
| **[GÜVENLİK POLİTİKASI (SECURITY.md)](SECURITY.md)** | Polkit izinleri, Flatpak sandbox güvenliği ve açık bildirim süreci |
| **[ÇATALLANMA VE YENİDEN YAPILANDIRMA (FORK.md)](FORK.md)** | Orijinal proje kökeni, çatallanma gerekçeleri ve mimari dönüşüm |
| **[SÜRÜM POLİTİKASI (VERSION.md)](VERSION.md)** | Semantik sürümleme (SemVer) ve paketleme yaşam döngüsü |

---

## Hızlı Başlangıç

Pars Linux Yazılım Merkezi'ni yerel ortamınızda kaynak koddan test etmek için:

```bash
git clone https://github.com/parslinux/parslinux-software.git
cd parslinux-software
./parslinux-software
```
Detaylı bilgi için [INSTALL.md](INSTALL.md) dosyasına göz atabilirsiniz.
