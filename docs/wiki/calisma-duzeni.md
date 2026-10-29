# Çalışma Düzeni

Proje boyunca (yapay zekâ ajanı ile) uyulan çalışma kuralları. Kaynak: `D002-HazirPromptlar/proje-altyapi-rehberi.md` bölüm 9; wiki anayasası `CLAUDE.md`. Test ve altyapı: [[test-stratejisi]], [[altyapi-kontrol-listesi]]. Plan: [[yol-haritasi]].

## Plan ve aşamalar

- Büyük işte önce plan; onaydan sonra uygula.
- Çok aşamalı işte her aşama sonunda **rapor ver ve dur**.
- Kod değişikliğiyle wiki güncellemesi **aynı turda** yapılır; her değişiklik `log.md`'ye yazılır.

## Commit ve etiket

- Commit yalnızca kullanıcı "commit at" deyince. Türkçe, `tip(kapsam): özet` biçimi. Her commit tek konu (kod + test + wiki birlikte). Commit öncesi `git status`.
- Rehberin kuralı: commit mesajında AI / `Co-Authored-By` satırı yok (kullanıcının kendi kuralı, araç varsayılanından önce gelir).
- **Etiket (tag) oluşturma ve itme yalnızca açık istekle.**

## Dürüst raporlama

- Doğrulanamayanı "doğrulanmadı" de (özellikle gerçek Windows'ta denenmemiş bildirim/tepsi/autostart davranışı).
- Başarısız testi çıktısıyla söyle; atlanan adımı belirt; yanlış pozitifi gizleme.
- Bu proje için ayrıca: mobil çıktısıyla karşılaştırılmamış vakit hesabı "doğru" diye raporlanmaz.

## Karar kaydı

Her karar [[kararlar]]'a gerekçesiyle ve **reddedilen seçenek + neden** ile yazılır; aynı tartışma tekrarlanmasın.

## Windows / araç tuzakları

- Kabuk heredoc'u ile kod yazma (kaçış dizileri bozulur: `\n`, `\b`, `\\`); `Write`/`Edit` veya betik dosyası kullan.
- Python, Git Bash'in `/tmp` ve `/c/...` yollarını görmez; betiklerde `C:/...` yolu kullan.
- Konsol cp1254 olduğundan betiklerde `PYTHONIOENCODING=utf-8`.
- PowerShell oturumunda `&&` yoktur (Windows PowerShell 5.1); komutlar ayrı çağrılır.
