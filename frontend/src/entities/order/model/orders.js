import { api, getList } from '../../../shared/api/client.js';

// Field names in the shape the «Мои заказы» page already uses.
function toOrder(order) {
  return {
    id: order.id,
    studentName: order.student_name,
    pickupTime: order.pickup_time,
    status: order.status_display,
    total: order.total,
    createdAt: new Date(order.created_at).toLocaleString('ru-RU'),
    items: order.items.map((item, index) => ({
      id: item.dish ?? `deleted-${index}`,
      name: item.dish_name,
      price: item.price,
      quantity: item.quantity,
    })),
  };
}

export async function fetchOrders() {
  const orders = await getList('/orders/');
  return orders.map(toOrder);
}

// The server checks the portions and counts the total itself, so only ids and quantities are sent.
export async function createOrder({ studentName, pickupTime, items }) {
  const response = await api.post('/orders/', {
    student_name: studentName,
    pickup_time: pickupTime,
    items: items.map(item => ({ dish: item.id, quantity: item.quantity })),
  });
  return toOrder(response.data);
}
