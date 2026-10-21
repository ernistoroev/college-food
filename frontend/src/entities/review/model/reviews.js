const STORAGE_KEY = 'college-food-reviews';

export function getReviews() {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    return value ? JSON.parse(value) : [];
  } catch {
    return [];
  }
}

export function addReview(review) {
  const reviews = getReviews();
  const updated = [
    {
      ...review,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      createdAt: new Date().toLocaleDateString('ru-RU')
    },
    ...reviews
  ];

  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}
