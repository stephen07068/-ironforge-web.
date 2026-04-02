import uuid
from flask import (Blueprint, render_template, request, session,
                   redirect, url_for, flash, current_app, jsonify)
from models import db, Product, Order, OrderItem
from urllib.parse import quote

orders_bp = Blueprint('orders', __name__)


def build_cart_items():
    """Return list of dicts (product, qty, subtotal, unit) and grand total."""
    cart  = session.get('cart', {})
    items = []
    total = 0
    for key, item in list(cart.items()):
        raw_pid = str(key).split('_')[0]
        product = Product.query.get(int(raw_pid))
        if product:
            price = item.get('price', product.price)
            subtotal = price * item['qty']
            total   += subtotal
            items.append({
                'product':  product,
                'qty':      item['qty'],
                'subtotal': subtotal,
                'price':    price,
                'unit':     item.get('unit', 'pieces')
            })
    return items, total


# ─────────────────────────────────────────────────────────────────────────────
#  Checkout Page
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    items, total = build_cart_items()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))

    if request.method == 'POST':
        name    = request.form.get('name',    '').strip()
        email   = request.form.get('email',   '').strip()
        phone   = request.form.get('phone',   '').strip()
        address = request.form.get('address', '').strip()
        method  = request.form.get('method',  'paystack')  # paystack | whatsapp

        if not all([name, email, phone, address]):
            flash('Please fill in all fields.', 'danger')
            return render_template('checkout.html', items=items, total=total)

        # ── Create order ──────────────────────────────────────────────────
        reference = f'IRONFORGE-{uuid.uuid4().hex[:12].upper()}'
        order = Order(
            reference        = reference,
            customer_name    = name,
            customer_email   = email,
            customer_phone   = phone,
            customer_address = address,
            total_amount     = total,
            payment_method   = method,
            payment_status   = 'pending',
        )
        db.session.add(order)
        db.session.flush()   # get order.id before committing

        # ── Save line items ───────────────────────────────────────────────
        for item in items:
            line = OrderItem(
                order_id   = order.id,
                product_id = item['product'].id,
                quantity   = item['qty'],
                unit_price = item['price'],
                unit       = item['unit']
            )
            db.session.add(line)

        db.session.commit()

        # Store order reference in session for payment callback
        session['pending_order_ref'] = reference

        # ── Route by payment method ───────────────────────────────────────
        if method == 'whatsapp':
            return redirect(url_for('orders.whatsapp_order',
                                    reference=reference))
        else:
            return redirect(url_for('payments.initiate',
                                    reference=reference))

    return render_template('checkout.html', items=items, total=total)


# ─────────────────────────────────────────────────────────────────────────────
#  WhatsApp Order
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/whatsapp/<reference>')
def whatsapp_order(reference):
    order = Order.query.filter_by(reference=reference).first_or_404()
    order.payment_status = 'whatsapp'
    db.session.commit()

    # Clear cart after order is placed
    session.pop('cart', None)

    # Build WhatsApp message
    lines = [
        "🔩 *NEW ORDER — IronForge Nigeria*",
        f"Order Ref: {order.reference}",
        "",
        "📦 *Items Ordered:*",
    ]
    for item in order.items:
        unit_str = 'Tons' if item.unit == 'tons' else 'Pieces'
        lines.append(
            f"  • {item.product.name} x{item.quantity} ({unit_str}) — ₦{item.subtotal():,}"
        )
    lines += [
        "",
        f"💰 *Total: ₦{order.total_amount:,}*",
        "",
        "👤 *Customer Details:*",
        f"  Name:    {order.customer_name}",
        f"  Phone:   {order.customer_phone}",
        f"  Email:   {order.customer_email}",
        f"  Address: {order.customer_address}",
    ]
    message = "\n".join(lines)
    wa_number = current_app.config['WHATSAPP_NUMBER']
    wa_url    = f"https://wa.me/{wa_number}?text={quote(message)}"

    return redirect(wa_url)


# ─────────────────────────────────────────────────────────────────────────────
#  AJAX Order Creation (for Paystack inline popup)
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/create-ajax', methods=['POST'])
def create_order_ajax():
    """Create order from AJAX, return JSON for Paystack inline JS."""
    items, total = build_cart_items()
    if not items:
        return jsonify({'success': False, 'error': 'Cart is empty'}), 400

    name    = request.form.get('name',    '').strip()
    email   = request.form.get('email',   '').strip()
    phone   = request.form.get('phone',   '').strip()
    address = request.form.get('address', '').strip()

    if not all([name, email, phone, address]):
        return jsonify({'success': False, 'error': 'Please fill in all fields.'}), 400

    reference = f'IRONFORGE-{uuid.uuid4().hex[:12].upper()}'
    order = Order(
        reference        = reference,
        customer_name    = name,
        customer_email   = email,
        customer_phone   = phone,
        customer_address = address,
        total_amount     = total,
        payment_method   = 'paystack',
        payment_status   = 'pending',
    )
    db.session.add(order)
    db.session.flush()

    for item in items:
        line = OrderItem(
            order_id   = order.id,
            product_id = item['product'].id,
            quantity   = item['qty'],
            unit_price = item['price'],
            unit       = item['unit']
        )
        db.session.add(line)

    db.session.commit()
    session['pending_order_ref'] = reference

    return jsonify({
        'success':            True,
        'reference':          reference,
        'email':              email,
        'amount_kobo':        total * 100,
        'paystack_public_key': current_app.config['PAYSTACK_PUBLIC_KEY'],
        'customer_name':      name,
        'customer_phone':     phone,
        'verify_url':         url_for('payments.verify',
                                      reference=reference, _external=True),
    })


# ─────────────────────────────────────────────────────────────────────────────
#  Order Success Page
# ─────────────────────────────────────────────────────────────────────────────
@orders_bp.route('/success/<reference>')
def success(reference):
    order = Order.query.filter_by(reference=reference).first_or_404()
    return render_template('success.html', order=order)
