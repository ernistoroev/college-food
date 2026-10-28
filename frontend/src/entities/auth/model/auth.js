import { api, getToken, setToken } from '../../../shared/api/client.js';

async function saveSession(response) {
  setToken(response.data.token);
  return response.data.user;
}

export function register({ name, email, password }) {
  return api.post('/auth/register/', { name, email, password }).then(saveSession);
}

export function login({ email, password }) {
  return api.post('/auth/login/', { email, password }).then(saveSession);
}

// Returns the logged-in user, or null if there is no token or it no longer works.
export async function fetchCurrentUser() {
  if (!getToken()) return null;

  try {
    const response = await api.get('/auth/me/');
    return response.data;
  } catch (error) {
    if (error.response?.status === 401) setToken(null);
    return null;
  }
}

export async function logout() {
  try {
    await api.post('/auth/logout/');
  } finally {
    setToken(null);
  }
}

// FormData, not JSON, because the avatar is a file.
export async function updateProfile({ name, course, faculty, avatarFile }) {
  const form = new FormData();
  form.append('name', name);
  form.append('course', course);
  form.append('faculty', faculty);
  if (avatarFile) form.append('avatar', avatarFile);

  const response = await api.patch('/auth/me/', form);
  return response.data;
}
