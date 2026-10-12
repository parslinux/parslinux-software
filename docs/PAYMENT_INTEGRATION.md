# Ödeme ve Bağış Entegrasyonu Kılavuzu (PAYMENT_INTEGRATION.md)

Bu belge, Pars Linux Yazılım Merkezi'nde açık kaynak geliştiricilerini desteklemek, bağış toplamak ve gelecekteki ücretli/isteğe bağlı katkı modellerini yönetmek için planlanan mimariyi açıklar.

---

## 1. Genel Bakış ve Felsefe

Linux ekosisteminde bağımsız yazılım geliştiricilerinin sürdürülebilirliği kritik önem taşır. Pars Linux Yazılım Merkezi, geliştiricilerin emeklerinin karşılığını alabilmesi için doğrudan bağış ve mikro-destek modellerini destekleyecek şekilde tasarlanmaktadır.

---

## 2. Flathub Bağış ve Destek Modeli

Flathub, AppStream standardı üzerinden geliştiricilerin bağış bağlantılarını paylaşmasına olanak tanır:

1. **AppStream `<url type="donation">` Etiketi:**
   - Bir uygulama geliştiricisi `metainfo.xml` dosyasına bağış linki (örn. GitHub Sponsors, Open Collective, Liberapay, Patreon) eklediğinde, Flathub API bu bilgiyi `/appstream/{id}` uç noktasında döner.
2. **Yazılım Merkezi Entegrasyonu:**
   - Detay sayfasında "Geliştiriciyi Destekle" veya "Bağış Yap" butonu bu URL'yi sistem varsayılan web tarayıcısında açar.

---

## 3. Planlanan Entegrasyon Fazları

### Faz 1: Doğrudan Bağış Bağlantıları (Mevcut Hedef)
- Uygulama detay sayfasına "Bağış Yap" butonu eklenmesi.
- Desteklenen platformlar:
  - Open Collective
  - GitHub Sponsors
  - Ko-fi / Buy Me a Coffee
  - Kripto (Bitcoin / Monero) adres kopyalama kutusu

### Faz 2: Flathub Ödeme Sistemi Entegrasyonu
- Flathub'ın resmi ödeme ve satın alma API'si ile entegrasyon (Stripe tabanlı).
- Kullanıcının Flathub hesabı ile oturum açarak satın aldığı veya desteklediği uygulamaları doğrulaması (Token-based verification).

### Faz 3: "Gönlünden Ne Koparsa" (Pay-What-You-Want) Modeli
- Kullanıcı bir uygulamayı indirmeden önce geliştiriciye önerilen miktarda (örn. 50 TL, 100 TL veya 0 TL) bağış yapma seçeneği sunulması.
- Satın almanın tamamen isteğe bağlı olması, açık kaynak kodun asla kısıtlanmaması ilkesi.

---

## 4. Güvenlik ve Gizlilik Prensipleri

1. **Sıfır Kart Verisi:** Yazılım merkezi hiçbir zaman kredi kartı, banka hesabı veya kişisel finansal veriyi yerel sistemde saklamaz veya işlemez.
2. **Güvenli Harici Ağ Geçitleri:** Tüm ödeme süreçleri doğrudan yetkili sağlayıcılar (Stripe, Open Collective) üzerinden HTTPS ve harici web tarayıcısı güvenliği ile yürütülür.
3. **Telemetri Yasağı:** Kimin hangi uygulamayı ne kadar bağışlayarak indirdiği bilgisi hiçbir merkezi Pars Linux sunucusuna telemetri olarak gönderilmez.
