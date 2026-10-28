import { api, clearTokens, getAccessToken, setTokens } from '../../../shared/api/client.js';

function saveSession(response) {
  setTokens({ access: response.data.access, refresh: response.data.refresh });
  return response.data.user;
}

export function register({ name, email, password }) {
  return api.post('/auth/register/', { name, email, password }).then(saveSession);
}

export function login({ email, password }) {
  return api.post('/auth/login/', { email, password }).then(saveSession);
}

// Returns the logged-in user (with role: 'student' / 'staff'), or null if there is no working token.
export async function fetchCurrentUser() {
  if (!getAccessToken()) return null;

  try {
    const response = await api.get('/auth/me/');
    return response.data;
  } catch (error) {
    if (error.response?.status === 401) clearTokens();
    return null;
  }
}

// JWT has no logout on the server: forgetting the tokens is enough.
export async function logout() {
  clearTokens();
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
