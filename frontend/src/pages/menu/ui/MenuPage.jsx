import { useState } from 'react';
import { Search, Plus, Minus, Utensils } from 'lucide-react';

export default function MenuPage({
  category,
  setCategory,
  categories,
  search,
  setSearch,
  filtered,
  addToCart,
  removeFromCart,
  cart,
  loading,
  error
}) {
  const [brokenImages, setBrokenImages] = useState([]);

  return (
    <>
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
            <span>◷</span> Ближайшая выдача <b>12:20</b>
          </div>
        </div>

        <img
          src="/images/plov.jpg"
          alt="Блюдо дня"
          onError={event => {
            event.currentTarget.style.display = 'none';
          }}
        />
      </section>

      <section id="menu">
        <div className="section-heading">
          <div className="menu-heading-centered">
            <span className="eyebrow">МЕНЮ СТОЛОВОЙ</span>
            <h2>Меню дня</h2>
            <p>Вкусное рядом — выбирай, что по душе.</p>
          </div>
        </div>

        <div className="menu-filters-row">
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

          <label className="search">
            <Search size={19} />
            <input
              placeholder="Найти блюдо..."
              value={search}
              onChange={event => setSearch(event.target.value)}
            />
          </label>
        </div>

        <div className="dish-grid">
          {filtered.map(dish => {
            const quantity = cart.find(item => item.id === dish.id)?.quantity || 0;
            const imageBroken = !dish.image || brokenImages.includes(dish.id);

            return (
              <article className="dish" key={dish.id}>
                {imageBroken ? (
                  <div className="dish-image-placeholder">
                    <Utensils size={36} />
                    <span>{dish.name}</span>
                  </div>
                ) : (
                  <img
                    src={dish.image}
                    alt={dish.name}
                    loading="lazy"
                    onError={() => {
                      setBrokenImages(old =>
                        old.includes(dish.id) ? old : [...old, dish.id]
                      );
                    }}
                  />
                )}

                <div className="dish-content">
                  <div className="dish-stock-badge">
                    {quantity > 0 ? `В корзине: ${quantity}` : dish.stock > 0
                      ? `Осталось порций: ${dish.stock}`
                      : 'На сегодня закончилось'}
                  </div>

                  <h3>{dish.name}</h3>

                  <div className="dish-meta">
                    <span>{dish.weight}</span>
                    {dish.rating && (
                      <>
                        <span className="meta-dot">·</span>
                        <span className="dish-rating">★ {dish.rating}</span>
                      </>
                    )}
                  </div>

                  <p className="dish-description">{dish.description}</p>

                  <div className="dish-bottom">
                    <strong>
                      {dish.price} <small>сом</small>
                    </strong>

                    {quantity > 0 ? (
                      <div className="dish-quantity" role="group" aria-label={`Количество: ${dish.name}`}>
                        <button type="button" onClick={() => removeFromCart(dish)}
                          aria-label={`Убрать порцию: ${dish.name}`}><Minus size={18} /></button>
                        <output aria-live="polite" aria-label={`В корзине: ${dish.name}`}>{quantity}</output>
                        <button type="button" onClick={() => addToCart(dish)} disabled={dish.stock <= 0}
                          aria-label={`Добавить порцию: ${dish.name}`}><Plus size={18} /></button>
                      </div>
                    ) : (
                      <button type="button" onClick={() => addToCart(dish)} disabled={dish.stock <= 0}
                        aria-label={`Добавить в корзину: ${dish.name}`}>
                        {dish.stock <= 0 ? 'Закончилось' : <><Plus size={15} /> Добавить</>}
                      </button>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>

        {loading && (
          <div className="empty">
            <h3>Загружаем меню…</h3>
          </div>
        )}

        {error && (
          <div className="empty">
            <h3>Не удалось загрузить меню</h3>
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="empty">
            <h3>Ничего не найдено</h3>
            <p>Попробуй другое название блюда.</p>
          </div>
        )}
      </section>
    </>
  );
}
