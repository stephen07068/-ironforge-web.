import os
import re
import smtplib
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, session,
                   redirect, url_for, flash, current_app)
from werkzeug.utils import secure_filename
from models import db, Product, Order, AdminResetToken

admin_bp = Blueprint('admin', __name__)

ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}


# ─────────────────────────────────────────────────────────────────────────────
#  Auth helpers
# ─────────────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED)


# ─────────────────────────────────────────────────────────────────────────────
#  Email utility
# ─────────────────────────────────────────────────────────────────────────────
def send_reset_email(to_address, reset_url):
    """Send a password-reset link to the admin inbox via SMTP/TLS."""
    cfg = current_app.config
    server   = cfg.get('MAIL_SERVER',   'smtp.gmail.com')
    port     = int(cfg.get('MAIL_PORT', 587))
    username = cfg.get('MAIL_USERNAME', '')
    password = cfg.get('MAIL_PASSWORD', '')

    if not username or not password:
        raise RuntimeError(
            'MAIL_USERNAME and MAIL_PASSWORD must be set in .env'
        )

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'IronForge Admin — Password Reset Request'
    msg['From']    = f'IronForge Admin <{username}>'
    msg['To']      = to_address

    # ── Plain-text body ───────────────────────────────────────────────────────
    text = f"""\
IronForge Nigeria — Admin Password Reset
=========================================

Someone requested a password reset for the admin account.

Click the link below to set a new password.
This link expires in 1 hour and can only be used once.

{reset_url}

If you did not request this, ignore this email — your password will not change.

— IronForge System
"""

    # ── HTML body ─────────────────────────────────────────────────────────────
    html = f"""\
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body {{ font-family: 'Inter', Arial, sans-serif; background:#f5f5f5; margin:0; padding:0; }}
    .wrap {{ max-width:560px; margin:40px auto; background:#fff; border-radius:16px; overflow:hidden;
             box-shadow:0 4px 24px rgba(0,0,0,.08); }}
    .header {{ background:#0a0a0a; padding:32px; text-align:center; }}
    .logo {{ font-size:28px; font-weight:900; color:#fff; letter-spacing:6px; }}
    .sub {{ font-size:10px; color:#f97316; letter-spacing:4px; margin-top:4px; }}
    .body {{ padding:40px 36px; }}
    h1 {{ font-size:20px; color:#0a0a0a; margin:0 0 12px; font-weight:700; }}
    p {{ font-size:14px; color:#555; line-height:1.7; margin:0 0 16px; }}
    .btn {{ display:inline-block; background:#f97316; color:#fff; font-weight:700;
            font-size:13px; letter-spacing:2px; text-transform:uppercase;
            padding:14px 32px; border-radius:8px; text-decoration:none; margin:8px 0 24px; }}
    .link {{ font-size:12px; color:#999; word-break:break-all; }}
    .footer {{ padding:24px 36px; border-top:1px solid #f0f0f0; text-align:center;
               font-size:11px; color:#bbb; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="logo">IRONFORGE</div>
      <div class="sub">Admin Access</div>
    </div>
    <div class="body">
      <h1>🔐 Password Reset Request</h1>
      <p>Someone requested a password reset for the <b>IronForge admin account</b>.<br/>
         Click the button below to choose a new password. This link expires in <b>1 hour</b>
         and can only be used <b>once</b>.</p>
      <a href="{reset_url}" class="btn">Reset My Password →</a>
      <p>Or copy this link into your browser:</p>
      <p class="link">{reset_url}</p>
      <p style="margin-top:24px;font-size:12px;color:#aaa;">
        If you did not request this, simply ignore this email — your password will not change.
      </p>
    </div>
    <div class="footer">© 2026 IronForge Nigeria · Precision Engineered</div>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html,  'html'))

    with smtplib.SMTP(server, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(username, [to_address], msg.as_string())


# ─────────────────────────────────────────────────────────────────────────────
#  Utility: rewrite ADMIN_PASSWORD in .env at runtime
# ─────────────────────────────────────────────────────────────────────────────
def _update_env_password(new_password: str) -> None:
    """Overwrite the ADMIN_PASSWORD line in the local .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    env_path = os.path.abspath(env_path)

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        with open(env_path, 'w', encoding='utf-8') as fh:
            for line in lines:
                if line.startswith('ADMIN_PASSWORD='):
                    fh.write(f'ADMIN_PASSWORD={new_password}\n')
                else:
                    fh.write(line)
    # Also update the in-memory config so the change takes effect immediately
    current_app.config['ADMIN_PASSWORD'] = new_password


# ─────────────────────────────────────────────────────────────────────────────
#  Login / Logout
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if (username == current_app.config['ADMIN_USERNAME'] and
                password == current_app.config['ADMIN_PASSWORD']):
            session['admin_logged_in'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials. Try again.', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin.login'))


