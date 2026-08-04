from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path(
        'address/',
        views.checkout_address,
        name='checkout'
    ),
    path(
        'payment/',
        views.checkout_payment,
        name='checkout_payment'
    ),
    path(
        'confirm/',
        views.checkout_confirm,
        name='checkout_confirm'
    ),
    path(
        'success/<int:order_id>/',
        views.checkout_success,
        name='checkout_success'
    ),
]