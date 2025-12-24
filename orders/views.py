from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from decimal import Decimal
import stripe
import json

from .models import Cart, CartItem, Order, OrderItem
from store.models import Product
from .forms import CheckoutForm

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_view(request):
    """Shopping cart view"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'orders/checkout_cart.html', context)


def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if product.stock < quantity:
        messages.error(request, 'Not enough stock available.')
        return redirect('store:product_detail', slug=product.slug)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += quantity
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
            messages.warning(request, f'Only {product.stock} items available.')
    else:
        cart_item.quantity = quantity
    
    cart_item.save()
    messages.success(request, f'{product.name} added to cart!')
    
    return redirect('orders:cart')


def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    action = request.POST.get('action')
    
    if action == 'increase':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, 'Maximum stock reached.')
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, 'Item removed from cart.')
    elif action == 'remove':
        cart_item.delete()
        messages.info(request, 'Item removed from cart.')
    
    return redirect('orders:cart')


def checkout_info_view(request):
    """Checkout information step"""
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders:cart')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Store form data in session
            request.session['checkout_data'] = form.cleaned_data
            # Convert Decimal to string for JSON serialization
            for key, value in request.session['checkout_data'].items():
                if isinstance(value, Decimal):
                    request.session['checkout_data'][key] = str(value)
            return redirect('orders:checkout_payment')
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'orders/checkout_info.html', context)


def checkout_payment_view(request):
    """Checkout payment step with Stripe"""
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders:cart')
    
    checkout_data = request.session.get('checkout_data')
    if not checkout_data:
        messages.warning(request, 'Please complete shipping information first.')
        return redirect('orders:checkout_info')
    
    # Calculate totals
    subtotal = cart.subtotal
    shipping_cost = Decimal('10.00')  # Fixed shipping cost
    tax = subtotal * Decimal('0.10')  # 10% tax
    total = subtotal + shipping_cost + tax
    
    # Create Stripe Payment Intent
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),  # Stripe uses cents
            currency='usd',
            metadata={
                'cart_id': str(cart.id),
            }
        )
        
        context = {
            'cart': cart,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'tax': tax,
            'total': total,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'client_secret': intent.client_secret,
            'checkout_data': checkout_data,
        }
        return render(request, 'orders/checkout_payment.html', context)
    
    except stripe.error.StripeError as e:
        messages.error(request, 'Payment processing error. Please try again.')
        return redirect('orders:cart')


@login_required
def create_order(request):
    """Create order after successful payment"""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        checkout_data = request.session.get('checkout_data')
        payment_intent_id = request.POST.get('payment_intent_id')
        
        if not checkout_data or not payment_intent_id:
            return JsonResponse({'error': 'Missing data'}, status=400)
        
        # Calculate totals
        subtotal = cart.subtotal
        shipping_cost = Decimal('10.00')
        tax = subtotal * Decimal('0.10')
        total = subtotal + shipping_cost + tax
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            full_name=checkout_data['full_name'],
            email=checkout_data['email'],
            phone=checkout_data['phone'],
            address=checkout_data['address'],
            city=checkout_data['city'],
            state=checkout_data['state'],
            postal_code=checkout_data['postal_code'],
            country=checkout_data['country'],
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            payment_status='completed',
            stripe_payment_intent=payment_intent_id,
            status='processing'
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity
            )
            
            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()
        
        # Send confirmation email
        try:
            send_mail(
                subject=f'Order Confirmation - {order.order_number}',
                message=f'''
                Hi {order.full_name},
                
                Thank you for your order!
                
                Order Number: {order.order_number}
                Total: ${order.total}
                
                We will send you a shipping confirmation once your order ships.
                
                Best regards,
                {settings.SITE_NAME}
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
        except:
            pass
        
        # Clear cart
        cart.items.all().delete()
        
        # Clear session data
        if 'checkout_data' in request.session:
            del request.session['checkout_data']
        
        return JsonResponse({
            'success': True,
            'order_id': str(order.id),
            'order_number': order.order_number
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def checkout_complete_view(request):
    """Order completion page"""
    order_number = request.GET.get('order_number')
    order = None
    
    if order_number:
        order = Order.objects.filter(order_number=order_number).first()
    
    context = {
        'order': order,
    }
    return render(request, 'orders/checkout_complete.html', context)


@login_required
def order_detail_view(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'orders/order_detail.html', context)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Update order status if needed
        Order.objects.filter(stripe_payment_intent=payment_intent['id']).update(
            payment_status='completed'
        )
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        Order.objects.filter(stripe_payment_intent=payment_intent['id']).update(
            payment_status='failed'
        )
    
    return HttpResponse(status=200)
