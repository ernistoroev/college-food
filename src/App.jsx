import { useEffect, useState } from 'react';
import axios from 'axios';
import { Search, ShoppingCart, Utensils, Clock } from 'lucide-react';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api';
const ALL = 'Всё меню';

export default function App() {
  const [dishes, setDishes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [category, setCategory] = useState(ALL);
  const [search, setSearch] = useState('');

  useEffect(() => {
    Promise.all([axios.get(`${API_URL}/dishes/`), axios.get(`${API_URL}/categories/`)])
      .then(([dishesResponse, categoriesResponse]) => {
        setDishes(dishesResponse.data);
        setCategories(categoriesResponse.data.map(item => item.name));
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const filtered = dishes.filter(dish =>
    (category === ALL || dish.category_name === category) &&
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
            {[ALL, ...categories].map(item => (
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
                {dish.image ? (
                  <img src={dish.image} alt={dish.name} />
                ) : (
                  <div className="dish-no-photo"><Utensils size={32} /></div>
                )}
                <div className="dish-content">
                  <span>{dish.category_name}</span>
                  <h3>{dish.name}</h3>
                  <div className="dish-bottom">
                    <strong>{dish.price} <small>сом</small></strong>

                  </div>
                </div>
              </article>
            ))}
          </div>

          {loading && (
            <div className="empty">
              <h3>Загружаем меню…</h3>
            </div>
          )}

          {error && (
            <div className="empty">
              <h3>Не удалось загрузить меню</h3>
              <p>Проверь, что backend запущен, и обнови страницу.</p>
            </div>
          )}

          {!loading && !error && filtered.length === 0 && (
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
