import { useMemo, useState } from "react";
import { BookOpen, Check, CheckCircle2, Eye, EyeOff, Sparkles } from "lucide-react";
import AudioPlayer from "./AudioPlayer";
import { isAutoGradableOrig, matchOrigMcqOption, matchOrigTF } from "../utils/grading";

function stripLeadingLetter(text) {
  return String(text || "").replace(/^[a-dA-D][.)]\s+/, "").trim();
}

export default function ReadingTab({
  passage,
  passageState,
  fontSize,
  onChangeFontSize,
  updateSkill,
}) {
  const [showVocab, setShowVocab] = useState(false);

  const rd = passage.reading;
  const st = passageState.reading;
  const vocabList = passage.writing?.useful_vocabulary || [];

  const paragraphs = useMemo(
    () =>
      String(passage.passage_text || "")
        .split(/\n{2,}/)
        .map((p) => p.trim())
        .filter(Boolean),
    [passage.passage_text]
  );

  const hasAutoOrig = rd.original_questions.some(isAutoGradableOrig);
  const extraChecked = st.extraChecked;
  const extraScore = extraChecked
    ? rd.extra_questions.reduce((acc, q, i) => (st.extra[i] === q.answer_index ? acc + 1 : acc), 0)
    : 0;

  const setOrigAnswer = (idx, value) => {
    updateSkill(passage.id, "reading", (prev) => ({
      ...prev,
      orig: { ...prev.orig, [idx]: value },
    }));
  };

  const toggleOrigReveal = (idx) => {
    updateSkill(passage.id, "reading", (prev) => ({
      ...prev,
      origRevealed: { ...prev.origRevealed, [idx]: !prev.origRevealed[idx] },
    }));
  };

  const setExtraAnswer = (idx, optIdx) => {
    updateSkill(passage.id, "reading", (prev) => ({
      ...prev,
      extra: { ...prev.extra, [idx]: optIdx },
    }));
  };

  return (
    <div className="content-container">
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <BookOpen size={18} style={{ color: "var(--accent)" }} />
            <h3 className="card-title">Okuma Parçası</h3>
          </div>

          <div className="reading-toolbar">
            <div className="font-stepper" role="group" aria-label="Yazı boyutu">
              <button type="button" onClick={() => onChangeFontSize(-1)} title="Yazıyı küçült">
                A-
              </button>
              <span>{fontSize}px</span>
              <button type="button" onClick={() => onChangeFontSize(1)} title="Yazıyı büyüt">
                A+
              </button>
            </div>
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => setShowVocab((v) => !v)}
            >
              <Sparkles size={13} />
              {showVocab ? "Kelimeleri Gizle" : `Kelime Kartları (${vocabList.length})`}
            </button>
          </div>
        </div>

        {showVocab && (
          <div className="vocab-grid">
            {vocabList.map((v, i) => (
              <div key={i} className="vocab-card">
                <div className="vocab-card-head">
                  <span className="vocab-card-term">{v.term}</span>
                  <span className="vocab-card-tr">{v.meaning_tr}</span>
                </div>
                <p className="vocab-card-ex">{v.example}</p>
              </div>
            ))}
          </div>
        )}

        <AudioPlayer src={passage.audio_path} compact />

        <article className="reading-sheet" style={{ fontSize: `${fontSize}px` }}>
          {paragraphs.map((para, idx) => (
            <p key={idx}>{para}</p>
          ))}
        </article>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <h3 className="card-title">Kitaptaki Orijinal Sorular</h3>
            <span className="section-pill">{rd.original_questions.length} soru</span>
          </div>
        </div>

        {rd.original_questions.length === 0 ? (
          <p className="muted-note">
            Bu pasajın kaynak PDF sayfasında orijinal soru yer almıyor; aşağıdaki Ekstra Sınav
            Sorularını çözebilirsiniz.
          </p>
        ) : (
          rd.original_questions.map((q, i) => {
            const showSection =
              q.section && (i === 0 || rd.original_questions[i - 1]?.section !== q.section);
            const auto = isAutoGradableOrig(q);

            if (auto && q.type === "mcq") {
              const sel = st.orig[i];
              const userRight = sel !== undefined && matchOrigMcqOption(q, sel, q.options[sel]);
              return (
                <div key={i}>
                  {showSection && <div className="q-section-label">{q.section}</div>}
                  <div className="question-item">
                    <div className="q-prompt">
                      {i + 1}. {q.prompt}
                    </div>
                    <div className="options-list">
                      {q.options.map((opt, oi) => {
                        const isSel = sel === oi;
                        let cls = isSel ? "selected" : "";
                        if (st.origChecked) {
                          if (matchOrigMcqOption(q, oi, opt)) cls = "correct";
                          else if (isSel) cls = "wrong";
                        }
                        return (
                          <label key={oi} className={`option-card ${cls}`}>
                            <input
                              type="radio"
                              className="sr-only"
                              name={`origq_${passage.id}_${i}`}
                              checked={isSel}
                              onChange={() => setOrigAnswer(i, oi)}
                            />
                            <span className="option-letter">{String.fromCharCode(65 + oi)}</span>
                            <span>{stripLeadingLetter(opt)}</span>
                          </label>
                        );
                      })}
                    </div>
                    {st.origChecked && (
                      <div className={`feedback-box ${userRight ? "ok" : "bad"}`}>
                        Cevap: <strong>{q.answer}</strong> — {q.explanation}
                      </div>
                    )}
                  </div>
                </div>
              );
            }

            if (auto) {
              const isThree = q.type === "true_false_ni";
              const choices = isThree ? ["True", "False", "No Information"] : ["True", "False"];
              const sel = st.orig[i];
              const userRight = Boolean(sel && matchOrigTF(q, sel));
              return (
                <div key={i}>
                  {showSection && <div className="q-section-label">{q.section}</div>}
                  <div className="question-item">
                    <div className="q-prompt">
                      {i + 1}. {q.prompt}
                    </div>
                    <div className={`tf-btn-row ${isThree ? "" : "tf-two"}`}>
                      {choices.map((c) => {
                        let cls = sel === c ? "selected" : "";
                        if (st.origChecked) {
                          if (matchOrigTF(q, c)) cls = "correct";
                          else if (sel === c) cls = "wrong";
                        }
                        return (
                          <button
                            key={c}
                            type="button"
                            className={`tf-btn ${cls}`}
                            onClick={() => setOrigAnswer(i, c)}
                          >
                            {c}
                          </button>
                        );
                      })}
                    </div>
                    {st.origChecked && (
                      <div className={`feedback-box ${userRight ? "ok" : "bad"}`}>
                        Cevap: <strong>{q.answer}</strong> — {q.explanation}
                      </div>
                    )}
                  </div>
                </div>
              );
            }

            const userText = st.orig[i] ?? "";
            const revealed = Boolean(st.origRevealed[i]);
            return (
              <div key={i}>
                {showSection && <div className="q-section-label">{q.section}</div>}
                <div className="question-item">
                  <div className="q-prompt">
                    {i + 1}. {q.prompt}
                  </div>
                  <div className="open-answer-row">
                    <input
                      type="text"
                      className="open-answer-input"
                      value={userText}
                      onChange={(e) => setOrigAnswer(i, e.target.value)}
                      placeholder="Yanıtınızı yazın..."
                    />
                    <button
                      type="button"
                      className="btn-secondary btn-sm"
                      onClick={() => toggleOrigReveal(i)}
                    >
                      {revealed ? <EyeOff size={14} /> : <Eye size={14} />}
                      {revealed ? "Cevabı Gizle" : "Cevabı Göster"}
                    </button>
                  </div>
                  {revealed && (
                    <div className="feedback-box">
                      <strong>Cevap:</strong> {q.answer}
                      <br />
                      <span className="muted-note">{q.explanation}</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {hasAutoOrig && (
          <div className="action-bar">
            <button
              type="button"
              className="btn-primary"
              onClick={() =>
                updateSkill(passage.id, "reading", (prev) => ({ ...prev, origChecked: true }))
              }
            >
              <CheckCircle2 size={15} /> Orijinal Testi Kontrol Et
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <h3 className="card-title">Ekstra Sınav Soruları (Proficiency / IELTS / TOEFL)</h3>
            <span className="section-pill">{rd.extra_questions.length} soru</span>
          </div>
          {extraChecked && (
            <span className="score-pill">
              {extraScore} / {rd.extra_questions.length} Doğru
            </span>
          )}
        </div>

        {rd.extra_questions.map((q, i) => {
          const sel = st.extra[i];
          return (
            <div key={i} className="question-item">
              <div className="q-prompt">
                {i + 1}. <span className="badge accent">{q.skill}</span> {q.prompt}
              </div>
              <div className="options-list">
                {q.options.map((opt, oi) => {
                  const isSel = sel === oi;
                  let cls = isSel ? "selected" : "";
                  if (extraChecked) {
                    if (oi === q.answer_index) cls = "correct";
                    else if (isSel) cls = "wrong";
                  }
                  return (
                    <label key={oi} className={`option-card ${cls}`}>
                      <input
                        type="radio"
                        className="sr-only"
                        name={`rextra_${passage.id}_${i}`}
                        checked={isSel}
                        onChange={() => setExtraAnswer(i, oi)}
                      />
                      <span className="option-letter">{String.fromCharCode(65 + oi)}</span>
                      <span>{opt}</span>
                    </label>
                  );
                })}
              </div>
              {extraChecked && (
                <div className={`feedback-box ${sel === q.answer_index ? "ok" : "bad"}`}>
                  {q.explanation}
                </div>
              )}
            </div>
          );
        })}

        <div className="action-bar">
          <button
            type="button"
            className="btn-primary"
            onClick={() =>
              updateSkill(passage.id, "reading", (prev) => ({
                ...prev,
                extraChecked: true,
                completed: true,
              }))
            }
          >
            <CheckCircle2 size={15} /> Ekstra Soruları Kontrol Et
          </button>
          <button
            type="button"
            className="btn-secondary"
            onClick={() =>
              updateSkill(passage.id, "reading", (prev) => ({
                ...prev,
                completed: !prev.completed,
              }))
            }
          >
            {st.completed ? (
              <>
                <Check size={15} /> Reading Tamamlandı
              </>
            ) : (
              "Reading Tamamlandı İşaretle"
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
