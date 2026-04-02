import requests as http
from flask import (Blueprint, redirect, url_for, request,
                   current_app, render_template, session, flash)
from models import db, Order

payments_bp = Blueprint('payments', __name__)

PAYSTACK_BASE = 'https://api.paystack.co'


def paystack_headers():
    secret = current_app.config['PAYSTACK_SECRET_KEY']
    return {
        'Authorization': f'Bearer {secret}',
        'Content-Type':  'application/json',
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Initiate Payment
# ─────────────────────────────────────────────────────────────────────────────
@payments_bp.route('/initiate/<reference>')
def initiate(reference):
    order = Order.query.filter_by(reference=reference).first_or_404()

    callback_url = url_for('payments.verify', reference=reference,
                           _external=True)
    payload = {
        'email':        order.customer_email,
        'amount':       order.total_in_kobo(),   # kobo = naira × 100
        'reference':    reference,
        'callback_url': callback_url,
        'metadata': {
            'customer_name':  order.customer_name,
            'customer_phone': order.customer_phone,
            'order_id':       order.id,
        },
    }

    response = http.post(
        f'{PAYSTACK_BASE}/transaction/initialize',
        json    = payload,
        headers = paystack_headers(),
        timeout = 30,
    )
    data = response.json()

    if data.get('status'):
        authorization_url = data['data']['authorization_url']
        return redirect(authorization_url)
    else:
        flash('Could not connect to Paystack. Please try again.', 'danger')
        return redirect(url_for('cart.view_cart'))


# ─────────────────────────────────────────────────────────────────────────────
#  Verify Payment (Paystack callback)
# ─────────────────────────────────────────────────────────────────────────────
@payments_bp.route('/verify/<reference>')
def verify(reference):
    order = Order.query.filter_by(reference=reference).first_or_404()

    response = http.get(
        f'{PAYSTACK_BASE}/transaction/verify/{reference}',
        headers = paystack_headers(),
        timeout = 30,
    )
    data = response.json()

    if data.get('status') and data['data']['status'] == 'success':
        order.payment_status = 'paid'
        db.session.commit()

        # Clear cart on successful payment
        session.pop('cart', None)

        return redirect(url_for('orders.success', reference=reference))
    else:
        order.payment_status = 'failed'
        db.session.commit()
        flash('Payment verification failed. Please contact support.', 'danger')
        return redirect(url_for('cart.view_cart'))
