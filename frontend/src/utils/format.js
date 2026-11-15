export const CUISINE_TITLES = {
  UKRAINIAN: 'Українська',
  ITALIAN: 'Італійська',
  JAPANESE: 'Японська',
  AMERICAN: 'Американська',
  GEORGIAN: 'Грузинська',
  ASIAN: 'Азійська',
  DESSERTS: 'Десерти та кава',
};

export const STATUS_TITLES = {
  NEW: 'Прийняте',
  PREPARING: 'Готується',
  DELIVERING: 'Доставляється',
  READY_FOR_PICKUP: 'Готове до видачі',
  DELIVERED: 'Доставлено',
  CANCELLED: 'Скасовано',
};

export const DELIVERY_TITLES = { STANDARD: 'Стандартна', EXPRESS: 'Експрес', PICKUP: 'Самовивіз' };
export const PAYMENT_TITLES = { CARD: 'Онлайн карткою', CASH: 'Готівкою' };
export const PAYMENT_STATUS_TITLES = { PAID: 'Оплачено', PENDING: 'Очікує оплати', REFUNDED: 'Повернено' };

export const money = (value) =>
  `${Number(value || 0).toLocaleString('uk-UA', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} ₴`;

export const parseDate = (s) => new Date(/[zZ]|[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`);

export const dateTime = (s) =>
  parseDate(s).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });

export const priceLevel = (level) => '₴'.repeat(level);

export const initials = (name) =>
  name.split(/\s+/).filter((w) => /[\p{L}]/u.test(w[0])).slice(0, 2).map((w) => w[0].toUpperCase()).join('');

export const LVIV_CENTER = [49.8397, 24.0297];
