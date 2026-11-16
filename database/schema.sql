-- Схема БД food_delivery (MySQL 8).
-- Бекенд створює ці таблиці автоматично під час першого запуску.
USE food_delivery;

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    email         VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(120) NOT NULL,
    phone         VARCHAR(30)  NULL,
    address       VARCHAR(255) NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'CLIENT',
    card_type     VARCHAR(20)  NOT NULL DEFAULT 'STANDARD',
    bonus_points  INT          NOT NULL DEFAULT 0,
    created_at    DATETIME     NOT NULL
);

CREATE TABLE IF NOT EXISTS restaurants (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    name              VARCHAR(120)  NOT NULL,
    description       TEXT          NOT NULL,
    cuisine           VARCHAR(30)   NOT NULL,
    price_level       INT           NOT NULL DEFAULT 2,
    delivery_time_min INT           NOT NULL DEFAULT 40,
    min_order         DECIMAL(10,2) NOT NULL DEFAULT 0,
    address           VARCHAR(255)  NOT NULL DEFAULT '',
    lat               FLOAT         NOT NULL,
    lng               FLOAT         NOT NULL,
    is_active         BOOLEAN       NOT NULL DEFAULT TRUE,
    rating            FLOAT         NOT NULL DEFAULT 0,
    reviews_count     INT           NOT NULL DEFAULT 0,
    created_at        DATETIME      NOT NULL,
    INDEX ix_restaurants_cuisine (cuisine)
);

CREATE TABLE IF NOT EXISTS dishes (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT           NOT NULL,
    name          VARCHAR(120)  NOT NULL,
    description   TEXT          NOT NULL,
    category      VARCHAR(60)   NOT NULL,
    price         DECIMAL(10,2) NOT NULL,
    weight_g      INT           NULL,
    is_available  BOOLEAN       NOT NULL DEFAULT TRUE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id       INT NOT NULL,
    restaurant_id INT NOT NULL,
    PRIMARY KEY (user_id, restaurant_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reviews (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT      NOT NULL,
    restaurant_id INT      NOT NULL,
    rating        INT      NOT NULL,
    text          TEXT     NOT NULL,
    created_at    DATETIME NOT NULL,
    CONSTRAINT uq_review_user_restaurant UNIQUE (user_id, restaurant_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT           NOT NULL,
    restaurant_id     INT           NOT NULL,
    status            VARCHAR(30)   NOT NULL DEFAULT 'NEW',
    delivery_type     VARCHAR(20)   NOT NULL,
    payment_method    VARCHAR(20)   NOT NULL,
    payment_status    VARCHAR(20)   NOT NULL DEFAULT 'PENDING',
    transaction_id    VARCHAR(64)   NULL,
    address           VARCHAR(255)  NULL,
    lat               FLOAT         NULL,
    lng               FLOAT         NULL,
    comment           VARCHAR(500)  NULL,
    subtotal          DECIMAL(10,2) NOT NULL,
    delivery_fee      DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount          DECIMAL(10,2) NOT NULL DEFAULT 0,
    bonus_used        INT           NOT NULL DEFAULT 0,
    bonus_earned      INT           NOT NULL DEFAULT 0,
    total             DECIMAL(10,2) NOT NULL,
    estimated_minutes INT           NOT NULL DEFAULT 40,
    created_at        DATETIME      NOT NULL,
    status_changed_at DATETIME      NOT NULL,
    INDEX ix_orders_user_id (user_id),
    INDEX ix_orders_status (status),
    INDEX ix_orders_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    order_id   INT           NOT NULL,
    dish_id    INT           NULL,
    dish_name  VARCHAR(120)  NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    quantity   INT           NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id) REFERENCES dishes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT          NOT NULL,
    order_id   INT          NULL,
    kind       VARCHAR(30)  NOT NULL DEFAULT 'ORDER_STATUS',
    title      VARCHAR(160) NOT NULL,
    message    VARCHAR(500) NOT NULL DEFAULT '',
    is_read    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at DATETIME     NOT NULL,
    INDEX ix_notifications_user_id (user_id),
    INDEX ix_notifications_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
);
