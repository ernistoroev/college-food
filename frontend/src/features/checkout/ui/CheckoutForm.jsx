
import { useState } from 'react';

export default function CheckoutForm({
  cart,
  cartTotal,
  onSubmit,
  onCancel
}) {
  const [studentName, setStudentName] = useState('');
  const [pickupTime, setPickupTime] = useState('12:20');

  function handleSubmit(event) {
    event.preventDefault();

    if (!studentName.trim()) return;

    onSubmit({
      studentName: studentName.trim(),
      pickupTime,
      items: cart.map(item => ({
        id: item.id,
        name: item.name,
        price: item.price,
        quantity: item.quantity
      })),
      total: cartTotal
    });
  }

  return (
    <form className="checkout-form" onSubmit={handleSubmit}>
      <h2>Оформление заказа</h2>
      <p>Укажи имя и удобное время получения.</p>

      <label>
        Имя студента
        <input
          type="text"
          value={studentName}
          onChange={event => setStudentName(event.target.value)}
          placeholder="Омурбек"
          required
          maxLength={80}
        />
      </label>

      <label>
        Время получения
        <select
          value={pickupTime}
          onChange={event => setPickupTime(event.target.value)}
        >
          <option value="12:20">12:20</option>
          <option value="12:40">12:40</option>
          <option value="13:00">13:00</option>
          <option value="13:20">13:20</option>
          <option value="13:40">13:40</option>
          <option value="14:00">14:00</option>
        </select>
      </label>

      <div className="checkout-form-total">
        <span>К оплате</span>
        <strong>{cartTotal} сом</strong>
      </div>

      <button type="submit" className="checkout-button">
        Подтвердить заказ
      </button>

      <button
        type="button"
        className="checkout-cancel"
        onClick={onCancel}
      >
        Вернуться в корзину
      </button>
    </form>
  );
}
