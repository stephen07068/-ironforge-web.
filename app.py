import os
from flask import Flask
from models import db
from config import Config

# Trigger reload

def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Proxy Fix for Railway / Render (Forces HTTPS callback URLs) ────────   
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ── Extensions ──────────────────────────────────────────────────────────
    db.init_app(app)

    # ── Upload folder ────────────────────────────────────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Blueprints ───────────────────────────────────────────────────────────
    from routes.shop     import shop_bp
    from routes.cart     import cart_bp
    from routes.orders   import orders_bp
    from routes.payments import payments_bp
    from routes.admin    import admin_bp

    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp,     url_prefix='/cart')
    app.register_blueprint(orders_bp,   url_prefix='/orders')
    app.register_blueprint(payments_bp, url_prefix='/payment')
    app.register_blueprint(admin_bp,    url_prefix=f"/{app.config['ADMIN_SECRET_PATH']}")

    # ── Jinja2 global helpers ────────────────────────────────────────────────
    @app.template_filter('naira')
    def naira_filter(value):
        """Format integer as ₦1,234,000"""
        try:
            return f"₦{int(value):,}"
        except (ValueError, TypeError):
            return value

    @app.context_processor
    def inject_cart_count():
        """Make cart_count available in every template."""
        from flask import session
        cart = session.get('cart', {})
        cart_count = sum(item['qty'] for item in cart.values())
        return dict(cart_count=cart_count)

    # ── Database init ────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        
        # Auto-seed if the product table is empty
        try:
            from models import Product
            if Product.query.count() == 0:
                print("Database is empty! Auto-seeding products...")
                from seed_db import SAMPLE_PRODUCTS
                for data in SAMPLE_PRODUCTS:
                    p = Product(**data)
                    db.session.add(p)
                db.session.commit()
                print("Auto-seed complete.")
        except Exception as e:
            print(f"Auto-seed skipped or failed: {e}")
            db.session.rollback()

    return app


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
