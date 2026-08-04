from django.conf import settings
from django.db import models
from store.models import Product
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator

class Coupon(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Промокод',
    )
    discount = models.PositiveSmallIntegerField(
        verbose_name='Знижка, %',
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100),
        ],
    )
    valid_from = models.DateTimeField(
        verbose_name='Діє з',
    )
    valid_to = models.DateTimeField(
        verbose_name='Діє до',
    )

    max_uses = models.PositiveIntegerField(
        default=1,
        verbose_name='Максимальна кількість використань',
    )
    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Кількість використань',
        editable=False,
    )
    active = models.BooleanField(
        default=True,
        verbose_name='Активний',
    )

    class Meta:
        ordering = ['-valid_from']
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоди'

    def clean(self):
        super().clean()

        if self.valid_from and self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError({
                'valid_to': (
                    'Дата завершення повинна бути пізнішою '
                    'за дату початку.'
                )
            })
        if self.used_count > self.max_uses:
            raise ValidationError({
                'valid_to': (
                    'Дата завершення повинна бути пізнішою '
                    'за дату початку.'
                )
            })

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to and self.used_count < self.max_uses

    def __str__(self):
        return f'{self.code} (-{self.discount}%)'

class StatusHistory(models.TextChoices):
    PENDING = 'pending', 'Очікує підтвердження'
    PROCESSING = 'processing', 'Обробляється'
    SHIPPED = 'shipped', 'Відправлено'
    DELIVERED = 'delivered', 'Доставлено'
    CANCELLED = 'cancelled', 'Скасовано'

class PaymentMethod(models.TextChoices):
    CARD = 'card', 'Оплата карткою'
    CASH = 'cash', 'Оплата готівкою (при отриманні)'

class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Очікує підтвердження'
    PROCESSING = 'processing', 'Обробляється'
    SHIPPED = 'shipped', 'Відправлено'
    DELIVERED = 'delivered', 'Доставлено'
    CANCELLED = 'cancelled', 'Скасовано'


class Order(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Користувач',
    )

    coupon = models.ForeignKey(
        Coupon,
        on_delete = models.SET_NULL,
        null = True,
        blank=True,
        related_name='orders',
        verbose_name='Промокод'
    )

    status = models.CharField(
        'Статус',
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )

    subtotal = models.DecimalField(
        'Сума товарів',
        max_digits=12,
        decimal_places=2,
        default=Decimal(0.00),
    )

    discount_amount = models.DecimalField(
        'Знижка',
        max_digits=12,
        decimal_places=2,
        default=Decimal(0.00),
    )

    total = models.DecimalField(
        'Загальна сума',
        max_digits=12,
        decimal_places=2,
        default=Decimal(0.00),
    )

    payment_method = models.CharField(
        'Спосіб оплати',
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CARD
    )

    estimated_delivery_date = models.DateTimeField(
        'Орієнтовна дата доставки',
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        'Дата створення',
        auto_now_add=True,
        db_index=True,
    )

    updated_at = models.DateTimeField(
        'Дата оновлення',
        auto_now=True,
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'

    def __str__(self):
        return f'Замовлення №{self.pk}'

    @property
    def can_be_cancelled(self):
        return self.status in {
            OrderStatus.PENDING,
            OrderStatus.PROCESSING,
        }

    def calculate_total(self):
        self.discount_amount = Decimal('0.00')

        if self.coupon and self.coupon.is_valid():
            discount_percent = Decimal(str(self.coupon.discount))

            self.discount_amount = (self.subtotal * self.discount_amount / Decimal('100')).quantize(Decimal('0.01'))

        self.total = (self.subtotal - self.discount_amount).quantize(Decimal('0.01'))

    def apply_coupon(self, coupon):
        if not coupon or not coupon.is_valid():
            return False

        self.coupon = coupon,
        self.calculate_total()

        return True



class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Замовлення',
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Товар',
    )

    product_name = models.CharField(
        'Назва товару',
        max_length=200,
    )

    price = models.DecimalField(
        'Ціна за одиницю',
        max_digits=12,
        decimal_places=2,
    )

    quantity = models.PositiveIntegerField(
        'Кількість',
        default=1,
    )


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'product'],
                name='unique_product_in_order',
            ),
        ]

        verbose_name = 'Позиція замовлення'
        verbose_name_plural = 'Позиції замовлення'

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='замовлення',
    )
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        verbose_name='статус',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null = True,
        blank=True,
        related_name='order_status_changes',
        verbose_name='хто змінив',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='коментар',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='дата зміни',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Історія статусу'
        verbose_name_plural = 'Історія статусів'

    def __str__(self):
        return f'Замовлення №{self.order.id} змінено на {self.get_status_display()}'


class ShippingAddress(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipping_address',
        verbose_name='Замовлення',
    )

    recipient_name = models.CharField(
        'Ім’я та прізвище',
        max_length=150,
    )

    recipient_email = models.EmailField(
        'Email',
        max_length=150,
    )

    phone = models.CharField(
        'Телефон',
        max_length=20,
    )

    city = models.CharField(
        'Місто',
        max_length=100,
    )

    postal_code = models.CharField(
        'Поштовий індекс',
        max_length=10,
        blank=True,
    )

    address_line = models.CharField(
        'Адреса або номер відділення',
        max_length=255,
    )

    comment = models.TextField(
        'Коментар до доставки',
        blank=True,
    )

    class Meta:
        verbose_name = 'Адреса доставки'
        verbose_name_plural = 'Адреси доставки'

    def __str__(self):
        return f'{self.city}, {self.address_line}'
