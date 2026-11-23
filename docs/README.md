# Reader at Work 1 & 2 — Reading, Listening & Writing Çalışma Platformu

Bu çalışma seti **Reader at Work 1** ve **Reader at Work 2** kitaplarındaki tüm tam pasajlar taranarak, temizlenerek, Edge-TTS nöral ses dosyalarıyla seslendirilerek ve her pasaj için kapsamlı **Listening, Reading ve Writing** soruları oluşturularak hazırlanmıştır.

## İçerik Özeti

- **Toplam Pasaj:** 326 (Reader at Work 1: 102 | Reader at Work 2: 224)
- **Toplam Reading Sorusu:** 2.989 (Kitap Orijinal: 2.016 + Ekstra Sınav Sorusu: 973)
- **Toplam Listening Sorusu:** 2.588 (Gap-Fill + Listening MCQ + True/False/Not Given)
- **Toplam Writing Görevi:** 652 (Her pasaj için Task 1 Özet/Kısa Yazım + Task 2 Paragraf/Mini-Kompozisyon + Model Cevaplar + Kelime Listesi)
- **MP3 Ses Dosyaları:** `audio/raw1/` ve `audio/raw2/` klasörlerinde toplam 326 adet doğal UK/US/AU aksanlı Edge-TTS kaydı

## React + Vite Web Platformunu Çalıştırma

Proje modern **React 19 + Vite** arayüzü ile çalışır ve mevcut `data/passages.json` ile `audio/` klasörünü kopyalamadan doğrudan sunar (HTTP Range akışı desteklidir):

1. İlk kurulumda bağımlılıkları yükleyin:
   ```bash
   npm install
   ```
2. Geliştirme sunucusunu başlatın:
   ```bash
   npm run dev
   ```
   Tarayıcınızda `http://localhost:5173` adresini açın.
3. Production derlemesi ve önizleme için:
   ```bash
   npm run build
   npm run preview
   ```

**Özellikler & Çalışma Sırası:**
1. **Listening:** Metni açmadan sesi dinleyin (`0.75x–1.25x` hız seçimi, `-5s / +5s` geri-ileri sarma, tekrar sayacı), Gap-Fill, MCQ ve T/F/NG sorularını çözüp kontrol edin.
2. **Reading:** Pasajı okuyun (`A- / A+` yazı boyutu, kelime önizlemesi ve kompakt sesli takip/shadowing oynatıcı), kitaptaki orijinal soruları ve ekstra Proficiency/IELTS/TOEFL tarzı soruları çözün.
3. **Writing:** Tıklanabilir kelime kalıplarından yararlanarak Task 1 ve Task 2 yazılarını yazın, canlı kelime sayacıyla hedef aralığı takip edin, model cevaplarla kıyaslayın veya `.txt` olarak indirin.
4. Tüm ilerleme ve yazı taslaklarınız `localStorage` üzerinde (`raw_study_suite_v1`) otomatik olarak saklanır; JSON olarak dışa/içe aktarılabilir. `Alt + Sol/Sağ Ok` kısayoluyla pasajlar arasında hızlı geçiş yapabilirsiniz.

## Markdown Doküman Arşivi (`docs/`)

- `Reader_at_Work_1_Questions.md` & `Reader_at_Work_1_Answers.md`
- `Reader_at_Work_2_Questions.md` & `Reader_at_Work_2_Answers.md`

## Kaynak PDF Notları

- Reader at Work 1 PDF covers Book Pages 1-150 (Passages 1-102).
- Reader at Work 2 PDF covers Passages 1-225 up to Book Page 448 (Passage #72 omitted in source Flipbook; Appendix A connector drills excluded).
