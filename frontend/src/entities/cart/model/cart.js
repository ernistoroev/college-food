
export function addItemToCart(cart, dish) {
  const found = cart.find(item => item.id === dish.id);

  if (found) {
    return cart.map(item =>
      item.id === dish.id
        ? { ...item, quantity: item.quantity + 1 }
        : item
    );
  }

  return [...cart, { ...dish, quantity: 1 }];
}

export function removeItemFromCart(cart, dishId) {
  return cart
    .map(item =>
      item.id === dishId
        ? { ...item, quantity: item.quantity - 1 }
        : item
    )
    .filter(item => item.quantity > 0);
}

export function deleteItemFromCart(cart, dishId) {
  return cart.filter(item => item.id !== dishId);
}

export function getCartCount(cart) {
  return cart.reduce((sum, item) => sum + item.quantity, 0);
}

export function getCartTotal(cart) {
  return cart.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );
}
