import { useEffect, useState } from 'react';
import { api } from '../../api.js';
import { CUISINE_TITLES, LVIV_CENTER, money, priceLevel } from '../../utils/format.js';

const EMPTY_RESTAURANT = {
  name: '', description: '', cuisine: 'UKRAINIAN', price_level: 2, delivery_time_min: 40, min_order: 0,
  address: '', lat: LVIV_CENTER[0], lng: LVIV_CENTER[1], image_url: '', is_active: true,
};
const EMPTY_DISH = { name: '', description: '', category: 'Основні страви', price: 100, weight_g: '', is_available: true };

function RestaurantForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial);
  const set = (key, num = false) => (e) => {
    const v = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [key]: num ? Number(v) : v }));
  };
  return (
    <form className="card form grid-form" onSubmit={(e) => { e.preventDefault(); onSave(form); }}>
      <h3 className="span-2">{initial.id ? `Редагування: ${initial.name}` : 'Новий заклад'}</h3>
      <label className="field">Назва<input value={form.name} onChange={set('name')} required /></label>
      <label className="field span-2">Опис<textarea rows={2} value={form.description} onChange={set('description')} /></label>
      <label className="field">Кухня
        <select value={form.cuisine} onChange={set('cuisine')}>
          {Object.entries(CUISINE_TITLES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </label>
      <label className="field">Ціновий рівень
        <select value={form.price_level} onChange={set('price_level', true)}>
          <option value={1}>₴</option><option value={2}>₴₴</option><option value={3}>₴₴₴</option>
        </select>
      </label>
      <label className="field">Час доставки, хв<input type="number" value={form.delivery_time_min} onChange={set('delivery_time_min', true)} /></label>
      <label className="field">Мін. замовлення, ₴<input type="number" value={form.min_order} onChange={set('min_order', true)} /></label>
      <label className="field span-2">Адреса<input value={form.address} onChange={set('address')} /></label>
      <label className="field span-2">Фото (посилання на зображення)<input value={form.image_url || ''} onChange={set('image_url')} placeholder="https://images.unsplash.com/..." /></label>
      <label className="field">Широта<input type="number" step="0.0001" value={form.lat} onChange={set('lat', true)} /></label>
      <label className="field">Довгота<input type="number" step="0.0001" value={form.lng} onChange={set('lng', true)} /></label>
      <label className="checkbox"><input type="checkbox" checked={form.is_active} onChange={set('is_active')} /> Активний</label>
      <div className="row span-2">
        <button className="btn btn-primary">Зберегти</button>
        <button type="button" className="btn btn-ghost" onClick={onCancel}>Скасувати</button>
      </div>
    </form>
  );
}

function DishEditor({ restaurant, onChanged }) {
  const [dishForm, setDishForm] = useState(null);
  const [error, setError] = useState('');

  const save = async (e) => {
    e.preventDefault();
    setError('');
    const body = { ...dishForm, price: Number(dishForm.price), weight_g: dishForm.weight_g ? Number(dishForm.weight_g) : null };
    try {
      if (dishForm.id) await api(`/admin/dishes/${dishForm.id}`, { method: 'PUT', body });
      else await api(`/admin/restaurants/${restaurant.id}/dishes`, { method: 'POST', body });
      setDishForm(null);
      onChanged();
    } catch (err) { setError(err.message); }
  };

  const remove = async (dish) => {
    if (!window.confirm(`Видалити «${dish.name}»?`)) return;
    await api(`/admin/dishes/${dish.id}`, { method: 'DELETE' });
    onChanged();
  };

  const toggle = async (dish) => {
    await api(`/admin/dishes/${dish.id}`, { method: 'PUT', body: { ...dish, is_available: !dish.is_available } });
    onChanged();
  };

  const set = (key) => (e) => setDishForm((f) => ({ ...f, [key]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));

  return (
    <div className="card">
      <div className="row-between">
        <h3>Меню: {restaurant.name}</h3>
        <button className="btn btn-primary" onClick={() => setDishForm(EMPTY_DISH)}>+ Страва</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      {dishForm && (
        <form className="form grid-form sub-form" onSubmit={save}>
          <label className="field">Назва<input value={dishForm.name} onChange={set('name')} required /></label>
          <label className="field">Категорія<input value={dishForm.category} onChange={set('category')} /></label>
          <label className="field">Ціна, ₴<input type="number" step="0.01" value={dishForm.price} onChange={set('price')} required /></label>
          <label className="field">Вага, г<input type="number" value={dishForm.weight_g ?? ''} onChange={set('weight_g')} /></label>
          <label className="checkbox"><input type="checkbox" checked={dishForm.is_available} onChange={set('is_available')} /> В наявності</label>
          <label className="field span-2">Опис<input value={dishForm.description} onChange={set('description')} /></label>
          <div className="row span-2">
            <button className="btn btn-primary">{dishForm.id ? 'Оновити' : 'Додати'}</button>
            <button type="button" className="btn btn-ghost" onClick={() => setDishForm(null)}>Скасувати</button>
          </div>
        </form>
      )}
      <table className="table">
        <thead><tr><th>Страва</th><th>Категорія</th><th>Ціна</th><th>Наявність</th><th></th></tr></thead>
        <tbody>
          {restaurant.dishes.map((d) => (
            <tr key={d.id} className={d.is_available ? '' : 'row-disabled'}>
              <td>{d.name}</td>
              <td className="small">{d.category}</td>
              <td>{money(d.price)}</td>
              <td><button className="btn btn-ghost small" onClick={() => toggle(d)}>{d.is_available ? 'Є' : 'Немає'}</button></td>
              <td className="actions">
                <button className="btn btn-ghost small" onClick={() => setDishForm({ ...d, weight_g: d.weight_g ?? '' })}>Змінити</button>
                <button className="btn btn-danger small" onClick={() => remove(d)}>Видалити</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminRestaurants() {
  const [restaurants, setRestaurants] = useState([]);
  const [editing, setEditing] = useState(null);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');

  const load = () => api('/admin/restaurants').then(setRestaurants).catch((e) => setError(e.message));
  const loadSelected = (id) => api(`/admin/restaurants/${id}`).then(setSelected);

  useEffect(() => { load(); }, []);

  const save = async (form) => {
    setError('');
    try {
      if (form.id) await api(`/admin/restaurants/${form.id}`, { method: 'PUT', body: form });
      else await api('/admin/restaurants', { method: 'POST', body: form });
      setEditing(null);
      load();
    } catch (e) { setError(e.message); }
  };

  const remove = async (r) => {
    if (!window.confirm(`Видалити заклад «${r.name}»? Якщо є замовлення — його буде деактивовано.`)) return;
    await api(`/admin/restaurants/${r.id}`, { method: 'DELETE' });
    if (selected?.id === r.id) setSelected(null);
    load();
  };

  return (
    <>
      <div className="row-between">
        <h1>Заклади та меню</h1>
        <button className="btn btn-primary" onClick={() => setEditing(EMPTY_RESTAURANT)}>+ Додати заклад</button>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      {editing && <RestaurantForm key={editing.id || 'new'} initial={editing} onSave={save} onCancel={() => setEditing(null)} />}
      <div className="card table-wrap">
        <table className="table">
          <thead><tr><th>Назва</th><th>Кухня</th><th>Ціна</th><th>Час</th><th>Рейтинг</th><th>Статус</th><th>Дії</th></tr></thead>
          <tbody>
            {restaurants.map((r) => (
              <tr key={r.id} className={r.is_active ? '' : 'row-disabled'}>
                <td><b>{r.name}</b><div className="small muted">{r.address}</div></td>
                <td>{CUISINE_TITLES[r.cuisine]}</td>
                <td>{priceLevel(r.price_level)}</td>
                <td>{r.delivery_time_min} хв</td>
                <td>★ {r.rating.toFixed(1)}</td>
                <td>{r.is_active ? 'Активний' : 'Неактивний'}</td>
                <td className="actions">
                  <button className="btn btn-ghost small" onClick={() => loadSelected(r.id)}>Меню</button>
                  <button className="btn btn-ghost small" onClick={() => setEditing(r)}>Змінити</button>
                  <button className="btn btn-danger small" onClick={() => remove(r)}>Видалити</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {selected && <DishEditor restaurant={selected} onChanged={() => { loadSelected(selected.id); }} />}
    </>
  );
}
