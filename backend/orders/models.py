from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F

from menu.models import Dish

# Pickup slots offered on the checkout form.
PICKUP_TIMES = [(time, time) for time in ['12:20', '12:40', '13:00', '13:20', '13:40', '14:00']]


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        COOKING = 'cooking', 'Готовится'
        READY = 'ready', 'Готов'
        DONE = 'done', 'Выдан'
        CANCELLED = 'cancelled', 'Отменён'

    # After these statuses the order is closed and its status cannot be changed through the API.
    FINAL_STATUSES = {Status.DONE, Status.CANCELLED}

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='пользователь',
    )
    student_name = models.CharField('имя студента', max_length=80)
    pickup_time = models.CharField('время получения', max_length=5, choices=PICKUP_TIMES)
    comment = models.TextField('комментарий', max_length=500, blank=True)
    status = models.CharField('статус', max_length=20, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField('сумма, сом', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('создан', auto_now_add=True)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ №{self.pk}'

    def return_portions(self):
        """A cancelled order gives its portions back to the menu."""
        for item in self.items.exclude(dish=None):
            Dish.objects.filter(pk=item.dish_id).update(portions_today=F('portions_today') + item.quantity)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='заказ')
    # The dish may be deleted later, so its name and price are copied into the order.
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='блюдо')
    name = models.CharField('название', max_length=200)
    price = models.DecimalField('цена, сом', max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField('количество', validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'

    def __str__(self):
        return f'{self.name} × {self.quantity}'


class Message(models.Model):
    """A chat message about an order between the student and canteen staff."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages', verbose_name='заказ')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='order_messages',
        verbose_name='автор',
    )
    text = models.TextField('текст', max_length=1000)
    created_at = models.DateTimeField('отправлено', auto_now_add=True)

    class Meta:
        verbose_name = 'сообщение'
        verbose_name_plural = 'сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author}: {self.text[:30]}'
