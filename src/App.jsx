import { useState } from 'react';
import { Search, ShoppingCart, Utensils, Clock } from 'lucide-react';
import './App.css';

const dishes = [
  { id: 1, name: 'Плов по-восточному', category: 'Горячее', price: 180, image: 'photo-1512058564366-18510be2db19' },
  { id: 2, name: 'Паста Болоньезе', category: 'Горячее', price: 160, image: 'photo-1473093295043-cdd812d0e601' },
  { id: 3, name: 'Куриный суп', category: 'Супы', price: 100, image: 'photo-1547592166-23ac45744acd' },
  { id: 4, name: 'Цезарь с курицей', category: 'Салаты', price: 140, image: 'photo-1546793665-c74683f339c1' },
  { id: 5, name: 'Самса с мясом', category: 'Выпечка', price: 70, image: 'photo-1601050690597-df0568f70950' },
  { id: 6, name: 'Лагман', category: 'Горячее', price: 170, image: 'photo-1563245372-f21724e3856d' },
  { id: 7, name: 'Чай', category: 'Напитки', price: 25, image: 'photo-1544787219-7f47ccb76574' },
  { id: 8, name: 'Компот', category: 'Напитки', price: 15, image: '/images/kompot.jpg' },
];

const categories = ['Всё меню', 'Горячее', 'Супы', 'Салаты', 'Выпечка', 'Напитки'];

export default function App() {
  const [category, setCategory] = useState('Всё меню');
  const [search, setSearch] = useState('');

  const filtered = dishes.filter(dish =>
    (category === 'Всё меню' || dish.category === category) &&
    dish.name.toLowerCase().includes(search.toLowerCase())
  );



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

        <button className="cart-button">
          <ShoppingCart size={18} />
          Корзина
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
                  src={dish.image.startsWith("/") ? dish.image : `https://images.unsplash.com/${dish.image}?auto=format&fit=crop&w=600&q=80`}
                  alt={dish.name}
                />
                <div className="dish-content">
                  <span>{dish.category}</span>
                  <h3>{dish.name}</h3>
                  <div className="dish-bottom">
                    <strong>{dish.price} <small>сом</small></strong>

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
    </div>
  );
}
