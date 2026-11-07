import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { login, logout } from '../../../entities/auth/model/auth.js';
import { getErrorMessage } from '../../../shared/api/client.js';
import './AdminLoginPage.css';

export default function AdminLoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await login({ email, password });

      if (user?.role !== 'staff') {
        await logout();
        setError('Доступ разрешён только сотрудникам столовой.');
        return;
      }

      navigate('/admin/dashboard', { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, 'Не удалось войти. Проверьте данные.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="admin-login">
      <section className="admin-login__card">
        <Link to="/" className="admin-login__brand">
          COLLEGE <span>FOOD</span>
        </Link>

        <div className="admin-login__label">РАБОЧЕЕ ПРОСТРАНСТВО</div>
        <h1>Вход сотрудников</h1>
        <p className="admin-login__description">
          Войдите, чтобы управлять меню и заказами столовой.
        </p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="admin-email">Электронная почта</label>
          <input
            id="admin-email"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={event => setEmail(event.target.value)}
            autoComplete="username"
            required
          />

          <label htmlFor="admin-password">Пароль</label>
          <input
            id="admin-password"
            type="password"
            placeholder="Введите пароль"
            value={password}
            onChange={event => setPassword(event.target.value)}
            autoComplete="current-password"
            required
          />

          {error && <div className="admin-login__error">{error}</div>}

          <button type="submit" disabled={loading}>
            {loading ? 'Входим...' : 'Войти в панель'}
          </button>
        </form>

        <Link to="/" className="admin-login__back">
          ← Вернуться на сайт столовой
        </Link>
      </section>
    </main>
  );
}
