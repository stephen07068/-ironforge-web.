from flask import (Blueprint, session, request, jsonify,
                   redirect, url_for, render_template)
from models import Product

cart_bp = Blueprint('cart', __name__)


def get_cart():
    """Return the cart dict from session, creating it if absent."""
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']


def save_cart(cart):
    session['cart'] = cart
    session.modified = True


# ─────────────────────────────────────────────────────────────────────────────
#  View Cart
# ─────────────────────────────────────────────────────────────────────────────
@cart_bp.route('/')
def view_cart():
    cart  = get_cart()
    items = []
    total = 0

    for key, item in list(cart.items()):
        raw_pid = str(key).split('_')[0]
        product = Product.query.get(int(raw_pid))
        if product:
            # Fallback to product.price if old cart structure
            price = item.get('price', product.price)
            subtotal = price * item['qty']
            total   += subtotal
            items.append({
                'key':      key,
                'product':  product,
                'qty':      item['qty'],
                'unit':     item.get('unit', 'pieces'),
                'price':    price,
                'subtotal': subtotal,
            })

    return render_template('cart.html', items=items, total=total)


# ─────────────────────────────────────────────────────────────────────────────
#  Add to Cart
# ─────────────────────────────────────────────────────────────────────────────
@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty     = int(request.form.get('qty', 1))
    unit    = request.form.get('unit', 'pieces')
    cart    = get_cart()

    key = f"{product_id}_{unit}"
    if key in cart:
        cart[key]['qty'] += qty
    else:
        price = product.price_per_ton if unit == 'tons' else product.price
        cart[key] = {
            'product_id': product_id,
            'qty': qty,
            'unit': unit,
            'price': price
        }

    save_cart(cart)

    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart_count = sum(i['qty'] for i in cart.values())
        return jsonify({'success': True, 'cart_count': cart_count,
                        'message': f'{product.name} added to cart'})

    return redirect(url_for('cart.view_cart'))


# ─────────────────────────────────────────────────────────────────────────────
#  Update Quantity
# ─────────────────────────────────────────────────────────────────────────────
@cart_bp.route('/update/<product_key>', methods=['POST'])
def update_cart(product_key):
    qty  = int(request.form.get('qty', 1))
    cart = get_cart()
    key  = str(product_key)

    if key in cart:
        if qty <= 0:
            del cart[key]
        else:
            cart[key]['qty'] = qty
        save_cart(cart)

    return redirect(url_for('cart.view_cart'))


# ─────────────────────────────────────────────────────────────────────────────
#  Remove Item
# ─────────────────────────────────────────────────────────────────────────────
@cart_bp.route('/remove/<product_key>', methods=['POST'])
def remove_from_cart(product_key):
    cart = get_cart()
    key  = str(product_key)
    if key in cart:
        del cart[key]
        save_cart(cart)
    return redirect(url_for('cart.view_cart'))


# ─────────────────────────────────────────────────────────────────────────────
#  Clear Cart
# ─────────────────────────────────────────────────────────────────────────────
@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('shop.index'))
