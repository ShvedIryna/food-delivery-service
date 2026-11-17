from tests.conftest import login


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_catalog_filters(client):
    all_r = client.get("/api/restaurants").json()
    assert len(all_r) == 7
    italian = client.get("/api/restaurants", params={"cuisine": "ITALIAN"}).json()
    assert all(r["cuisine"] == "ITALIAN" for r in italian)
    fast = client.get("/api/restaurants", params={"max_delivery_time": 30}).json()
    assert all(r["delivery_time_min"] <= 30 for r in fast)
    detail = client.get(f"/api/restaurants/{all_r[0]['id']}").json()
    assert detail["dishes"]


def test_register_and_profile(client):
    r = client.post("/api/auth/register", json={
        "email": "new@food.ua", "password": "secret1", "full_name": "Новий Клієнт"})
    assert r.status_code == 201
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    me = client.get("/api/me", headers=headers).json()
    assert me["bonus_points"] == 50 and me["card_type"] == "STANDARD"
    assert client.post("/api/auth/register", json={
        "email": "new@food.ua", "password": "secret1", "full_name": "Дубль"}).status_code == 409


def _first_restaurant_with_dishes(client, cuisine="AMERICAN"):
    r = client.get("/api/restaurants", params={"cuisine": cuisine}).json()[0]
    return client.get(f"/api/restaurants/{r['id']}").json()


def test_order_full_lifecycle(client):
    headers = login(client, "client@food.ua", "client123")
    admin = login(client, "admin@food.ua", "admin123")
    rest = _first_restaurant_with_dishes(client)
    body = {
        "restaurant_id": rest["id"],
        "items": [{"dish_id": rest["dishes"][0]["id"], "quantity": 2}],
        "delivery_type": "STANDARD",
        "payment_method": "CARD",
        "card_number": "4242 4242 4242 4242",
        "address": "вул. Стрийська, 45",
        "lat": 49.83, "lng": 24.045,
        "use_bonus": 20,
    }
    quote = client.post("/api/orders/quote", json=body, headers=headers).json()
    assert quote["bonus_used"] == 20
    bonus_before = client.get("/api/me", headers=headers).json()["bonus_points"]

    order = client.post("/api/orders", json=body, headers=headers)
    assert order.status_code == 201, order.text
    order = order.json()
    assert order["status"] == "NEW" and order["payment_status"] == "PAID"
    assert abs(order["total"] - quote["total"]) < 0.01

    for expected in ("PREPARING", "DELIVERING", "DELIVERED"):
        r = client.post(f"/api/admin/orders/{order['id']}/advance", headers=admin)
        assert r.json()["status"] == expected

    me = client.get("/api/me", headers=headers).json()
    final = client.get(f"/api/orders/{order['id']}", headers=headers).json()
    assert final["bonus_earned"] > 0
    assert me["bonus_points"] == bonus_before - 20 + final["bonus_earned"]

    notes = client.get("/api/me/notifications", headers=headers).json()
    assert any("доставлено" in n["title"].lower() for n in notes)

    tracking = client.get(f"/api/orders/{order['id']}/tracking", headers=headers).json()
    assert tracking["progress"] == 1.0

    repeat = client.post(f"/api/orders/{order['id']}/repeat", headers=headers)
    assert repeat.status_code == 201
    cancel = client.post(f"/api/orders/{repeat.json()['id']}/cancel", headers=headers)
    assert cancel.json()["status"] == "CANCELLED"


def test_invalid_card_and_pickup(client):
    headers = login(client, "premium@food.ua", "premium123")
    rest = _first_restaurant_with_dishes(client, "ASIAN")
    body = {"restaurant_id": rest["id"], "items": [{"dish_id": rest["dishes"][0]["id"], "quantity": 1}],
            "delivery_type": "PICKUP", "payment_method": "CARD", "card_number": "1234"}
    assert client.post("/api/orders", json=body, headers=headers).status_code == 400
    body["payment_method"] = "CASH"
    r = client.post("/api/orders", json=body, headers=headers)
    assert r.status_code == 201 and r.json()["delivery_fee"] == 0


def test_admin_requires_role(client):
    headers = login(client, "client@food.ua", "client123")
    assert client.get("/api/admin/stats", headers=headers).status_code == 403
    admin = login(client, "admin@food.ua", "admin123")
    stats = client.get("/api/admin/stats", headers=admin).json()
    assert stats["orders_total"] > 0 and stats["revenue"] > 0
