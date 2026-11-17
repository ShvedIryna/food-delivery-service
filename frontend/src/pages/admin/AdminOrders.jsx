import { useCallback, useEffect, useState } from 'react';
import { api } from '../../api.js';
import { DELIVERY_TITLES, PAYMENT_STATUS_TITLES, PAYMENT_TITLES, STATUS_TITLES, dateTime, money } from '../../utils/format.js';

const NEXT_LABEL = {
  NEW: 'Почати готувати',
  PREPARING: 'Готово',
  DELIVERING: 'Доставлено',
  READY_FOR_PICKUP: 'Видано',
};

export default function AdminOrders() {
  const [orders, setOrders] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(() => {
    api('/admin/orders', { params: { status_filter: statusFilter } }).then(setOrders).catch((e) => setError(e.message));
  }, [statusFilter]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  const action = async (id, kind) => {
    setError('');
    try {
      await api(`/admin/orders/${id}/${kind}`, { method: 'POST' });
      load();
    } catch (e) { setError(e.message); }
  };

  return (
    <>
      <div className="row-between">
        <h1>Замовлення</h1>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">Усі статуси</option>
          {Object.entries(STATUS_TITLES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr><th>№</th><th>Дата</th><th>Заклад</th><th>Склад</th><th>Доставка</th><th>Оплата</th><th>Сума</th><th>Статус</th><th>Дії</th></tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.id}</td>
                <td className="small">{dateTime(o.created_at)}</td>
                <td>{o.restaurant_name}</td>
                <td className="small">{o.items.map((i) => `${i.dish_name}×${i.quantity}`).join(', ')}</td>
                <td className="small">{DELIVERY_TITLES[o.delivery_type]}{o.address ? <><br />{o.address}</> : null}</td>
                <td className="small">{PAYMENT_TITLES[o.payment_method]}<br />{PAYMENT_STATUS_TITLES[o.payment_status] || o.payment_status}</td>
                <td><b>{money(o.total)}</b></td>
                <td><span className={`status status-${o.status}`}>{o.status_title}</span></td>
                <td className="actions">
                  {NEXT_LABEL[o.status] && (
                    <button className="btn btn-primary small" onClick={() => action(o.id, 'advance')}>
                      {o.status === 'PREPARING' && o.delivery_type !== 'PICKUP' ? 'Передати кур\'єру' : NEXT_LABEL[o.status]}
                    </button>
                  )}
                  {['NEW', 'PREPARING'].includes(o.status) && (
                    <button className="btn btn-danger small" onClick={() => action(o.id, 'cancel')}>Скасувати</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
