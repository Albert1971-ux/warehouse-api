
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///warehouse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# ===== МОДЕЛИ =====

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False, default='pending')
    total = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


# ===== ТОВАРЫ =====

@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id, 'name': p.name,
        'description': p.description,
        'price': p.price, 'quantity': p.quantity
    } for p in products])


@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        quantity=data['quantity']
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({'id': product.id, 'message': 'Товар создан'}), 201


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({
        'id': product.id, 'name': product.name,
        'description': product.description,
        'price': product.price, 'quantity': product.quantity
    })


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.quantity = data.get('quantity', product.quantity)
    db.session.commit()
    return jsonify({'message': 'Товар обновлён'})


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Товар удалён'})


# ===== ЗАКАЗЫ =====

@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([{
        'id': o.id, 'status': o.status,
        'total': o.total, 'created_at': str(o.created_at)
    } for o in orders])


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    total = 0
    order = Order()
    db.session.add(order)
    db.session.flush()

    for item in data['items']:
        product = Product.query.get_or_404(item['product_id'])
        if product.quantity < item['quantity']:
            return jsonify({'error': f'Недостаточно товара: {product.name}'}), 400
        product.quantity -= item['quantity']
        total += product.price * item['quantity']
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item['quantity'],
            price=product.price
        )
        db.session.add(order_item)

    order.total = total
    db.session.commit()
    return jsonify({'id': order.id, 'total': total, 'message': 'Заказ создан'}), 201


@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    return jsonify({
        'id': order.id, 'status': order.status,
        'total': order.total, 'created_at': str(order.created_at),
        'items': [{'product_id': i.product_id,
                   'quantity': i.quantity,
                   'price': i.price} for i in order.items]
    })


@app.route('/orders/<int:id>', methods=['PATCH'])
def update_order_status(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify({'message': 'Статус обновлён'})


# ===== ЗАПУСК =====

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
