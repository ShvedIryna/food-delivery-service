import { Navigate, Route, Routes } from 'react-router-dom';
import Header from './components/Header.jsx';
import { useAuth } from './context/AuthContext.jsx';
import CatalogPage from './pages/CatalogPage.jsx';
import RestaurantPage from './pages/RestaurantPage.jsx';
import CartPage from './pages/CartPage.jsx';
import OrdersPage from './pages/OrdersPage.jsx';
import OrderDetailPage from './pages/OrderDetailPage.jsx';
import ProfilePage from './pages/ProfilePage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import RegisterPage from './pages/RegisterPage.jsx';

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container"><p className="muted">Завантаження…</p></div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<CatalogPage />} />
          <Route path="/restaurants/:id" element={<RestaurantPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/orders" element={<Protected><OrdersPage /></Protected>} />
          <Route path="/orders/:id" element={<Protected><OrderDetailPage /></Protected>} />
          <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <footer className="footer">© 2026 Смак Експрес — доставка їжі зі смаком</footer>
    </>
  );
}
