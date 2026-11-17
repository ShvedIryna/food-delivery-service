import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { money } from '../../utils/format.js';

function Bars({ rows, value, label, format = (v) => v }) {
  const max = Math.max(1, ...rows.map(value));
  return (
    <div className="bars">
      {rows.map((r) => (
        <div key={label(r)} className="bar-row">
          <span className="bar-label">{label(r)}</span>
          <div className="bar-track"><div className="bar" style={{ width: `${(value(r) / max) * 100}%` }} /></div>
          <span className="bar-value">{format(value(r))}</span>
        </div>
      ))}
    </div>
  );
}

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const load = () => api('/admin/stats').then(setStats).catch(() => {});
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  if (!stats) return <p className="muted">Завантаження…</p>;

  const tiles = [
    ['Замовлень усього', stats.orders_total],
    ['За останні 7 днів', stats.orders_last_7_days],
    ['Виручка (доставлені)', money(stats.revenue)],
    ['Користувачів', `${stats.users} (преміум: ${stats.premium_users})`],
    ['Закладів', stats.restaurants],
  ];

  return (
    <>
      <h1>Огляд</h1>
      <div className="tiles">
        {tiles.map(([t, v]) => (
          <div key={t} className="card tile"><div className="tile-value">{v}</div><div className="small muted">{t}</div></div>
        ))}
      </div>
      <div className="layout-2 even">
        <div className="card">
          <h3>Виручка за закладами</h3>
          <Bars rows={stats.revenue_by_restaurant} value={(r) => r.revenue} label={(r) => r.name} format={money} />
        </div>
        <div className="card">
          <h3>Найпопулярніші страви</h3>
          <Bars rows={stats.top_dishes} value={(r) => r.quantity} label={(r) => r.name} format={(v) => `${v} шт.`} />
        </div>
        <div className="card">
          <h3>Замовлення за статусами</h3>
          <Bars rows={stats.orders_by_status} value={(r) => r.count} label={(r) => r.title} />
        </div>
      </div>
    </>
  );
}
