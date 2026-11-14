# Web Guard

Claude Code ve Codex için kanıta dayalı web güvenlik denetimi, düzeltme ve yeniden test skill'i.

Evidence-led website security auditing, remediation and before/after verification for Claude Code and Codex.

## Ne yapar?

1. Yetkili hedefi ve erişim kapsamını belirler.
2. Dış gözlem, erişilebilir kaynak kodu ve sunucu kontrollerini ayrı değerlendirir.
3. Kanıtlı bulguları ve test edilemeyen alanları raporlar.
4. Verilen yetki dahilinde erişilebilir kod/yapılandırma açıklarını düzeltir.
5. Güncel dosyaları, değişiklikleri ve geri alma adımlarını teslim eder.
6. Eşdeğer yeniden testle önce/sonra farkını gösterir.

API, kimlik/oturum/yetki, ağ ve sunucu, bulut/Kubernetes, veri, bağımlılıklar, CI/CD, SOC/EDR/DLP, iş mantığı, gizlilik, kurtarma ve kanıt bütünlüğü kontrollerini içerir. İlgili modüller teknoloji, risk ve erişime göre seçilir.

## Gereksinimler

- Skill destekli Claude Code veya Codex ortamı.
- Yardımcı betikler için Python 3.10 veya üzeri; Python standart kütüphanesi yeterlidir.
- Yapılacak işe göre ağ, dosya, terminal veya onaylı sunucu bağlantısı.
- İncelenecek hedef için sahiplik veya açık test yetkisi.

Bu paket bağımsız bir pentest tarayıcısı veya iki modeli birlikte çağıran bir servis değildir. Aktif host model iş akışını yürütür; kurulu araçları kullanır. Ek tarayıcılar ve hizmetler ayrı gereksinim/lisans taşıyabilir.

## GitHub'a yükleme

ZIP'i aç. `web-guard-github` klasörünün İÇİNDEKİ dosya ve klasörleri kendi GitHub deponun köküne yükle. ZIP dosyasını tek başına yüklemek yerine kaynak dosyaları yükle.

Depo kökünde README.md, SHA256SUMS ve skills/web-guard/ bulunmalıdır. Tüm scripts, references, agents ve assets klasörlerini koru.

## Kurulum

Yalnızca `skills/web-guard` klasörünün tamamını seçtiğin hostun skill dizinine kopyala. Hedef klasörün adı `web-guard` olmalı; SKILL.md doğrudan onun içinde bulunmalı.

| Ortam | Kullanıcı kurulumu | Proje kurulumu |
|---|---|---|
| Claude Code | ~/.claude/skills/web-guard/ | .claude/skills/web-guard/ |
| Codex | ~/.agents/skills/web-guard/ | .agents/skills/web-guard/ |

### Windows / PowerShell

Depo kökünde çalıştır. Mevcut kurulum varsa bu örnek onu üzerine yazmadan durur.

Claude Code:

```powershell
$destination = Join-Path $HOME '.claude/skills/web-guard'
if (Test-Path $destination) { throw 'Mevcut kurulum var; güncellemeden önce yedekle.' }
New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
Copy-Item -Recurse -LiteralPath './skills/web-guard' -Destination $destination
```

Codex:

```powershell
$destination = Join-Path $HOME '.agents/skills/web-guard'
if (Test-Path $destination) { throw 'Mevcut kurulum var; güncellemeden önce yedekle.' }
New-Item -ItemType Directory -Force -Path (Split-Path $destination) | Out-Null
Copy-Item -Recurse -LiteralPath './skills/web-guard' -Destination $destination
```

Linux/macOS'ta aynı kaynak klasörü tablodaki kullanıcı veya proje konumuna kopyala. ChatGPT'deki kurulum başka bir bilgisayara otomatik aktarılmaz.

## Kullanım

Claude Code sohbetine yaz:

```text
/web-guard https://example.com
/web-guard https://example.com fix --repo /path/project --run /path/audit-run
/web-guard https://example.com retest --run /path/audit-run
```

