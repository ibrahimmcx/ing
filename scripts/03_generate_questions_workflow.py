import json
from pathlib import Path

WORKSPACE = Path(WORKSPACES[0]) if WORKSPACES else Path(r"c:\Users\culfa\Desktop\ing")
RAW_PATH = WORKSPACE / "data" / "raw_passages.json"
BATCH_DIR = WORKSPACE / "data" / "batches"

PASSAGE_SCHEMA = {
    "type": "object",
    "required": ["passages"],
    "properties": {
        "passages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "book",
                    "passage_number",
                    "title",
                    "cefr_level",
                    "topic",
                    "book_pages",
                    "passage_text",
                    "tts_script",
                    "reading",
                    "listening",
                    "writing",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "book": {"type": "integer"},
                    "passage_number": {"type": "integer"},
                    "title": {"type": "string"},
                    "cefr_level": {"type": "string", "enum": ["A1", "A2", "B1", "B2", "C1"]},
                    "topic": {"type": "string"},
                    "book_pages": {"type": "array", "items": {"type": "integer"}},
                    "passage_text": {"type": "string"},
                    "tts_script": {"type": "string"},
                    "reading": {
                        "type": "object",
                        "required": ["original_questions", "extra_questions"],
                        "properties": {
                            "original_questions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["section", "type", "prompt", "options", "answer", "explanation"],
                                    "properties": {
                                        "section": {"type": "string"},
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "true_false",
                                                "true_false_ni",
                                                "mcq",
                                                "reference",
                                                "vocabulary",
                                                "fill_blank",
                                                "open_ended",
                                            ],
                                        },
                                        "prompt": {"type": "string"},
                                        "options": {"type": "array", "items": {"type": "string"}},
                                        "answer": {"type": "string"},
                                        "explanation": {"type": "string"},
                                    },
                                },
                            },
                            "extra_questions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["skill", "prompt", "options", "answer_index", "explanation"],
                                    "properties": {
                                        "skill": {"type": "string"},
                                        "prompt": {"type": "string"},
                                        "options": {"type": "array", "items": {"type": "string"}},
                                        "answer_index": {"type": "integer"},
                                        "explanation": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                    "listening": {
                        "type": "object",
                        "required": ["gap_fill", "mcq", "true_false"],
                        "properties": {
                            "gap_fill": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["prompt", "answers", "hint"],
                                    "properties": {
                                        "prompt": {"type": "string"},
                                        "answers": {"type": "array", "items": {"type": "string"}},
                                        "hint": {"type": "string"},
                                    },
                                },
                            },
                            "mcq": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["prompt", "options", "answer_index", "explanation"],
                                    "properties": {
                                        "prompt": {"type": "string"},
                                        "options": {"type": "array", "items": {"type": "string"}},
                                        "answer_index": {"type": "integer"},
                                        "explanation": {"type": "string"},
                                    },
                                },
                            },
                            "true_false": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["statement", "answer", "explanation"],
                                    "properties": {
                                        "statement": {"type": "string"},
                                        "answer": {"type": "string", "enum": ["True", "False", "Not Given"]},
                                        "explanation": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                    "writing": {
                        "type": "object",
                        "required": ["task1", "task2", "useful_vocabulary", "checklist"],
                        "properties": {
                            "task1": {
                                "type": "object",
                                "required": ["title", "prompt", "target_words", "model_answer"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "prompt": {"type": "string"},
                                    "target_words": {"type": "string"},
                                    "model_answer": {"type": "string"},
                                },
                            },
                            "task2": {
                                "type": "object",
                                "required": ["title", "prompt", "target_words", "model_answer"],
                                "properties": {
                                    "title": {"type": "string"},
                                    "prompt": {"type": "string"},
                                    "target_words": {"type": "string"},
                                    "model_answer": {"type": "string"},
                                },
                            },
                            "useful_vocabulary": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["term", "meaning_tr", "example"],
                                    "properties": {
                                        "term": {"type": "string"},
                                        "meaning_tr": {"type": "string"},
                                        "example": {"type": "string"},
                                    },
                                },
                            },
                            "checklist": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        }
    },
}


