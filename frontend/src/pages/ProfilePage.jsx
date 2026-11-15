import { useEffect, useState } from 'react';
import { api } from '../api.js';
import RestaurantCard from '../components/RestaurantCard.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { dateTime, money } from '../utils/format.js';

export default function ProfilePage() {
  const { user, setUser } = useAuth();
  const [form, setForm] = useState({ full_name: user.full_name, phone: user.phone || '', address: user.address || '' });
  const [loyalty, setLoyalty] = useState(null);
  const [favorites, setFavorites] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const loadLoyalty = () => api('/me/loyalty').then(setLoyalty);

  useEffect(() => {
    loadLoyalty();
    api('/me/favorites').then(setFavorites);
    api('/me/notifications').then(setNotifications);
  }, []);

  const save = async (e) => {
    e.preventDefault();
    setError('');
    try {
      setUser(await api('/me', { method: 'PUT', body: form }));
      setMessage('Профіль збережено');
      setTimeout(() => setMessage(''), 2000);
    } catch (err) { setError(err.message); }
  };

  const buyPremium = async () => {
    if (!window.confirm(`Оформити преміум-картку за ${money(loyalty.premium_price)}/міс? (оплата імітується)`)) return;
    try {
      setUser(await api('/me/loyalty/premium', { method: 'POST' }));
      loadLoyalty();
    } catch (err) { setError(err.message); }
  };

  const removeFavorite = async (r) => {
    await api(`/me/favorites/${r.id}`, { method: 'DELETE' });
    setFavorites((list) => list.filter((x) => x.id !== r.id));
  };

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  return (
    <div className="container">
      <h1>Особистий кабінет</h1>
      <div className="layout-2">
        <section>
          <div className="card">
            <h3>Профіль</h3>
            <form onSubmit={save} className="form">
              <label className="field">E-mail<input value={user.email} disabled /></label>
              <label className="field">ПІБ<input value={form.full_name} onChange={set('full_name')} /></label>
              <label className="field">Телефон<input value={form.phone} onChange={set('phone')} placeholder="+380…" /></label>
              <label className="field">Адреса за замовчуванням<input value={form.address} onChange={set('address')} /></label>
              <button className="btn btn-primary">Зберегти</button>
              {message && <span className="text-green"> {message}</span>}
              {error && <div className="alert alert-error">{error}</div>}
            </form>
          </div>

          <div className="card">
            <h3>Улюблені заклади</h3>
            {favorites.length === 0 && <p className="muted small">Додайте заклади в улюблені на сторінці каталогу.</p>}
            <div className="grid grid-small">
              {favorites.map((r) => (
                <RestaurantCard key={r.id} restaurant={{ ...r, is_favorite: true }} onToggleFavorite={removeFavorite} />
              ))}
            </div>
          </div>
        </section>

        <aside>
          {loyalty && (
            <div className={`card loyalty-card ${loyalty.card.type === 'PREMIUM' ? 'premium' : ''}`}>
              <div className="loyalty-title">{loyalty.card.title}</div>
              <div className="loyalty-points">{loyalty.bonus_points} <span>бонусів</span></div>
              <ul className="small">{loyalty.card.perks.map((p) => <li key={p}>{p}</li>)}</ul>
              <div className="small">Виконано замовлень: <b>{loyalty.delivered_orders}</b></div>
              {loyalty.regular_discount_percent > 0 && (
                <div className="small">Знижка постійного клієнта: <b>{loyalty.regular_discount_percent}%</b></div>
              )}
              {loyalty.next_level && (
                <div className="small">Ще {loyalty.next_level.orders_needed} замовл. — і знижка {loyalty.next_level.discount_percent}%</div>
              )}
            </div>
          )}
          {loyalty && loyalty.card.type !== 'PREMIUM' && (
            <div className="card">
              <h3>Преміум-картка</h3>
              <ul className="small">{loyalty.premium_offer.perks.map((p) => <li key={p}>{p}</li>)}</ul>
              <button className="btn btn-primary btn-block" onClick={buyPremium}>
                Оформити за {money(loyalty.premium_price)}/міс
              </button>
            </div>
          )}
          <div className="card">
            <h3>Сповіщення</h3>
            {notifications.length === 0 && <p className="muted small">Сповіщень немає</p>}
            {notifications.slice(0, 8).map((n) => (
              <div key={n.id} className="review">
                <b className="small">{n.title}</b>
                <div className="small">{n.message}</div>
                <div className="small muted">{dateTime(n.created_at)}</div>
              </div>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
