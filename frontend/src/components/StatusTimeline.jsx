import { STATUS_TITLES } from '../utils/format.js';

const DELIVERY_FLOW = ['NEW', 'PREPARING', 'DELIVERING', 'DELIVERED'];
const PICKUP_FLOW = ['NEW', 'PREPARING', 'READY_FOR_PICKUP', 'DELIVERED'];

export default function StatusTimeline({ status, pickup }) {
  if (status === 'CANCELLED') return <div className="alert alert-error">Замовлення скасовано</div>;
  const flow = pickup ? PICKUP_FLOW : DELIVERY_FLOW;
  const current = flow.indexOf(status);
  return (
    <ol className="timeline">
      {flow.map((s, i) => (
        <li key={s} className={i < current ? 'done' : i === current ? 'current' : ''}>
          <span className="timeline-icon">{i + 1}</span>
          <span>{s === 'DELIVERED' && pickup ? 'Отримано' : STATUS_TITLES[s]}</span>
        </li>
      ))}
    </ol>
  );
}
