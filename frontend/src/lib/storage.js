// This browser's layout preferences (collapsed panels, sizes, the column
// split). Best effort: storage can be blocked or cleared, and the page must
// work the same without it.
const PREFIX = 'fmlink.';
// Keys saved before the FMlink rename; read when there's no new one yet.
const OLD_PREFIX = 'openwave.';

export function load(key, fallback) {
  try {
    let raw = localStorage.getItem(PREFIX + key);
    if (raw === null) raw = localStorage.getItem(OLD_PREFIX + key);
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
