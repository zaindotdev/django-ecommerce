from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<uuid:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<uuid:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/info/', views.checkout_info_view, name='checkout_info'),
    path('checkout/payment/', views.checkout_payment_view, name='checkout_payment'),
    path('checkout/complete/', views.checkout_complete_view, name='checkout_complete'),
    path('create-order/', views.create_order, name='create_order'),
    path('order/<uuid:order_id>/', views.order_detail_view, name='order_detail'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]