# ─────────────────────────────────────────────────────────────────────────────
#  Forgot Password
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        admin_email = current_app.config.get('ADMIN_EMAIL', '').strip()

        if not admin_email:
            flash(
                'No admin email is configured. '
                'Please set ADMIN_EMAIL in your .env file.',
                'danger'
            )
            return render_template('admin/forgot_password.html')

        # Invalidate any existing unused tokens before creating a new one
        AdminResetToken.query.filter_by(used=False).delete()
        db.session.commit()

        token_obj = AdminResetToken()
        db.session.add(token_obj)
        db.session.commit()

        reset_url = url_for(
            'admin.reset_password',
            token=token_obj.token,
            _external=True
        )

        try:
            send_reset_email(admin_email, reset_url)
            flash(
                f'A password-reset link has been sent to {admin_email}. '
                'It expires in 1 hour.',
                'success'
            )
        except Exception as exc:
            db.session.delete(token_obj)
            db.session.commit()
            flash(
                f'Could not send email: {exc}. '
                'Check your MAIL_USERNAME / MAIL_PASSWORD in .env.',
                'danger'
            )

        return redirect(url_for('admin.forgot_password'))

    return render_template('admin/forgot_password.html')


# ─────────────────────────────────────────────────────────────────────────────
#  Reset Password  (link from email)
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    token_obj = AdminResetToken.query.filter_by(token=token).first()

    if not token_obj or not token_obj.is_valid():
        flash(
            'This reset link is invalid or has expired. '
            'Please request a new one.',
            'danger'
        )
        return redirect(url_for('admin.forgot_password'))

    if request.method == 'POST':
        new_password  = request.form.get('new_password', '').strip()
        confirm       = request.form.get('confirm_password', '').strip()

        error = None
        if len(new_password) < 8:
            error = 'Password must be at least 8 characters.'
        elif new_password != confirm:
            error = 'Passwords do not match.'

        if error:
            flash(error, 'danger')
            return render_template('admin/reset_password.html', token=token)

        # Save new password
        _update_env_password(new_password)

        # Mark token as used
        token_obj.used = True
        db.session.commit()

        flash('Password updated successfully! You can now sign in.', 'success')
        return redirect(url_for('admin.login'))

    return render_template('admin/reset_password.html', token=token)


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.count()
    total_orders   = Order.query.count()
    paid_orders    = Order.query.filter_by(payment_status='paid').count()
    pending_orders = Order.query.filter_by(payment_status='pending').count()

    revenue = (db.session.query(db.func.sum(Order.total_amount))
               .filter_by(payment_status='paid').scalar() or 0)

    recent_orders = (Order.query
                     .order_by(Order.created_at.desc())
                     .limit(5).all())

    stats = {
        'total_products': total_products,
        'total_orders':   total_orders,
        'paid_orders':    paid_orders,
        'pending_orders': pending_orders,
        'revenue':        revenue,
    }
    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_orders=recent_orders)


# ─────────────────────────────────────────────────────────────────────────────
#  Products — list
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/products')
@login_required
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=all_products)


# ─────────────────────────────────────────────────────────────────────────────
#  Products — create
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        return _save_product(None)
    return render_template('admin/product_form.html', product=None)


# ─────────────────────────────────────────────────────────────────────────────
#  Products — edit
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        return _save_product(product)
    return render_template('admin/product_form.html', product=product)


def _save_product(product):
    """Shared save logic for create and edit."""
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price       = int(request.form.get('price', 0))
    diameter    = request.form.get('diameter', '').strip()
    length      = request.form.get('length', '').strip()
    weight      = request.form.get('weight', '').strip()
    grade       = request.form.get('grade', '').strip()
    compliance  = request.form.get('compliance', '').strip()
    category    = request.form.get('category', 'tmt_bars')
    badge       = request.form.get('badge', '').strip()
    featured    = bool(request.form.get('featured'))
    in_stock    = bool(request.form.get('in_stock'))

    # Auto-generate slug from name
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    # Ensure slug uniqueness for new products
    if product is None:
        existing = Product.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{Product.query.count() + 1}"

    if product is None:
        product = Product()
        db.session.add(product)

    product.name        = name
    product.slug        = slug
    product.description = description
    product.price       = price
    product.diameter    = diameter
    product.length      = length
    product.weight      = weight
    product.grade       = grade
    product.compliance  = compliance
    product.category    = category
    product.badge       = badge
    product.featured    = featured
    product.in_stock    = in_stock

    # Handle image upload
    file = request.files.get('image')
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, filename))
        product.image = filename

    db.session.commit()
    flash(f'Product "{product.name}" saved successfully.', 'success')
    return redirect(url_for('admin.products'))


# ─────────────────────────────────────────────────────────────────────────────
#  Products — delete
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" deleted.', 'warning')
    return redirect(url_for('admin.products'))


# ─────────────────────────────────────────────────────────────────────────────
#  Orders — list
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/orders')
@login_required
def orders():
    status = request.args.get('status', 'all')
    query  = Order.query.order_by(Order.created_at.desc())
    if status != 'all':
        query = query.filter_by(payment_status=status)
    all_orders = query.all()
    return render_template('admin/orders.html',
                           orders=all_orders,
                           active_status=status)


# ─────────────────────────────────────────────────────────────────────────────
#  Orders — mark as paid
# ─────────────────────────────────────────────────────────────────────────────
@admin_bp.route('/orders/<int:order_id>/mark-paid', methods=['POST'])
@login_required
def mark_paid(order_id):
    order = Order.query.get_or_404(order_id)
    order.payment_status = 'paid'
    db.session.commit()
    flash(f'Order {order.reference} marked as paid.', 'success')
    return redirect(url_for('admin.orders'))
