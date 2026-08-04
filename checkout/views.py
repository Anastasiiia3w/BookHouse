from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from orders.forms import ShippingAddressForm, CouponApplyForm
from .forms import PaymentMethodForm
from django.db import transaction
from django.core.exceptions import ValidationError
from store.models import Product
from orders.models import Order, OrderItem, ShippingAddress
from .letter import send_order_email
from decimal import Decimal
from django.contrib import messages
from orders.models import OrderStatus


# Користувач вводить адресу доставки і переходить на наступний крок (оплата)
@login_required
def checkout_address(request):
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)

        if form.is_valid():
            request.session['checkout_address'] = form.cleaned_data

            return redirect('checkout:checkout_payment')
    else:
        form = ShippingAddressForm(
            initial=request.session.get('checkout_address')
        )

    return render(
        request,
        'checkout/checkout.html',
        {
            'address_form': form,
        }
    )



@login_required
def checkout_payment(request):
    checkout_address = request.session.get('checkout_address')

    if not checkout_address:
        return redirect('checkout:checkout_address')

    cart = request.session.get('cart', {})

    cart_items = []
    subtotal = Decimal('0.00')

    products = Product.objects.filter(
        id__in=cart.keys()
    )

    for product in products:
        cart_item = cart.get(str(product.id), {})
        quantity = int(cart_item.get('quantity', 0))
        total_price = product.price * quantity

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': total_price,
        })

        subtotal += total_price

    if not cart_items:
        return redirect('cart:cart_detail')

    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)

        if form.is_valid():
            request.session['checkout_payment'] = form.cleaned_data

            return redirect('checkout:checkout_confirm')
    else:
        form = PaymentMethodForm(
            initial=request.session.get('checkout_payment')
        )

    context = {
        'payment_form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': subtotal,
        'checkout_address': checkout_address,
    }

    return render(
        request,
        'checkout/checkout_payment.html',
        context
    )

@login_required
def checkout_confirm(request):
    checkout_address = request.session.get('checkout_address')
    payment_data = request.session.get('checkout_payment')
    cart = request.session.get('cart', {})

    # Якщо немає адреси — повертаємо на перший крок
    if not checkout_address:
        messages.warning(
            request,
            'Спочатку заповніть адресу доставки.'
        )
        return redirect('checkout:checkout_address')

    # Якщо не вибрано оплату — повертаємо на сторінку оплати
    if not payment_data:
        messages.warning(
            request,
            'Оберіть спосіб оплати.'
        )
        return redirect('checkout:checkout_payment')

    # Якщо кошик порожній
    if not cart:
        messages.warning(
            request,
            'Ваш кошик порожній.'
        )
        return redirect('cart:cart_detail')

    cart_items = []
    subtotal = Decimal('0.00')

    products = Product.objects.filter(
        id__in=cart.keys()
    )

    for product in products:
        cart_data = cart.get(str(product.id), {})

        # Якщо в cart зберігається словник
        if isinstance(cart_data, dict):
            quantity = int(cart_data.get('quantity', 0))

        # Якщо в cart зберігається тільки число
        else:
            quantity = int(cart_data)

        if quantity <= 0:
            continue

        item_total = product.price * quantity

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': item_total,
        })

        subtotal += item_total

    if not cart_items:
        messages.warning(
            request,
            'У кошику немає доступних товарів.'
        )
        return redirect('cart:cart_detail')

    payment_method = payment_data.get(
        'payment_method'
    ) if isinstance(payment_data, dict) else payment_data



    discount_amount = Decimal('0.00')
    total = subtotal - discount_amount

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Блокуємо товари до завершення транзакції
                product_ids = [
                    item['product'].id
                    for item in cart_items
                ]

                locked_products = {
                    product.id: product
                    for product in Product.objects
                    .select_for_update()
                    .filter(id__in=product_ids)
                }

                # Перевіряємо залишки
                for item in cart_items:
                    product = locked_products.get(
                        item['product'].id
                    )

                    if product is None:
                        messages.error(
                            request,
                            'Один із товарів більше не доступний.'
                        )
                        return redirect('cart:cart_detail')

                    if product.stock < item['quantity']:
                        messages.error(
                            request,
                            (
                                f'Недостатньо товару '
                                f'«{product.name}». '
                                f'Доступно: {product.stock}.'
                            )
                        )
                        return redirect('cart:cart_detail')

                # Створюємо замовлення
                order = Order.objects.create(
                    user=request.user,
                    status=OrderStatus.PENDING,
                    subtotal=subtotal,
                    total=total,
                    payment_method=payment_method,
                )

                ShippingAddress.objects.create(
                    order=order,
                    recipient_name=checkout_address.get(
                        'recipient_name',
                        ''
                    ),
                    recipient_email=checkout_address.get(
                        'recipient_email',
                        ''
                    ),
                    phone=checkout_address.get(
                        'phone',
                        ''
                    ),
                    city=checkout_address.get(
                        'city',
                        ''
                    ),
                    postal_code=checkout_address.get(
                        'postal_code',
                        ''
                    ),
                    address_line=checkout_address.get(
                        'address_line',
                        ''
                    ),
                    comment=checkout_address.get(
                        'comment',
                        ''
                    ),
                )

                order_items = []

                for item in cart_items:
                    product = locked_products[
                        item['product'].id
                    ]

                    quantity = item['quantity']

                    order_items.append(
                        OrderItem(
                            order=order,
                            product=product,
                            product_name=product.name,
                            quantity=quantity,
                            price=product.price,
                        )
                    )

                    product.stock -= quantity

                    if product.stock == 0:
                        product.is_available = False

                    product.save(
                        update_fields=[
                            'stock',
                            'is_available',
                        ]
                    )

                OrderItem.objects.bulk_create(
                    order_items
                )

        except Exception:
            messages.error(
                request,
                'Не вдалося створити замовлення.'
            )

            return redirect(
                'checkout:checkout_confirm'
            )


        request.session.pop('cart', None)
        request.session.pop('checkout_address', None)
        request.session.pop('checkout_payment', None)

        request.session.modified = True

        return redirect(
            'checkout:checkout_success',
            order_id=order.id
        )

    context = {
        'checkout_address': checkout_address,
        'payment_method': payment_method,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'total': total,
    }

    return render(
        request,
        'checkout/checkout_confirm.html',
        context
    )

from django.shortcuts import get_object_or_404


@login_required
def checkout_success(request, order_id):
    order = get_object_or_404(
        Order.objects
        .select_related(
            'user',
            'shipping_address',
        )
        .prefetch_related(
            'items__product',
        ),
        id=order_id,
        user=request.user,
    )

    return render(
        request,
        'checkout/checkout_success.html',
        {
            'order': order,
        }
    )