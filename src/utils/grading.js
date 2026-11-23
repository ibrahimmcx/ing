export function normAnswer(str) {
  return String(str ?? "")
    .toLowerCase()
    .replace(/[-_]/g, " ")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

export function matchGapFill(answers, userVal) {
  const normUser = normAnswer(userVal);
  if (!normUser) return false;
  return (answers || []).some((a) => normAnswer(a) === normUser);
}

export function matchOrigMcqOption(question, optIdx, optText) {
  const ans = String(question?.answer || "").trim();
  const ansLow = ans.toLowerCase();
  const mLetter = ansLow.match(/^([a-d])[.)]/);
  if (mLetter && mLetter[1].charCodeAt(0) - 97 === optIdx) return true;
  if (/^[a-d]$/.test(ansLow) && ansLow.charCodeAt(0) - 97 === optIdx) return true;
  const nAns = normAnswer(ans);
  const nOpt = normAnswer(optText);
  return Boolean(nAns && (nAns === nOpt || (nOpt.includes(nAns) && nAns.length > 3)));
}

export function matchOrigTF(question, choice) {
  const a = normAnswer(question?.answer);
  const c = normAnswer(choice);
  if (c === "true" && (a === "true" || a === "t")) return true;
  if (c === "false" && (a === "false" || a === "f")) return true;
  if (c === "no information" && (a === "no information" || a === "ni" || a === "not given")) {
    return true;
  }
  return false;
}

export function isAutoGradableOrig(question) {
  return (
    question?.type === "true_false" ||
    question?.type === "true_false_ni" ||
    (question?.type === "mcq" && Array.isArray(question.options) && question.options.length > 0)
  );
}

export function countWords(text) {
  const trimmed = String(text || "").trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

export function parseTargetRange(targetStr) {
  const nums = String(targetStr || "").match(/\d+/g);
  if (!nums) return [30, 200];
  if (nums.length >= 2) return [parseInt(nums[0], 10), parseInt(nums[1], 10)];
  const n = parseInt(nums[0], 10);
  return [Math.max(10, Math.round(n * 0.8)), Math.round(n * 1.25)];
}

export function formatTime(sec) {
  if (!Number.isFinite(sec) || sec < 0) return "0:00";
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function buildWritingExportText(passage, writingState) {
  const wr = passage.writing;
  return [
    `Reader at Work ${passage.book} - Passage #${passage.passage_number}: ${passage.title}`,
    `Level: ${passage.cefr_level} | Topic: ${passage.topic}`,
    "",
    `=== TASK 1: ${wr.task1.title} (${wr.task1.target_words}) ===`,
    `Prompt: ${wr.task1.prompt}`,
    "",
    "My Draft:",
    writingState?.task1Text || "(Boş)",
    "",
    "Model Answer:",
    wr.task1.model_answer,
    "",
    `=== TASK 2: ${wr.task2.title} (${wr.task2.target_words}) ===`,
    `Prompt: ${wr.task2.prompt}`,
    "",
    "My Draft:",
    writingState?.task2Text || "(Boş)",
    "",
    "Model Answer:",
    wr.task2.model_answer,
  ].join("\n");
}
