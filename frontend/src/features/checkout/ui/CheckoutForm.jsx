
import { useState } from 'react';

export default function CheckoutForm({
  cart,
  cartTotal,
  canteens,
  onSubmit,
  onCancel,
  currentUser
}) {
  const [studentName, setStudentName] = useState(currentUser?.name || '');
  const [chosenCanteen, setChosenCanteen] = useState(null);
  const [pickupTime, setPickupTime] = useState('12:20');

  // Only the floors every dish in the cart is delivered to.
  const available = canteens.filter(item => cart.every(dish => dish.canteens?.includes(item.id)));
  const canteen = available.some(item => item.id === chosenCanteen) ? chosenCanteen : available[0]?.id;

  function handleSubmit(event) {
    event.preventDefault();

    if (!studentName.trim() || !canteen) return;

    onSubmit({
      studentName: studentName.trim(),
      canteen,
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
      <p>Укажи имя, этаж и удобное время доставки.</p>

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
        На какой этаж доставить
        {available.length > 0 ? (
          <select
            value={canteen}
            onChange={event => setChosenCanteen(Number(event.target.value))}
          >
            {available.map(item => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        ) : (
          <span className="checkout-form-warning">
            Нет этажа, на который доставляют все блюда из корзины. Оформи их отдельными заказами.
          </span>
        )}
      </label>

      <label>
        Время доставки
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

      <button type="submit" className="checkout-button" disabled={!canteen}>
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
