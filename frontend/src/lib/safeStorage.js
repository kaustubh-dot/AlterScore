function getStorage(name) {
  try {
    const storage = globalThis?.[name];
    if (!storage || typeof storage.getItem !== 'function') return null;
    return storage;
  } catch {
    return null;
  }
}

export function getSessionStorage() {
  return getStorage('sessionStorage');
}

export function getLocalStorage() {
  return getStorage('localStorage');
}

export function readStorageItem(storage, key) {
  try {
    return storage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

export function writeStorageItem(storage, key, value) {
  try {
    storage?.setItem(key, value);
    return Boolean(storage);
  } catch {
    return false;
  }
}

export function removeStorageItem(storage, key) {
  try {
    storage?.removeItem(key);
  } catch {
    // Storage may be disabled or revoked; clearing is best effort.
  }
}
