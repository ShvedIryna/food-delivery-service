# Смак Експрес — сервіс доставки їжі

Автор: Ірина Швед.

Веб-застосунок для замовлення страв із ресторанів і кафе. Користувач обирає страви з меню, оформлює
замовлення, оплачує його онлайн або готівкою й відстежує кур'єра на карті. Адміністратор керує закладами,
меню, замовленнями та користувачами.

## Можливості

| Модуль | Функції |
|---|---|
| Каталог | заклади та меню; фільтри за кухнею, ціною та часом доставки; пошук; сортування; рейтинги й відгуки |
| Замовлення та оплата | кошик; доставка **стандартна / експрес / самовивіз**; оплата **онлайн карткою** (імітація) або **готівкою**; попередній розрахунок вартості |
| Особистий кабінет | історія замовлень; **повторне замовлення в 1 клік**; улюблені заклади; редагування профілю |
| Лояльність | бонусні бали (3% або 7%); списання бонусами до 50% суми; знижка постійного клієнта (5% або 10%); **преміум-картка з безкоштовною доставкою** |
| Відстеження | карта OpenStreetMap з маршрутом і позицією кур'єра; сповіщення про статус: прийняте → готується → доставляється → доставлено |
| Адмін-панель | статистика (виручка, топ страв); CRUD закладів і страв; керування статусами замовлень; ролі, картки й бонуси користувачів |

## Технології

- **Бекенд:** Python 3.12, FastAPI, SQLAlchemy 2.0, PyMySQL, JWT (PyJWT), bcrypt, Pydantic 2, pytest
- **Фронтенд:** React 18, Vite 5, React Router 6, Leaflet + React-Leaflet
- **БД:** MySQL 8
- **Інфраструктура:** Docker, docker-compose

## GoF-патерни

| Патерн | Де застосовано | Файл |
|---|---|---|
| **Strategy** | способи доставки (`StandardDelivery`, `ExpressDelivery`, `PickupDelivery`) і оплати (`OnlineCardPayment`, `CashPayment`) | `backend/app/domain/delivery.py`, `payment.py` |
| **State** | життєвий цикл замовлення (`NewState` → `PreparingState` → `DeliveringState` / `ReadyForPickupState` → `DeliveredState`, `CancelledState`) | `backend/app/domain/order_state.py` |
| **Observer** | `OrderEventPublisher` повідомляє `NotificationObserver`, `LoyaltyObserver` і `PaymentObserver` | `backend/app/domain/events.py`, `services/observers.py` |
| **Builder** | `OrderBuilder` покроково формує й перевіряє `OrderDraft` | `backend/app/domain/order_builder.py` |
| **Decorator** | ланцюжок розрахунку ціни: базова → знижка постійного клієнта → безкоштовна доставка (преміум) → списання бонусів | `backend/app/domain/pricing.py` |
| **Factory Method** | `LoyaltyCardFactory.create()` повертає `StandardCard` або `PremiumCard` | `backend/app/domain/loyalty.py` |
| **Facade** | `OrderService` дає простий інтерфейс до всієї підсистеми замовлень | `backend/app/services/order_service.py` |
| **Singleton** | `Settings` — єдиний об'єкт конфігурації | `backend/app/core/config.py` |

Діаграми лежать у теці [`docs/diagrams`](docs/diagrams): Use Case, діаграма класів, ER-діаграма,
діаграма станів, sequence-діаграма та схема архітектури.

## Структура проєкту

```
food-delivery/
├── backend/
│   ├── app/
│   │   ├── api/          # REST-маршрути (контролери) + залежності (JWT, ролі)
│   │   ├── core/         # конфігурація (Singleton), безпека
│   │   ├── db/           # підключення до БД
│   │   ├── domain/       # бізнес-логіка та GoF-патерни (без фреймворків)
│   │   ├── services/     # фасад замовлень, каталог, спостерігачі, імітація
│   │   ├── models.py     # ORM-моделі (таблиці MySQL)
│   │   ├── schemas.py    # Pydantic DTO
│   │   ├── seed.py       # демо-дані
│   │   └── main.py       # точка входу FastAPI
│   ├── tests/            # модульні та інтеграційні тести
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/        # сторінки клієнта та адмін-панелі
│       ├── components/   # карта, сповіщення, картки
│       ├── context/      # авторизація та кошик
│       └── api.js
├── database/             # SQL: створення БД і користувача, схема таблиць
├── docs/diagrams/        # UML-діаграми
└── docker-compose.yml
```

## Запуск

### Варіант 1 — Docker (рекомендовано)

Потрібен встановлений [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/ShvedIryna/food-delivery-service.git
cd food-delivery-service
docker compose up --build
```

Після запуску відкрийте:
- застосунок: http://localhost:5173
- документацію API (Swagger UI): http://localhost:8000/docs

Під час першого запуску таблиці й демо-дані створюються автоматично. Зупинити застосунок: `Ctrl+C` або `docker compose down`.
Видалити разом із даними БД: `docker compose down -v`.

### Варіант 2 — локально, без Docker

Потрібні Python 3.11+, Node.js 18+ та MySQL 8.

**1. База даних** — виконайте скрипт `database/init.sql` у MySQL (через MySQL Workbench або `mysql -u root -p < database/init.sql`).
Таблиці бекенд створить сам під час першого запуску; їхня схема описана в `database/schema.sql`.

**2. Бекенд:**

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # у Windows: copy .env.example .env
uvicorn app.main:app --reload
```

**3. Фронтенд** (в іншому терміналі):

```bash
cd frontend
npm install
npm run dev
```

Відкрийте http://localhost:5173.

### Демо-акаунти

| Роль | E-mail | Пароль |
|---|---|---|
| Клієнт (стандартна картка) | client@food.ua | client123 |
| Клієнт (преміум-картка) | premium@food.ua | premium123 |
| Адміністратор | admin@food.ua | admin123 |

### Імітація доставки

Фоновий процес сам просуває активні замовлення: приблизно кожні 20 секунд змінюється статус, а кур'єр
їде маршрутом близько 90 секунд. Налаштування задаються у `.env` (`SIM_STEP_SECONDS`, `SIM_DELIVERY_SECONDS`).
Щоб керувати статусами лише вручну з адмін-панелі, вимкніть імітацію: `SIMULATION_ENABLED=0`.

## Тести

```bash
cd backend
pytest -v
```

- `tests/test_domain.py` — модульні тести GoF-патернів (без БД);
- `tests/test_api.py` — інтеграційні тести REST API (тимчасова SQLite-БД).

## Основні REST-ендпоінти

| Метод | Шлях | Опис |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | реєстрація та вхід (JWT) |
| GET | `/api/restaurants?cuisine=&price_level=&max_delivery_time=&q=&sort=` | каталог із фільтрами |
| GET | `/api/restaurants/{id}` | заклад і меню |
| GET/POST | `/api/restaurants/{id}/reviews` | відгуки |
| GET | `/api/orders/options` | способи доставки й оплати |
| POST | `/api/orders/quote` | попередній розрахунок вартості |
| POST/GET | `/api/orders` | створення замовлення / історія |
| POST | `/api/orders/{id}/repeat`, `/api/orders/{id}/cancel` | повторення / скасування |
| GET | `/api/orders/{id}/tracking` | маршрут і позиція кур'єра |
| GET/PUT | `/api/me`; `/api/me/loyalty`; `/api/me/favorites`; `/api/me/notifications` | особистий кабінет |
| * | `/api/admin/...` | адмін-панель (лише роль ADMIN) |

Повний опис усіх ендпоінтів доступний у Swagger: http://localhost:8000/docs.
