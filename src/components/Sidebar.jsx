import { useMemo, useRef } from "react";
import { BookOpen, Download, Moon, Search, Sun, Trash2, Upload, X } from "lucide-react";
import { normalizePassageState } from "../hooks/useStudyStore";

export default function Sidebar({
  passages,
  studyState,
  currentPassageId,
  onSelectPassage,
  activeBook,
  onBookChange,
  activeCefr,
  onCefrChange,
  activeProgress,
  onProgressChange,
  searchQuery,
  onSearchChange,
  onToggleTheme,
  onExportProgress,
  onImportProgress,
  onResetProgress,
  isOpen,
  onCloseMobile,
}) {
  const fileInputRef = useRef(null);

  const stats = useMemo(() => {
    let fullDone = 0;
    let lDone = 0;
    let rDone = 0;
    let wDone = 0;
    for (const p of passages) {
      const ps = studyState.passages[p.id];
      if (!ps) continue;
      if (ps.listening?.completed) lDone++;
      if (ps.reading?.completed) rDone++;
      if (ps.writing?.completed) wDone++;
      if (ps.listening?.completed && ps.reading?.completed && ps.writing?.completed) fullDone++;
    }
    const pct = passages.length ? Math.round((fullDone / passages.length) * 100) : 0;
    return { fullDone, lDone, rDone, wDone, pct };
  }, [passages, studyState.passages]);

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return passages.filter((p) => {
      if (activeBook !== "all" && String(p.book) !== activeBook) return false;
      if (activeCefr !== "all" && p.cefr_level !== activeCefr) return false;
      const ps = normalizePassageState(studyState.passages[p.id]);
      const isDone = Boolean(ps.listening.completed && ps.reading.completed && ps.writing.completed);
      if (activeProgress === "completed" && !isDone) return false;
      if (activeProgress === "remaining" && isDone) return false;
      if (q) {
        const hay = `${p.passage_number} ${p.title} ${p.topic} ${p.cefr_level}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [passages, studyState.passages, activeBook, activeCefr, activeProgress, searchQuery]);

  const handleImportFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      onImportProgress(text);
    } catch (err) {
      alert(err?.message || "Dosya içe aktarılamadı.");
    } finally {
      e.target.value = "";
    }
  };

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onCloseMobile} />}
      <aside className={`sidebar ${isOpen ? "open" : ""}`} aria-label="Pasaj Listesi">
        <div className="sidebar-top">
          <div className="brand-row">
            <div className="brand-identity">
              <span className="brand-logo" aria-hidden="true">
                <BookOpen size={18} />
              </span>
              <div>
                <h1 className="brand-title">Reader at Work</h1>
                <p className="brand-sub">1 &amp; 2 · Çalışma Stüdyosu</p>
              </div>
            </div>
            <div className="sidebar-header-actions">
              <button
                type="button"
                className="icon-btn"
                onClick={onToggleTheme}
                title={studyState.theme === "dark" ? "Açık Tema" : "Koyu Tema"}
                aria-label="Tema Değiştir"
              >
                {studyState.theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
              </button>
              <button
                type="button"
                className="icon-btn mobile-only"
                onClick={onCloseMobile}
                aria-label="Menüyü Kapat"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          <div className="overall-progress-card">
            <div className="progress-head">
              <span>
                {stats.fullDone} / {passages.length} pasaj tamamlandı
              </span>
              <span className="progress-pct">{stats.pct}%</span>
            </div>
            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${stats.pct}%` }} />
            </div>
            <div className="skill-mini-stats">
              <span>Listening: {stats.lDone}</span>
              <span>Reading: {stats.rDone}</span>
              <span>Writing: {stats.wDone}</span>
            </div>
          </div>

          <div className="filter-group">
            <div className="segmented-control" role="group" aria-label="Kitap Filtresi">
              {[
                { key: "all", label: "Tümü" },
                { key: "1", label: "Kitap 1" },
                { key: "2", label: "Kitap 2" },
              ].map((item) => (
                <button
                  key={item.key}
                  type="button"
                  className={`seg-btn ${activeBook === item.key ? "active" : ""}`}
                  onClick={() => onBookChange(item.key)}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className="filter-row">
              <select
                value={activeCefr}
                onChange={(e) => onCefrChange(e.target.value)}
                aria-label="Seviye Filtresi"
              >
                <option value="all">Tüm Seviyeler</option>
                <option value="A1">A1</option>
                <option value="A2">A2</option>
                <option value="B1">B1</option>
                <option value="B2">B2</option>
                <option value="C1">C1</option>
              </select>

              <select
                value={activeProgress}
                onChange={(e) => onProgressChange(e.target.value)}
                aria-label="İlerleme Filtresi"
              >
                <option value="all">Tüm Durumlar</option>
                <option value="remaining">Kalanlar</option>
                <option value="completed">Tamamlananlar</option>
              </select>
            </div>

            <div className="search-wrap">
              <Search size={14} className="search-icon" />
              <input
                type="search"
                className="search-input"
                placeholder="No, başlık veya konu ara..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                autoComplete="off"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear"
                  onClick={() => onSearchChange("")}
                  aria-label="Aramayı temizle"
                >
                  <X size={13} />
                </button>
              )}
            </div>

            <div className="filter-count-row">
              <span>Listelenen pasaj</span>
              <span>
                {filtered.length} / {passages.length}
              </span>
            </div>
          </div>
        </div>

        <div className="passage-list">
          {filtered.length === 0 ? (
            <div className="passage-list-empty">Eşleşen pasaj bulunamadı.</div>
          ) : (
            filtered.map((p) => {
              const ps = normalizePassageState(studyState.passages[p.id]);
              return (
                <button
                  key={p.id}
                  type="button"
                  className={`passage-item ${p.id === currentPassageId ? "active" : ""}`}
                  onClick={() => onSelectPassage(p.id)}
                >
                  <div className="passage-item-top">
                    <div className="passage-item-left">
                      <span className="passage-num-pill">
                        K{p.book}·#{p.passage_number}
                      </span>
                      <span className="passage-item-title">{p.title}</span>
                    </div>
                    <span className={`cefr-pill cefr-${p.cefr_level}`}>{p.cefr_level}</span>
                  </div>
                  <div className="passage-item-meta">
                    <span className="passage-item-topic">{p.topic}</span>
                    <span className="rlw-dots">
                      <span className={`rlw-dot ${ps.listening.completed ? "done" : ""}`}>L</span>
                      <span className={`rlw-dot ${ps.reading.completed ? "done" : ""}`}>R</span>
                      <span className={`rlw-dot ${ps.writing.completed ? "done" : ""}`}>W</span>
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>

        <div className="sidebar-footer">
          <button type="button" className="btn-secondary btn-sm" onClick={onExportProgress}>
            <Download size={13} /> Yedekle
          </button>
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={13} /> Yükle
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            style={{ display: "none" }}
            onChange={handleImportFile}
          />
          <button
            type="button"
            className="btn-danger-ghost"
            onClick={onResetProgress}
            title="Tüm ilerlemeyi sıfırla"
            aria-label="Sıfırla"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </aside>
    </>
  );
}
