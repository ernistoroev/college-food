from django.contrib import admin

from .models import Message, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['dish', 'name', 'price', 'quantity']
    can_delete = False


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['author', 'text', 'created_at']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'student_name', 'pickup_time', 'total', 'status', 'created_at']
    # Staff change the status right in the list: «Новый» → «Готовится» → «Готов» → «Выдан».
    list_editable = ['status']
    list_filter = ['status', 'pickup_time', 'created_at']
    search_fields = ['student_name', 'user__username']
    readonly_fields = ['user', 'student_name', 'pickup_time', 'comment', 'total', 'created_at']
    inlines = [OrderItemInline, MessageInline]

    def save_model(self, request, obj, form, change):
        # Cancelling in the admin gives the portions back too, the same as through the API.
        was_cancelled = change and Order.objects.filter(pk=obj.pk, status=Order.Status.CANCELLED).exists()
        super().save_model(request, obj, form, change)
        if obj.status == Order.Status.CANCELLED and not was_cancelled:
            obj.return_portions()
