import random
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.timeutil import utcnow
from app.models import Dish, Restaurant, Review, User

RESTAURANTS = [
    {
        "name": "Бабусина кухня", "cuisine": "UKRAINIAN", "price_level": 1,
        "delivery_time_min": 35, "min_order": 150, "lat": 49.8419, "lng": 24.0315,
        "address": "вул. Руська, 12",
        "description": "Домашні вареники, борщ і деруни за бабусиними рецептами.",
        "dishes": [
            ("Борщ з пампушками", "Перші страви", 125, 400, "Червоний борщ на яловичому бульйоні, пампушки з часником"),
            ("Вареники з картоплею", "Вареники", 110, 300, "З підсмаженою цибулькою та сметаною"),
            ("Вареники з вишнею", "Вареники", 130, 300, "Подаються з медовим соусом"),
            ("Деруни зі сметаною", "Основні страви", 115, 280, "Картопляні деруни, сметана, зелень"),
            ("Голубці", "Основні страви", 145, 350, "З м'ясом і рисом у томатному соусі"),
            ("Узвар", "Напої", 45, 400, "Компот із сухофруктів"),
        ],
    },
    {
        "name": "Mamma Mia", "cuisine": "ITALIAN", "price_level": 2,
        "delivery_time_min": 40, "min_order": 200, "lat": 49.8383, "lng": 24.0232,
        "address": "пл. Ринок, 5",
        "description": "Неаполітанська піца з дров'яної печі та свіжа паста.",
        "dishes": [
            ("Піца Маргарита", "Піца", 189, 450, "Томати, моцарела, базилік"),
            ("Піца Чотири сири", "Піца", 249, 480, "Моцарела, горгонзола, пармезан, дорблю"),
            ("Піца Пепероні", "Піца", 229, 470, "Гостра салямі пепероні, моцарела"),
            ("Паста Карбонара", "Паста", 215, 320, "Спагеті, гуанчале, жовток, пекоріно"),
            ("Лазанья Болоньєзе", "Паста", 235, 350, "Класична лазанья з м'ясним рагу"),
            ("Тірамісу", "Десерти", 125, 150, "Маскарпоне, савоярді, кава"),
        ],
    },
    {
        "name": "Сакура Суші", "cuisine": "JAPANESE", "price_level": 3,
        "delivery_time_min": 50, "min_order": 300, "lat": 49.8352, "lng": 24.0141,
        "address": "просп. Свободи, 28",
        "description": "Роли, суші та рамен від шефа з Осаки.",
        "dishes": [
            ("Філадельфія класична", "Роли", 389, 260, "Лосось, вершковий сир, огірок"),
            ("Каліфорнія з крабом", "Роли", 319, 250, "Сніжний краб, авокадо, ікра масаго"),
            ("Дракон", "Роли", 429, 280, "Вугор, авокадо, соус унагі"),
            ("Сет «Сакура»", "Сети", 899, 1100, "4 види ролів, 32 шт."),
            ("Рамен з куркою", "Супи", 245, 450, "Бульйон тонкоцу, локшина, яйце"),
            ("Місо-суп", "Супи", 99, 300, "Тофу, водорості вакаме"),
        ],
    },
    {
        "name": "Бургерна №1", "cuisine": "AMERICAN", "price_level": 2,
        "delivery_time_min": 30, "min_order": 0, "lat": 49.8445, "lng": 24.0378,
        "address": "вул. Шевченка, 3",
        "description": "Соковиті бургери з мармурової яловичини та картопля фрі.",
        "dishes": [
            ("Класичний бургер", "Бургери", 189, 320, "Яловичина, чедер, соус барбекю"),
            ("Чізбургер подвійний", "Бургери", 249, 420, "Дві котлети, подвійний сир"),
            ("Курячий бургер", "Бургери", 169, 300, "Хрустке куряче філе, капуста коул-слоу"),
            ("Картопля фрі", "Гарніри", 69, 150, "З соусом на вибір"),
            ("Курячі крильця BBQ", "Закуски", 159, 300, "8 крилець у соусі барбекю"),
            ("Мілкшейк ванільний", "Напої", 89, 400, "Морозиво, молоко, ваніль"),
        ],
    },
    {
        "name": "Тбілісо", "cuisine": "GEORGIAN", "price_level": 2,
        "delivery_time_min": 45, "min_order": 250, "lat": 49.8325, "lng": 24.0359,
        "address": "вул. Городоцька, 40",
        "description": "Хачапурі, хінкалі та шашлик на вугіллі.",
        "dishes": [
            ("Хачапурі по-аджарськи", "Випічка", 195, 400, "Сир сулугуні, яйце, вершкове масло"),
            ("Хачапурі по-імеретинськи", "Випічка", 175, 450, "З сиром імеретинським"),
            ("Хінкалі з яловичиною (5 шт.)", "Основні страви", 165, 350, "Соковиті хінкалі ручної ліпки"),
            ("Шашлик зі свинини", "Гриль", 259, 300, "Подається з цибулею та лавашем"),
            ("Салат по-грузинськи", "Салати", 129, 250, "Томати, огірки, горіхова заправка"),
        ],
    },
    {
        "name": "Вок & Ролл", "cuisine": "ASIAN", "price_level": 1,
        "delivery_time_min": 25, "min_order": 0, "lat": 49.8478, "lng": 24.0247,
        "address": "вул. Липинського, 9",
        "description": "Локшина вок, пад тай та азійські закуски.",
        "dishes": [
            ("Вок з куркою теріякі", "Вок", 165, 400, "Локшина удон, курка, овочі"),
            ("Пад тай з креветками", "Вок", 219, 380, "Рисова локшина, арахіс, лайм"),
            ("Вок з яловичиною", "Вок", 199, 400, "Яйчна локшина, соус устричний"),
            ("Спрінг-роли (4 шт.)", "Закуски", 99, 200, "Хрусткі роли з овочами"),
            ("Том ям", "Супи", 189, 400, "Гострий суп з креветками"),
        ],
    },
    {
        "name": "Солодкий Львів", "cuisine": "DESSERTS", "price_level": 1,
        "delivery_time_min": 30, "min_order": 100, "lat": 49.8401, "lng": 24.0287,
        "address": "вул. Вірменська, 15",
        "description": "Львівський сирник, штрудлі та кава зі всього світу.",
        "dishes": [
            ("Львівський сирник", "Десерти", 95, 180, "Класичний рецепт з родзинками"),
            ("Штрудель яблучний", "Десерти", 89, 170, "З кульковою морозива"),
            ("Еклер ванільний", "Десерти", 59, 80, "Заварне тісто, ванільний крем"),
            ("Капучино", "Кава", 65, 300, "Арабіка 100%"),
            ("Гарячий шоколад", "Напої", 75, 300, "Бельгійський шоколад"),
        ],
    },
]

