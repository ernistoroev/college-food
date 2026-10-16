import { useState, useEffect } from 'react';
import {Search,ShoppingCart,Utensils,Clock,Plus,X,Minus,Trash2} 
from 'lucide-react';
import './App.css';

const dishes = [
  { id: 1, name: 'Плов по-восточному', category: 'Горячее', price: 230, image: '/images/plov.jpg', stock: 12 },
  { id: 2, name: 'Паста Болоньезе', category: 'Горячее', price: 340, image: '/images/pasta.jpg', stock: 6 },
  { id: 3, name: 'Куриный суп', category: 'Супы', price: 160, image: '/images/sup.jpg', stock: 8 },
  { id: 4, name: 'Цезарь с курицей', category: 'Салаты', price: 140, image: '/images/salat.jpg', stock: 3 },
  { id: 5, name: 'Самса с мясом', category: 'Выпечка', price: 70, image: '/images/samsa.jpg', stock: 20 },
  { id: 6, name: 'Лагман', category: 'Горячее', price: 250, image: '/images/lagman.jpg', stock: 12 },
  { id: 7, name: 'Чай', category: 'Напитки', price: 25, image: '/images/tea.jpg', stock: 50 },
  { id: 8, name: 'Компот', category: 'Напитки', price: 15, image: '/images/kompot.jpg', stock: 17 },
];

const categories = ['Всё меню', 'Горячее', 'Супы', 'Салаты', 'Выпечка', 'Напитки'];

export default function App() {
  const [category, setCategory] = useState('Всё меню');
  const [menuDishes, setMenuDishes] = useState(dishes);
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const cartTotal = cart.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );

  const filtered = menuDishes.filter(dish =>
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
        item.id === dish.id ? { ...item, stock: item.stock - 1 } : item
      )
    );

    setCart(old => {
      const found = old.find(item => item.id === dish.id);

      if (found) {
        return old.map(item =>
          item.id === dish.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }

      return [...old, { ...dish, quantity: 1 }];
    });
  }

  function removeFromCart(dish) {
    const cartItem = cart.find(item => item.id === dish.id);
    if (!cartItem) return;

    setCart(old =>
      old
        .map(item =>
          item.id === dish.id
            ? { ...item, quantity: item.quantity - 1 }
            : item
        )
        .filter(item => item.quantity > 0)
    );

    setMenuDishes(old =>
      old.map(item =>
        item.id === dish.id ? { ...item, stock: item.stock + 1 } : item
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

    setCart(old => old.filter(item => item.id !== dish.id));
  }

  return (
    <div className="app">
      <header className="header">
        <a href="#" className="logo">
          <span className="logo-icon"><Utensils /></span>
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
        <section className="hero">
          <div>
            <span className="open">
              <i /> СТОЛОВАЯ ОТКРЫТА ДО 16:00
            </span>

            <h1>
              Вкусный обед.<br />
              <em>Без лишнего ожидания.</em>
            </h1>

            <p>Выбирай любимые блюда и забирай в удобное время.</p>

            <div className="pickup">
              <Clock size={17} /> Ближайшая выдача <b>12:20</b>
            </div>
          </div>

          <img
            src="https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=800&q=80"
            alt="Блюдо дня"
          />
        </section>

        <section id="menu">
          <div className="section-heading">
            <div>
              <span className="eyebrow">МЕНЮ СТОЛОВОЙ</span>
              <h2>Меню дня</h2>
              <p>Вкусное рядом — выбирай, что по душе.</p>
            </div>

            <label className="search">
              <Search size={19} />
              <input
                placeholder="Найти блюдо..."
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </label>
          </div>

          <div className="categories">
            {categories.map(item => (
              <button
                key={item}
                className={category === item ? 'selected' : ''}
                onClick={() => setCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>

          <div className="dish-grid">
            {filtered.map(dish => (
              <article className="dish" key={dish.id}>
                <img src={dish.image} alt={dish.name} />

                <div className="dish-content">
                  <span>{dish.category}</span>
                  <h3>{dish.name}</h3>

                  <p className={`stock ${
                    dish.stock === 0 ? 'out' : dish.stock <= 3 ? 'low' : ''
                  }`}>
                    {dish.stock === 0
                      ? 'Закончилось'
                      : dish.stock <= 3
                        ? `Осталось ${dish.stock} порц.`
                        : `В наличии: ${dish.stock} порц.`}
                  </p>

                  <div className="dish-bottom">
                    <strong>{dish.price} <small>сом</small></strong>

                    <button
                      type="button"
                      onClick={() => addToCart(dish)}
                      disabled={dish.stock === 0}
                    >
                      {dish.stock === 0 ? (
                        'Закончилось'
                      ) : (
                        <>
                          <Plus size={15} /> Добавить
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>

          {filtered.length === 0 && (
            <div className="empty">
              <h3>Ничего не найдено</h3>
              <p>Попробуй другое название блюда.</p>
            </div>
          )}
        </section>
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
            if (event.target === event.currentTarget) setCartOpen(false);
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
                        <strong>{item.price * item.quantity} сом</strong>
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
                              menuDishes.find(dish => dish.id === item.id)?.stock === 0
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
                    onClick={() => alert('Оформление заказа добавим следующим шагом!')}
                  >
                    Оформить заказ
                  </button>

                  <p className="cart-note">
                    Заказ пока не отправляется — подключим оформление следующим шагом.
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
