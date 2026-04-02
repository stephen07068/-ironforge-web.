import json
import secrets
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
#  Product Model
# ─────────────────────────────────────────────────────────────────────────────
class Product(db.Model):
    __tablename__ = 'products'

    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    slug        = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text)
    price       = db.Column(db.Integer, nullable=False)   # Price in Naira (whole number)
    diameter    = db.Column(db.String(50))                # e.g. "12.0 mm"
    length      = db.Column(db.String(50))                # e.g. "12.0 Meters"
    weight      = db.Column(db.String(50))                # e.g. "~53.2 Kg"
    grade       = db.Column(db.String(50))                # e.g. "Grade 60"
    compliance  = db.Column(db.String(50))                # e.g. "ASTM A615"
    category    = db.Column(db.String(50), default='tmt_bars')
    # Categories: tmt_bars | round_bars | square_bars
    image       = db.Column(db.String(300), default='default_rod.jpg')
    in_stock    = db.Column(db.Boolean, default=True)
    featured    = db.Column(db.Boolean, default=False)
    badge       = db.Column(db.String(50))                # e.g. "POPULAR", "IN STOCK"
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def price_formatted(self):
        """Return price formatted with Naira symbol and commas."""
        return f"₦{self.price:,}"

    def price_in_kobo(self):
        """Return price in kobo for Paystack (1 Naira = 100 kobo)."""
        return self.price * 100
        
    @property
    def price_per_ton(self):
        import re
        if not self.weight:
            return self.price * 10
        match = re.search(r'([\d.]+)', self.weight)
        if match:
            kg = float(match.group(1))
            if kg > 0:
                pieces = 1000.0 / kg
                return int(self.price * pieces)
        return self.price * 10
        
    def price_per_ton_formatted(self):
        return f"₦{self.price_per_ton:,}"

    def to_dict(self):
        return {
            'id':       self.id,
            'name':     self.name,
            'slug':     self.slug,
            'price':    self.price,
            'image':    self.image,
            'diameter': self.diameter,
            'grade':    self.grade,
            'in_stock': self.in_stock,
        }

    def __repr__(self):
        return f'<Product {self.name}>'


# ─────────────────────────────────────────────────────────────────────────────
#  Order Model
# ─────────────────────────────────────────────────────────────────────────────
class Order(db.Model):
    __tablename__ = 'orders'

    id               = db.Column(db.Integer, primary_key=True)
    reference        = db.Column(db.String(100), unique=True, nullable=False)

    # Customer details
    customer_name    = db.Column(db.String(200), nullable=False)
    customer_email   = db.Column(db.String(200), nullable=False)
    customer_phone   = db.Column(db.String(50),  nullable=False)
    customer_address = db.Column(db.Text,         nullable=False)

    # Financials
    total_amount     = db.Column(db.Integer, nullable=False)   # in Naira

    # Status
    payment_status   = db.Column(db.String(50), default='pending')
    # Values: pending | paid | failed | whatsapp
    payment_method   = db.Column(db.String(50), default='paystack')
    # Values: paystack | whatsapp

    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to line items
    items = db.relationship('OrderItem', backref='order', lazy=True,
                            cascade='all, delete-orphan')

    def total_formatted(self):
        return f"₦{self.total_amount:,}"

    def total_in_kobo(self):
        return self.total_amount * 100

    def __repr__(self):
        return f'<Order {self.reference}>'


# ─────────────────────────────────────────────────────────────────────────────
#  Order Item Model (line items)
# ─────────────────────────────────────────────────────────────────────────────
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('orders.id'),   nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity   = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Integer, nullable=False)   # price at time of order (Naira)
    unit       = db.Column(db.String(20), default='pieces')

    def subtotal(self):
        return self.unit_price * self.quantity

    def subtotal_formatted(self):
        return f"₦{self.subtotal():,}"


# ─────────────────────────────────────────────────────────────────────────────
#  Admin Password Reset Token
# ─────────────────────────────────────────────────────────────────────────────
class AdminResetToken(db.Model):
    __tablename__ = 'admin_reset_tokens'

    id         = db.Column(db.Integer, primary_key=True)
    token      = db.Column(db.String(128), unique=True, nullable=False,
                           default=lambda: secrets.token_urlsafe(48))
    expires_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.utcnow() + timedelta(hours=1))
    used       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        """Return True if the token is unused and not expired."""
        return not self.used and datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f'<AdminResetToken expires={self.expires_at}>'
