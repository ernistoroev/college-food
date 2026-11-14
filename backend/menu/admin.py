
from django import forms
from django.contrib import admin

from .models import Canteen, Category, Dish


@admin.register(Canteen)
class CanteenAdmin(admin.ModelAdmin):
    list_display = ['name', 'floor']


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
        'served_in',
    ]
    list_editable = [
        'price',
        'weight',
        'weight_unit',
        'portions_today',
        'is_available',
    ]
    list_filter = ['category', 'canteens', 'is_available']
    search_fields = ['name', 'description']
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('canteens')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # Three canteens fit as checkboxes better than the default multi-select list.
        if db_field.name == 'canteens':
            kwargs['widget'] = forms.CheckboxSelectMultiple
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        # A new dish is ticked for all canteens; staff untick the ones that do not serve it.
        return {**super().get_changeform_initial_data(request), 'canteens': Canteen.objects.all()}

    @admin.display(description='этажи доставки')
    def served_in(self, dish):
        return ', '.join(f'{canteen.floor} эт.' for canteen in dish.canteens.all()) or '—'
