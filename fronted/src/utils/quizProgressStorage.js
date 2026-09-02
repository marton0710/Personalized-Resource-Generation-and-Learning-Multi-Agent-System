const QUIZ_PROGRESS_STORAGE_PREFIX = "zhidao:quiz-progress";

function getLocalStorage() {
  try {
    return typeof window === "undefined" ? null : window.localStorage;
  } catch {
    return null;
  }
}

export function getQuizProgressKey(notebookId, artifactId) {
  const normalizedNotebookId = Number(notebookId);
  if (!Number.isFinite(normalizedNotebookId) || !artifactId) {
    return "";
  }
  return `${QUIZ_PROGRESS_STORAGE_PREFIX}:${normalizedNotebookId}:${artifactId}`;
}

export function readQuizProgress(notebookId, artifactId) {
  const key = getQuizProgressKey(notebookId, artifactId);
  const storage = getLocalStorage();
  if (!key || !storage) {
    return null;
  }
  try {
    const raw = storage.getItem(key);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function writeQuizProgress(notebookId, artifactId, progress) {
  const key = getQuizProgressKey(notebookId, artifactId);
  const storage = getLocalStorage();
  if (!key || !storage) {
    return;
  }
  try {
    storage.setItem(key, JSON.stringify(progress));
  } catch {
    // localStorage may be blocked by browser policy; in-page state still works.
  }
}

export function removeQuizProgress(notebookId, artifactId) {
  const key = getQuizProgressKey(notebookId, artifactId);
  const storage = getLocalStorage();
  if (!key || !storage) {
    return;
  }
  try {
    storage.removeItem(key);
  } catch {
    // Ignore local cache cleanup failures after server-side deletion succeeds.
  }
}

export function clearNotebookQuizProgress(notebookId) {
  const normalizedNotebookId = Number(notebookId);
  const storage = getLocalStorage();
  if (!Number.isFinite(normalizedNotebookId) || !storage) {
    return;
  }

  const prefix = `${QUIZ_PROGRESS_STORAGE_PREFIX}:${normalizedNotebookId}:`;
  try {
    const keys = [];
    for (let index = 0; index < storage.length; index += 1) {
      const key = storage.key(index);
      if (key?.startsWith(prefix)) {
        keys.push(key);
      }
    }
    keys.forEach((key) => storage.removeItem(key));
  } catch {
    // Ignore local cache cleanup failures after server-side deletion succeeds.
  }
}
