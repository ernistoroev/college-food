import { useCallback, useEffect, useState } from 'react';
import { api, getList, getErrorMessage } from '../../../shared/api/client.js';

const statuses = [
  { value: 'new', label: 'Новый' },
  { value: 'cooking', label: 'Готовится' },
  { value: 'ready', label: 'Готов' },
  { value: 'done', label: 'Выдан' },
  { value: 'cancelled', label: 'Отменён' },
];

const finalStatuses = ['done', 'cancelled'];

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(null);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const params = filter === 'all' ? {} : { status: filter };
      const data = await getList('/orders/', params);
      setOrders(data);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Не удалось загрузить заказы.'));
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  async function changeStatus(order, nextStatus) {
    if (finalStatuses.includes(order.status) || updating === order.id) return;

    setUpdating(order.id);
    setError('');

    try {
      const response = await api.patch(`/orders/${order.id}/status/`, {
        status: nextStatus,
      });

      setOrders(current =>
        current.map(item =>
          item.id === order.id ? response.data : item
        )
      );

      if (selectedOrder?.id === order.id) {
        setSelectedOrder(response.data);
      }
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'Не удалось изменить статус.'));
    } finally {
      setUpdating(null);
    }
  }

  function formatDate(value) {
    return value
      ? new Date(value).toLocaleString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : '—';
  }

  function statusLabel(order) {
    return order.status_display ||
      statuses.find(item => item.value === order.status)?.label ||
      order.status;
  }

  return (
    <div className="admin-orders">
      <div className="admin-page-heading">
        <div>
          <span className="admin-eyebrow">COLLEGE FOOD / УПРАВЛЕНИЕ</span>
          <h1>Заказы</h1>
          <p>Принимайте заказы и следите за их выполнением.</p>
        </div>

        <button className="admin-refresh" onClick={loadOrders} disabled={loading}>
          ↻ Обновить
        </button>
      </div>

      <div className="admin-order-filters">
        {[
          { value: 'all', label: 'Все заказы' },
          ...statuses,
        ].map(item => (
          <button
            key={item.value}
            className={filter === item.value ? 'active' : ''}
            onClick={() => setFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="admin-orders-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="admin-orders-empty">Загружаем заказы...</div>
      ) : orders.length === 0 ? (
        <div className="admin-orders-empty">
          <span>▤</span>
          <h3>Заказов пока нет</h3>
          <p>Когда студенты оформят заказы, они появятся здесь.</p>
        </div>
      ) : (
        <div className="admin-orders-list">
          {orders.map(order => (
            <article className="admin-order-card" key={order.id}>
              <div className="admin-order-main">
                <div>
                  <span className="admin-order-number">ЗАКАЗ №{order.id}</span>
                  <h3>{order.student_name || 'Студент'}</h3>
                  <p>
                    {formatDate(order.created_at)} · Получение: {order.pickup_time || '—'}
                  </p>
                </div>

                <span className={`admin-order-status status-${order.status}`}>
                  {statusLabel(order)}
                </span>
              </div>

              <div className="admin-order-items">
                {(order.items || []).map((item, index) => (
                  <div className="admin-order-item" key={`${item.dish ?? 'dish'}-${index}`}>
                    <span>{item.dish_name || item.name}</span>
                    <span>{item.quantity} × {item.price} сом</span>
                  </div>
                ))}
              </div>

              {order.comment && (
                <div className="admin-order-comment">
                  Комментарий: {order.comment}
                </div>
              )}

              <div className="admin-order-footer">
                <strong>{Number(order.total || 0).toLocaleString('ru-RU')} сом</strong>

                <div className="admin-order-actions">
                  <button
                    className="admin-order-details"
                    onClick={async () => {
                      try {
                        const response = await api.get(`/orders/${order.id}/`);
                        setSelectedOrder(response.data);
                      } catch (requestError) {
                        setError(getErrorMessage(requestError, 'Не удалось открыть заказ.'));
                      }
                    }}
                  >
                    Подробнее
                  </button>

                  {finalStatuses.includes(order.status) ? (
                    <span className="admin-order-closed">Заказ закрыт</span>
                  ) : (
                    <select
                      value={order.status}
                      disabled={updating === order.id}
                      onChange={event => changeStatus(order, event.target.value)}
                      aria-label={`Статус заказа ${order.id}`}
                    >
                      {statuses.map(item => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {selectedOrder && (
        <div className="admin-order-modal-backdrop" onClick={() => setSelectedOrder(null)}>
          <section
            className="admin-order-modal"
            onClick={event => event.stopPropagation()}
          >
            <button
              className="admin-order-modal-close"
              onClick={() => setSelectedOrder(null)}
              aria-label="Закрыть"
            >
              ×
            </button>

            <span className="admin-eyebrow">ПОДРОБНОСТИ ЗАКАЗА</span>
            <h2>Заказ №{selectedOrder.id}</h2>

            <div className="admin-order-detail">
              <span>Имя студента</span>
              <strong>{selectedOrder.customer_name || selectedOrder.student_name || '—'}</strong>
            </div>
            <div className="admin-order-detail">
              <span>Email</span>
              <strong>{selectedOrder.customer_email || '—'}</strong>
            </div>
            <div className="admin-order-detail">
              <span>Время получения</span>
              <strong>{selectedOrder.pickup_time || '—'}</strong>
            </div>
            <div className="admin-order-detail">
              <span>Статус</span>
              <strong>{statusLabel(selectedOrder)}</strong>
            </div>
            <div className="admin-order-detail">
              <span>Создан</span>
              <strong>{formatDate(selectedOrder.created_at)}</strong>
            </div>

            <h3>Состав заказа</h3>
            {(selectedOrder.items || []).map((item, index) => (
              <div className="admin-order-item" key={index}>
                <span>{item.dish_name || item.name} × {item.quantity}</span>
                <strong>{Number(item.price) * item.quantity} сом</strong>
              </div>
            ))}

            <div className="admin-order-modal-total">
              Итого: {Number(selectedOrder.total || 0).toLocaleString('ru-RU')} сом
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
