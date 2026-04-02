from flask import (Blueprint, render_template, request,
                   redirect, url_for, abort, flash, current_app)
from models import Product, db
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

shop_bp = Blueprint('shop', __name__)


# ─────────────────────────────────────────────────────────────────────────────
#  Home / Landing Page
# ─────────────────────────────────────────────────────────────────────────────
@shop_bp.route('/')
def index():
    featured = (Product.query
                .filter_by(featured=True, in_stock=True)
                .order_by(Product.id)
                .limit(4).all())
    return render_template('index.html', featured_products=featured)


# ─────────────────────────────────────────────────────────────────────────────
#  About Page
# ─────────────────────────────────────────────────────────────────────────────
@shop_bp.route('/about')
def about():
    return render_template('about.html')

# ─────────────────────────────────────────────────────────────────────────────
#  Product Listing Page
# ─────────────────────────────────────────────────────────────────────────────
@shop_bp.route('/shop')
def shop():
    category = request.args.get('category', 'all')
    sort     = request.args.get('sort', 'default')

    query = Product.query.filter_by(in_stock=True)

    if category != 'all':
        query = query.filter_by(category=category)

    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.id)

    products = query.all()
    return render_template('shop.html',
                           products=products,
                           active_category=category,
                           active_sort=sort)


# ─────────────────────────────────────────────────────────────────────────────
#  Product Detail Page
# ─────────────────────────────────────────────────────────────────────────────
@shop_bp.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    related = (Product.query
               .filter(Product.id != product.id,
                       Product.in_stock == True)
               .limit(3).all())
    return render_template('product.html',
                           product=product,
                           related_products=related)

# ─────────────────────────────────────────────────────────────────────────────
#  Newsletter Subscription
# ─────────────────────────────────────────────────────────────────────────────
def send_welcome_email(to_address):
    cfg = current_app.config
    server   = cfg.get('MAIL_SERVER',   'smtp.gmail.com')
    port     = int(cfg.get('MAIL_PORT', 587))
    username = cfg.get('MAIL_USERNAME', '')
    password = cfg.get('MAIL_PASSWORD', '')

    if not username or not password:
        return # Skip if SMTP isn't configured

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Welcome to the IronForge Newsletter!'
    msg['From']    = f'IronForge Nigeria <{username}>'
    msg['To']      = to_address

    text = "Welcome to IronForge Nigeria!\nThanks for joining our newsletter. You'll now receive our latest updates and bulk pricing deals."
    
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 40px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
          <h2 style="color: #0a0a0a; margin-bottom: 20px;">Welcome to IronForge!</h2>
          <p style="color: #555; line-height: 1.6; font-size: 16px;">
            Thank you for joining our newsletter. You will now be the first to know about our latest premium steel stock, bulk pricing opportunities, and exclusive construction insights.
          </p>
          <hr style="border: none; border-top: 1px solid #f0f0f0; margin: 30px 0;">
          <p style="font-size: 12px; color: #aaa;">
            © 2026 IronForge Nigeria • Precision Engineered
          </p>
        </div>
      </body>
    </html>
    """

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    def _send_email_async():
        try:
            with smtplib.SMTP(server, port, timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(username, password)
                smtp.sendmail(username, [to_address], msg.as_string())
        except Exception as e:
            print(f"Failed to send welcome email: {e}")

    import threading
    threading.Thread(target=_send_email_async).start()

@shop_bp.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('email', '').strip()
    if email:
        print(f"[NEWSLETTER] New Subscriber: {email}")
        send_welcome_email(email)
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {"success": True, "message": "Thanks for subscribing!"}
        
    flash("Thanks for subscribing to our newsletter!", "success")
    return redirect(request.referrer or url_for('shop.index'))
