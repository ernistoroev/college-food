const STORAGE_KEY = 'college-food-user';

export function getCurrentUser() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

export function saveCurrentUser(user) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

export function clearCurrentUser() {
  localStorage.removeItem(STORAGE_KEY);
}
