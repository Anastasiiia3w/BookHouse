from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .services import transport_session_cart_to_db

# буде викликатись підчас авторизації користувача, щоб замінити сесійний кошик на базу
@receiver(user_logged_in)
def user_logged_in(sender, request, user, **kwargs):
    #кошик аноніма
    cart = request.session.get('cart', {})

    if cart:
        transport_session_cart_to_db(user, cart)

        request.session['cart'] = {}
        request.session.modified = True