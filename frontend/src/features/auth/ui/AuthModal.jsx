import { useState } from 'react';
import { X, UserRound, Mail, Lock, ArrowRight } from 'lucide-react';
import { login, register } from '../../../entities/auth/model/auth.js';
import { getErrorMessage } from '../../../shared/api/client.js';

export default function AuthModal({ onClose, onLogin }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');

    if (mode === 'register' && name.trim().length < 2) {
      setError('Введи имя не короче двух символов.');
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError('Введи корректный email.');
      return;
    }

    setSending(true);
    try {
      const user = mode === 'register'
        ? await register({ name: name.trim(), email: email.trim(), password })
        : await login({ email: email.trim(), password });

      onLogin(user);
      onClose();
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="auth-overlay" onMouseDown={event => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <section className="auth-modal">
        <button className="auth-close" onClick={onClose} aria-label="Закрыть">
          <X size={21} />
        </button>

        <div className="auth-icon">
          <UserRound size={28} />
        </div>

        <h2
        style={{
          color: "#171717",
          fontFamily: "Inter, system-ui, sans-serif",
          fontSize: "28px",
          fontWeight: 700,
          letterSpacing: "-0.8px",
          marginBottom: "8px"
        }}
      >
        {mode === 'login' ? 'С возвращением!' : 'Создать аккаунт'}
      </h2>
        <p className="auth-subtitle">
          {mode === 'login'
            ? 'Войди, чтобы оформлять заказы.'
            : 'Зарегистрируйся в College Food.'}
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <label>
              Имя
              <input
                value={name}
                onChange={event => setName(event.target.value)}
                placeholder="Как тебя зовут?"
                autoComplete="name"
                required
              />
            </label>
          )}

          <label>
            Электронная почта
            <span className="auth-input">
              <Mail size={17} />
              <input
                type="email"
                value={email}
                onChange={event => setEmail(event.target.value)}
                placeholder="student@example.com"
                autoComplete="email"
                required
              />
            </span>
          </label>

          <label>
            Пароль
            <span className="auth-input">
              <Lock size={17} />
              <input
                type="password"
                value={password}
                onChange={event => setPassword(event.target.value)}
                placeholder={mode === 'register' ? 'Не меньше 8 символов' : 'Твой пароль'}
                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                required
              />
            </span>
          </label>

          {error && <p className="auth-error">{error}</p>}

          <button className="auth-submit" type="submit" disabled={sending}>
            {sending ? 'Подождите…' : mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
            <ArrowRight size={17} />
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'login' ? 'Впервые здесь?' : 'Уже есть аккаунт?'}{' '}
          <button
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login');
              setError('');
            }}
          >
            {mode === 'login' ? 'Регистрация' : 'Войти'}
          </button>
        </p>
      </section>
    </div>
  );
}
