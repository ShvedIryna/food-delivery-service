import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useCart } from '../context/CartContext.jsx';
import { CartIcon } from './Icons.jsx';
import NotificationBell from './NotificationBell.jsx';

export default function Header() {
  const { user, logout } = useAuth();
  const { count } = useCart();
  const navigate = useNavigate();
  const isAdmin = user?.role === 'ADMIN';

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="logo">Смак Експрес</Link>
        <nav className="nav">
          <NavLink to="/" end>Заклади</NavLink>
          {user && !isAdmin && <NavLink to="/orders">Мої замовлення</NavLink>}
          {isAdmin && <NavLink to="/admin">Адмін-панель</NavLink>}
        </nav>
        <div className="header-actions">
          {!isAdmin && (
            <Link to="/cart" className="icon-link" title="Кошик" aria-label="Кошик">
              <CartIcon />
              {count > 0 && <span className="badge badge-dot">{count}</span>}
            </Link>
          )}
          {user ? (
            <>
              <NotificationBell />
              <Link to="/profile" className="user-chip">
                {user.full_name.split(' ')[0]}
                {user.card_type === 'PREMIUM' && <span className="premium-chip">Premium</span>}
                <span className="bonus-chip">{user.bonus_points} б.</span>
              </Link>
              <button className="btn btn-ghost" onClick={() => { logout(); navigate('/'); }}>Вийти</button>
            </>
          ) : (
            <Link to="/login" className="btn btn-primary">Увійти</Link>
          )}
        </div>
      </div>
    </header>
  );
}