def make_batches(raw_passages: list[dict]) -> list[tuple[int, list[dict]]]:
    batches: list[tuple[int, list[dict]]] = []
    cur: list[dict] = []
    cur_chars = 0
    for p in raw_passages:
        clen = len(p["raw_text"])
        if cur and (len(cur) >= 4 or cur_chars + clen > 8500):
            batches.append((len(batches), cur))
            cur = []
            cur_chars = 0
        cur.append(p)
        cur_chars += clen
    if cur:
        batches.append((len(batches), cur))
    return batches


def validate_batch_payload(payload: object, expected_items: list[dict]) -> tuple[bool, str]:
    if not isinstance(payload, dict) or "passages" not in payload or not isinstance(payload["passages"], list):
        return False, "Missing 'passages' list"
    raw_got = [x for x in payload["passages"] if isinstance(x, dict)]
    exp_ids = [x["id"] for x in expected_items]
    by_id: dict[str, dict] = {}
    for item in raw_got:
        pid = item.get("id")
        if pid in exp_ids and pid not in by_id:
            by_id[pid] = item
    if sorted(by_id.keys()) != sorted(exp_ids):
        got_ids = [x.get("id") for x in raw_got]
        return False, f"ID mismatch: expected {exp_ids}, got {got_ids}"
    got = [by_id[eid] for eid in exp_ids]
    for p in got:
        if len(p.get("passage_text", "").split()) < 20:
            return False, f"{p.get('id')} passage_text too short"
        if len(p.get("tts_script", "").split()) < 20:
            return False, f"{p.get('id')} tts_script too short"
        rd = p.get("reading", {})
        ls = p.get("listening", {})
        wr = p.get("writing", {})
        if len(rd.get("extra_questions", [])) < 2:
            return False, f"{p.get('id')} needs >=2 reading.extra_questions"
        for q in rd.get("extra_questions", []):
            if len(q.get("options", [])) != 4 or not (0 <= q.get("answer_index", -1) <= 3):
                return False, f"{p.get('id')} invalid reading.extra_questions MCQ"
        if len(ls.get("gap_fill", [])) < 2:
            return False, f"{p.get('id')} needs >=2 listening.gap_fill"
        if len(ls.get("mcq", [])) < 2:
            return False, f"{p.get('id')} needs >=2 listening.mcq"
        for q in ls.get("mcq", []):
            if len(q.get("options", [])) != 4 or not (0 <= q.get("answer_index", -1) <= 3):
                return False, f"{p.get('id')} invalid listening.mcq"
        if len(ls.get("true_false", [])) < 2:
            return False, f"{p.get('id')} needs >=2 listening.true_false"
        if not wr.get("task1", {}).get("model_answer") or not wr.get("task2", {}).get("model_answer"):
            return False, f"{p.get('id')} missing writing model_answer"
        if len(wr.get("useful_vocabulary", [])) < 4 or len(wr.get("checklist", [])) < 3:
            return False, f"{p.get('id')} insufficient vocabulary/checklist"
    return True, "ok"


