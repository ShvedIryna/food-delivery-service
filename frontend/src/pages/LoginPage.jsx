import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

const DEMO = [
  ['client@food.ua', 'client123', 'Клієнт'],
  ['premium@food.ua', 'premium123', 'Преміум-клієнт'],
  ['admin@food.ua', 'admin123', 'Адміністратор'],
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const user = await login(email, password);
      navigate(user.role === 'ADMIN' ? '/admin' : '/');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="container auth">
      <div className="card">
        <h1>Вхід</h1>
        <form onSubmit={submit} className="form">
          <label className="field">E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label className="field">Пароль<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          {error && <div className="alert alert-error">{error}</div>}
          <button className="btn btn-primary btn-block">Увійти</button>
        </form>
        <p className="small">Немає акаунту? <Link to="/register">Зареєструватися</Link></p>
        <div className="demo">
          <div className="small muted">Демо-акаунти:</div>
          {DEMO.map(([em, pw, title]) => (
            <button key={em} className="btn btn-ghost small" onClick={() => { setEmail(em); setPassword(pw); }}>
              {title}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
