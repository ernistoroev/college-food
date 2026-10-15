import { useState } from 'react';
import { Search, ShoppingCart, Utensils, Clock, Plus, Minus, Trash2, X } from 'lucide-react';
import './App.css';

const dishes = [
  { id: 1, name: 'Плов по-восточному', category: 'Горячее', price: 180, image: 'photo-1512058564366-18510be2db19' },
  { id: 2, name: 'Паста Болоньезе', category: 'Горячее', price: 160, image: 'photo-1473093295043-cdd812d0e601' },
  { id: 3, name: 'Куриный суп', category: 'Супы', price: 100, image: 'photo-1547592166-23ac45744acd' },
  { id: 4, name: 'Цезарь с курицей', category: 'Салаты', price: 140, image: 'photo-1546793665-c74683f339c1' },
  { id: 5, name: 'Самса с мясом', category: 'Выпечка', price: 70, image: 'photo-1601050690597-df0568f70950' },
  { id: 6, name: 'Лагман', category: 'Горячее', price: 170, image: 'photo-1563245372-f21724e3856d' },
  { id: 7, name: 'Чай', category: 'Напитки', price: 25, image: 'photo-1544787219-7f47ccb76574' },
  { id: 8, name: 'Компот', category: 'Напитки', price: 35, image: 'photo-1513558161293-cafd765edfd7' },
];

const categories = ['Всё меню', 'Горячее', 'Супы', 'Салаты', 'Выпечка', 'Напитки'];

export default function App() {
  const [category, setCategory] = useState('Всё меню');
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState([]);
  const [cartOpen, setCartOpen] = useState(false);

  const filtered = dishes.filter(dish =>
    (category === 'Всё меню' || dish.category === category) &&
    dish.name.toLowerCase().includes(search.toLowerCase())
  );

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  function changeQuantity(id, delta) {
    setCart(old => old
      .map(item => item.id === id
        ? { ...item, quantity: item.quantity + delta }
        : item)
      .filter(item => item.quantity > 0)
    );
  }

  const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);

  function addToCart(dish) {
    setCart(old => {
      const found = old.find(item => item.id === dish.id);
      return found
        ? old.map(item => item.id === dish.id
          ? { ...item, quantity: item.quantity + 1 }
          : item)
        : [...old, { ...dish, quantity: 1 }];
    });
  }

  return (
    <div className="app">
      <header className="header">
        <a href="#" className="logo">
          <span className="logo-icon"><Utensils /></span>
          <span>COLLEGE <b>FOOD</b><small>СТУДЕНЧЕСКАЯ СТОЛОВАЯ</small></span>
        </a>

        <nav>
          <a className="active" href="#menu">Меню</a>
          <a href="#orders">Мои заказы</a>
          <a href="#contacts">Контакты</a>
        </nav>

        <button className="cart-button" onClick={() => setCartOpen(true)}>
          <ShoppingCart size={18} />
          Корзина {cartCount > 0 && <b>{cartCount}</b>}
        </button>
      </header>

      <main>
        <section className="hero">
          <div>
            <span className="open"><i /> СТОЛОВАЯ ОТКРЫТА ДО 16:00</span>
            <h1>Вкусный обед.<br /><em>Без лишнего ожидания.</em></h1>
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
                <img
                  src={`https://images.unsplash.com/${dish.image}?auto=format&fit=crop&w=600&q=80`}
                  alt={dish.name}
                />
                <div className="dish-content">
                  <span>{dish.category}</span>
                  <h3>{dish.name}</h3>
                  <div className="dish-bottom">
                    <strong>{dish.price} <small>сом</small></strong>
                    <button onClick={() => addToCart(dish)}>
                      <Plus size={15} /> Добавить
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

      {cartOpen && (
        <div className="cart-overlay" onClick={() => setCartOpen(false)}>
          <section className="cart-panel" onClick={e => e.stopPropagation()}>
            <div className="cart-heading">
              <div>
                <span className="eyebrow">ВАШ ЗАКАЗ</span>
                <h2>Корзина <small>({cartCount})</small></h2>
              </div>
              <button className="cart-close" onClick={() => setCartOpen(false)} aria-label="Закрыть корзину">
                <X />
              </button>
            </div>

            {cart.length === 0 ? (
              <div className="cart-empty">
                <ShoppingCart size={42} />
                <h3>Корзина пока пуста</h3>
                <p>Добавь любимые блюда из меню.</p>
                <button className="checkout-button" onClick={() => setCartOpen(false)}>Перейти к меню</button>
              </div>
            ) : (
              <>
                <div className="cart-items">
                  {cart.map(item => (
                    <article className="cart-item" key={item.id}>
                      <img
                        src={`https://images.unsplash.com/${item.image}?auto=format&fit=crop&w=200&q=80`}
                        alt={item.name}
                      />
                      <div className="cart-item-info">
                        <h3>{item.name}</h3>
                        <strong>{item.price * item.quantity} сом</strong>
                        <div className="quantity-control">
                          <button onClick={() => changeQuantity(item.id, -1)} aria-label="Уменьшить количество"><Minus size={14} /></button>
                          <span>{item.quantity}</span>
                          <button onClick={() => changeQuantity(item.id, 1)} aria-label="Увеличить количество"><Plus size={14} /></button>
                          <button className="remove-item" onClick={() => setCart(old => old.filter(x => x.id !== item.id))} aria-label="Удалить блюдо"><Trash2 size={15} /></button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
                <div className="cart-summary">
                  <div><span>Количество блюд</span><b>{cartCount}</b></div>
                  <div className="cart-total"><span>Итого</span><strong>{cartTotal} сом</strong></div>
                  <button className="checkout-button" onClick={() => alert('Оформление заказа подключим следующим этапом.')}>
                    Перейти к оформлению
                  </button>
                  <p className="cart-note">Оплата и подтверждение заказа будут добавлены следующим этапом.</p>
                </div>
              </>
            )}
          </section>
        </div>
      )}

      <footer id="contacts">
        <b>COLLEGE <em>FOOD</em></b>
        <span>Вкусная еда для больших идей.</span>
        <small>Пн–Пт · 08:00–16:00 · © 2026 College Food</small>
      </footer>
    </div>
  );
}
