from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from store.models import Product
from .forms import CartAddProductForm
from .services import Cart
from .models import CartModel


def cart_detail(request):
    cart = Cart(request)

    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={
                'quantity': item['quantity'],
                'override': True,
            }
        )

    return render(
        request,
        'cart/detail.html',
        {'cart': cart}
    )

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id = product_id,
        is_available = True
    )

    form = CartAddProductForm(request.POST)

    if form.is_valid() and product.stock > 0:
        cart.add(
            product = product,
            quantity = form.cleaned_data['quantity'],
            override_quantity = form.cleaned_data['override']
        )

    return redirect('cart:detail')

@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)

    product = get_object_or_404(
        Product,
        id=product_id
    )

    cart.remove(product)

    return redirect('cart:detail')

@require_POST
def cart_clear(request):
    cart = Cart(request)
    cart.clear()

    return redirect('cart:detail')

def cart_view(request):
    cart_item = []
    total_cost = 0

    # Зареєстрований користувач має кошик у базі даних
    if request.user.is_autenticated:
        cart = CartModel.objects.get_or_create(user = request.user)
        items = cart.item.select_related('product')

        for item in items:
            cart_item.append({
                'product' : item.product,
                'quantity' : item.quantity,
                'total_price' : item.total
            })

        total_cost = cart.total


    # Не зареєстрований користувач має кошик у сессії
    else:
        session_cart = request.session.get('cart', {})

        ids = session_cart.keys()

        if session_cart:
            session_items = Product.objects.filter(id__in = ids)
            for session_item in session_items:
                quantity = session_items[str(session_item.id)]
                item_total = session_item.price * quantity
                total_cost += item_total
                cart_item.append({
                    'product' : session_item,
                    'quantity' : quantity,
                    'total_price' : item_total
                })
    context = {
        'cart_item' : cart_item,
        'total_cost' : total_cost
    }

    return render(request, 'detail.html', context)
