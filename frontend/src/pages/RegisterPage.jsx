import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: '', email: '', phone: '', password: '' });
  const [error, setError] = useState('');

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await register({ ...form, phone: form.phone || null });
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container auth">
      <div className="card">
        <h1>Реєстрація</h1>
        <p className="small muted">Після реєстрації ви отримаєте 50 вітальних бонусів</p>
        <form onSubmit={submit} className="form">
          <label className="field">ПІБ<input value={form.full_name} onChange={set('full_name')} required /></label>
          <label className="field">E-mail<input type="email" value={form.email} onChange={set('email')} required /></label>
          <label className="field">Телефон<input value={form.phone} onChange={set('phone')} placeholder="+380…" /></label>
          <label className="field">Пароль (мін. 6 символів)<input type="password" value={form.password} onChange={set('password')} minLength={6} required /></label>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="btn btn-primary btn-block">Зареєструватися</button>
        </form>
        <p className="small">Вже є акаунт? <Link to="/login">Увійти</Link></p>
      </div>
    </div>
  );
}
