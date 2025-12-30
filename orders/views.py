from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from decimal import Decimal
import stripe

from .models import Cart, CartItem, Order, OrderItem
from store.models import Product
from .forms import CheckoutForm

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
    
    # Handle proceed to checkout
    if request.method == 'POST' and 'proceed_checkout' in request.POST:
        if not cart_items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('orders:cart')
        return redirect('orders:checkout_info')
    
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
            checkout_data = {}
            for key, value in form.cleaned_data.items():
                # Convert Decimal to string for JSON serialization
                if isinstance(value, Decimal):
                    checkout_data[key] = str(value)
                else:
                    checkout_data[key] = value
            request.session['checkout_data'] = checkout_data
            request.session.modified = True
            messages.success(request, 'Shipping information saved.')
            return redirect('orders:checkout_payment')
    else:
        # Pre-fill form with existing session data if available
        initial_data = request.session.get('checkout_data', {})
        form = CheckoutForm(initial=initial_data, user=request.user)
    
    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'orders/checkout_info.html', context)


def checkout_payment_view(request):
    """Checkout payment step with Stripe"""
    print(f"checkout_payment_view called - Method: {request.method}")
    
    cart = get_or_create_cart(request)
    
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('orders:cart')
    
    # Validate shipping address exists in session
    checkout_data = request.session.get('checkout_data')
    required_fields = ['full_name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'country']
    
    if not checkout_data:
        messages.warning(request, 'Please add your shipping address first.')
        return redirect('orders:checkout_info')
    
    # Verify all required fields are present
    missing_fields = [field for field in required_fields if not checkout_data.get(field)]
    if missing_fields:
        messages.warning(request, 'Please complete all shipping information fields.')
        return redirect('orders:checkout_info')
    
    subtotal = cart.subtotal
    shipping_cost = Decimal('10.00')  
    tax = round(subtotal * Decimal('0.10'),2)  
    total = subtotal + shipping_cost + tax
    
    if request.method == 'POST':
        try:
            line_items = []
            for item in cart.items.all():
                # Get product image URL if available
                image_url = None
                if hasattr(item.product, 'images') and item.product.images.exists():
                    first_image = item.product.images.first()
                    if first_image and hasattr(first_image, 'image'):
                        image_url = request.build_absolute_uri(first_image.image.url)
                
                line_items.append({
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': item.product.name,
                            'images': [image_url] if image_url else [],
                        },
                        'unit_amount': int(item.product.price * 100),  # Convert to cents
                    },
                    'quantity': item.quantity,
                })
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Shipping',
                    },
                    'unit_amount': int(shipping_cost * 100),
                },
                'quantity': 1,
            })
            
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Tax',
                    },
                    'unit_amount': int(tax * 100),
                },
                'quantity': 1,
            })
            
            print(f"Creating Stripe session with {len(line_items)} items for total: ${total}")
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['cashapp','card'],
                line_items=line_items,
                mode='payment',
                success_url=request.build_absolute_uri('/orders/checkout/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/orders/checkout/payment/'),
                customer_email=checkout_data.get('email'),
                metadata={
                    'cart_id': str(cart.id),
                    'user_id': str(request.user.id) if request.user.is_authenticated else '',
                },
            )
            
            print(f"Stripe session created: {checkout_session.id}")
            print(f"Redirecting to: {checkout_session.url}")
            
            request.session['stripe_session_id'] = checkout_session.id
            request.session.modified = True
            
            return redirect(checkout_session.url)
        
        except stripe.error.StripeError as e:
            print(f"Stripe error: {str(e)}")
            messages.error(request, f'Payment processing error: {str(e)}. Please try again.')
            return redirect('orders:checkout_payment')
        except Exception as e:
            print(f"General error: {str(e)}")
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('orders:checkout_payment')
    
    context = {
        'cart': cart,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'tax': tax,
        'total': total,
        'checkout_data': checkout_data,
    }
    return render(request, 'orders/checkout_payment.html', context)


def checkout_success_view(request):
    """Handle successful Stripe Checkout"""
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, 'Invalid payment session.')
        return redirect('orders:cart')
    
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status != 'paid':
            messages.error(request, 'Payment was not successful.')
            return redirect('orders:checkout_payment')
        
        cart = get_or_create_cart(request)
        checkout_data = request.session.get('checkout_data')
        
        if not checkout_data:
            messages.error(request, 'Checkout data not found.')
            return redirect('orders:cart')
        
        # Check if order already exists for this session to prevent duplicates
        existing_order = Order.objects.filter(stripe_payment_intent=checkout_session.payment_intent).first()
        if existing_order:
            # Order already created, redirect to completion page
            return redirect(f'/orders/checkout/complete/?order_number={existing_order.order_number}')
        
        subtotal = cart.subtotal
        shipping_cost = Decimal('10.00')
        tax = subtotal * Decimal('0.10')
        total = subtotal + shipping_cost + tax
        
        # Create order for authenticated or guest user
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
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
            stripe_payment_intent=checkout_session.payment_intent,
            status='processing'
        )
        
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity
            )
            
            product = cart_item.product
            product.stock -= cart_item.quantity
            product.save()
            
        try:
            send_mail(
                subject=f'Order Confirmation - {order.order_number}',
                message=f'''Hi {order.full_name},

Thank you for your order!

Order Number: {order.order_number}
Total: ${order.total}

We will send you a shipping confirmation once your order ships.

Best regards,
{settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'Our Store'}
''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        # Clear cart
        cart.items.all().delete()
        
        # Clear session data
        if 'checkout_data' in request.session:
            del request.session['checkout_data']
        if 'stripe_session_id' in request.session:
            del request.session['stripe_session_id']
        
        messages.success(request, 'Your order has been placed successfully!')
        return redirect(f'/orders/checkout/complete/?order_number={order.order_number}')
    
    except stripe.error.StripeError as e:
        messages.error(request, f'Error verifying payment: {str(e)}')
        return redirect('orders:cart')
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('orders:cart')


@login_required
def create_order(request):
    """Create order after successful payment"""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        checkout_data = request.session.get('checkout_data')
        payment_intent_id = request.POST.get('payment_intent_id')
        
        if not checkout_data:
            return JsonResponse({'error': 'Shipping address not found. Please add shipping information.'}, status=400)
        
        if not payment_intent_id:
            return JsonResponse({'error': 'Payment information missing.'}, status=400)
        
        subtotal = cart.subtotal
        shipping_cost = Decimal('10.00')
        tax = subtotal * Decimal('0.10')
        total = subtotal + shipping_cost + tax
        
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
    event = None
    
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


@login_required
def order_list_view(request):
    """List of user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'orders/order_list.html', context)