from django.contrib import admin
from .models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'product_name', 'product_price', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__username', 'full_name']
    readonly_fields = ['order_number', 'stripe_payment_intent', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    list_editable = ['status']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Shipping Information', {
            'fields': ('full_name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Payment Information', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'total', 'payment_method', 'payment_status', 'stripe_payment_intent')
        }),
        ('Additional', {
            'fields': ('notes',)
        }),
    )


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'created_at', 'total_items']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__username', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'
