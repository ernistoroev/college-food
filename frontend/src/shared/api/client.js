import axios from 'axios';

const TOKEN_KEY = 'college-food-token';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';

export const api = axios.create({ baseURL: API_URL });

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // Without localStorage the user just stays logged in until the page is reloaded.
  }
}

// Every request carries the token of the logged-in student, if there is one.
api.interceptors.request.use(config => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Turns a DRF error ({"email": ["..."]}, {"detail": "..."}) into one line of text.
export function getErrorMessage(error, fallback = 'Что-то пошло не так. Попробуй ещё раз.') {
  if (!error.response) {
    return 'Нет связи с сервером. Проверь, что backend запущен.';
  }

  const data = error.response.data;
  if (typeof data === 'string' || !data) return fallback;
  if (data.detail) return data.detail;

  const messages = Object.values(data).flat(Infinity).filter(item => typeof item === 'string');
  return messages.length ? messages.join(' ') : fallback;
}
