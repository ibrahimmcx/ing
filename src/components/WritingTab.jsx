import { useRef, useState } from "react";
import { Check, Download, Eye, EyeOff, Plus, Sparkles } from "lucide-react";
import { buildWritingExportText, countWords, parseTargetRange } from "../utils/grading";

function WordBadge({ words, targetStr }) {
  if (!words) {
    return <span className="badge">0 kelime · Hedef: {targetStr}</span>;
  }
  const [minW, maxW] = parseTargetRange(targetStr);
  const cls = words >= minW && words <= maxW ? "success" : "warn";
  return (
    <span className={`badge ${cls}`}>
      {words} kelime · Hedef: {targetStr}
    </span>
  );
}

export default function WritingTab({ passage, passageState, updateSkill }) {
  const [showModel1, setShowModel1] = useState(false);
  const [showModel2, setShowModel2] = useState(false);
  const [activeField, setActiveField] = useState("task2");
  const task1Ref = useRef(null);
  const task2Ref = useRef(null);

  const wr = passage.writing;
  const st = passageState.writing;
  const checklist = wr.checklist || [];
  const checkedCount = checklist.filter((_, i) => Boolean(st.checklist[i])).length;

  const setText = (key, val) => {
    updateSkill(passage.id, "writing", (prev) => ({ ...prev, [key]: val }));
  };

  const insertTerm = (term) => {
    const useTask1 = activeField === "task1";
    const targetEl = useTask1 ? task1Ref.current : task2Ref.current;
    const fieldKey = useTask1 ? "task1Text" : "task2Text";
    const curVal = st[fieldKey] || "";

    const start = targetEl?.selectionStart ?? curVal.length;
    const end = targetEl?.selectionEnd ?? curVal.length;
    const before = curVal.slice(0, start);
    const after = curVal.slice(end);
    const pad = before && !before.endsWith(" ") && !before.endsWith("\n") ? " " : "";
    const nextVal = before + pad + term + after;

    setText(fieldKey, nextVal);
    if (targetEl) {
      requestAnimationFrame(() => {
        targetEl.focus();
        const cursor = (before + pad + term).length;
        targetEl.setSelectionRange(cursor, cursor);
      });
    }
  };

  const handleDownload = () => {
    const content = buildWritingExportText(passage, st);
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${passage.id}_writing.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="writing-layout">
      <div className="writing-main-col">
        <div className={`card ${activeField === "task1" ? "active-editor-card" : ""}`}>
          <div className="card-header">
            <div className="card-title-group">
              <h3 className="card-title">Task 1 · {wr.task1.title}</h3>
              {activeField === "task1" && <span className="badge accent">Aktif alan</span>}
            </div>
            <span className="section-pill">{wr.task1.target_words}</span>
          </div>
          <p className="writing-prompt">{wr.task1.prompt}</p>
          <textarea
            ref={task1Ref}
            className="writing-textarea"
            value={st.task1Text || ""}
            onFocus={() => setActiveField("task1")}
            onChange={(e) => setText("task1Text", e.target.value)}
            placeholder="Task 1 yazınızı buraya yazın..."
          />
          <div className="word-counter-row">
            <WordBadge words={countWords(st.task1Text)} targetStr={wr.task1.target_words} />
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => setShowModel1((v) => !v)}
            >
              {showModel1 ? <EyeOff size={14} /> : <Eye size={14} />}
              {showModel1 ? "Model Cevabı Gizle" : "Model Cevabı Göster"}
            </button>
          </div>
          {showModel1 && <div className="model-answer-box">{wr.task1.model_answer}</div>}
        </div>

        <div className={`card ${activeField === "task2" ? "active-editor-card" : ""}`}>
          <div className="card-header">
            <div className="card-title-group">
              <h3 className="card-title">Task 2 · {wr.task2.title}</h3>
              {activeField === "task2" && <span className="badge accent">Aktif alan</span>}
            </div>
            <span className="section-pill">{wr.task2.target_words}</span>
          </div>
          <p className="writing-prompt">{wr.task2.prompt}</p>
          <textarea
            ref={task2Ref}
            className="writing-textarea writing-textarea-lg"
            value={st.task2Text || ""}
            onFocus={() => setActiveField("task2")}
            onChange={(e) => setText("task2Text", e.target.value)}
            placeholder="Task 2 yazınızı buraya yazın..."
          />
          <div className="word-counter-row">
            <WordBadge words={countWords(st.task2Text)} targetStr={wr.task2.target_words} />
            <button
              type="button"
              className="btn-secondary btn-sm"
              onClick={() => setShowModel2((v) => !v)}
            >
              {showModel2 ? <EyeOff size={14} /> : <Eye size={14} />}
              {showModel2 ? "Model Cevabı Gizle" : "Model Cevabı Göster"}
            </button>
          </div>
          {showModel2 && <div className="model-answer-box">{wr.task2.model_answer}</div>}
        </div>
      </div>

      <aside className="writing-side-rail" aria-label="Yazma Yardımcıları">
        <div className="card card-compact">
          <div className="card-header" style={{ marginBottom: 10 }}>
            <div className="card-title-group">
              <Sparkles size={15} style={{ color: "var(--accent)" }} />
              <h3 className="card-title">Faydalı Kelimeler</h3>
            </div>
            <span className="section-pill">
              {activeField === "task1" ? "Task 1'e ekler" : "Task 2'ye ekler"}
            </span>
          </div>
          <div className="vocab-chips-rail">
            {(wr.useful_vocabulary || []).map((v, i) => (
              <button
                key={i}
                type="button"
                className="vocab-chip"
                title={v.example}
                onClick={() => insertTerm(v.term)}
              >
                <div className="vocab-chip-top">
                  <span className="vocab-chip-term">{v.term}</span>
                  <Plus size={13} style={{ color: "var(--accent)", flexShrink: 0 }} />
                </div>
                <div className="vocab-chip-tr">{v.meaning_tr}</div>
              </button>
            ))}
          </div>
        </div>

        <div className="card card-compact">
          <div className="card-header" style={{ marginBottom: 8 }}>
            <h3 className="card-title">Öz Değerlendirme</h3>
            <span className="section-pill">
              {checkedCount} / {checklist.length}
            </span>
          </div>
          {checklist.map((item, i) => (
            <label key={i} className="checklist-item">
              <input
                type="checkbox"
                checked={Boolean(st.checklist[i])}
                onChange={(e) =>
                  updateSkill(passage.id, "writing", (prev) => ({
                    ...prev,
                    checklist: { ...prev.checklist, [i]: e.target.checked },
                  }))
                }
              />
              <span>{item}</span>
            </label>
          ))}

          <div className="action-bar" style={{ flexDirection: "column", alignItems: "stretch" }}>
            <button
              type="button"
              className="btn-primary"
              onClick={() =>
                updateSkill(passage.id, "writing", (prev) => ({
                  ...prev,
                  completed: !prev.completed,
                }))
              }
            >
              {st.completed ? (
                <>
                  <Check size={15} /> Writing Tamamlandı
                </>
              ) : (
                "Writing Tamamlandı İşaretle"
              )}
            </button>
            <button type="button" className="btn-secondary" onClick={handleDownload}>
              <Download size={14} /> Yazılarımı İndir (.txt)
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
}
