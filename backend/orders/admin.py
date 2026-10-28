from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['dish', 'name', 'price', 'quantity']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'student_name', 'pickup_time', 'total', 'status', 'created_at']
    # Staff change the status right in the list: «Готовится» → «Готов к выдаче» → «Выдан».
    list_editable = ['status']
    list_filter = ['status', 'pickup_time', 'created_at']
    search_fields = ['student_name', 'user__username']
    readonly_fields = ['user', 'student_name', 'pickup_time', 'total', 'created_at']
    inlines = [OrderItemInline]
