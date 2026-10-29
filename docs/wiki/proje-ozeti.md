# Proje Özeti

## Amaç

Mobil Namaz Takip uygulamasının (Flutter, Android + iOS) **basit bir Windows masaüstü sürümü**. Gerekçe: iOS cihaz kullanılamıyor; vakitleri, namaz işaretlemeyi ve kaza borcunu bilgisayardan takip etmek isteniyor. Kullanıcı tek kişidir (geliştirici); mağaza dağıtımı yoktur.

Uygulama **sıfırdan** yazılır. Mobil uygulama yalnızca mantık ve görünüm referansıdır, kodu kopyalanmaz ([[mobil-referans]]). Yığın: Python + PySide6/QML + SQLite ([[mimari]]).

## Kapsam içi (v1)

| Alan | İçerik |
|---|---|
| Ezan vakitleri | Seçili şehrin günlük 6 vakti (Sabah, Güneş, Öğle, İkindi, Akşam, Yatsı), sıradaki vakte geri sayım, hesaplama yöntemi (varsayılan Diyanet). Cihazda hesaplanır, internet gerekmez. [[vakit-hesabi]] |
| Namaz işaretleme | Beş farz vakit için "Kıldım (cemaatle/yalnız)" ve "Kılmadım". Kaza listesi işaretlerden türetildiği için bu özellik v1'dedir. [[takip-gunu-ve-kaza]] |
| Kaza namazı | Takip başlangıcından bu yana kılınmayan veya işaretlenmeyen vakitler, "Kaza Et", geçmiş yıllardan kalan toplu borç, günlük hedef ve tahmini bitiş. [[takip-gunu-ve-kaza]] |
| Ayarlar | Şehir (81 il), hesaplama yöntemi, bildirim açık/kapalı + hatırlatma süresi, tema (5 tema), masaüstü seçenekleri. [[ekranlar]] |
| Bildirim ve tepsi | Uygulama tepsideyken vakit girince Windows bildirimi. [[bildirim-ve-tepsi]] |

## Kapsam dışı (v1)

Mobilde olup masaüstüne alınmayanlar: istatistik / ısı haritası, seri ve rozetler, zikir ve tesbihat, kıble pusulası, hicri takvim, ana ekran widget'ı, yapay zeka (Gemini) ile içerik kazıma, paylaşım, arka plan görevi, GPS ile otomatik konum. İstenirse sonra eklenir; ilk sürüm küçük tutulur.

## Sayfa haritası

Kararlar: [[kararlar]]. Plan ve riskler: [[yol-haritasi]]. Tüm sayfalar: [[index]].
