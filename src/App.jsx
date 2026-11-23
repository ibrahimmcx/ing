import { useEffect, useMemo, useState } from "react";
import { BookOpen, Check, Headphones, PenTool } from "lucide-react";
import { normalizePassageState, useStudyStore } from "./hooks/useStudyStore";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import ListeningTab from "./components/ListeningTab";
import ReadingTab from "./components/ReadingTab";
import WritingTab from "./components/WritingTab";

export default function App() {
  const {
    state: studyState,
    toggleTheme,
    changeFontSize,
    setLastPassageId,
    updatePassageSkill,
    importStateJson,
    resetAllProgress,
  } = useStudyStore();

  const [passages, setPassages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [currentTab, setCurrentTab] = useState("listening");
  const [activeBook, setActiveBook] = useState("all");
  const [activeCefr, setActiveCefr] = useState("all");
  const [activeProgress, setActiveProgress] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let active = true;
    fetch("/data/passages.json")
      .then((res) => {
        if (!res.ok) throw new Error(`Veri yüklenemedi (HTTP ${res.status})`);
        return res.json();
      })
      .then((json) => {
        if (!active) return;
        const list = Array.isArray(json?.passages) ? json.passages : [];
        setPassages(list);
        if (
          list.length > 0 &&
          (!studyState.lastPassageId || !list.some((p) => p.id === studyState.lastPassageId))
        ) {
          setLastPassageId(list[0].id);
        }
        setLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.message || "Veri dosyası okunamadı.");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const currentIdx = useMemo(() => {
    if (!passages.length) return -1;
    const idx = passages.findIndex((p) => p.id === studyState.lastPassageId);
    return idx >= 0 ? idx : 0;
  }, [passages, studyState.lastPassageId]);

  const currentPassage = currentIdx >= 0 ? passages[currentIdx] : null;
  const currentPassageState = useMemo(
    () => normalizePassageState(currentPassage ? studyState.passages[currentPassage.id] : null),
    [currentPassage, studyState.passages]
  );

  const goPrev = () => {
    if (currentIdx > 0) setLastPassageId(passages[currentIdx - 1].id);
  };
  const goNext = () => {
    if (currentIdx >= 0 && currentIdx < passages.length - 1) {
      setLastPassageId(passages[currentIdx + 1].id);
    }
  };

  useEffect(() => {
    const onKeyDown = (e) => {
      if (!e.altKey) return;
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goPrev();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goNext();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  const handleExportProgress = () => {
    const blob = new Blob([JSON.stringify(studyState, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "reader_at_work_progress.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleResetProgress = () => {
    if (!window.confirm("Tüm ilerlemeniz ve yazdığınız taslaklar sıfırlansın mı?")) return;
    resetAllProgress();
  };

  if (loading) {
    return (
      <div className="center-screen">
        <h2>Reader at Work 1 &amp; 2 Yükleniyor...</h2>
        <p className="muted-note">326 pasaj ve çalışma soruları hazırlanıyor.</p>
      </div>
    );
  }

  if (error || !currentPassage) {
    return (
      <div className="center-screen">
        <h2>Veri Yüklenemedi</h2>
        <p className="muted-note">{error || "Pasaj listesi boş."}</p>
      </div>
    );
  }

  const lsCount =
    currentPassage.listening.gap_fill.length +
    currentPassage.listening.mcq.length +
    currentPassage.listening.true_false.length;
  const rdCount =
    currentPassage.reading.original_questions.length +
    currentPassage.reading.extra_questions.length;

  const tabs = [
    { key: "listening", label: "Listening", count: `${lsCount} soru`, Icon: Headphones },
    { key: "reading", label: "Reading", count: `${rdCount} soru`, Icon: BookOpen },
    { key: "writing", label: "Writing", count: "2 görev", Icon: PenTool },
  ];

  return (
    <div className="app-shell">
      <Sidebar
        passages={passages}
        studyState={studyState}
        currentPassageId={currentPassage.id}
        onSelectPassage={(pid) => {
          setLastPassageId(pid);
          setMobileMenuOpen(false);
        }}
        activeBook={activeBook}
        onBookChange={setActiveBook}
        activeCefr={activeCefr}
        onCefrChange={setActiveCefr}
        activeProgress={activeProgress}
        onProgressChange={setActiveProgress}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onToggleTheme={toggleTheme}
        onExportProgress={handleExportProgress}
        onImportProgress={importStateJson}
        onResetProgress={handleResetProgress}
        isOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      <main className="main-area">
        <header className="studio-header">
          <Topbar
            passage={currentPassage}
            hasPrev={currentIdx > 0}
            hasNext={currentIdx >= 0 && currentIdx < passages.length - 1}
            onPrev={goPrev}
            onNext={goNext}
            onOpenMenu={() => setMobileMenuOpen(true)}
          />

          <div className="skill-tabs-bar">
            <nav className="skill-tabs" role="tablist" aria-label="Beceri Sekmeleri">
              {tabs.map(({ key, label, count, Icon }) => {
                const done = Boolean(currentPassageState[key]?.completed);
                const active = currentTab === key;
                return (
                  <button
                    key={key}
                    type="button"
                    role="tab"
                    aria-selected={active}
                    className={`tab-btn ${active ? "active" : ""}`}
                    onClick={() => setCurrentTab(key)}
                  >
                    <Icon size={15} />
                    <span>{label}</span>
                    <span className="tab-count">{count}</span>
                    {done && (
                      <span className="tab-done-icon" aria-label="Tamamlandı">
                        <Check size={11} />
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>

            <span className="shortcut-hint">Kısayol: Alt + ← / →</span>
          </div>
        </header>

        <section className="tab-content">
          {currentTab === "listening" && (
            <ListeningTab
              key={`l_${currentPassage.id}`}
              passage={currentPassage}
              passageState={currentPassageState}
              updateSkill={updatePassageSkill}
            />
          )}
          {currentTab === "reading" && (
            <ReadingTab
              key={`r_${currentPassage.id}`}
              passage={currentPassage}
              passageState={currentPassageState}
              fontSize={studyState.fontSize || 17}
              onChangeFontSize={changeFontSize}
              updateSkill={updatePassageSkill}
            />
          )}
          {currentTab === "writing" && (
            <WritingTab
              key={`w_${currentPassage.id}`}
              passage={currentPassage}
              passageState={currentPassageState}
              updateSkill={updatePassageSkill}
            />
          )}
        </section>
      </main>
    </div>
  );
}
