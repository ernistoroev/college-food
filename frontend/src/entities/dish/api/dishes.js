import { getList } from '../../../shared/api/client.js';

export const ALL_CATEGORIES = 'Всё меню';

// The API speaks Django field names; the cards use the names the frontend already had.
function toDish(dish) {
  return {
    id: dish.id,
    name: dish.name,
    category: dish.category_name,
    price: dish.price,
    image: dish.image,
    // An unavailable dish stays in the menu but cannot be added: the card shows «На сегодня закончилось».
    stock: dish.is_available ? dish.portions_today : 0,
    weight: dish.weight ? `${dish.weight} ${dish.weight_unit}` : '',
    rating: dish.rating ? dish.rating.toFixed(1).replace('.', ',') : null,
    description: dish.description,
  };
}

export async function fetchMenu() {
  const [dishes, categories] = await Promise.all([
    getList('/dishes/'),
    getList('/categories/'),
  ]);

  return {
    dishes: dishes.map(toDish),
    categories: [ALL_CATEGORIES, ...categories.map(category => category.name)],
  };
}
