import json
from pathlib import Path

WORKSPACE = Path(WORKSPACES[0]) if WORKSPACES else Path(r"c:\Users\culfa\Desktop\ing")
DATA_JSON = WORKSPACE / "data" / "passages.json"
TR_BATCH_DIR = WORKSPACE / "data" / "tr_batches"

TR_SCHEMA = {
    "type": "object",
    "required": ["translations"],
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "tts_script_tr"],
                "properties": {
                    "id": {"type": "string"},
                    "tts_script_tr": {"type": "string"},
                },
            },
        }
    },
}


def make_batches(passages: list[dict]) -> list[tuple[int, list[dict]]]:
    batches: list[tuple[int, list[dict]]] = []
    cur: list[dict] = []
    cur_chars = 0
    for p in passages:
        txt = p.get("tts_script", "")
        if cur and (len(cur) >= 7 or cur_chars + len(txt) > 11500):
            batches.append((len(batches), cur))
            cur = []
            cur_chars = 0
        cur.append({"id": p["id"], "title": p["title"], "tts_script": txt})
        cur_chars += len(txt)
    if cur:
        batches.append((len(batches), cur))
    return batches


def validate_payload(payload: object, expected_items: list[dict]) -> tuple[bool, str, dict[str, str]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("translations"), list):
        return False, "Missing 'translations' list", {}

    exp_by_id = {x["id"]: x["tts_script"] for x in expected_items}
    got_by_id: dict[str, str] = {}
    for row in payload["translations"]:
        if not isinstance(row, dict):
            continue
        pid = row.get("id")
        tr = row.get("tts_script_tr")
        if pid in exp_by_id and pid not in got_by_id and isinstance(tr, str):
            got_by_id[pid] = tr.strip()

    if sorted(got_by_id.keys()) != sorted(exp_by_id.keys()):
        return False, f"ID mismatch: expected {list(exp_by_id)}, got {list(got_by_id)}", {}

    for pid, en_text in exp_by_id.items():
        tr_text = got_by_id[pid]
        min_len = max(40, int(len(en_text) * 0.45))
        if len(tr_text) < min_len:
            return False, f"{pid} translation too short ({len(tr_text)} < {min_len} chars)", {}

    return True, "ok", got_by_id


def build_prompt(batch_idx: int, items: list[dict], retry_note: str = "") -> str:
    retry_block = f"\n\nPREVIOUS ATTEMPT FAILED: {retry_note}\nFix that issue carefully." if retry_note else ""
    return f"""Translate Batch {batch_idx:04d} ({len(items)} English listening transcripts) into natural, accurate Turkish.
Do NOT read or write any workspace files. All inputs are below. Call `finish` with the JSON object matching the schema.

Strict Rules:
1. Output EXACTLY {len(items)} unique items in `translations` matching every input `id` (NO duplicate IDs, NO omitted items).
2. Translate the ENTIRE `tts_script` (including the title line at the top and every sentence) into fluent, natural Turkish using proper Turkish characters (`ç, ğ, ı, İ, ö, ş, ü`).
3. **CRITICAL PARAGRAPH ALIGNMENT**: Preserve the EXACT same `\\n\\n` paragraph breaks as the input `tts_script`!
   - If the input `tts_script` has 1 title paragraph + 3 body paragraphs (4 blocks separated by `\\n\\n`), `tts_script_tr` MUST also have 4 blocks separated by `\\n\\n` (translated title + 3 translated body paragraphs).
4. Keep names, numbers, dates, and idioms accurate while making the Turkish smooth and easy for an English learner to follow alongside the audio.{retry_block}

INPUT TRANSCRIPTS JSON:
{json.dumps(items, ensure_ascii=False)}"""


async def process_batch(batch_tuple: tuple[int, list[dict]]) -> dict:
    batch_idx, items = batch_tuple
    out_file = TR_BATCH_DIR / f"tr_batch_{batch_idx:04d}.json"
    ids_label = ",".join(x["id"] for x in items)

    last_err = ""
    for _ in range(2):
        try:
            prompt = build_prompt(batch_idx, items, retry_note=last_err)
            res = await agent(
                prompt=prompt,
                schema=TR_SCHEMA,
                role=f"TR Batch {batch_idx:04d} ({ids_label})",
                type_name="self",
                model="flash",
            )
            ok, msg, got_by_id = validate_payload(res, items)
            if ok:
                ordered = [{"id": x["id"], "tts_script_tr": got_by_id[x["id"]]} for x in items]
                out_file.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
                return {"status": "ok", "batch_idx": batch_idx, "count": len(ordered)}
            last_err = msg
        except Exception as exc:
            last_err = f"{type(exc).__name__}: {exc}"

    return {"status": "error", "batch_idx": batch_idx, "ids": ids_label, "error": last_err}


async def main() -> None:
    TR_BATCH_DIR.mkdir(parents=True, exist_ok=True)
    passages = json.loads(DATA_JSON.read_text(encoding="utf-8"))["passages"]
    all_batches = make_batches(passages)

    phase("Check existing translation batches")
    pending: list[tuple[int, list[dict]]] = []
    skipped = 0
    for batch_idx, items in all_batches:
        out_file = TR_BATCH_DIR / f"tr_batch_{batch_idx:04d}.json"
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text(encoding="utf-8"))
                ok, _, _ = validate_payload({"translations": existing}, items)
                if ok:
                    skipped += 1
                    continue
            except Exception:
                pass
        pending.append((batch_idx, items))

    log(f"Total TR batches: {len(all_batches)} | Already valid: {skipped} | Pending: {len(pending)}")
    if not pending:
        log("All translation batches already completed!")
        return

    phase("Translate transcripts in waves")
    WAVE_SIZE = 10
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
            log(f"  FAILED tr_batch_{err['batch_idx']:04d} ({err['ids']}): {err['error']}")

    phase("Summary")
    log(f"Finished: {ok_total}/{len(all_batches)} translation batches valid, {len(failed)} failed.")
    if failed:
        print("FAILED_TR_BATCHES:", json.dumps(failed, ensure_ascii=False))
    else:
        print("ALL_TR_BATCHES_SUCCEEDED:", ok_total)


await main()
