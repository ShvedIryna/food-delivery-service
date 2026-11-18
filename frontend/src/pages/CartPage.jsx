import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import LocationPicker from '../components/LocationPicker.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useCart } from '../context/CartContext.jsx';
import { money } from '../utils/format.js';

export default function CartPage() {
  const cart = useCart();
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [options, setOptions] = useState({ delivery: [], payment: [] });
  const [restaurant, setRestaurant] = useState(null);
  const [form, setForm] = useState({
    delivery_type: 'STANDARD',
    payment_method: 'CARD',
    address: user?.address || '',
    point: null,
    comment: '',
    useBonus: false,
    card_number: '4242 4242 4242 4242',
  });
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api('/orders/options').then(setOptions).catch(() => {});
  }, []);

  useEffect(() => {
    if (cart.restaurant) api(`/restaurants/${cart.restaurant.id}`).then(setRestaurant).catch(() => {});
  }, [cart.restaurant]);

  useEffect(() => {
    if (user?.address) setForm((f) => (f.address ? f : { ...f, address: user.address }));
  }, [user]);

  const needsAddress = form.delivery_type !== 'PICKUP';

  const buildBody = () => ({
    restaurant_id: cart.restaurant.id,
    items: cart.items.map((i) => ({ dish_id: i.dish_id, quantity: i.quantity })),
    delivery_type: form.delivery_type,
    payment_method: form.payment_method,
    address: needsAddress ? form.address : null,
    lat: needsAddress && form.point ? form.point[0] : null,
    lng: needsAddress && form.point ? form.point[1] : null,
    comment: form.comment || null,
    use_bonus: form.useBonus ? user.bonus_points : 0,
    card_number: form.payment_method === 'CARD' ? form.card_number : null,
  });

  useEffect(() => {
    if (!user || !cart.restaurant || cart.items.length === 0) {
      setQuote(null);
      return undefined;
    }
    const body = buildBody();
    if (needsAddress && (!body.address || body.lat === null)) {
      body.delivery_type = form.delivery_type;
      body.address = body.address || '—';
      body.lat = body.lat ?? 49.84;
      body.lng = body.lng ?? 24.03;
    }
    const timer = setTimeout(() => {
      api('/orders/quote', { method: 'POST', body })
        .then((q) => { setQuote(q); setError(''); })
        .catch((e) => { setQuote(null); setError(e.message); });
    }, 300);
    return () => clearTimeout(timer);
  }, [user, cart.items, cart.restaurant, form.delivery_type, form.useBonus]);

  const set = (key) => (e) =>
    setForm((f) => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  const submit = async () => {
    setError('');
    if (needsAddress && !form.point) {
      setError('Позначте точку доставки на карті');
      return;
    }
    setSubmitting(true);
    try {
      const order = await api('/orders', { method: 'POST', body: buildBody() });
      cart.clear();
      await refresh();
      navigate(`/orders/${order.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (cart.items.length === 0) {
    return (
      <div className="container">
        <div className="empty card">
          <h2>Кошик порожній</h2>
          <Link to="/" className="btn btn-primary">Обрати заклад</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>Оформлення замовлення</h1>
      <div className="layout-2">
        <section>
          <div className="card">
            <h3>{cart.restaurant.name}</h3>
            {cart.items.map((i) => (
              <div key={i.dish_id} className="cart-row">
                <span className="grow">{i.name}</span>
                <div className="qty">
                  <button onClick={() => cart.setQuantity(i.dish_id, i.quantity - 1)}>−</button>
                  <span>{i.quantity}</span>
                  <button onClick={() => cart.setQuantity(i.dish_id, i.quantity + 1)}>+</button>
                </div>
                <span className="cart-sum">{money(i.price * i.quantity)}</span>
              </div>
            ))}
            <div className="cart-actions">
              <button className="btn btn-ghost small" onClick={cart.clear}>Очистити кошик</button>
            </div>
          </div>

          {!user ? (
            <div className="card">
              <p>Щоб оформити замовлення, <Link to="/login">увійдіть</Link> або <Link to="/register">зареєструйтесь</Link>.</p>
            </div>
          ) : (
            <>
              <div className="card">
                <h3>Спосіб доставки</h3>
                <div className="options">
                  {options.delivery.map((d) => (
                    <label key={d.code} className={`option ${form.delivery_type === d.code ? 'selected' : ''}`}>
                      <input type="radio" name="delivery" value={d.code} checked={form.delivery_type === d.code} onChange={set('delivery_type')} />
                      <b>{d.title}</b>
                      <span className="small muted">{d.description}</span>
                    </label>
                  ))}
                </div>
                {needsAddress ? (
                  <>
                    <label className="field">Адреса доставки
                      <input value={form.address} onChange={set('address')} placeholder="вул. Городоцька, 10, кв. 5" />
                    </label>
                    <p className="small muted">Клікніть на карті, щоб позначити точку доставки:</p>
                    <LocationPicker value={form.point} onChange={(p) => setForm((f) => ({ ...f, point: p }))} restaurant={restaurant} />
                  </>
                ) : (
                  restaurant && <p className="small">Заберіть замовлення за адресою: <b>{restaurant.address}</b></p>
                )}
                <label className="field">Коментар для кур'єра / закладу
                  <input value={form.comment} onChange={set('comment')} placeholder="Домофон 15, без цибулі…" />
                </label>
              </div>

              <div className="card">
                <h3>Оплата</h3>
                <div className="options">
                  {options.payment.map((p) => (
                    <label key={p.code} className={`option ${form.payment_method === p.code ? 'selected' : ''}`}>
                      <input type="radio" name="payment" value={p.code} checked={form.payment_method === p.code} onChange={set('payment_method')} />
                      <b>{p.title}</b>
                    </label>
                  ))}
                </div>
                {form.payment_method === 'CARD' && (
                  <div className="card-form">
                    <label className="field">Номер картки (тестова)
                      <input value={form.card_number} onChange={set('card_number')} />
                    </label>
                    <div className="row">
                      <label className="field">Термін<input defaultValue="12/29" /></label>
                      <label className="field">CVV<input defaultValue="123" type="password" /></label>
                    </div>
                    <p className="small muted">Оплата імітується, реальні кошти не списуються.</p>
                  </div>
                )}
                {user.bonus_points > 0 && (
                  <label className="checkbox">
                    <input type="checkbox" checked={form.useBonus} onChange={set('useBonus')} />
                    Списати бонуси (доступно {user.bonus_points}, до 50% суми)
                  </label>
                )}
              </div>
            </>
          )}
        </section>

        <aside>
          <div className="card sticky">
            <h3>Підсумок</h3>
            <div className="row-between"><span>Страви</span><span>{money(quote?.subtotal ?? cart.subtotal)}</span></div>
            {quote && (
              <>
                <div className="row-between"><span>Доставка</span><span>{money(quote.delivery_fee)}</span></div>
                {quote.discount > 0 && <div className="row-between text-green"><span>Знижка</span><span>−{money(quote.discount)}</span></div>}
                {quote.bonus_used > 0 && <div className="row-between text-green"><span>Бонуси</span><span>−{money(quote.bonus_used)}</span></div>}
                {quote.notes.map((n) => <div key={n} className="small text-green">{n}</div>)}
                <div className="row-between total-row"><span>До сплати</span><b>{money(quote.total)}</b></div>
                <div className="small muted">Орієнтовно {quote.estimated_minutes} хв · +{quote.bonus_to_earn} бонусів</div>
              </>
            )}
            {error && <div className="alert alert-error">{error}</div>}
            <button className="btn btn-primary btn-block" disabled={!user || submitting} onClick={submit}>
              {submitting ? 'Оформлюємо…' : 'Підтвердити замовлення'}
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
