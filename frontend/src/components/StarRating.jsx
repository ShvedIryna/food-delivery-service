export default function StarRating({ value = 0, onChange }) {
  const rounded = Math.round(value);
  return (
    <span className={`stars ${onChange ? 'stars-input' : ''}`}>
      {[1, 2, 3, 4, 5].map((n) => (
        <span
          key={n}
          className={n <= rounded ? 'star on' : 'star'}
          onClick={onChange ? () => onChange(n) : undefined}
        >
          ★
        </span>
      ))}
    </span>
  );
}
