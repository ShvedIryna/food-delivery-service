import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';
import { DELIVERY_TITLES, dateTime, initials, money } from '../utils/format.js';

export default function OrdersPage() {
  const [orders, setOrders] = useState(null);
  const [error, setError] = useState('');
  const { refresh } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    api('/orders').then(setOrders).catch((e) => setError(e.message));
  }, []);

  const repeat = async (id) => {
    try {
      const order = await api(`/orders/${id}/repeat`, { method: 'POST' });
      await refresh();
      navigate(`/orders/${order.id}`);
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="container">
      <h1>Історія замовлень</h1>
      {error && <div className="alert alert-error">{error}</div>}
      {orders === null && <p className="muted">Завантаження…</p>}
      {orders?.length === 0 && <p className="muted">Ви ще нічого не замовляли. <Link to="/">До каталогу →</Link></p>}
      <div className="order-list">
        {orders?.map((o) => (
          <div key={o.id} className="card order-card">
            <div className="avatar">{initials(o.restaurant_name)}</div>
            <div className="grow">
              <div className="row-between">
                <Link to={`/orders/${o.id}`} className="card-title">№{o.id} · {o.restaurant_name}</Link>
                <span className={`status status-${o.status}`}>{o.status_title}</span>
              </div>
              <div className="small muted">{dateTime(o.created_at)} · {DELIVERY_TITLES[o.delivery_type]}</div>
              <div className="small">{o.items.map((i) => `${i.dish_name} × ${i.quantity}`).join(', ')}</div>
              <div className="row-between">
                <b>{money(o.total)}</b>
                <div className="row">
                  <Link to={`/orders/${o.id}`} className="btn btn-ghost">Деталі</Link>
                  <button className="btn btn-primary" onClick={() => repeat(o.id)} title="Повторне замовлення в один клік">
                    Повторити
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
