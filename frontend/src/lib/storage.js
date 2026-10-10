// This browser's layout preferences (collapsed panels, sizes, the column
// split). Best effort: storage can be blocked or cleared, and the page must
// work the same without it.
const PREFIX = 'openwave.';

export function load(key, fallback) {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function save(key, value) {
  try {
    if (value === null || value === undefined) localStorage.removeItem(PREFIX + key);
    else localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    /* not available - fine */
  }
}
