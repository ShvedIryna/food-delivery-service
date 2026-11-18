import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useAuth } from '../context/AuthContext.jsx';
import { dateTime } from '../utils/format.js';
import { BellIcon } from './Icons.jsx';

export default function NotificationBell() {
  const { refresh } = useAuth();
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const lastUnread = useRef(0);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const data = await api('/me/notifications');
        if (!alive) return;
        setItems(data);
        const unread = data.filter((n) => !n.is_read).length;
        if (unread !== lastUnread.current) {
          lastUnread.current = unread;
          refresh(); // оновлюємо баланс бонусів у шапці
        }
      } catch {
        /* мережеві помилки ігноруємо */
      }
    };
    load();
    const timer = setInterval(load, 10000);
    return () => { alive = false; clearInterval(timer); };
  }, [refresh]);

  const unread = items.filter((n) => !n.is_read).length;

  const toggle = async () => {
    setOpen((o) => !o);
    if (!open && unread) {
      await api('/me/notifications/read-all', { method: 'POST' });
      setItems((list) => list.map((n) => ({ ...n, is_read: true })));
      lastUnread.current = 0;
    }
  };

  return (
    <div className="bell">
      <button className="icon-link" onClick={toggle} title="Сповіщення" aria-label="Сповіщення">
        <BellIcon />
        {unread > 0 && <span className="badge badge-dot">{unread}</span>}
      </button>
      {open && (
        <div className="bell-dropdown" onMouseLeave={() => setOpen(false)}>
          <div className="bell-title">Сповіщення</div>
          {items.length === 0 && <p className="muted small">Сповіщень поки немає</p>}
          {items.slice(0, 12).map((n) => (
            <div key={n.id} className={`bell-item ${n.is_read ? '' : 'unread'}`}>
              <div className="bell-item-title">
                {n.title}
              </div>
              <div className="small">{n.message}</div>
              <div className="small muted">
                {dateTime(n.created_at)}
                {n.order_id && <> · <Link to={`/orders/${n.order_id}`} onClick={() => setOpen(false)}>Замовлення №{n.order_id}</Link></>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
