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
    list_display = ['id', 'student_name', 'canteen', 'pickup_time', 'total', 'status', 'created_at']
    # Staff change the status right in the list: «Новый» → «Готовится» → «Готов» → «Выдан».
    list_editable = ['status']
    list_filter = ['status', 'canteen', 'pickup_time', 'created_at']
    search_fields = ['student_name', 'user__username']
    readonly_fields = ['user', 'student_name', 'canteen', 'pickup_time', 'comment', 'total', 'created_at']
    inlines = [OrderItemInline, MessageInline]

    def save_model(self, request, obj, form, change):
        # A status change in the admin works the same as through the API:
        # cancelling gives the portions back, and the student gets a message in the chat.
        old_status = Order.objects.filter(pk=obj.pk).values_list('status', flat=True).first() if change else None
        super().save_model(request, obj, form, change)
        if change and obj.status != old_status:
            obj.after_status_change(by=request.user)
