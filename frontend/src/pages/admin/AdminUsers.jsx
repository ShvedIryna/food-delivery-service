import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { dateTime } from '../../utils/format.js';

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api('/admin/users').then(setUsers).catch((e) => setError(e.message));
  }, []);

  const update = async (id, patch) => {
    setError('');
    try {
      const updated = await api(`/admin/users/${id}`, { method: 'PATCH', body: patch });
      setUsers((list) => list.map((u) => (u.id === id ? updated : u)));
    } catch (e) { setError(e.message); }
  };

  return (
    <>
      <h1>Користувачі</h1>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="card table-wrap">
        <table className="table">
          <thead>
            <tr><th>ID</th><th>ПІБ</th><th>E-mail</th><th>Телефон</th><th>Роль</th><th>Картка</th><th>Бонуси</th><th>Зареєстрований</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td className="small">{u.phone}</td>
                <td>
                  <select value={u.role} onChange={(e) => update(u.id, { role: e.target.value })}>
                    <option value="CLIENT">Клієнт</option>
                    <option value="ADMIN">Адміністратор</option>
                  </select>
                </td>
                <td>
                  <select value={u.card_type} onChange={(e) => update(u.id, { card_type: e.target.value })}>
                    <option value="STANDARD">Стандартна</option>
                    <option value="PREMIUM">Преміум</option>
                  </select>
                </td>
                <td>
                  <input
                    type="number"
                    className="input-small"
                    defaultValue={u.bonus_points}
                    min={0}
                    onBlur={(e) => Number(e.target.value) !== u.bonus_points && update(u.id, { bonus_points: Number(e.target.value) })}
                  />
                </td>
                <td className="small">{dateTime(u.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
