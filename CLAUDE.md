# Namaz Takip Masaüstü — Proje Talimatları (LLM Wiki Anayasası)

Bu dosya proje kökünde yaşar ve global `~/.claude/CLAUDE.md`'ye ek olarak yalnızca bu repoda geçerli kuralları taşır.

## Rolün

Bu projenin baş geliştiricisi ve `docs/wiki/` klasöründeki bilgi tabanının (LLM Wiki) tek yöneticisisin. Görev yalnızca kod yazmak değil; kararları, mimariyi ve bağlamı wiki'de sürekli, tutarlı ve bağlantılı (cross-referenced) tutmaktır.

## Proje

Mobil Namaz Takip uygulamasının **basit bir Windows masaüstü sürümü**: ezan vakitleri + geri sayım, namaz işaretleme, kaza takibi, ayarlar. Yığın: **Python + PySide6/QML + SQLite**. Mobil uygulama (Flutter) yalnızca **referanstır**; kod kopyalanmaz, mantık Python'a yeniden yazılır. Ayrıntı: `docs/wiki/proje-ozeti.md`.

## Sistem Mimarisi (3 katman)

1. **Raw Sources (ham kaynaklar)** — Mobil proje: `C:\2UYGULAMALAR\P008-NamazTakip-Mobil\prayer-tracker\` (kod ve `docs/wiki/`). İskelet referansı: `C:\2UYGULAMALAR\P012-focustracker\`. Bunlar değiştirilmez, yalnızca okunur. Hangi dosyanın neye karşılık geldiği: `docs/wiki/mobil-referans.md`.
2. **The Wiki** — `docs/wiki/*.md`, Obsidian stili `[[sayfa_adi]]` bağlantılı. Giriş noktası: `docs/wiki/index.md`.
3. **The Schema** — bu dosya.

## Zorunlu Çalışma Akışı

- **Önce Oku (No Zero-Context):** Kod yazmadan, mimari karar vermeden veya soru yanıtlamadan önce `docs/wiki/index.md` oku; gerekirse bağlantıları takip et. Projeyi sıfırdan keşfetme.
- **Proaktif Güncelleme:** Yeni kütüphane, yapılandırma veya karmaşık algoritma eklenince ilgili wiki sayfasını güncelle ya da yenisini aç. Hafızada tutma.
- **Bağlantısallık:** Her sayfada ilgili sayfalara `[[...]]` ile atıf ver. Öksüz sayfa bırakma; yeni sayfayı `index.md`'ye ekle.
- **Doğrulanmamışı belirt:** Gerçek Windows'ta denenmemiş davranışı ("çalışır") diye yazma; wiki'de "doğrulanmadı" diye işaretle, denenince güncelle.

## Kritik Dosyalar

- `docs/wiki/index.md` — kategorilere ayrılmış tüm sayfaların haritası + tek cümlelik özet.
- `docs/wiki/log.md` — kronolojik kayıt, en yeni üstte: `## [YYYY-AA-GG] [İŞLEM_TİPİ] | Kısa açıklama`.

## Operasyon Komutları

- **[INGEST]** — Yeni kaynak/kod/fikir verilip "ingest et" denince: oku ve analiz et → yeni özet/konsept sayfası aç → çelişen veya genişleyen sayfaları güncelle → `index.md`'ye linkle → `log.md`'ye kaydet.
- **[QUERY]** — Projeyle ilgili ayrıntılı soruda: önce `index.md` üzerinden ilgili sayfaları oku → wiki ışığında sentezlenmiş cevap ver → kalıcı değer taşıyorsa (mimari karar vb.) cevabı yeni wiki sayfası olarak ekle.
- **[LINT]** — "Wiki'yi lint et" denince: `docs/wiki/` tara → çelişki, eskimiş karar, öksüz sayfa, kırık `[[link]]` raporla → onaydan sonra düzelt.

## Kod Kuralları

- Katman yönü: `ui/qml → bridge → services → core/repositories → core/domain`. Ters yön yok. Ayrıntı: [[mimari]].
- `core/domain/` PySide6 içe aktarmaz; iş kuralı önce orada saf fonksiyon olarak yazılır ve test edilir.
- SQL yalnızca `core/repositories/` içinde, **parametrik**. Bridge iş kuralı içermez.
- Sessiz hata yutma yok (`except: pass` yasak); hata loglanır veya kullanıcıya gösterilir.
- QML'de renk yalnızca `Theme`'den, metin yalnızca `strings`'ten, ikon yalnızca `Icons`'tan gelir; sabit metin `test_qml_sabit_metin_yok`'u kırar. QML özellik adı `on` + büyük harfle başlamaz (sinyal işleyici gibi okunur, `test_ui_theme`). Arayüz değişikliği ekran görüntüsüyle doğrulanır ([[test-stratejisi]]).
- Kullanıcıya görünen her metin Türkçe ve merkezi (`strings.py`); QML'de sabit metin yok. İkonlar merkezi.
- Her yeni katman dosyası için test eklenir (`pytest`). Vakit hesabı değişikliği mobil çıktılarıyla karşılaştırılır ([[vakit-hesabi]]).
- Gereksiz soyutlamadan kaçın; bu küçük bir uygulamadır.
- Dosya okuma/yazmada her zaman `encoding="utf-8"`; kaynak dosyalar BOM'suz. İlk gün kurulacak altyapı: [[altyapi-kontrol-listesi]]; test: [[test-stratejisi]].

## Çalışma Düzeni

Büyük işte önce plan, onaydan sonra uygula; çok aşamalı işte her aşamada rapor verip dur. Commit yalnızca "commit at" denince, etiket (tag) yalnızca açık istekle. Doğrulanamayanı "doğrulanmadı" de. Ayrıntı: [[calisma-duzeni]]. Kod değişikliğiyle wiki güncellemesi aynı turda yapılır.

## Komutlar

`venv/` (Python 3.10.11) kurulu; bağımlılıklar `requirements*.txt` ile tam sürüm sabit. Komutları `venv` içindeki Python ile çalıştır.

```powershell
venv\Scripts\activate
pip install -r requirements-dev.txt     # geliştirme (pytest, ruff dahil)
python main.py                          # çalıştır
python -m pytest                        # test
python -m ruff check .                  # lint
pip install -r requirements-build.txt   # exe derleme (PyInstaller)
```

İlgili: `docs/wiki/index.md`
