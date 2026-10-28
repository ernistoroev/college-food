
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField('название', max_length=100, unique=True)
    order = models.PositiveSmallIntegerField(
        'порядок',
        default=0,
        help_text='Чем меньше число, тем выше категория в меню.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Dish(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='dishes',
        verbose_name='категория',
    )

    name = models.CharField('название', max_length=200)

    description = models.TextField(
        'описание',
        blank=True
    )

    price = models.DecimalField(
        'цена, сом',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )

    image = models.ImageField(
        'фото',
        upload_to='dishes/',
        blank=True
    )

    
    weight = models.PositiveIntegerField(
        'вес или объём',
        default=0,
    )
    weight_unit = models.CharField(
        'единица измерения',
        max_length=2,
        choices=[
            ('г', 'Граммы (г)'),
            ('мл', 'Миллилитры (мл)'),
        ],
        default='г',
    )
    portions_today = models.PositiveIntegerField(
        'порций на сегодня',
        default=0,
    )


    is_available = models.BooleanField(
        'в наличии',
        default=True,
        help_text='Снимите галочку, если блюда сейчас нет: оно останется в меню с пометкой и его нельзя будет заказать.'
    )

    # The name in lower case, filled in save(). SQLite cannot compare Cyrillic letters without
    # case, so the search compares lower-case strings instead.
    search_name = models.CharField(max_length=200, editable=False, default='')

    created_at = models.DateTimeField(
        'создано',
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        'изменено',
        auto_now=True
    )

    class Meta:
        verbose_name = 'блюдо'
        verbose_name_plural = 'блюда'
        ordering = [
            'category__order',
            'category__name',
            'name'
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.search_name = self.name.lower()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'name' in update_fields:
            kwargs['update_fields'] = {*update_fields, 'search_name'}
        super().save(*args, **kwargs)
