# 🦇 Basic Battery Analyzer
*🇬🇧 [Click here for English documentation](README.md)*

Android cihazlardaki karmaşık `dumpsys batterystats` loglarını saniyeler içinde okunabilir, renkli ve anlamlı bir özet raporuna dönüştüren güçlü bir CLI (Komut Satırı) aracıdır.

Özellikle Custom ROM, Kernel (örneğin crDroid, SUSFS) değişiklikleri veya Root (KernelSU/Magisk) işlemleri sonrasında cihazın **Deep Sleep (Derin Uyku)** durumunu test etmek isteyen geliştiriciler ve ileri düzey kullanıcılar için tasarlanmıştır.

## 🚀 Özellikler
* **Çift Dil Desteği:** Komut satırı parametresi ile tam Türkçe ve İngilizce desteği.
* **Deep Sleep Hesaplama:** Cihazın gerçekte yüzde kaç oranında derin uykuda kaldığını otomatik hesaplar.
* **Top Drainers:** Bataryayı en çok sömüren donanım ve uygulamaları (mAh cinsinden) listeler.
* **Akıllı Bug Tespiti:** Bilinen donanım/kernel kilitlenmelerini (örn: `error -16`, `smp2p`, `IPA`) yakalar ve kullanıcıyı uyarır.
* **Markdown Dışa Aktarma:** Raporları forumlarda veya Telegram gruplarında paylaşmak için temiz bir `.md` dosyası olarak kaydeder.
* **Filtreleme:** Önemsiz milisaniyelik uyanmaları gizleme seçeneği sunar.

## 🛠️ Kurulum
Bu araç tamamen standart kütüphaneler kullanır, ekstra bir paket yüklemenize (`pip install`) gerek yoktur.
Sadece Python 3.x yüklü olması yeterlidir.

```bash
git clone https://github.com/trup40/basicbatteryanalyzer.git
cd basicbatteryanalyzer
```

## 📱 Log Dosyası Nasıl Alınır?
Aracı kullanmadan önce cihazınızdan batarya istatistiklerini çekmelisiniz.
*(Not: Temiz bir test için log almadan önce eski verileri sıfırlayıp cihazı en az 10 dakika uykuya bırakmanız şiddetle önerilir.)*

**Yöntem 1: Bilgisayar Üzerinden (ADB - Root Gerektirmez)**
USB Hata Ayıklama açıkken cihazınızı bilgisayara bağlayın.
```bash
# 1. Eski batarya verilerini sıfırlayın
adb shell dumpsys batterystats --reset

# 2. Cihazı bir süre uykuda bırakın ve ardından log dosyasını çekin
adb shell dumpsys batterystats > pil_raporu.txt
```

**Yöntem 2: Cihaz Üzerinden (Termux vb. - Root Gerekli)**
```bash
su
# 1. Eski batarya verilerini sıfırlayın
dumpsys batterystats --reset

# 2. Cihazı bir süre uykuda bırakın ve ardından log dosyasını çekin
dumpsys batterystats > pil_raporu.txt
```

## 💻 Kullanım
Log dosyasını aldıktan sonra script'e parametre olarak verin:

**Standart Analiz (Varsayılan İngilizce):**
```bash
python basic_battery_analyzer.py pil_raporu.txt
```

**Türkçe Dilinde, Filtreleyerek ve Markdown Olarak Kaydet:**
```bash
python basic_battery_analyzer.py pil_raporu.txt --lang tr --min-ms 50 --export sonuc.md
```

## ⚙️ Parametreler
* `--lang`  : Çıktı dili (`en` veya `tr`). Varsayılan `en`'dir.
* `--limit` : Her kategori için gösterilecek maksimum satır sayısını belirler (Varsayılan: 20).
* `--min-ms`: Belirtilen milisaniyenin altındaki (kısa süreli) uyanmaları gizler.
* `--export`: Çıktıyı renk kodlarından arındırılmış temiz bir markdown (`.md`) dosyasına kaydeder.


## ☕ Bağış Yap

Geliştirdiğim bu yazılım tamamen ücretsiz ve açık kaynaklıdır. Eğer projem işinize yaradıysa, bana bir kahve ısmarlayarak çalışmalarıma destek olabilirsiniz! 🚀

### 🪙 Kripto Para Adreslerim

| Coin | Ağ (Network) | Cüzdan Adresi |
| :--- | :--- | :--- |
| **USDT (Tether)** | **TRC20** (Tron) | `TWxJVQ3PBCd8ZJJVkX2joe8WRGcSCdh8Ws` |
| **BTC (Bitcoin)** | Bitcoin (Bech32)| `bc1q7207qk3wk94a94xvxx43lxawsg69zpm0atvtd8` |
| **ETH (Ethereum)** | ERC20 | `0x1f5A2e35752c6f01c753F334292Fc7635Caeef56` |
| **BNB** | **BSC** (BEP20) | `0x93845c5Fb889C36E072B5683f1616C625C2deBe7` |

> [!IMPORTANT]
> Lütfen gönderim yaparken **Ağ (Network)** seçiminin yukarıdaki tablo ile birebir aynı olduğundan emin olun. Yanlış ağ seçimi varlık kaybına neden olabilir.

---

**⭐ Çalışmayı faydalı bulduysanız yıldızlamayı unutmayın!**
