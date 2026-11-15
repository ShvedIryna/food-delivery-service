import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useCart } from '../context/CartContext.jsx';
import NotificationBell from './NotificationBell.jsx';

export default function Header() {
  const { user, logout } = useAuth();
  const { count } = useCart();
  const navigate = useNavigate();

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="logo">Смак Експрес</Link>
        <nav className="nav">
          <NavLink to="/" end>Заклади</NavLink>
          {user && <NavLink to="/orders">Мої замовлення</NavLink>}
        </nav>
        <div className="header-actions">
          <Link to="/cart" className="cart-link">
            Кошик {count > 0 && <span className="badge">{count}</span>}
          </Link>
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
