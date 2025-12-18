from orders.models import Cart
from store.models import Product


def cart_context(request):
    """Add cart information to all template contexts"""
    cart = None
    cart_items_count = 0
    
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        elif request.session.session_key:
            cart = Cart.objects.filter(session_key=request.session.session_key).first()
        
        if cart:
            cart_items_count = cart.total_items
    except:
        pass
    
    return {
        'cart': cart,
        'cart_items_count': cart_items_count,
    }


def product_context(request):
    """Add product-related context variables"""
    trending_products = Product.objects.filter(is_active=True).order_by('-created_at')[:5]
    featured_products = Product.objects.filter(is_active=True, is_featured=True).order_by('-created_at')[:5]
    new_products = Product.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    return {
        'trending_products': trending_products,
        'featured_products': featured_products,
        'new_products': new_products,
    }