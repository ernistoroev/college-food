const STORAGE_KEY = 'college-food-orders';

export function getSavedOrders() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

export function saveOrder(order) {
  const orders = getSavedOrders();
  const updatedOrders = [order, ...orders];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedOrders));
  return updatedOrders;
}