def build_prompt(batch_idx: int, items: list[dict], retry_note: str = "") -> str:
    compact_inputs = []
    for item in items:
        compact_inputs.append(
            {
                "id": item["id"],
                "book": item["book"],
                "passage_number": item["display_number"],
                "ocr_title": item["title"],
                "book_pages": item["book_pages"],
                "page_gap_after": item.get("page_gap_after", False),
                "raw_ocr_text": item["raw_text"],
            }
        )

    retry_block = f"\n\nPREVIOUS ATTEMPT FAILED VALIDATION: {retry_note}\nFix that exact issue." if retry_note else ""

    return f"""Process Batch {batch_idx:04d} of Reader at Work passages ({len(items)} passage(s)).
Do NOT read or write any workspace files. All input data is embedded below. Call `finish` with the JSON object matching the schema.

For EVERY input passage (output EXACTLY {len(items)} unique items in `passages`, with NO duplicate IDs), produce one complete entry in `passages` preserving the exact `id`, `book`, `passage_number`, and `book_pages`:

1. **OCR Cleanup & Metadata**:
   - `title`: Properly capitalized, OCR-corrected English title (fix typos like `DAV`->`DAY`, `RUTIN`->`RUIN`, `SIZ`->`SİZ` only if Turkish word `'SEN' OR 'SİZ'?` in #87).
   - `cefr_level`: Assign realistic level (`A1`/`A2`/`B1` for Book 1, `B1`/`B2`/`C1` for Book 2).
   - `topic`: 2-4 word topic tag (e.g. "Astronomy & Space").
   - `passage_text`: 100% clean English passage ONLY. Separate paragraphs with `\\n\\n`. Remove ALL stray line numbers, page numbers, OCR smudges, and ALL exercise/question text at the bottom. Fix OCR errors (`ali.`->`all.`, `oi`->`of`, `] ,000`->`1,000`, `Will`->`will`, `İ`->`I`, `Şato`->`Sato`, broken hyphenation, etc.) while staying faithful to the original passage wording! If `page_gap_after` is true and the raw text ends mid-sentence, trim cleanly or note naturally without inventing false facts.
   - `tts_script`: Natural spoken narration script for Edge-TTS. Begin with `<title>.\\n\\n` followed by smooth spoken text (expand awkward symbols/footnotes like `*`, remove print artifacts/URLs or read ads/letters cleanly so TTS sounds natural).

2. **Reading (`reading`)**:
   - `original_questions`: Extract ALL original questions/exercises present in `raw_ocr_text` (or `[]` only if none appear in `raw_ocr_text`).
     * Clean OCR typos in prompts and options.
     * `type`: `"true_false"`, `"true_false_ni"`, `"mcq"`, `"reference"`, `"vocabulary"`, `"fill_blank"`, or `"open_ended"`.
     * **CRITICAL**: Whenever an original question refers to a line number (e.g. `Line 4, 'they' refers to` or `'currencies' (line 6)`), include the surrounding short quote from `passage_text` inside the prompt (e.g. `What does 'they' refer to in "First, they may provide bonds"?`) so the question is completely solvable WITHOUT line numbers!
     * For `true_false`, set `options: ["True", "False"]`. For `true_false_ni`, set `options: ["True", "False", "No Information"]`. For `mcq`, include clean `options` (`["a) ...", "b) ...", ...]`). For open-ended/reference/vocabulary/fill_blank, set `options: []`.
     * Provide accurate `answer` and concise `explanation` citing evidence from the passage.
   - `extra_questions`: Add **2 to 3** exam-grade MCQs (Proficiency / IELTS / TOEFL style: Main Idea, Inference, Vocabulary in Context, Detail, or Author's Purpose). Each has `skill`, `prompt`, `options` (4 clean choices WITHOUT `"A) "` prefix), `answer_index` (0..3), and `explanation`.

3. **Listening (`listening`)** — Solvable strictly from hearing `tts_script` (never ask about line numbers or spelling quirks):
   - `gap_fill`: **2 to 3** sentence-completion items with `____` for ONE missing word or short 1-2 word phrase. **CRITICAL**: `answers` MUST list 1-3 accepted forms where the primary answer appears **verbatim** (case-insensitive) inside `tts_script`! Include a short `hint` (e.g. `"number"`, `"noun"`, `"adjective"`).
   - `mcq`: **2 to 3** comprehension MCQs (`prompt`, 4 `options` without prefix, `answer_index` 0..3, `explanation`).
   - `true_false`: **2** statements (`statement`, `answer`: `"True"` | `"False"` | `"Not Given"`, `explanation`).

4. **Writing (`writing`)** — Scaled to `cefr_level`:
   - `task1`: Summary/Paraphrase (or Guided Short Response for A1-A2) with `title`, `prompt`, `target_words` (e.g. `"60-80 words"` or `"100-120 words"`), and full `model_answer`.
   - `task2`: Opinion/Discussion Paragraph (Book 1) or Mini-Essay (Book 2) with `title`, `prompt`, `target_words` (e.g. `"80-110 words"` for A1-A2, `"150-200 words"` for B1-C1), and full `model_answer`.
   - `useful_vocabulary`: **5 to 6** useful words/collocations from the passage, each with `term`, concise Turkish meaning `meaning_tr`, and natural `example` sentence.
   - `checklist`: **4** concise Turkish self-assessment checklist items for the student.

Ensure ZERO Turkish OCR noise characters (`üÜşŞğĞıİöÖçÇ`) appear in any English field (`passage_text`, `tts_script`, prompts, options, model answers), except genuine Turkish words if explicitly quoted (like `'SEN' OR 'SİZ'?`).{retry_block}

INPUT PASSAGES JSON:
{json.dumps(compact_inputs, ensure_ascii=False)}"""


