import { ChevronLeft, ChevronRight, Menu } from "lucide-react";

export default function Topbar({ passage, hasPrev, hasNext, onPrev, onNext, onOpenMenu }) {
  const pagesStr =
    passage.book_pages && passage.book_pages.length
      ? `Sayfa ${passage.book_pages.join("-")}`
      : `PDF s.${(passage.pdf_pages || []).join("-")}`;

  return (
    <div className="topbar-wrapper">
      <div className="topbar-main-row">
        <div className="topbar-left-group">
          <button
            type="button"
            className="icon-btn mobile-only"
            onClick={onOpenMenu}
            aria-label="Menüyü Aç"
          >
            <Menu size={18} />
          </button>

          <div className="topbar-pills">
            <span className="badge accent">
              Kitap {passage.book} · #{passage.passage_number}
            </span>
            <span className={`cefr-pill cefr-${passage.cefr_level}`}>{passage.cefr_level}</span>
          </div>
        </div>

        <div className="topbar-actions">
          <button
            type="button"
            className="btn-secondary btn-nav"
            disabled={!hasPrev}
            onClick={onPrev}
            title="Önceki Pasaj (Alt + Sol Ok)"
          >
            <ChevronLeft size={15} />
            <span>Önceki</span>
          </button>
          <button
            type="button"
            className="btn-secondary btn-nav"
            disabled={!hasNext}
            onClick={onNext}
            title="Sonraki Pasaj (Alt + Sağ Ok)"
          >
            <span>Sonraki</span>
            <ChevronRight size={15} />
          </button>
        </div>
      </div>

      <div className="topbar-title-row">
        <h2 className="passage-heading">{passage.title}</h2>
        <span className="topbar-submeta">
          {passage.topic} · {pagesStr} · {passage.word_count} kelime
        </span>
      </div>
    </div>
  );
}
