import { NavLink, Route, Routes } from 'react-router-dom';
import AdminDashboard from './AdminDashboard.jsx';
import AdminOrders from './AdminOrders.jsx';
import AdminRestaurants from './AdminRestaurants.jsx';
import AdminUsers from './AdminUsers.jsx';

export default function AdminPage() {
  return (
    <div className="container admin">
      <aside className="admin-nav card">
        <div className="admin-nav-title">Адмін-панель</div>
        <NavLink to="/admin" end>Огляд</NavLink>
        <NavLink to="/admin/orders">Замовлення</NavLink>
        <NavLink to="/admin/restaurants">Заклади та меню</NavLink>
        <NavLink to="/admin/users">Користувачі</NavLink>
      </aside>
      <section className="admin-content">
        <Routes>
          <Route index element={<AdminDashboard />} />
          <Route path="orders" element={<AdminOrders />} />
          <Route path="restaurants" element={<AdminRestaurants />} />
          <Route path="users" element={<AdminUsers />} />
        </Routes>
      </section>
    </div>
  );
}
