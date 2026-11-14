import { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { fetchCurrentUser, logout } from '../../../entities/auth/model/auth.js';
import './AdminLayout.css';

export default function AdminLayout() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;

    fetchCurrentUser()
      .then(currentUser => {
        if (!active) return;

        if (!currentUser) {
          navigate('/staff/login', { replace: true });
          return;
        }

        if (currentUser.role !== 'staff') {
          navigate('/', { replace: true });
          return;
        }

        setUser(currentUser);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [navigate]);

  async function handleLogout() {
    await logout();
    navigate('/staff/login', { replace: true });
  }

  if (loading || !user) {
    return <div className="admin-loading">Загрузка панели управления...</div>;
  }

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <div className="admin-brand-icon">CF</div>
          <div>
            <strong>COLLEGE FOOD</strong>
            <span>ПАНЕЛЬ СОТРУДНИКА</span>
          </div>
        </div>

        <div className="admin-nav-label">МЕНЮ</div>

        <nav className="admin-nav">
          <NavLink to="/staff/dashboard">⌂ <span>Обзор</span></NavLink>
          <NavLink to="/staff/orders">▤ <span>Заказы</span></NavLink>
          <NavLink to="/staff/dishes">♨ <span>Блюда</span></NavLink>
        </nav>

        <div className="admin-sidebar-bottom">
          <div className="admin-user">
            <div className="admin-avatar">
              {(user.name || user.email || 'С')[0].toUpperCase()}
            </div>
            <div className="admin-user-info">
              <strong>{user.name || 'Сотрудник'}</strong>
              <span>{user.email}</span>
            </div>
          </div>

          <button className="admin-logout" onClick={handleLogout}>
            ↪ Выйти из аккаунта
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <span>Административная панель</span>
          <span className="admin-status">● Система активна</span>
        </header>

        <section className="admin-content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}
