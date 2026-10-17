
import { useState, useEffect } from 'react';
import {
  ShoppingCart,
  Utensils,
  X,
  Minus,
  Plus,
  Trash2
} from 'lucide-react';

import './App.css';
import { dishes, categories } from './entities/dish/model/dishes.js';
import MenuPage from './pages/menu/ui/MenuPage.jsx';

import {
  addItemToCart,
  removeItemFromCart,
  deleteItemFromCart,
  getCartCount,
  getCartTotal
} from './entities/cart/model/cart.js';

export default function App() {
  const [category, setCategory] = useState('Всё меню');
  const [menuDishes, setMenuDishes] = useState(dishes);
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);

  const cartCount = getCartCount(cart);
  const cartTotal = getCartTotal(cart);

  const filtered = menuDishes.filter(
    dish =>
      (category === 'Всё меню' || dish.category === category) &&
      dish.name.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    function handleEscape(event) {
      if (event.key === 'Escape') setCartOpen(false);
    }

    if (cartOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [cartOpen]);

  function addToCart(dish) {
    const currentDish = menuDishes.find(item => item.id === dish.id);

    if (!currentDish || currentDish.stock <= 0) return;

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id
          ? { ...item, stock: item.stock - 1 }
          : item
      )
    );

    setCart(old => addItemToCart(old, currentDish));
  }

  function removeFromCart(dish) {
    const cartItem = cart.find(item => item.id === dish.id);

    if (!cartItem) return;

    setCart(old => removeItemFromCart(old, dish.id));

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id
          ? { ...item, stock: item.stock + 1 }
          : item
      )
    );
  }

  function deleteFromCart(dish) {
    const cartItem = cart.find(item => item.id === dish.id);

    if (!cartItem) return;

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id
          ? { ...item, stock: item.stock + cartItem.quantity }
          : item
      )
    );

    setCart(old => deleteItemFromCart(old, dish.id));
  }

  return (
    <div className="app">
      <header className="header">
        <a href="#" className="logo">
          <span className="logo-icon">
            <Utensils />
          </span>

          <span>
            COLLEGE <b>FOOD</b>
            <small>СТУДЕНЧЕСКАЯ СТОЛОВАЯ</small>
          </span>
        </a>

        <nav>
          <a className="active" href="#menu">Меню</a>
          <a href="#menu">Мои заказы</a>
          <a href="#contacts">Контакты</a>
        </nav>

        <button
          type="button"
          className="cart-button"
          onClick={() => setCartOpen(true)}
        >
          <ShoppingCart size={18} />
          Корзина
          {cartCount > 0 && <b>{cartCount}</b>}
        </button>
      </header>

      <main>
        <MenuPage
          category={category}
          setCategory={setCategory}
          categories={categories}
          search={search}
          setSearch={setSearch}
          filtered={filtered}
          addToCart={addToCart}
        />
      </main>

      <footer id="contacts">
        <b>COLLEGE <em>FOOD</em></b>
        <span>Вкусная еда для больших идей.</span>
        <small>Пн–Пт · 08:00–16:00 · © 2026 College Food</small>
      </footer>

      {cartOpen && (
        <div
          className="cart-overlay"
          onMouseDown={event => {
            if (event.target === event.currentTarget) {
              setCartOpen(false);
            }
          }}
        >
          <section
            className="cart-panel"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cart-title"
          >
            <div className="cart-heading">
              <div>
                <span className="eyebrow">COLLEGE FOOD</span>
                <h2 id="cart-title">
                  Корзина <small>({cartCount})</small>
                </h2>
              </div>

              <button
                type="button"
                className="cart-close"
                onClick={() => setCartOpen(false)}
                aria-label="Закрыть корзину"
              >
                <X size={20} />
              </button>
            </div>

            {cart.length === 0 ? (
              <div className="cart-empty">
                <ShoppingCart size={42} />
                <h3>Корзина пока пустая</h3>
                <p>Добавь любимые блюда из меню.</p>

                <button
                  type="button"
                  className="checkout-button"
                  onClick={() => setCartOpen(false)}
                >
                  Вернуться к меню
                </button>
              </div>
            ) : (
              <>
                <div className="cart-items">
                  {cart.map(item => (
                    <article className="cart-item" key={item.id}>
                      <img src={item.image} alt={item.name} />

                      <div className="cart-item-info">
                        <h3>{item.name}</h3>
                        <strong>
                          {item.price * item.quantity} сом
                        </strong>
                        <p>{item.price} сом за порцию</p>

                        <div className="quantity-control">
                          <button
                            type="button"
                            onClick={() => removeFromCart(item)}
                            aria-label="Уменьшить количество"
                          >
                            <Minus size={15} />
                          </button>

                          <span>{item.quantity}</span>

                          <button
                            type="button"
                            onClick={() => addToCart(item)}
                            disabled={
                              menuDishes.find(
                                dish => dish.id === item.id
                              )?.stock === 0
                            }
                            aria-label="Увеличить количество"
                          >
                            <Plus size={15} />
                          </button>

                          <button
                            type="button"
                            className="remove-item"
                            onClick={() => deleteFromCart(item)}
                            aria-label="Удалить блюдо"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>

                <div className="cart-summary">
                  <div>
                    <span>Количество порций</span>
                    <span>{cartCount}</span>
                  </div>

                  <div className="cart-total">
                    <span>Итого</span>
                    <strong>{cartTotal} сом</strong>
                  </div>

                  <button
                    type="button"
                    className="checkout-button"
                    onClick={() =>
                      alert('Оформление заказа добавим следующим шагом!')
                    }
                  >
                    Оформить заказ
                  </button>

                  <p className="cart-note">
                    Заказ пока не отправляется — подключим оформление
                    следующим шагом.
                  </p>
                </div>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
