import { createContext, useContext, useEffect, useMemo, useState } from 'react';

const CartContext = createContext(null);
const EMPTY = { restaurant: null, items: [] };

function load() {
  try {
    return JSON.parse(localStorage.getItem('cart')) || EMPTY;
  } catch {
    return EMPTY;
  }
}

export function CartProvider({ children }) {
  const [cart, setCart] = useState(load);

  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(cart));
  }, [cart]);

  const addItem = (restaurant, dish) => {
    let replace = false;
    if (cart.restaurant && cart.restaurant.id !== restaurant.id) {
      replace = window.confirm(
        `У кошику є страви з «${cart.restaurant.name}». Очистити кошик і додати страву з «${restaurant.name}»?`,
      );
      if (!replace) return;
    }
    setCart((prev) => {
      const base = replace ? EMPTY : prev;
      const existing = base.items.find((i) => i.dish_id === dish.id);
      const items = existing
        ? base.items.map((i) => (i.dish_id === dish.id ? { ...i, quantity: i.quantity + 1 } : i))
        : [...base.items, { dish_id: dish.id, name: dish.name, price: dish.price, quantity: 1 }];
      return {
        restaurant: { id: restaurant.id, name: restaurant.name, min_order: restaurant.min_order },
        items,
      };
    });
  };

  const setQuantity = (dishId, quantity) =>
    setCart((prev) => {
      const items = prev.items
        .map((i) => (i.dish_id === dishId ? { ...i, quantity } : i))
        .filter((i) => i.quantity > 0);
      return items.length ? { ...prev, items } : EMPTY;
    });

  const clear = () => setCart(EMPTY);

  const value = useMemo(() => {
    const count = cart.items.reduce((s, i) => s + i.quantity, 0);
    const subtotal = cart.items.reduce((s, i) => s + i.price * i.quantity, 0);
    return { ...cart, count, subtotal, addItem, setQuantity, clear };
  }, [cart]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export const useCart = () => useContext(CartContext);
