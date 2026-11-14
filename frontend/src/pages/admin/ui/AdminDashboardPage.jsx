import { useEffect, useState } from 'react';
import { api, getErrorMessage } from '../../../shared/api/client.js';

const statistics = [
  {
    key: 'dishes_total',
    title: 'Всего блюд',
    description: 'Позиций в меню',
    icon: '♨',
  },
  {
    key: 'dishes_unavailable',
    title: 'Недоступно',
    description: 'Временно отключены',
    icon: '⊘',
  },
  {
    key: 'dishes_sold_out',
    title: 'Закончились порции',
    description: 'Нет порций на сегодня',
    icon: '◷',
  },
  {
    key: 'orders_new',
    title: 'Новые заказы',
    description: 'Ожидают обработки',
    icon: '＋',
  },
  {
    key: 'orders_cooking',
    title: 'Готовятся',
    description: 'На кухне',
    icon: '♨',
  },
  {
    key: 'orders_ready',
    title: 'Готовы к доставке',
    description: 'Ожидают доставки',
    icon: '✓',
  },
];

export default function AdminDashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    api.get('/staff/dashboard/')
      .then(response => {
        if (active) setData(response.data);
      })
      .catch(requestError => {
        if (active) {
          setError(getErrorMessage(requestError, 'Не удалось загрузить статистику.'));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="admin-dashboard">
      <div className="admin-page-heading">
        <div>
          <span className="admin-eyebrow">COLLEGE FOOD / ПАНЕЛЬ</span>
          <h1>Обзор</h1>
          <p>Состояние столовой и текущие показатели.</p>
        </div>
      </div>

      {loading && (
        <div className="admin-message">Загружаем статистику...</div>
      )}

      {error && (
        <div className="admin-error">
          <strong>Не удалось получить данные</strong>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>
            Повторить
          </button>
        </div>
      )}

      {data && (
        <>
          <div className="admin-stat-grid">
            {statistics.map(item => (
              <article className="admin-stat-card" key={item.key}>
                <div className="admin-stat-top">
                  <span>{item.title}</span>
                  <span className="admin-stat-icon">{item.icon}</span>
                </div>

                <strong className="admin-stat-value">
                  {data[item.key] ?? 0}
                </strong>

                <span className="admin-stat-description">
                  {item.description}
                </span>
              </article>
            ))}
          </div>

          <section className="admin-dashboard-section">
            <div>
              <h2>Последние отзывы</h2>
              <p>Отзывы посетителей столовой</p>
            </div>

            {data.latest_reviews?.length ? (
              <div className="admin-reviews">
                {data.latest_reviews.map((review, index) => (
                  <article className="admin-review" key={review.id ?? index}>
                    <div>
                      <strong>
                        {review.user_name || review.user || 'Посетитель'}
                      </strong>
                      <span>Оценка: {review.rating ?? '—'}</span>
                    </div>
                    <p>{review.text || 'Без текста'}</p>
                  </article>
                ))}
              </div>
            ) : (
              <div className="admin-empty">
                Пока отзывов нет.
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
