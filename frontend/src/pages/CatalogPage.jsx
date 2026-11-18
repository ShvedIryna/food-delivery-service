import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import RestaurantCard from '../components/RestaurantCard.jsx';
import { useAuth } from '../context/AuthContext.jsx';

const INITIAL = { q: '', cuisine: '', price_level: '', max_delivery_time: '', sort: 'rating', favorites_only: false };

export default function CatalogPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [filters, setFilters] = useState(INITIAL);
  const [cuisines, setCuisines] = useState([]);
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api('/cuisines').then(setCuisines).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      api('/restaurants', { params: { ...filters, favorites_only: filters.favorites_only || undefined } })
        .then((data) => { setRestaurants(data); setError(''); })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(timer);
  }, [filters, user]);

  const set = (key) => (e) =>
    setFilters((f) => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const toggleFavorite = async (r) => {
    if (!user) return navigate('/login');
    await api(`/me/favorites/${r.id}`, { method: r.is_favorite ? 'DELETE' : 'POST' });
    setRestaurants((list) =>
      list
        .map((x) => (x.id === r.id ? { ...x, is_favorite: !x.is_favorite } : x))
        .filter((x) => !filters.favorites_only || x.is_favorite),
    );
  };

  return (
    <div className="container">
      <section className="hero">
        <h1>Їжа з улюблених закладів Львова — до ваших дверей</h1>
        <p>Обирайте страви, оплачуйте онлайн і стежте за кур'єром на карті.</p>
      </section>

      <div className="filters card">
        <input placeholder="Пошук закладу…" value={filters.q} onChange={set('q')} />
        <select value={filters.cuisine} onChange={set('cuisine')}>
          <option value="">Усі кухні</option>
          {cuisines.map((c) => <option key={c.code} value={c.code}>{c.title}</option>)}
        </select>
        <select value={filters.price_level} onChange={set('price_level')}>
          <option value="">Будь-яка ціна</option>
          <option value="1">₴ — бюджетно</option>
          <option value="2">до ₴₴ — середньо</option>
          <option value="3">до ₴₴₴ — преміум</option>
        </select>
        <select value={filters.max_delivery_time} onChange={set('max_delivery_time')}>
          <option value="">Будь-який час доставки</option>
          <option value="30">до 30 хв</option>
          <option value="40">до 40 хв</option>
          <option value="60">до 60 хв</option>
        </select>
        <select value={filters.sort} onChange={set('sort')}>
          <option value="rating">За рейтингом</option>
          <option value="delivery_time">За часом доставки</option>
          <option value="price">За ціною</option>
          <option value="name">За назвою</option>
        </select>
        {user && user.role !== 'ADMIN' && (
          <button
            type="button"
            className={`toggle ${filters.favorites_only ? 'active' : ''}`}
            onClick={() => setFilters((f) => ({ ...f, favorites_only: !f.favorites_only }))}
          >
            Лише улюблені
          </button>
        )}
        <button className="btn btn-ghost" onClick={() => setFilters(INITIAL)}>Скинути</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading && <p className="muted">Завантаження…</p>}
      {!loading && restaurants.length === 0 && <p className="muted">Нічого не знайдено за обраними фільтрами.</p>}

      <div className="grid">
        {restaurants.map((r) => (
          <RestaurantCard key={r.id} restaurant={r} onToggleFavorite={toggleFavorite} />
        ))}
      </div>
    </div>
  );
}