USERS = [
    ("admin@food.ua", "admin123", "Адміністратор Системи", "ADMIN", "STANDARD", 0),
    ("client@food.ua", "client123", "Олена Коваль", "CLIENT", "STANDARD", 120),
    ("premium@food.ua", "premium123", "Андрій Мельник", "CLIENT", "PREMIUM", 340),
    ("maria@food.ua", "maria123", "Марія Бойко", "CLIENT", "STANDARD", 40),
    ("taras@food.ua", "taras123", "Тарас Гнатюк", "CLIENT", "PREMIUM", 210),
    ("sofia@food.ua", "sofia123", "Софія Кравець", "CLIENT", "STANDARD", 15),
]

REVIEW_TEXTS = {
    5: ["Дуже смачно, доставили гарячим!", "Найкраще у місті, замовляю щотижня.", "Швидко і смачно, рекомендую."],
    4: ["Смачно, але доставка трохи затрималась.", "Гарні порції, хороша якість.", "Все сподобалось, буду замовляти ще."],
    3: ["Нормально, але очікувала більшого.", "Смачно, проте холодне."],
}

def seed(db: Session) -> None:
    rng = random.Random(8)
    users = []
    for email, pwd, name, role, card, bonus in USERS:
        u = User(email=email, password_hash=hash_password(pwd), full_name=name, role=role,
                 card_type=card, bonus_points=bonus, phone="+380 67 " + str(rng.randint(1000000, 9999999)))
        db.add(u)
        users.append(u)

    restaurants = []
    for data in RESTAURANTS:
        data = dict(data)
        dishes = data.pop("dishes")
        data["min_order"] = Decimal(data["min_order"])
        r = Restaurant(**data)
        for name, cat, price, weight, desc in dishes:
            r.dishes.append(Dish(name=name, category=cat, price=Decimal(price), weight_g=weight, description=desc))
        db.add(r)
        restaurants.append(r)
    db.flush()

    clients = [u for u in users if u.role == "CLIENT"]
    now = utcnow()
    for r in restaurants:
        reviewers = rng.sample(clients, k=rng.randint(2, len(clients)))
        for u in reviewers:
            rating = rng.choice([5, 5, 4, 4, 3])
            db.add(Review(user_id=u.id, restaurant_id=r.id, rating=rating, text=rng.choice(REVIEW_TEXTS[rating]),
                          created_at=now - timedelta(days=rng.randint(0, 25))))
    db.flush()
    for r in restaurants:
        avg, cnt = db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.restaurant_id == r.id)).one()
        r.rating, r.reviews_count = round(float(avg), 2), int(cnt)

    client = users[1]
    client.favorites = [restaurants[0], restaurants[1]]
    db.commit()


def seed_if_empty(db: Session) -> bool:
    if db.scalar(select(func.count(User.id))):
        return False
    seed(db)
    print("[seed] Демонстраційні дані додано")
    return True


if __name__ == "__main__":
    from app.db.session import Base, SessionLocal, engine

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if not seed_if_empty(session):
            print("[seed] БД вже містить дані — пропущено")
