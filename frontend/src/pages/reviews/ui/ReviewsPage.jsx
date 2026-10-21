import { useState } from 'react';
import { Star, MessageSquare, Send } from 'lucide-react';
import { getReviews, addReview } from '../../../entities/review/model/reviews.js';

export default function ReviewsPage({ currentUser, onLogin }) {
  const [reviews, setReviews] = useState(() => getReviews());
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [text, setText] = useState('');

  const average = reviews.length
    ? reviews.reduce((sum, review) => sum + Number(review.rating), 0) / reviews.length
    : 0;

  function publishReview(event) {
    event.preventDefault();

    if (!currentUser) {
      onLogin();
      return;
    }

    if (!text.trim()) return;

    const updated = addReview({
      name: currentUser.name,
      rating,
      text: text.trim()
    });

    setReviews(updated);
    setText('');
    setRating(5);
  }

  return (
    <section className="reviews-page">
      <div className="reviews-heading">
        <span className="eyebrow">МНЕНИЕ СТУДЕНТОВ</span>
        <h1
          style={{
            color: "black",
            fontFamily: "Inter, system-ui, 'Segoe UI', Roboto, sans-serif",
            fontSize: "36px",
            fontWeight: 700,
            letterSpacing: "-1px"
          }}
        >
          Отзывы
        </h1>
        <p>Расскажи о своём опыте и помоги нам стать лучше.</p>
      </div>

      <div className="reviews-overview">
        <div className="reviews-score">
          <strong>{average ? average.toFixed(1) : '—'}</strong>
          <div className="reviews-stars">
            {[1, 2, 3, 4, 5].map(star => (
              <Star key={star} size={19} fill={star <= Math.round(average) ? 'currentColor' : 'none'} />
            ))}
          </div>
          <span>{reviews.length} {reviews.length === 1 ? 'отзыв' : reviews.length >= 2 && reviews.length <= 4 ? 'отзыва' : 'отзывов'}</span>
        </div>

        <div className="rating-bars">
          {[5, 4, 3, 2, 1].map(star => {
            const count = reviews.filter(review => Number(review.rating) === star).length;
            const percent = reviews.length ? count / reviews.length * 100 : 0;

            return (
              <div className="rating-row" key={star}>
                <span>{star} <Star size={14} fill="currentColor" /></span>
                <div className="rating-track">
                  <div className="rating-fill" style={{ width: `${percent}%` }} />
                </div>
                <span>{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="reviews-layout">
        <form className="review-form" onSubmit={publishReview}>
          <h2
            style={{
              color: "#171717",
              fontFamily: "Inter, system-ui, sans-serif",
              fontSize: "28px",
              fontWeight: 700,
              letterSpacing: "-0.8px",
              marginBottom: "16px"
            }}
          >
            Оставить отзыв
          </h2>
          <p>Поделись впечатлениями о блюдах и обслуживании.</p>

          <label>Твоя оценка</label>
          <div className="review-rating-picker">
            {[1, 2, 3, 4, 5].map(star => (
              <button
                key={star}
                type="button"
                aria-label={`Оценка ${star}`}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                onClick={() => setRating(star)}
              >
                <Star
                  size={30}
                  fill={star <= (hoverRating || rating) ? 'currentColor' : 'none'}
                />
              </button>
            ))}
          </div>

          <label htmlFor="review-text">Твой отзыв</label>
          <textarea
            id="review-text"
            value={text}
            onChange={event => setText(event.target.value)}
            placeholder="Что тебе понравилось? Что можно улучшить?"
            rows={5}
            maxLength={1000}
            required
          />

          {!currentUser && (
            <p className="review-login-note">Чтобы опубликовать отзыв, нужно войти в аккаунт.</p>
          )}

          <button className="review-submit" type="submit">
            {currentUser ? <><Send size={17} /> Опубликовать отзыв</> : 'Войти и оставить отзыв'}
          </button>
        </form>

        <div className="reviews-list">
          <div className="reviews-list-heading">
            <h2>Отзывы студентов</h2>
            <span>{reviews.length}</span>
          </div>

          {reviews.length === 0 ? (
            <div className="reviews-empty">
              <MessageSquare size={34} />
              <h3>Пока нет отзывов</h3>
              <p>Будь первым, кто поделится впечатлениями!</p>
            </div>
          ) : (
            reviews.map(review => (
              <article className="review-card" key={review.id}>
                <div className="review-card-top">
                  <div className="review-avatar">
                    {(review.name || 'С').trim().charAt(0).toUpperCase()}
                  </div>
                  <div className="review-author">
                    <strong>{review.name}</strong>
                    <span>{review.createdAt}</span>
                  </div>
                  <div className="review-card-stars" aria-label={`Оценка ${review.rating} из 5`}>
                    {Array.from({ length: 5 }, (_, index) => (
                      <Star
                        key={index}
                        size={15}
                        fill={index < Number(review.rating) ? 'currentColor' : 'none'}
                      />
                    ))}
                  </div>
                </div>
                <p className="review-card-text">{review.text}</p>
              </article>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
