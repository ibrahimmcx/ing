import { useEffect, useMemo, useRef, useState } from "react";
import { FileText, Headphones, Pause, Play, RotateCcw, RotateCw } from "lucide-react";
import { formatTime } from "../utils/grading";

const FULL_RATES = [0.75, 0.9, 1, 1.15, 1.25];
const COMPACT_RATES = [0.85, 1, 1.15];

function splitParagraphs(text) {
  return String(text || "")
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean);
}

export default function AudioPlayer({
  src,
  accent,
  voice,
  rate,
  replays = 0,
  compact = false,
  onPlayCount,
  transcript,
  transcriptTr,
}) {
  const audioRef = useRef(null);
  const countedPlayRef = useRef(false);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [showTranscript, setShowTranscript] = useState(false);
  const [transcriptMode, setTranscriptMode] = useState("both");

  const resolvedSrc = src ? (src.startsWith("/") ? src : `/${src}`) : "";
  const speeds = compact ? COMPACT_RATES : FULL_RATES;

  const enParas = useMemo(() => splitParagraphs(transcript), [transcript]);
  const trParas = useMemo(() => splitParagraphs(transcriptTr), [transcriptTr]);
  const hasTr = trParas.length > 0;
  const effectiveMode = hasTr ? transcriptMode : "en";

  useEffect(() => {
    const audio = audioRef.current;
    countedPlayRef.current = false;
    setIsPlaying(false);
    setCurrentTime(0);
    setDuration(0);
    setShowTranscript(false);
    if (!audio) return;
    audio.pause();
    audio.currentTime = 0;
    audio.load();
    audio.playbackRate = playbackRate;
  }, [resolvedSrc]);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (audio.paused) {
      audio.play().catch(() => {});
    } else {
      audio.pause();
    }
  };

  const seekBy = (delta) => {
    const audio = audioRef.current;
    if (!audio) return;
    const maxT = Number.isFinite(audio.duration) ? audio.duration : 9999;
    audio.currentTime = Math.max(0, Math.min(maxT, audio.currentTime + delta));
  };

  const handleScrub = (e) => {
    const audio = audioRef.current;
    if (!audio || !audio.duration) return;
    const pct = parseFloat(e.target.value);
    audio.currentTime = (pct / 100) * audio.duration;
  };

  const scrubVal = duration > 0 ? (currentTime / duration) * 100 : 0;

  const audioEl = (
    <audio
      ref={audioRef}
      src={resolvedSrc}
      preload="metadata"
      onPlay={() => {
        setIsPlaying(true);
        if (!countedPlayRef.current && onPlayCount) {
          countedPlayRef.current = true;
          onPlayCount();
        }
      }}
      onPause={() => setIsPlaying(false)}
      onEnded={() => {
        setIsPlaying(false);
        countedPlayRef.current = false;
      }}
      onLoadedMetadata={(e) => setDuration(e.currentTarget.duration || 0)}
      onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime || 0)}
    />
  );

  if (compact) {
    return (
      <div className="audio-compact-wrap">
        {audioEl}
        <div className="audio-controls-row">
          <button type="button" className="btn-secondary btn-sm" onClick={togglePlay}>
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
            {isPlaying ? "Duraklat" : "Sesli Takip"}
          </button>

          <div className="audio-seek-group">
            <button type="button" className="btn-secondary btn-sm" onClick={() => seekBy(-5)} title="5 sn geri">
              <RotateCcw size={13} />
            </button>
            <button type="button" className="btn-secondary btn-sm" onClick={() => seekBy(5)} title="5 sn ileri">
              <RotateCw size={13} />
            </button>
          </div>

          <div className="audio-scrubber-wrap">
            <input
              type="range"
              className="audio-scrubber"
              style={{ "--progress": `${scrubVal}%` }}
              min="0"
              max="100"
              step="0.5"
              value={scrubVal}
              onChange={handleScrub}
              aria-label="Ses konumu"
            />
            <span className="audio-time">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>

          <div className="speed-pills">
            {speeds.map((s) => (
              <button
                key={s}
                type="button"
                className={`speed-btn ${playbackRate === s ? "active" : ""}`}
                onClick={() => setPlaybackRate(s)}
              >
                {s === 1 ? "1.0x" : `${s}x`}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card audio-studio-card">
      {audioEl}
      <div className="card-header">
        <div className="card-title-group">
          <Headphones size={18} style={{ color: "var(--accent)" }} />
          <h3 className="card-title">Ses Kaydı (Metni Açmadan Dinleyin)</h3>
        </div>
        <div className="badge-row" style={{ marginBottom: 0 }}>
          <span className="badge accent">
            {accent} · {voice} ({rate})
          </span>
          <span className="badge">Dinleme: {replays}</span>
        </div>
      </div>

      <div className="audio-dock">
        <button
          type="button"
          className="audio-hero-play"
          onClick={togglePlay}
          aria-label={isPlaying ? "Duraklat" : "Dinle"}
        >
          {isPlaying ? <Pause size={18} /> : <Play size={18} style={{ marginLeft: "2px" }} />}
        </button>

        <div className="audio-seek-group">
          <button type="button" className="btn-secondary btn-sm" onClick={() => seekBy(-5)}>
            <RotateCcw size={13} /> 5s
          </button>
          <button type="button" className="btn-secondary btn-sm" onClick={() => seekBy(5)}>
            5s <RotateCw size={13} />
          </button>
        </div>

        <div className="audio-scrubber-wrap">
          <input
            type="range"
            className="audio-scrubber"
            style={{ "--progress": `${scrubVal}%` }}
            min="0"
            max="100"
            step="0.5"
            value={scrubVal}
            onChange={handleScrub}
            aria-label="Ses konumu"
          />
          <span className="audio-time">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>

      <div className="audio-footer-row">
        <div className="speed-pills" role="group" aria-label="Oynatma hızı">
          {speeds.map((s) => (
            <button
              key={s}
              type="button"
              className={`speed-btn ${playbackRate === s ? "active" : ""}`}
              onClick={() => setPlaybackRate(s)}
            >
              {s === 1 ? "1.0x" : `${s}x`}
            </button>
          ))}
        </div>

        {transcript && (
          <button
            type="button"
            className="btn-secondary btn-sm"
            onClick={() => setShowTranscript((v) => !v)}
          >
            <FileText size={14} />
            {showTranscript ? "Transkripti Gizle" : "Transkripti Göster"}
          </button>
        )}
      </div>

      {transcript && showTranscript && (
        <div className="transcript-panel">
          <div className="transcript-header">
            <span className="transcript-title">Dinleme Metni (Transkript)</span>
            {hasTr && (
              <div className="transcript-mode-pills" role="group" aria-label="Transkript Dili">
                {[
                  { key: "both", label: "EN + TR" },
                  { key: "en", label: "İngilizce" },
                  { key: "tr", label: "Türkçe" },
                ].map((opt) => (
                  <button
                    key={opt.key}
                    type="button"
                    className={`transcript-mode-btn ${effectiveMode === opt.key ? "active" : ""}`}
                    onClick={() => setTranscriptMode(opt.key)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {effectiveMode === "en" && (
            <div className="transcript-body">
              {enParas.map((para, i) => (
                <p key={i} className="transcript-en">
                  {para}
                </p>
              ))}
            </div>
          )}

          {effectiveMode === "tr" && (
            <div className="transcript-body">
              {trParas.map((para, i) => (
                <p key={i} className="transcript-tr transcript-tr-standalone">
                  {para}
                </p>
              ))}
            </div>
          )}

          {effectiveMode === "both" &&
            (enParas.length === trParas.length ? (
              <div className="transcript-pairs">
                {enParas.map((para, i) => (
                  <div key={i} className="transcript-pair">
                    <p className="transcript-en">{para}</p>
                    <p className="transcript-tr">{trParas[i]}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="transcript-body">
                {enParas.map((para, i) => (
                  <p key={`en-${i}`} className="transcript-en">
                    {para}
                  </p>
                ))}
                <div className="transcript-divider">Türkçe Çeviri</div>
                {trParas.map((para, i) => (
                  <p key={`tr-${i}`} className="transcript-tr">
                    {para}
                  </p>
                ))}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
