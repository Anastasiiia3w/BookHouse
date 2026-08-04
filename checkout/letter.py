from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from orders.models import Order
import logging

logger = logging.getLogger(__name__)

# Створюємо та надсилаємо емейл лист про успішне замовленн
def send_order_email(order_id):
    try:
        order = Order.objects.select_related('user', 'shipping_address').prefetch_related('items__product').get(id = order_id)

        subject = f'Замовлення № {order.id} успішно оформлено!'
        from_email = settings.DEFAUL_FROM_EMAIL
        to_email = order.user.email

        if not to_email:
            logger.warning('Не вдалося надіслати лист: у користувача не має email'
                           'Order ID: %s')
            return

        context = {
            'order' : order,
            'user' : order.user,
            'items' : order.items.all(),
            'address' : order.shipping_address
        }

        html_content = render_to_string('checkout/email/order_confirmation.html', context)
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(subject = subject, body = text_content, from_email = from_email, to = [to_email])
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

    except Order.DoesNotExist:
        logger.error('Замовлення з ID %s не знайдено', order_id,)

    except Exception:
        logger.exception('Помилка під час відправлення листа для замовлення %s', order_id,)