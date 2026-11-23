# Reader at Work 1 & 2 — Reading, Listening & Writing Çalışma Platformu

**Reader at Work 1** ve **Reader at Work 2** kitaplarındaki tüm tam okuma parçalarını OCR ile dijitalleştirip temizleyerek, **Edge-TTS** nöral ses kayıtlarıyla seslendiren ve her pasaj için kapsamlı **Listening, Reading ve Writing** soruları sunan interaktif **React + Vite** çalışma platformu.

---

## İçerik İstatistikleri

| Bileşen | Kapsam |
| --- | --- |
| **Toplam Pasaj** | **326 pasaj** (Reader at Work 1: **102** · Reader at Work 2: **224**) |
| **Reading Soruları** | **2.989 soru** (**2.016** kitaptaki orijinal soru + **973** ekstra Proficiency / IELTS / TOEFL sorusu) |
| **Listening Soruları** | **2.588 soru** (Gap-Fill boşluk doldurma, Listening MCQ, True / False / Not Given) |
| **Writing Görevleri** | **652 görev** (her pasaj için Task 1 Özet/Kısa Yazım + Task 2 Paragraf/Mini-Kompozisyon + model cevaplar) |
| **Ses Arşivi (Edge-TTS)** | **326 MP3** (`237.91 MB`, UK/US/AU kadın & erkek nöral sesler dönüşümlü) |

