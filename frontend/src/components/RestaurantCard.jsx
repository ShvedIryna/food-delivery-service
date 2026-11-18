import { Link } from 'react-router-dom';
import { CUISINE_TITLES, initials, money, priceLevel } from '../utils/format.js';
import StarRating from './StarRating.jsx';

export default function RestaurantCard({ restaurant, onToggleFavorite }) {
  const r = restaurant;
  return (
    <div className="card restaurant-card">
      <Link to={`/restaurants/${r.id}`} className="restaurant-cover">
        {r.image_url
          ? <img src={r.image_url} alt={r.name} loading="lazy" />
          : <span className="restaurant-initials">{initials(r.name)}</span>}
      </Link>
      <div className="card-body">
        <div className="row-between">
          <Link to={`/restaurants/${r.id}`} className="card-title">{r.name}</Link>
          {onToggleFavorite && (
            <button
              className={`fav-btn ${r.is_favorite ? 'active' : ''}`}
              title={r.is_favorite ? 'Прибрати з улюблених' : 'Додати в улюблені'}
              onClick={() => onToggleFavorite(r)}
            >
              {r.is_favorite ? 'В улюблених' : 'В улюблені'}
            </button>
          )}
        </div>
        <div className="muted small">{CUISINE_TITLES[r.cuisine] || r.cuisine} · {priceLevel(r.price_level)}</div>
        <p className="small description">{r.description}</p>
        <div className="row-between small">
          <span><StarRating value={r.rating} /> {r.rating.toFixed(1)} ({r.reviews_count})</span>
          <span>{r.delivery_time_min} хв</span>
        </div>
        {r.min_order > 0 && <div className="small muted">Мін. замовлення {money(r.min_order)}</div>}
      </div>
    </div>
  );
}
