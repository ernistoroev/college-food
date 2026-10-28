import { api, getList } from '../../../shared/api/client.js';

function toReview(review) {
  return {
    id: review.id,
    name: review.user_name,
    rating: review.rating,
    text: review.text,
    createdAt: new Date(review.created_at).toLocaleDateString('ru-RU'),
  };
}

// The «Отзывы» page shows reviews of the canteen in general (dish=none), not of single dishes.
export async function fetchReviews() {
  const reviews = await getList('/reviews/', { dish: 'none' });
  return reviews.map(toReview);
}

export async function createReview({ rating, text }) {
  const response = await api.post('/reviews/', { rating, text });
  return toReview(response.data);
}
