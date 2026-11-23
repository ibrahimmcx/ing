"""Step 6a: Export structured Markdown Question Workbooks, Answer Keys, and README from passages.json."""

import json
from pathlib import Path

WORKSPACE = Path(r"c:\Users\culfa\Desktop\ing")
DATA_JSON = WORKSPACE / "data" / "passages.json"
DOCS_DIR = WORKSPACE / "docs"


def export_book_markdown(passages: list[dict], book_num: int) -> None:
    title_book = f"Reader at Work {book_num}"
    q_lines = [
        f"# {title_book} — Reading, Listening & Writing Çalışma Kitabı\n",
        f"> Toplam **{len(passages)}** pasaj | Her pasaj için Dinleme (Edge-TTS MP3), Okuma (Kitap + Ekstra Sınav Soruları) ve Yazma (2 Seviyeli Görev + Kelime Listesi) içerir.\n",
        "---\n",
    ]
    a_lines = [
        f"# {title_book} — Cevap Anahtarı ve Model Yazılar\n",
        f"> Toplam **{len(passages)}** pasaj için tüm Reading, Listening cevap anahtarları, açıklamalar ve Writing model cevapları.\n",
        "---\n",
    ]

    for p in passages:
        num = p["passage_number"]
        pages_str = ", ".join(str(x) for x in p.get("book_pages", [])) or "-"
        header = f"## Passage {num}: {p['title']}"
        meta_line = (
            f"- **ID:** `{p['id']}` | **Seviye:** `{p['cefr_level']}` | **Konu:** {p['topic']} | "
            f"**Sayfa:** {pages_str}\n"
            f"- **Ses Dosyası:** `../{p['audio_path']}` (*{p['accent']} · {p['voice']} · Hız {p['rate']}*)\n"
        )

        # === QUESTIONS WORKBOOK ===
        q_lines.append(f"{header}\n")
        q_lines.append(meta_line)

        # Listening first (so learners can try listening before reading!)
        ls = p["listening"]
        q_lines.append("### 1. Listening (Metni Okumadan Dinleyerek Çözün)\n")
        q_lines.append("**A. Gap-Fill (Boşluk Doldurma)**\n")
        for idx, g in enumerate(ls["gap_fill"], 1):
            q_lines.append(f"{idx}. {g['prompt']} *(İpucu: {g['hint']})*\n")

        q_lines.append("\n**B. Listening Multiple Choice**\n")
        for idx, m in enumerate(ls["mcq"], 1):
            q_lines.append(f"{idx}. {m['prompt']}\n")
            for o_i, opt in enumerate(m["options"]):
                letter = chr(65 + o_i)
                q_lines.append(f"   - {letter}) {opt}\n")

        q_lines.append("\n**C. True / False / Not Given**\n")
        for idx, tf in enumerate(ls["true_false"], 1):
            q_lines.append(f"{idx}. [ ] True  [ ] False  [ ] Not Given — {tf['statement']}\n")

        # Reading Passage + Questions
        q_lines.append("\n### 2. Reading\n")
        q_lines.append(p["passage_text"].strip() + "\n")

        rd = p["reading"]
        if rd["original_questions"]:
            q_lines.append("\n**A. Kitaptaki Orijinal Sorular**\n")
            cur_sec = None
            for idx, oq in enumerate(rd["original_questions"], 1):
                if oq.get("section") and oq["section"] != cur_sec:
                    cur_sec = oq["section"]
                    q_lines.append(f"\n*{cur_sec}*\n")
                q_lines.append(f"{idx}. {oq['prompt']}\n")
                for opt in oq.get("options", []):
                    q_lines.append(f"   - {opt}\n")

        q_lines.append("\n**B. Ekstra Sınav Soruları (Proficiency / IELTS / TOEFL)**\n")
        for idx, eq in enumerate(rd["extra_questions"], 1):
            q_lines.append(f"{idx}. *[{eq['skill']}]* {eq['prompt']}\n")
            for o_i, opt in enumerate(eq["options"]):
                letter = chr(65 + o_i)
                q_lines.append(f"   - {letter}) {opt}\n")

        # Writing
        wr = p["writing"]
        q_lines.append("\n### 3. Writing\n")
        q_lines.append(f"- **Task 1 — {wr['task1']['title']}** ({wr['task1']['target_words']}): {wr['task1']['prompt']}\n")
        q_lines.append(f"- **Task 2 — {wr['task2']['title']}** ({wr['task2']['target_words']}): {wr['task2']['prompt']}\n")
        q_lines.append("\n**Useful Vocabulary & Collocations:**\n")
        for v in wr["useful_vocabulary"]:
            q_lines.append(f"- **{v['term']}** (*{v['meaning_tr']}*): {v['example']}\n")
        q_lines.append("\n**Self-Assessment Checklist:**\n")
        for c in wr["checklist"]:
            q_lines.append(f"- [ ] {c}\n")
        q_lines.append("\n---\n\n")

        # === ANSWERS WORKBOOK ===
        a_lines.append(f"{header} (`{p['id']}` · `{p['cefr_level']}`)\n")
        a_lines.append("### Listening Cevapları\n")
        a_lines.append("**A. Gap-Fill:**\n")
        for idx, g in enumerate(ls["gap_fill"], 1):
            a_lines.append(f"{idx}. **{' / '.join(g['answers'])}**\n")
        a_lines.append("\n**B. Listening MCQ:**\n")
        for idx, m in enumerate(ls["mcq"], 1):
            ans_letter = chr(65 + m["answer_index"])
            ans_text = m["options"][m["answer_index"]]
            a_lines.append(f"{idx}. **{ans_letter}) {ans_text}** — {m['explanation']}\n")
        a_lines.append("\n**C. True / False / Not Given:**\n")
        for idx, tf in enumerate(ls["true_false"], 1):
            a_lines.append(f"{idx}. **{tf['answer']}** — {tf['explanation']}\n")

        a_lines.append("\n### Reading Cevapları\n")
        if rd["original_questions"]:
            a_lines.append("**A. Kitaptaki Orijinal Sorular:**\n")
            for idx, oq in enumerate(rd["original_questions"], 1):
                a_lines.append(f"{idx}. **{oq['answer']}** — {oq['explanation']}\n")
        a_lines.append("\n**B. Ekstra Sınav Soruları:**\n")
        for idx, eq in enumerate(rd["extra_questions"], 1):
            ans_letter = chr(65 + eq["answer_index"])
            ans_text = eq["options"][eq["answer_index"]]
            a_lines.append(f"{idx}. **{ans_letter}) {ans_text}** — {eq['explanation']}\n")

        a_lines.append("\n### Writing Model Cevapları\n")
        a_lines.append(f"**Task 1 ({wr['task1']['title']}):**\n\n{wr['task1']['model_answer']}\n\n")
        a_lines.append(f"**Task 2 ({wr['task2']['title']}):**\n\n{wr['task2']['model_answer']}\n")
        a_lines.append("\n---\n\n")

    (DOCS_DIR / f"Reader_at_Work_{book_num}_Questions.md").write_text("\n".join(q_lines), encoding="utf-8")
    (DOCS_DIR / f"Reader_at_Work_{book_num}_Answers.md").write_text("\n".join(a_lines), encoding="utf-8")


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    dataset = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    passages = dataset["passages"]
    counts = dataset["meta"]["counts"]

    b1 = [p for p in passages if p["book"] == 1]
    b2 = [p for p in passages if p["book"] == 2]

    export_book_markdown(b1, 1)
    export_book_markdown(b2, 2)

    readme = f"""# Reader at Work 1 & 2 — Reading, Listening & Writing Çalışma Platformu

Bu çalışma seti **Reader at Work 1** ve **Reader at Work 2** kitaplarındaki tüm tam pasajlar taranarak, temizlenerek, Edge-TTS nöral ses dosyalarıyla seslendirilerek ve her pasaj için kapsamlı **Listening, Reading ve Writing** soruları oluşturularak hazırlanmıştır.

## İçerik Özeti

- **Toplam Pasaj:** {counts['total_passages']} (Reader at Work 1: {counts['book1_passages']} | Reader at Work 2: {counts['book2_passages']})
- **Toplam Reading Sorusu:** {counts['total_reading_questions']} (Kitap Orijinal: {counts['original_reading_questions']} + Ekstra Sınav Sorusu: {counts['extra_reading_questions']})
- **Toplam Listening Sorusu:** {counts['listening_questions']} (Gap-Fill + Listening MCQ + True/False/Not Given)
- **Toplam Writing Görevi:** {counts['writing_tasks']} (Her pasaj için Task 1 Özet/Kısa Yazım + Task 2 Paragraf/Mini-Kompozisyon + Model Cevaplar + Kelime Listesi)
- **MP3 Ses Dosyaları:** `audio/raw1/` ve `audio/raw2/` klasörlerinde toplam {counts['total_passages']} adet doğal UK/US/AU aksanlı Edge-TTS kaydı

## Nasıl Kullanılır?

1. **İnteraktif Web Platformu (Önerilen):**
   - Ana klasördeki `index.html` dosyasına çift tıklayarak doğrudan tarayıcınızda açabilirsiniz (internetsiz / çevrimdışı çalışır, kurulum gerektirmez).
   - Sol menüden kitap (`Kitap 1` / `Kitap 2`), CEFR seviyesi (`A1`–`C1`), ilerleme durumu veya başlık araması ile pasaj seçin.
   - **Önerilen Çalışma Sırası:**
     1. Önce **Listening** sekmesinde metni açmadan sesi dinleyin (`0.75x` – `1.25x` hız seçimi ve `-5s / +5s` geri-ileri sarma mevcuttur), boşluk doldurma ve soruları çözüp kontrol edin.
     2. Ardından **Reading** sekmesinde pasajı okuyun, kitaptaki orijinal soruları ve ekstra Proficiency/IELTS/TOEFL tarzı soruları çözün.
     3. Son olarak **Writing** sekmesinde verilen kelimelerden faydalanarak Task 1 ve Task 2 yazılarını yazın, kelime sayacı ile hedef aralığı takip edin ve model cevaplarla karşılaştırın.
   - Tüm ilerlemeniz ve yazdığınız metinler tarayıcınızın `localStorage` hafızasında otomatik olarak saklanır.

2. **Markdown Doküman Arşivi (`docs/`):**
   - `Reader_at_Work_1_Questions.md` & `Reader_at_Work_1_Answers.md`
   - `Reader_at_Work_2_Questions.md` & `Reader_at_Work_2_Answers.md`

## Kaynak PDF Notları

- {dataset['meta']['source_notes']['book1']}
- {dataset['meta']['source_notes']['book2']}
"""
    (DOCS_DIR / "README.md").write_text(readme, encoding="utf-8")
    print(f"Exported Markdown workbooks and README to {DOCS_DIR}")


if __name__ == "__main__":
    main()