async def process_batch(batch_tuple: tuple[int, list[dict]]) -> dict:
    batch_idx, items = batch_tuple
    out_file = BATCH_DIR / f"batch_{batch_idx:04d}.json"
    ids_label = ",".join(x["id"] for x in items)

    last_err = ""
    for attempt in range(2):
        try:
            prompt = build_prompt(batch_idx, items, retry_note=last_err)
            res = await agent(
                prompt=prompt,
                schema=PASSAGE_SCHEMA,
                role=f"Batch {batch_idx:04d} ({ids_label})",
                type_name="self",
                model="flash",
            )
            ok, msg = validate_batch_payload(res, items)
            if ok:
                # Reorder passages to match input item order (keep first occurrence per ID)
                by_id: dict[str, dict] = {}
                for p in res["passages"]:
                    pid = p.get("id")
                    if pid and pid not in by_id:
                        by_id[pid] = p
                ordered = [by_id[x["id"]] for x in items]
                out_file.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
                return {"status": "ok", "batch_idx": batch_idx, "count": len(ordered)}
            last_err = msg
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"

    return {"status": "error", "batch_idx": batch_idx, "ids": ids_label, "error": last_err}


async def main() -> None:
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    raw_passages = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    all_batches = make_batches(raw_passages)

    phase("Check existing batches")
    pending: list[tuple[int, list[dict]]] = []
    skipped = 0
    for batch_idx, items in all_batches:
        out_file = BATCH_DIR / f"batch_{batch_idx:04d}.json"
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text(encoding="utf-8"))
                ok, _ = validate_batch_payload({"passages": existing}, items)
                if ok:
                    skipped += 1
                    continue
            except Exception:
                pass
        pending.append((batch_idx, items))

    log(f"Total batches: {len(all_batches)} | Already valid: {skipped} | Pending: {len(pending)}")

    if not pending:
        log("All batches already completed!")
        return

    phase("Generate questions in waves")
    WAVE_SIZE = 8
    ok_total = skipped
    failed: list[dict] = []

    for start in range(0, len(pending), WAVE_SIZE):
        wave = pending[start : start + WAVE_SIZE]
        wave_num = start // WAVE_SIZE + 1
        total_waves = (len(pending) + WAVE_SIZE - 1) // WAVE_SIZE
        log(f"Starting wave {wave_num}/{total_waves} ({len(wave)} batches)...")
        results = await parallel(wave, process_batch)
        wave_ok = sum(1 for r in results if r["status"] == "ok")
        wave_err = [r for r in results if r["status"] != "ok"]
        ok_total += wave_ok
        failed.extend(wave_err)
        log(f"Wave {wave_num}/{total_waves} done: +{wave_ok} ok, {len(wave_err)} failed | Cumulative ok: {ok_total}/{len(all_batches)}")
        for err in wave_err:
            log(f"  FAILED batch {err['batch_idx']:04d} ({err['ids']}): {err['error']}")

    phase("Summary")
    log(f"Finished: {ok_total}/{len(all_batches)} batches valid, {len(failed)} failed.")
    if failed:
        print("FAILED_BATCHES:", json.dumps(failed, ensure_ascii=False))
    else:
        print("ALL_BATCHES_SUCCEEDED:", ok_total)


await main()
