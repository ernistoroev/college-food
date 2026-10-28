import { api } from '../../../shared/api/client.js';

export const ALL_CATEGORIES = 'Всё меню';

// The API speaks Django field names; the cards use the names the frontend already had.
function toDish(dish) {
  return {
    id: dish.id,
    name: dish.name,
    category: dish.category_name,
    price: dish.price,
    image: dish.image,
    stock: dish.portions_today,
    weight: dish.weight ? `${dish.weight} ${dish.weight_unit}` : '',
    description: dish.description,
  };
}

export async function fetchMenu() {
  const [dishes, categories] = await Promise.all([
    api.get('/dishes/'),
    api.get('/categories/'),
  ]);

  return {
    dishes: dishes.data.map(toDish),
    categories: [ALL_CATEGORIES, ...categories.data.map(category => category.name)],
  };
}
