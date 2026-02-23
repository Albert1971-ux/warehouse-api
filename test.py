
import requests

# Создаём второй товар
requests.post('http://127.0.0.1:5000/products', json={
    "name": "Мышка",
    "description": "Игровая мышка",
    "price": 3000,
    "quantity": 5
})

# Создаём заказ
response = requests.post('http://127.0.0.1:5000/orders', json={
    "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 2, "quantity": 1}
    ]
})
print("Создан заказ:", response.json())

# Список товаров (проверяем остатки)
response = requests.get('http://127.0.0.1:5000/products')
print("Остатки:", response.json())
