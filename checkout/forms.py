from django import forms


class PaymentMethodForm(forms.Form):
    PAYMENT_CHOICES = [
        ('card', 'Оплата карткою'),
        ('cash', 'Оплата готівкою (при отриманні)'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(
            attrs={'class': 'payment-radio-input'}
        ),
        label='Оберіть спосіб оплати',
    )