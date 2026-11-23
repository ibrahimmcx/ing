import { CheckCircle2, RotateCcw } from "lucide-react";
import AudioPlayer from "./AudioPlayer";
import { matchGapFill } from "../utils/grading";

const TF_CHOICES = ["True", "False", "Not Given"];

function renderPromptWithBlanks(prompt) {
  const parts = String(prompt || "").split("____");
  if (parts.length === 1) return prompt;
  return parts.map((chunk, idx) => (
    <span key={idx}>
      {chunk}
      {idx < parts.length - 1 && <span className="inline-blank" aria-label="boşluk" />}
    </span>
  ));
}

export default function ListeningTab({ passage, passageState, updateSkill }) {
  const ls = passage.listening;
  const st = passageState.listening;
  const checked = st.checked;

  const totalQs = ls.gap_fill.length + ls.mcq.length + ls.true_false.length;
  const answeredCount =
    ls.gap_fill.filter((_, i) => String(st.gap[i] ?? "").trim().length > 0).length +
    ls.mcq.filter((_, i) => st.mcq[i] !== undefined).length +
    ls.true_false.filter((_, i) => st.tf[i] !== undefined).length;

  const setGap = (idx, value) => {
    updateSkill(passage.id, "listening", (prev) => ({
      ...prev,
      gap: { ...prev.gap, [idx]: value },
    }));
  };

  const setMcq = (idx, optIdx) => {
    updateSkill(passage.id, "listening", (prev) => ({
      ...prev,
      mcq: { ...prev.mcq, [idx]: optIdx },
    }));
  };

  const setTf = (idx, val) => {
    updateSkill(passage.id, "listening", (prev) => ({
      ...prev,
      tf: { ...prev.tf, [idx]: val },
    }));
  };

  const handleCheck = () => {
    let score = 0;
    ls.gap_fill.forEach((g, i) => {
      if (matchGapFill(g.answers, st.gap[i] ?? "")) score++;
    });
    ls.mcq.forEach((q, i) => {
      if (st.mcq[i] === q.answer_index) score++;
    });
    ls.true_false.forEach((tf, i) => {
      if (st.tf[i] === tf.answer) score++;
    });

    updateSkill(passage.id, "listening", (prev) => ({
      ...prev,
      checked: true,
      score,
      total: totalQs,
      completed: true,
    }));
  };

  const handleReset = () => {
    updateSkill(passage.id, "listening", (prev) => ({
      ...prev,
      gap: {},
      mcq: {},
      tf: {},
      checked: false,
      score: 0,
      completed: false,
    }));
  };

  const scorePct = st.total > 0 ? Math.round((st.score / st.total) * 100) : 0;

  return (
    <div className="content-container">
      <AudioPlayer
        src={passage.audio_path}
        accent={passage.accent}
        voice={passage.voice}
        rate={passage.rate}
        replays={st.replays || 0}
        transcript={passage.tts_script}
        onPlayCount={() =>
          updateSkill(passage.id, "listening", (prev) => ({
            ...prev,
            replays: (prev.replays || 0) + 1,
          }))
        }
      />

      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <h3 className="card-title">Bölüm A · Boşluk Doldurma</h3>
            <span className="section-pill">{ls.gap_fill.length} soru</span>
          </div>
        </div>
        {ls.gap_fill.map((g, i) => {
          const userVal = st.gap[i] ?? "";
          const ok = checked ? matchGapFill(g.answers, userVal) : false;
          return (
            <div key={i} className="question-item">
              <div className="q-prompt">
                {i + 1}. {renderPromptWithBlanks(g.prompt)}
              </div>
              <div className="gap-input-row">
                <input
                  type="text"
                  className={`gap-input ${checked ? (ok ? "correct" : "wrong") : ""}`}
                  value={userVal}
                  onChange={(e) => setGap(i, e.target.value)}
                  placeholder="Duyduğunuz kelimeyi yazın..."
                />
                <span className="badge">İpucu: {g.hint}</span>
              </div>
              {checked && (
                <div className={`feedback-box ${ok ? "ok" : "bad"}`}>
                  {ok ? (
                    "Doğru!"
                  ) : (
                    <>
                      Doğru cevap: <strong>{g.answers.join(" / ")}</strong>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <h3 className="card-title">Bölüm B · Dinlediğini Anlama</h3>
            <span className="section-pill">{ls.mcq.length} soru</span>
          </div>
        </div>
        {ls.mcq.map((q, i) => {
          const sel = st.mcq[i];
          return (
            <div key={i} className="question-item">
              <div className="q-prompt">
                {i + 1}. {q.prompt}
              </div>
              <div className="options-list">
                {q.options.map((opt, oi) => {
                  const isSel = sel === oi;
                  let cls = isSel ? "selected" : "";
                  if (checked) {
                    if (oi === q.answer_index) cls = "correct";
                    else if (isSel) cls = "wrong";
                  }
                  return (
                    <label key={oi} className={`option-card ${cls}`}>
                      <input
                        type="radio"
                        className="sr-only"
                        name={`lmcq_${passage.id}_${i}`}
                        checked={isSel}
                        onChange={() => setMcq(i, oi)}
                      />
                      <span className="option-letter">{String.fromCharCode(65 + oi)}</span>
                      <span>{opt}</span>
                    </label>
                  );
                })}
              </div>
              {checked && (
                <div className={`feedback-box ${sel === q.answer_index ? "ok" : "bad"}`}>
                  {q.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <h3 className="card-title">Bölüm C · True / False / Not Given</h3>
            <span className="section-pill">{ls.true_false.length} ifade</span>
          </div>
        </div>
        {ls.true_false.map((tf, i) => {
          const sel = st.tf[i];
          return (
            <div key={i} className="question-item">
              <div className="q-prompt">
                {i + 1}. {tf.statement}
              </div>
              <div className="tf-btn-row">
                {TF_CHOICES.map((choice) => {
                  let cls = sel === choice ? "selected" : "";
                  if (checked) {
                    if (choice === tf.answer) cls = "correct";
                    else if (sel === choice) cls = "wrong";
                  }
                  return (
                    <button
                      key={choice}
                      type="button"
                      className={`tf-btn ${cls}`}
                      onClick={() => setTf(i, choice)}
                    >
                      {choice}
                    </button>
                  );
                })}
              </div>
              {checked && (
                <div className={`feedback-box ${sel === tf.answer ? "ok" : "bad"}`}>
                  Doğru: <strong>{tf.answer}</strong> — {tf.explanation}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="grading-footer">
        <div className="action-bar" style={{ marginTop: 0 }}>
          <button type="button" className="btn-primary" onClick={handleCheck}>
            <CheckCircle2 size={16} /> Cevapları Kontrol Et
          </button>
          <button type="button" className="btn-secondary" onClick={handleReset}>
            <RotateCcw size={14} /> Sıfırla
          </button>
        </div>

        {checked ? (
          <div className="score-pill">
            Skor: {st.score} / {st.total} Doğru ({scorePct}%)
          </div>
        ) : (
          <span className="muted-note">
            {answeredCount} / {totalQs} soru yanıtlandı
          </span>
        )}
      </div>
    </div>
  );
}
