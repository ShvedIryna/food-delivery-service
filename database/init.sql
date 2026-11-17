-- Створення бази та користувача (для запуску без Docker)
CREATE DATABASE IF NOT EXISTS food_delivery CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'food'@'localhost' IDENTIFIED BY 'food';
GRANT ALL PRIVILEGES ON food_delivery.* TO 'food'@'localhost';
FLUSH PRIVILEGES;
