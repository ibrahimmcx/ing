"""Step 4: Merge generated batches, validate all schemas/fields, attach audio metadata, and emit passages.json + passages.js."""

import datetime
import json
import re
from pathlib import Path

WORKSPACE = Path(r"c:\Users\culfa\Desktop\ing")
RAW_PATH = WORKSPACE / "data" / "raw_passages.json"
BATCH_DIR = WORKSPACE / "data" / "batches"
OUT_JSON = WORKSPACE / "data" / "passages.json"
OUT_JS = WORKSPACE / "data" / "passages.js"
OUT_REPORT = WORKSPACE / "data" / "validation_report.json"

TR_MAP = str.maketrans("üÜşŞğĞıİöÖçÇ", "uUsSgGiIoOcC")
TR_RE = re.compile(r"[üÜşŞğĞıİöÖçÇ]")

VOICES = [
    ("en-GB-SoniaNeural", "UK"),
    ("en-US-GuyNeural", "US"),
    ("en-US-AriaNeural", "US"),
    ("en-GB-RyanNeural", "UK"),
    ("en-US-JennyNeural", "US"),
    ("en-AU-NatashaNeural", "AU"),
]


def clean_english_str(s: str, allow_turkish_title: bool = False) -> tuple[str, bool]:
    if not isinstance(s, str):
        return "", False
    had_tr = bool(TR_RE.search(s))
    if had_tr and not allow_turkish_title:
        s = s.translate(TR_MAP)
    s = s.replace("•", "'").replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    return s.strip(), had_tr


def strip_opt_prefix(opts: list[str]) -> list[str]:
    if not opts:
        return opts
    pref_re = re.compile(r"^[A-Da-d][\.\)]\s+")
    if all(pref_re.match(o.strip()) for o in opts):
        return [pref_re.sub("", o.strip(), count=1).strip() for o in opts]
    return [o.strip() for o in opts]


def slugify(text: str, max_len: int = 32) -> str:
    s = text.lower().translate(TR_MAP)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return (s[:max_len].strip("_")) or "passage"


