from decimal import Decimal
from .models import CartModel, CartItem
from store.models import Product

CART_SESSION_ID = 'cart'

class Cart:
    def __init__(self, request):
        self.session = request.session

        cart = self.session.get(CART_SESSION_ID)

        if cart is None:
            cart = self.session[CART_SESSION_ID] = {}

        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False):
        product_id = str(product.id)

        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price),
            }

        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity

        self.session.modified = True

    def save(self):
        self.session.modified = True

    def remove(self, product):
        product_id  = str(product.id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def __iter__(self):
        products_ids = self.cart.keys()

        products = Product.objects.filter(
            id__in = products_ids,
            is_available = True
        ).select_related('category')

        cart = self.cart.copy()

        for product in products:
            product_id = str(product.id)
            cart[product_id]['product'] = product

        for item in cart.values():
            if 'product' not in item:
                continue

            item['price'] = Decimal(item['price'])
            item['total_price'] = (
                item['price'] * item['quantity']
            )

            yield item

    def __len__(self):
        return sum(
            item['quantity']
            for item in self.cart.values()
        )

    def get_total_price(self):
        return sum(
            Decimal(item['price']) * item['quantity']
                    for item in self.cart.values()
        )

    def clear(self):
        self.session.pop(CART_SESSION_ID, None)
        self.save()


def transport_session_cart_to_db(user, session_cart):
    if not session_cart:
        return

    cart, created = CartModel.objects.get_or_create(user = user)

    product_ids = []
    for product_id in session_cart.keys():
        product_ids.append(int(product_id))

    products = Product.objects.filter(id__in = product_ids)

    product_dict = {product.id: product for product in products}

    for id, quantity in session_cart.items():
        product_id = int(id)
        if product_id not in product_dict:
            continue

    cart_item, item_created = CartItem.objects.get_or_create(
        cart = cart,
        product = product_id,
        defaults={'quantity' : quantity}
    )

    if not cart_item:
        cart_item.quantity += quantity
        cart_item.save()