Codex sohbetine yaz veya /skills seçicisinden seç:

```text
$web-guard https://example.com
$web-guard https://example.com --repo /path/project --token-budget 12000
```

Bunlar terminal komutu değildir. Kaynak kodu, staging ve sunucu erişimi uygun aşamada sağlanır. Parola veya özel anahtarı sohbete yapıştırmak yerine mevcut SSH agent/alias, secret manager ya da onaylı bağlantı kullan.

## Dosya yapısı

- skills/web-guard/SKILL.md: Ortak çekirdek iş akışı.
- references/: Temel, genişletilmiş ve ileri güvence kontrolleri; erişim, raporlama ve kurulum sözleşmeleri.
- scripts/observe.py: Tek istekli sınırlı HTTP gözlemi; zafiyet tarayıcısı değildir.
- scripts/results.py: Önce/sonra sonuçlarını muhafazakâr biçimde karşılaştırır.
- scripts/gate.py: Açıkça seçilmiş yayın politikasına göre geçer/bloke/hata sonucu üretir.
- scripts/evidence.py: Seçilmiş kanıt dosyalarının SHA-256 bütünlüğünü kontrol eder; imza doğrulama motoru değildir.
- scripts/test_helpers.py ve scripts/test_evidence.py: Toplam 34 yerel test.
- agents/openai.yaml ve assets/: Host arayüz bilgileri.

## Çıktılar

Kapsama göre başlangıç/son rapor, yönetici özeti, teknik rapor, baseline/final JSON, karşılaştırma, düzeltme takibi, güncellenmiş dosyalar ve geri alma talimatları üretilir. Kanıt, bütçe ve özel modül kayıtları ayrı tutulur. Kaynak paketi sunucu/provider ayarlarını kendiliğinden dağıtmaz.

## Token yaklaşımı

Kısa çekirdek yönergeler, ihtiyaca göre okunan modüller, dosya tabanlı durum, sınırlı araç çıktısı ve tekrar kullanılabilir keşif kullanılır. Gerçek tüketim hosttan alınabiliyorsa kaydedilir. Ölçüm/denetim yoksa kesin token veya maliyet tavanı garanti edilmez. İkinci bir model varsayılan olarak çağrılmaz.

## Sınırlar

Yalnızca URL ile tüm açıklar doğrulanamaz. Eksik erişimler test edilmedi olarak kalır. Sıfır açık, kesintisizlik veya sertifikasyon garantisi yoktur. Üretimde kesinti, veri kaybı, yetki/anahtar değişikliği veya kapsam genişlemesi yaratabilecek işler mevcut yetkiyle sınırlıdır. Gerçek müşteri verisiyle saldırı kanıtı toplanmaz. Hash uyumu, testin gerçekten yürütüldüğünü veya bulgunun doğru olduğunu tek başına kanıtlamaz.

Bu depo denetlenen projelerin raporlarını, müşteri dosyalarını veya kimlik bilgilerini içermemelidir. CI yayın kapısını ve imzalama entegrasyonunu gerçek ortamda ayrıca yapılandırıp doğrulamak gerekir.

## Yardımcı betik testleri

Linux/macOS/WSL üzerinde depo kökünden:

```bash
python3 -B skills/web-guard/scripts/test_helpers.py
python3 -B skills/web-guard/scripts/test_evidence.py
```

Symlink güvenlik testleri sembolik bağlantı oluşturma izni gerektirir. Testler dış hedeflere bağlanmaz; HTTP yardımcı testi yalnızca geçici yerel sunucu kullanır. 34 testin geçmesi gerçek bir web sitesinin güvenli olduğu anlamına gelmez.

## Paket bütünlüğü

SHA256SUMS her teslim dosyasının hash değerini listeler; kendisini listelemez. Bu dosya dijital imza değildir. Depoyu değiştirdiğinde eski teslim hash listesi güncel kaynak durumunu temsil etmez; yeni dağıtımda yeniden üret.
