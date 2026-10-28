import axios from 'axios';

const ACCESS_KEY = 'college-food-access';
const REFRESH_KEY = 'college-food-refresh';

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';

export const api = axios.create({ baseURL: API_URL });

function read(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function getAccessToken() {
  return read(ACCESS_KEY);
}

// JWT: access goes with every request (30 minutes), refresh gets a new access (7 days).
export function setTokens({ access, refresh } = {}) {
  try {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    else localStorage.removeItem(ACCESS_KEY);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
    else if (!access) localStorage.removeItem(REFRESH_KEY);
  } catch {
    // Without localStorage the user just stays logged in until the page is reloaded.
  }
}

export function clearTokens() {
  setTokens();
}

api.interceptors.request.use(config => {
  const access = getAccessToken();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

// When the access token has expired (401), get a new one with the refresh token and repeat the request once.
api.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config;
    const refresh = read(REFRESH_KEY);

    if (error.response?.status !== 401 || !refresh || original._retried || original.url === '/auth/refresh/') {
      return Promise.reject(error);
    }

    original._retried = true;
    try {
      const response = await api.post('/auth/refresh/', { refresh });
      setTokens({ access: response.data.access, refresh });
      return api(original);
    } catch {
      clearTokens();
      return Promise.reject(error);
    }
  }
);

// Lists come in pages {count, next, previous, results}; page_size=100 gets everything the site needs at once.
export async function getList(url, params = {}) {
  const response = await api.get(url, { params: { page_size: 100, ...params } });
  return response.data.results;
}

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