def normalize_for_match(text: str) -> str:
    s = text.lower().translate(TR_MAP)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def clean_passage_object(p: dict, raw_meta: dict, global_idx: int, warnings: list[dict]) -> dict:
    pid = p["id"]
    is_tr_passage = (p["book"] == 1 and p["passage_number"] == 87)

    p["pdf_pages"] = raw_meta.get("pdf_pages", [])
    if not p.get("book_pages"):
        p["book_pages"] = raw_meta.get("book_pages", [])

    # Clean English fields from any residual Turkish OCR noise
    p["title"], tr_title = clean_english_str(p.get("title", ""), allow_turkish_title=is_tr_passage)
    p["topic"], _ = clean_english_str(p.get("topic", "General Reading"))
    p["passage_text"], tr_body = clean_english_str(p.get("passage_text", ""), allow_turkish_title=is_tr_passage)
    p["tts_script"], tr_tts = clean_english_str(p.get("tts_script", ""), allow_turkish_title=is_tr_passage)

    if (tr_title or tr_body or tr_tts) and not is_tr_passage:
        warnings.append({"id": pid, "type": "cleaned_tr_ocr_chars", "detail": "Cleaned stray Turkish OCR chars in main text"})

    # Reading cleanup
    rd = p.get("reading", {})
    cleaned_orig = []
    for q in rd.get("original_questions", []):
        q["section"], _ = clean_english_str(q.get("section", "Questions"))
        q["prompt"], _ = clean_english_str(q.get("prompt", ""))
        q["answer"], _ = clean_english_str(q.get("answer", ""))
        q["explanation"], _ = clean_english_str(q.get("explanation", ""))
        q["options"] = [clean_english_str(opt)[0] for opt in q.get("options", [])]
        cleaned_orig.append(q)
    rd["original_questions"] = cleaned_orig

    cleaned_extra = []
    for q in rd.get("extra_questions", []):
        q["skill"], _ = clean_english_str(q.get("skill", "Comprehension"))
        q["prompt"], _ = clean_english_str(q.get("prompt", ""))
        q["explanation"], _ = clean_english_str(q.get("explanation", ""))
        opts = [clean_english_str(opt)[0] for opt in q.get("options", [])]
        q["options"] = strip_opt_prefix(opts)
        cleaned_extra.append(q)
    rd["extra_questions"] = cleaned_extra
    p["reading"] = rd

    # Listening cleanup & gap-fill TTS check
    ls = p.get("listening", {})
    norm_tts = normalize_for_match(p["tts_script"])
    cleaned_gap = []
    for g in ls.get("gap_fill", []):
        g["prompt"], _ = clean_english_str(g.get("prompt", ""))
        g["hint"], _ = clean_english_str(g.get("hint", "word"))
        ans_list = [clean_english_str(a)[0] for a in g.get("answers", []) if clean_english_str(a)[0]]
        g["answers"] = ans_list
        if ans_list:
            matched = any(normalize_for_match(a) in norm_tts for a in ans_list)
            if not matched:
                warnings.append({
                    "id": pid,
                    "type": "gap_fill_not_verbatim_in_tts",
                    "prompt": g["prompt"],
                    "answers": ans_list,
                })
        cleaned_gap.append(g)
    ls["gap_fill"] = cleaned_gap

    cleaned_lmcq = []
    for q in ls.get("mcq", []):
        q["prompt"], _ = clean_english_str(q.get("prompt", ""))
        q["explanation"], _ = clean_english_str(q.get("explanation", ""))
        opts = [clean_english_str(opt)[0] for opt in q.get("options", [])]
        q["options"] = strip_opt_prefix(opts)
        cleaned_lmcq.append(q)
    ls["mcq"] = cleaned_lmcq

    cleaned_ltf = []
    for tf in ls.get("true_false", []):
        tf["statement"], _ = clean_english_str(tf.get("statement", ""))
        tf["explanation"], _ = clean_english_str(tf.get("explanation", ""))
        cleaned_ltf.append(tf)
    ls["true_false"] = cleaned_ltf
    p["listening"] = ls

    # Writing cleanup (keep meaning_tr and checklist Turkish intact!)
    wr = p.get("writing", {})
    for tkey in ("task1", "task2"):
        tk = wr.get(tkey, {})
        tk["title"], _ = clean_english_str(tk.get("title", ""))
        tk["prompt"], _ = clean_english_str(tk.get("prompt", ""))
        tk["target_words"], _ = clean_english_str(tk.get("target_words", ""))
        tk["model_answer"], _ = clean_english_str(tk.get("model_answer", ""))
        wr[tkey] = tk

    cleaned_vocab = []
    for v in wr.get("useful_vocabulary", []):
        v["term"], _ = clean_english_str(v.get("term", ""))
        v["meaning_tr"] = v.get("meaning_tr", "").strip()
        v["example"], _ = clean_english_str(v.get("example", ""))
        cleaned_vocab.append(v)
    wr["useful_vocabulary"] = cleaned_vocab
    wr["checklist"] = [c.strip() for c in wr.get("checklist", []) if isinstance(c, str) and c.strip()]
    p["writing"] = wr

    # Word count & Audio metadata
    p["word_count"] = len(p["passage_text"].split())
    voice, accent = VOICES[global_idx % len(VOICES)]
    if p["book"] == 1:
        rate = "-8%" if p["passage_number"] <= 40 else "-4%"
    else:
        rate = "+0%"
    slug = slugify(p["title"])
    p["voice"] = voice
    p["accent"] = accent
    p["rate"] = rate
    p["audio_path"] = f"audio/raw{p['book']}/{pid}_{slug}.mp3"

    return p


def validate_strict(p: dict) -> list[str]:
    errs = []
    if len(p.get("passage_text", "").split()) < 25:
        errs.append("passage_text < 25 words")
    if len(p.get("tts_script", "").split()) < 25:
        errs.append("tts_script < 25 words")
    if p.get("book") == 1 and p.get("passage_number") != 87:
        if TR_RE.search(p["passage_text"]) or TR_RE.search(p["tts_script"]):
            errs.append("stray Turkish chars in English text")
    rd = p.get("reading", {})
    if len(rd.get("extra_questions", [])) < 2:
        errs.append("reading.extra_questions < 2")
    for idx, q in enumerate(rd.get("extra_questions", [])):
        if len(q.get("options", [])) != 4 or not (0 <= q.get("answer_index", -1) <= 3):
            errs.append(f"reading.extra_questions[{idx}] invalid options/answer_index")
    ls = p.get("listening", {})
    if len(ls.get("gap_fill", [])) < 2:
        errs.append("listening.gap_fill < 2")
    for idx, g in enumerate(ls.get("gap_fill", [])):
        if not g.get("answers"):
            errs.append(f"listening.gap_fill[{idx}] empty answers")
    if len(ls.get("mcq", [])) < 2:
        errs.append("listening.mcq < 2")
    for idx, q in enumerate(ls.get("mcq", [])):
        if len(q.get("options", [])) != 4 or not (0 <= q.get("answer_index", -1) <= 3):
            errs.append(f"listening.mcq[{idx}] invalid options/answer_index")
    if len(ls.get("true_false", [])) < 2:
        errs.append("listening.true_false < 2")
    for idx, tf in enumerate(ls.get("true_false", [])):
        if tf.get("answer") not in ("True", "False", "Not Given"):
            errs.append(f"listening.true_false[{idx}] invalid answer")
    wr = p.get("writing", {})
    if not wr.get("task1", {}).get("model_answer") or not wr.get("task2", {}).get("model_answer"):
        errs.append("missing writing model_answer")
    if len(wr.get("useful_vocabulary", [])) < 4:
        errs.append("useful_vocabulary < 4")
    if len(wr.get("checklist", [])) < 3:
        errs.append("checklist < 3")
    return errs


