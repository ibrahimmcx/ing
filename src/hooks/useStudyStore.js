import { useCallback, useEffect, useState } from "react";

export const STORAGE_KEY = "raw_study_suite_v1";

export function createEmptyPassageState() {
  return {
    listening: {
      gap: {},
      mcq: {},
      tf: {},
      checked: false,
      score: 0,
      total: 0,
      replays: 0,
      completed: false,
    },
    reading: {
      orig: {},
      extra: {},
      origChecked: false,
      extraChecked: false,
      origRevealed: {},
      completed: false,
    },
    writing: {
      task1Text: "",
      task2Text: "",
      checklist: {},
      completed: false,
    },
  };
}

const DEFAULT_STATE = {
  theme: "light",
  fontSize: 17,
  lastPassageId: null,
  passages: {},
};

function loadInitialState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...DEFAULT_STATE, passages: {} };
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_STATE,
      ...parsed,
      passages: parsed?.passages && typeof parsed.passages === "object" ? parsed.passages : {},
    };
  } catch {
    return { ...DEFAULT_STATE, passages: {} };
  }
}

export function normalizePassageState(rawEntry) {
  const base = createEmptyPassageState();
  if (!rawEntry) return base;
  return {
    listening: { ...base.listening, ...(rawEntry.listening || {}) },
    reading: { ...base.reading, ...(rawEntry.reading || {}) },
    writing: { ...base.writing, ...(rawEntry.writing || {}) },
  };
}

export function useStudyStore() {
  const [state, setState] = useState(loadInitialState);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", state.theme);
  }, [state.theme]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      // ignore storage quota errors
    }
  }, [state]);

  const toggleTheme = useCallback(() => {
    setState((prev) => ({
      ...prev,
      theme: prev.theme === "dark" ? "light" : "dark",
    }));
  }, []);

  const changeFontSize = useCallback((delta) => {
    setState((prev) => ({
      ...prev,
      fontSize: Math.min(24, Math.max(13, (prev.fontSize || 17) + delta)),
    }));
  }, []);

  const setLastPassageId = useCallback((pid) => {
    setState((prev) => (prev.lastPassageId === pid ? prev : { ...prev, lastPassageId: pid }));
  }, []);

  const updatePassageSkill = useCallback((pid, skill, updater) => {
    setState((prev) => {
      const currentPassage = normalizePassageState(prev.passages[pid]);
      const nextSkill =
        typeof updater === "function" ? updater(currentPassage[skill]) : { ...currentPassage[skill], ...updater };
      return {
        ...prev,
        passages: {
          ...prev.passages,
          [pid]: {
            ...currentPassage,
            [skill]: nextSkill,
          },
        },
      };
    });
  }, []);

  const importStateJson = useCallback((rawText) => {
    const parsed = JSON.parse(rawText);
    if (!parsed || typeof parsed !== "object" || typeof parsed.passages !== "object") {
      throw new Error("Geçersiz ilerleme dosyası biçimi.");
    }
    setState({
      ...DEFAULT_STATE,
      ...parsed,
      passages: parsed.passages || {},
    });
  }, []);

  const resetAllProgress = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setState({ ...DEFAULT_STATE, passages: {} });
  }, []);

  return {
    state,
    toggleTheme,
    changeFontSize,
    setLastPassageId,
    updatePassageSkill,
    importStateJson,
    resetAllProgress,
  };
}
