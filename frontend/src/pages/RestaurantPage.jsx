import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../api.js';
import StarRating from '../components/StarRating.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useCart } from '../context/CartContext.jsx';
import { CUISINE_TITLES, dateTime, initials, money, priceLevel } from '../utils/format.js';

export default function RestaurantPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const cart = useCart();
  const [restaurant, setRestaurant] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [category, setCategory] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [error, setError] = useState('');
  const [added, setAdded] = useState(null);

  useEffect(() => {
    api(`/restaurants/${id}`).then(setRestaurant).catch((e) => setError(e.message));
    api(`/restaurants/${id}/reviews`).then(setReviews).catch(() => {});
  }, [id, user]);

  const categories = useMemo(
    () => [...new Set((restaurant?.dishes || []).map((d) => d.category))],
    [restaurant],
  );

  if (error) return <div className="container"><div className="alert alert-error">{error}</div></div>;
  if (!restaurant) return <div className="container"><p className="muted">Завантаження…</p></div>;

  const dishes = restaurant.dishes.filter(
    (d) => (!category || d.category === category) && (!maxPrice || d.price <= Number(maxPrice)),
  );

  const toggleFavorite = async () => {
    await api(`/me/favorites/${restaurant.id}`, { method: restaurant.is_favorite ? 'DELETE' : 'POST' });
    setRestaurant((r) => ({ ...r, is_favorite: !r.is_favorite }));
  };

  const add = (dish) => {
    cart.addItem(restaurant, dish);
    setAdded(dish.id);
    setTimeout(() => setAdded(null), 900);
  };

  return (
    <div className="container">
      <div className="restaurant-header card">
        <div className="restaurant-header-initials">{initials(restaurant.name)}</div>
        <div className="grow">
          <h1>{restaurant.name}</h1>
          <p>{restaurant.description}</p>
          <div className="meta">
            <span>{CUISINE_TITLES[restaurant.cuisine]}</span>
            <span>{priceLevel(restaurant.price_level)}</span>
            <span><StarRating value={restaurant.rating} /> {restaurant.rating.toFixed(1)} ({restaurant.reviews_count} відгуків)</span>
            <span>Доставка {restaurant.delivery_time_min} хв</span>
            <span>{restaurant.address}</span>
            {restaurant.min_order > 0 && <span>Мін. замовлення {money(restaurant.min_order)}</span>}
          </div>
        </div>
        {user && (
          <button className="btn btn-ghost" onClick={toggleFavorite}>
            {restaurant.is_favorite ? 'В улюблених' : 'Додати в улюблені'}
          </button>
        )}
      </div>

      <div className="layout-2">
        <section>
          <div className="row-between">
            <h2>Меню</h2>
            <div className="inline-filters">
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">Усі категорії</option>
                {categories.map((c) => <option key={c}>{c}</option>)}
              </select>
              <select value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)}>
                <option value="">Будь-яка ціна</option>
                <option value="100">до 100 ₴</option>
                <option value="200">до 200 ₴</option>
                <option value="300">до 300 ₴</option>
              </select>
            </div>
          </div>
          <div className="dish-list">
            {dishes.map((d) => (
              <div key={d.id} className="card dish">
                <div className="grow">
                  <div className="card-title">{d.name}</div>
                  <div className="small muted">{d.category}{d.weight_g ? ` · ${d.weight_g} г` : ''}</div>
                  <div className="small">{d.description}</div>
                </div>
                <div className="dish-buy">
                  <div className="price">{money(d.price)}</div>
                  <button className="btn btn-primary" onClick={() => add(d)}>
                    {added === d.id ? 'Додано' : '+ У кошик'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <aside>
          {cart.restaurant?.id === restaurant.id && cart.count > 0 && (
            <div className="card sticky">
              <h3>Ваш кошик</h3>
              {cart.items.map((i) => (
                <div key={i.dish_id} className="row-between small">
                  <span>{i.name} × {i.quantity}</span>
                  <span>{money(i.price * i.quantity)}</span>
                </div>
              ))}
              <div className="row-between total-row"><span>Разом</span><b>{money(cart.subtotal)}</b></div>
              <Link to="/cart" className="btn btn-primary btn-block">Оформити замовлення</Link>
            </div>
          )}

          <div className="card">
            <h3>Відгуки</h3>
            {reviews.length === 0 && <p className="muted small">Відгуків поки немає</p>}
            {reviews.map((r) => (
              <div key={r.id} className="review">
                <div className="row-between">
                  <b>{r.author}</b>
                  <StarRating value={r.rating} />
                </div>
                <div className="small">{r.text}</div>
                <div className="small muted">{dateTime(r.created_at)}</div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
