import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api.js';
import StarRating from '../components/StarRating.jsx';
import StatusTimeline from '../components/StatusTimeline.jsx';
import TrackingMap from '../components/TrackingMap.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { DELIVERY_TITLES, PAYMENT_STATUS_TITLES, PAYMENT_TITLES, dateTime, money } from '../utils/format.js';

const ACTIVE = ['NEW', 'PREPARING', 'DELIVERING', 'READY_FOR_PICKUP'];

export default function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refresh } = useAuth();
  const [order, setOrder] = useState(null);
  const [error, setError] = useState('');
  const [review, setReview] = useState({ rating: 5, text: '' });
  const [reviewSent, setReviewSent] = useState(false);

  const load = useCallback(() => {
    api(`/orders/${id}`).then(setOrder).catch((e) => setError(e.message));
  }, [id]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!order || !ACTIVE.includes(order.status)) return undefined;
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [order, load]);

  const onStatusChange = useCallback(() => { load(); refresh(); }, [load, refresh]);

  const cancel = async () => {
    if (!window.confirm('Скасувати замовлення?')) return;
    try {
      setOrder(await api(`/orders/${id}/cancel`, { method: 'POST' }));
      refresh();
    } catch (e) { setError(e.message); }
  };

  const repeat = async () => {
    try {
      const o = await api(`/orders/${id}/repeat`, { method: 'POST' });
      refresh();
      navigate(`/orders/${o.id}`);
    } catch (e) { setError(e.message); }
  };

  const sendReview = async (e) => {
    e.preventDefault();
    try {
      await api(`/restaurants/${order.restaurant_id}/reviews`, { method: 'POST', body: review });
      setReviewSent(true);
    } catch (err) { setError(err.message); }
  };

  if (error && !order) return <div className="container"><div className="alert alert-error">{error}</div></div>;
  if (!order) return <div className="container"><p className="muted">Завантаження…</p></div>;

  const pickup = order.delivery_type === 'PICKUP';

  return (
    <div className="container">
      <div className="row-between">
        <h1>Замовлення №{order.id}</h1>
        <span className={`status status-${order.status}`}>{order.status_title}</span>
      </div>
      <StatusTimeline status={order.status} pickup={pickup} />
      {error && <div className="alert alert-error">{error}</div>}

      <div className="layout-2">
        <section>
          {!pickup && order.status !== 'CANCELLED' && (
            <div className="card">
              <h3>Відстеження доставки</h3>
              <TrackingMap orderId={order.id} active={ACTIVE.includes(order.status)} onStatusChange={onStatusChange} />
            </div>
          )}
          <div className="card">
            <h3>{order.restaurant_name}</h3>
            {order.items.map((i) => (
              <div key={i.id} className="row-between">
                <span>{i.dish_name} × {i.quantity}</span>
                <span>{money(i.unit_price * i.quantity)}</span>
              </div>
            ))}
          </div>
          {order.status === 'DELIVERED' && (
            <div className="card">
              <h3>Оцініть заклад</h3>
              {reviewSent ? <p className="text-green">Дякуємо за відгук!</p> : (
                <form onSubmit={sendReview}>
                  <StarRating value={review.rating} onChange={(rating) => setReview((r) => ({ ...r, rating }))} />
                  <textarea rows={3} placeholder="Ваші враження…" value={review.text}
                    onChange={(e) => setReview((r) => ({ ...r, text: e.target.value }))} />
                  <button className="btn btn-primary">Надіслати відгук</button>
                </form>
              )}
            </div>
          )}
        </section>

        <aside>
          <div className="card">
            <h3>Деталі</h3>
            <div className="kv"><span>Створено</span><span>{dateTime(order.created_at)}</span></div>
            <div className="kv"><span>Доставка</span><span>{DELIVERY_TITLES[order.delivery_type]}</span></div>
            {order.address && <div className="kv"><span>Адреса</span><span>{order.address}</span></div>}
            <div className="kv"><span>Оплата</span><span>{PAYMENT_TITLES[order.payment_method]}</span></div>
            <div className="kv"><span>Статус оплати</span><span>{PAYMENT_STATUS_TITLES[order.payment_status] || order.payment_status}</span></div>
            {order.transaction_id && <div className="kv"><span>Транзакція</span><span className="small">{order.transaction_id}</span></div>}
            {order.comment && <div className="kv"><span>Коментар</span><span>{order.comment}</span></div>}
            <hr />
            <div className="kv"><span>Страви</span><span>{money(order.subtotal)}</span></div>
            <div className="kv"><span>Доставка</span><span>{money(order.delivery_fee)}</span></div>
            {order.discount > 0 && <div className="kv text-green"><span>Знижка</span><span>−{money(order.discount)}</span></div>}
            {order.bonus_used > 0 && <div className="kv text-green"><span>Бонуси</span><span>−{money(order.bonus_used)}</span></div>}
            <div className="kv total-row"><span>Разом</span><b>{money(order.total)}</b></div>
            {order.bonus_earned > 0 && <div className="small text-green">Нараховано {order.bonus_earned} бонусів</div>}
            <div className="stack">
              {order.can_cancel && <button className="btn btn-danger btn-block" onClick={cancel}>Скасувати</button>}
              <button className="btn btn-primary btn-block" onClick={repeat}>Повторити замовлення</button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