def main() -> None:
    raw_list = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    raw_by_id = {item["id"]: item for item in raw_list}

    batch_files = sorted(BATCH_DIR.glob("batch_*.json"))
    generated_by_id: dict[str, dict] = {}
    for bf in batch_files:
        items = json.loads(bf.read_text(encoding="utf-8"))
        for item in items:
            generated_by_id[item["id"]] = item

    missing_ids = [item["id"] for item in raw_list if item["id"] not in generated_by_id]
    if missing_ids:
        raise SystemExit(f"ERROR: Missing {len(missing_ids)} passage(s) from batches: {missing_ids[:20]}")

    warnings: list[dict] = []
    fatal_errors: dict[str, list[str]] = {}
    final_passages: list[dict] = []

    for g_idx, raw_item in enumerate(raw_list):
        pid = raw_item["id"]
        merged = clean_passage_object(dict(generated_by_id[pid]), raw_item, g_idx, warnings)
        errs = validate_strict(merged)
        if errs:
            fatal_errors[pid] = errs
        final_passages.append(merged)

    b1_cnt = sum(1 for p in final_passages if p["book"] == 1)
    b2_cnt = sum(1 for p in final_passages if p["book"] == 2)
    orig_q_cnt = sum(len(p["reading"]["original_questions"]) for p in final_passages)
    extra_q_cnt = sum(len(p["reading"]["extra_questions"]) for p in final_passages)
    ls_q_cnt = sum(
        len(p["listening"]["gap_fill"]) + len(p["listening"]["mcq"]) + len(p["listening"]["true_false"])
        for p in final_passages
    )
    wr_t_cnt = len(final_passages) * 2

    dataset = {
        "meta": {
            "title": "Reader at Work 1 & 2 — Reading, Listening & Writing Study Suite",
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "counts": {
                "total_passages": len(final_passages),
                "book1_passages": b1_cnt,
                "book2_passages": b2_cnt,
                "original_reading_questions": orig_q_cnt,
                "extra_reading_questions": extra_q_cnt,
                "total_reading_questions": orig_q_cnt + extra_q_cnt,
                "listening_questions": ls_q_cnt,
                "writing_tasks": wr_t_cnt,
            },
            "source_notes": {
                "book1": "Reader at Work 1 PDF covers Book Pages 1-150 (Passages 1-102).",
                "book2": "Reader at Work 2 PDF covers Passages 1-225 up to Book Page 448 (Passage #72 omitted in source Flipbook; Appendix A connector drills excluded).",
            },
        },
        "passages": final_passages,
    }

    OUT_JSON.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_JS.write_text("window.PASSAGES_DATA = " + json.dumps(dataset, ensure_ascii=False) + ";\n", encoding="utf-8")

    report = {
        "fatal_errors_count": len(fatal_errors),
        "fatal_errors": fatal_errors,
        "warnings_count": len(warnings),
        "warnings": warnings,
    }
    OUT_REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Merged {len(final_passages)} passages (Book 1: {b1_cnt}, Book 2: {b2_cnt})")
    print(f"Original Reading Qs: {orig_q_cnt} | Extra Reading Qs: {extra_q_cnt} | Listening Qs: {ls_q_cnt} | Writing Tasks: {wr_t_cnt}")
    print(f"Fatal schema errors: {len(fatal_errors)} | Warnings: {len(warnings)}")
    if fatal_errors:
        for pid, errs in list(fatal_errors.items())[:15]:
            print(f"  FATAL {pid}: {errs}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
