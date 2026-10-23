
from django.contrib import admin

from .models import Category, Dish


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']
    search_fields = ['name']


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'category',
        'price',
        'weight',
        'weight_unit',
        'portions_today',
        'is_available',
    ]
    list_editable = [
        'price',
        'weight',
        'weight_unit',
        'portions_today',
        'is_available',
    ]
    list_filter = ['category', 'is_available']
    search_fields = ['name', 'description']