> **Kaynak Kapsam Notu:** Reader at Work 1 Flipbook PDF'i kitap sayfası **1–150** arasını (**Pasaj 1–102**), Reader at Work 2 Flipbook PDF'i ise kitap sayfası **1–448** arasını (**Pasaj 1–225**; kaynak PDF'te giriş sayfası bulunmayan **#72** hariç) kapsamaktadır. Sondaki *Appendix A* bağlaç alıştırmaları bağımsız dilbilgisi testi olduğu için okuma pasajlarından ayrıştırılmıştır.

---

## Ne İçin Yaptık?

ODTÜ Temel İngilizce Bölümü'nün klasik **Reader at Work 1 & 2** kitapları güçlü okuma parçalarına sahip olsa da elimizdeki kaynaklar yalnızca **taranmış görsel (Flipbook) PDF** formatındaydı ve sadece okuma sorularını içeriyordu:

- Görsel PDF'lerden metin kopyalanamıyor, pasajlar sesli dinlenemiyordu.
- Proficiency, IELTS ve TOEFL gibi sınavlara hazırlanırken **Reading** yanında **Listening** (not alma, boşluk doldurma, detay/çıkarım) ve **Writing** (özetleme, görüş paragrafı, akademik kelime kullanımı) pratiğini tek çatı altında birleştirmek gerekiyordu.
- Tüm içeriği masaüstü ve telefonda hızla açılan, ilerlemeyi kaydeden, hız ayarlı ses çalabilen etkileşimli bir web uygulamasına dönüştürmek amaçlandı.

---

## Nasıl Yaptık? (6 Aşamalı Pipeline & Arayüz)

Proje ham taranmış PDF sayfalarından başlayarak uçtan uca otomatik bir Python + PowerShell + Yapay Zekâ iş akışı ve React arayüzü ile üretildi:

1. **Görsel Çıkarım & Windows OCR (`scripts/01_ocr_extract.py`, `scripts/win_ocr_batch.ps1`):**
   - `PyMuPDF` ile iki PDF'in toplam **478 içerik sayfasından** orijinal çözünürlüklü gömülü sayfa görselleri çıkarıldı.
   - `PIL` + `numpy` ile sayfa ayırıcı yatay çizgilerin piksel koordinatları (`y_bars`) tespit edildi.
   - `Windows.Media.Ocr.OcrEngine` kullanılarak her satırın metni ve `(x, y, w, h)` koordinat kutuları çıkarıldı.
2. **Uzamsal Temizleme & Pasaj Bölümleme (`scripts/02_segment_passages.py`):**
   - Koordinat bilgisiyle sol kenardaki `5, 10, 15...` satır numaraları, alt sayfa numaraları ve tarama gürültüleri temizlendi.
   - Kalın başlık çizgileri, büyük pasaj numaraları ve büyük harfli ortalanmış başlıklar yakalanarak pasajlar ayrıştırıldı; kaynak PDF'teki eksik sayfa atlamalarında yanlış birleştirmeyi önleyen sayfa-boşluğu koruması uygulandı.
3. **Metin Düzeltme & Çoklu Soru Üretimi (`scripts/03_generate_questions_workflow.py`):**
   - 326 pasaj **121 grup** halinde işlenerek OCR hataları düzeltildi, seslendirme için akıcı `tts_script` hazırlandı.
   - Kitaptaki orijinal sorulardaki satır numarası referansları (`Line 4, 'they'...`) pasajdan alıntılanan ifadeyle bağlamsallaştırılarak satır numarası olmadan da çözülebilir hale getirildi.
   - Her pasaj için ekstra Proficiency/IELTS/TOEFL tarzı Reading soruları, birebir sesten yakalanan Listening soruları, 2 seviyeli Writing görevleri, Türkçe anlamlı faydalı kelimeler ve öz değerlendirme kontrol listesi eklendi.
4. **Birleştirme & Şema Doğrulama (`scripts/04_merge_and_validate.py`):**
   - Tüm pasajlar tek [data/passages.json](data/passages.json) dosyasında birleştirildi; boşluk doldurma cevaplarının ses metninde birebir geçip geçmediği ve şema bütünlüğü doğrulandı (`0` hata).
5. **Edge-TTS Nöral Ses Üretimi (`scripts/05_generate_audio.py`):**
   - 6 farklı İngilizce nöral ses (`en-GB-SoniaNeural`, `en-US-GuyNeural`, `en-US-AriaNeural`, `en-GB-RyanNeural`, `en-US-JennyNeural`, `en-AU-NatashaNeural`) dönüşümlü atandı.
   - Başlangıç seviyesine uyum için Kitap 1'in ilk 40 pasajı `-8%`, sonraki pasajları `-4%`, Kitap 2 pasajları ise `+0%` doğal hızda `audio/raw1/` ve `audio/raw2/` klasörlerine MP3 olarak sentezlendi.
6. **Markdown Kitapçıklar & React + Vite Web Arayüzü (`scripts/06_export_markdown.py`, `src/`):**
   - `docs/` altında çıktısı alınabilir soru kitapçıkları ve cevap anahtarları oluşturuldu.
   - **React 19 + Vite** ile masaüstü ve telefona tam uyumlu, ten rengi & beyaz (ve koyu) temalı tek sayfa çalışma stüdyosu geliştirildi.

---

## Arayüz Özellikleri

- **🎧 Listening Stüdyosu:** `0.75x–1.25x` hız seçimi, `-5s / +5s` sarma, ilerleme dolgulu özel oynatıcı, dinleme sayacı, gizlenebilir transkript, Gap-Fill, MCQ ve True/False/Not Given anında puanlama.
- **📖 Reading Sayfası:** `Lora` serif tipografiyle rahat okuma düzeni, `A- / A+` yazı boyutu ayarı, 2 sütunlu **Kelime Kartları** önizlemesi, kompakt sesli takip (shadowing) oynatıcı, kitaptaki orijinal sorular + ekstra sınav soruları.
- **✍️ Writing Stüdyosu:** Masaüstünde 2 sütunlu editör + yapışkan kelime ve kontrol listesi paneli; tıklayarak aktif alana kelime ekleme, canlı kelime sayacı, açılır model cevaplar ve `.txt` olarak taslak indirme.
- **📱 Tam Mobil & Tema Desteği:** Küçük telefon ekranlarına (`<= 640px`) tam uyumlu 3 sütunlu sekme yapısı ve çekmece menü; ten rengi & beyaz açık tema ve koyu espresso tema.
- **💾 Otomatik İlerleme Kaydı:** Tüm cevaplar ve yazı taslakları tarayıcının `localStorage` (`raw_study_suite_v1`) alanında otomatik saklanır; JSON olarak dışa/içe aktarılabilir.

---

## Klasör Yapısı

```text
├── index.html                   # Vite React giriş dosyası
├── vite.config.js               # React + geliştirme/build medya eklentisi (/audio, /data)
├── vercel.json                  # Vercel yönlendirme ve önbellek başlıkları
├── package.json                 # React 19, Lucide Icons ve Vite bağımlılıkları
├── src/
│   ├── App.jsx                  # Ana uygulama düzeni, veri yükleme ve kısayollar (Alt + ←/→)
│   ├── main.jsx                 # React kök bağlama noktası
│   ├── hooks/useStudyStore.js   # localStorage durum yönetimi ve JSON yedekleme
│   ├── utils/grading.js         # Cevap eşleştirme, kelime sayacı ve .txt dışa aktarım
│   ├── styles/global.css        # Ten rengi/beyaz tema ve responsive stil sistemi
│   └── components/              # Sidebar, Topbar, AudioPlayer, Listening/Reading/WritingTab
├── data/
│   └── passages.json            # 326 pasajlık birleşik veri seti (5.38 MB)
├── audio/
│   ├── raw1/                    # Reader at Work 1 MP3 dosyaları (102 adet)
│   └── raw2/                    # Reader at Work 2 MP3 dosyaları (224 adet)
├── docs/                        # Markdown çalışma kitapçıkları ve cevap anahtarları
└── scripts/                     # OCR, bölümleme, soru üretimi, doğrulama, Edge-TTS ve MD scriptleri
```

---

## Yerel Kurulum ve Çalıştırma

**Gereksinimler:** Node.js 18+

```bash
# 1. Depoyu klonlayın
git clone https://github.com/ibrahimmcx/ing.git
cd ing

# 2. Bağımlılıkları yükleyin
npm install

# 3. Geliştirme sunucusunu başlatın
npm run dev
```

Tarayıcıda `http://localhost:5173` adresini açabilirsiniz. Production derlemesi için:

```bash
npm run build
npm run preview
```

---

## Vercel'de Yayınlama

Repoda `vercel.json` ve `npm run build` sırasında `/data/passages.json` ile `/audio/` klasörünü `dist/` çıktısına kopyalayan Vite yapılandırması hazırdır:

1. [vercel.com](https://vercel.com) üzerinde **Add New → Project** seçip GitHub hesabınızdan **`ibrahimmcx/ing`** reposunu içe aktarın.
2. Framework Preset otomatik **Vite** olarak algılanacaktır (`Build Command: npm run build`, `Output Directory: dist`).
3. **Deploy** butonuna tıklayın; yayına alındıktan sonra tüm metinler, sorular ve 326 MP3 dosyası doğrudan CDN üzerinden çalışacaktır.

---

## Telif ve Kaynak Notu

Orijinal tarama PDF dosyaları hem dosya boyutu (GitHub 100 MB dosya sınırı) hem de telif hakları nedeniyle depoya dahil edilmemiştir.
