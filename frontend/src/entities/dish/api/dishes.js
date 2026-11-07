import { api, getList } from '../../../shared/api/client.js';

export const ALL_CATEGORIES = 'Всё меню';

// The API speaks Django field names; the cards use the names the frontend already had.
// floors: canteen id → floor, to show where the dish is served.
function toDish(dish, floors) {
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
    // Ids of the canteens that serve the dish: the order can be collected only there.
    canteens: dish.canteens,
    floors: dish.canteens.map(id => floors[id]).filter(Boolean).join(', '),
  };
}

export async function fetchMenu() {
  const [dishes, categories, canteens] = await Promise.all([
    getList('/dishes/'),
    getList('/categories/'),
    api.get('/canteens/').then(response => response.data),
  ]);
  const floors = Object.fromEntries(canteens.map(canteen => [canteen.id, canteen.floor]));

  return {
    dishes: dishes.map(dish => toDish(dish, floors)),
    categories: [ALL_CATEGORIES, ...categories.map(category => category.name)],
    canteens,
  };
}
