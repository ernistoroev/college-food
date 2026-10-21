import { useState } from 'react';
import { X, UserRound, Mail, ArrowRight } from 'lucide-react';
import { saveCurrentUser } from '../../../entities/auth/model/auth.js';

export default function AuthModal({ onClose, onLogin }) {
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(event) {
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

    const user = {
      name: mode === 'register' ? name.trim() : email.split('@')[0],
      email: email.trim().toLowerCase()
    };

    saveCurrentUser(user);
    onLogin(user);
    onClose();
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

          {error && <p className="auth-error">{error}</p>}

          <button className="auth-submit" type="submit">
            {mode === 'login' ? 'Войти' : 'Зарегистрироваться'}
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

        <p className="auth-demo-note">
          Демоверсия: вход сохраняется в этом браузере и пока не проверяет пароль или email.
        </p>
      </section>
    </div>
  );
}
