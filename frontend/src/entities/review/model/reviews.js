import { api } from '../../../shared/api/client.js';

function toReview(review) {
  return {
    id: review.id,
    name: review.name,
    rating: review.rating,
    text: review.text,
    createdAt: new Date(review.created_at).toLocaleDateString('ru-RU'),
  };
}

export async function fetchReviews() {
  const response = await api.get('/reviews/');
  return response.data.map(toReview);
}

export async function createReview({ rating, text }) {
  const response = await api.post('/reviews/', { rating, text });
  return toReview(response.data);
}
