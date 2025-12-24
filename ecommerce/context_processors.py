from orders.models import Cart
from store.models import Product, Category, SubCategory


def cart_context(request):
    """Add cart information to all template contexts"""
    cart = None
    cart_items_count = 0

    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        elif request.session.session_key:
            cart = Cart.objects.filter(
                session_key=request.session.session_key).first()

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
    trending_products = Product.objects.filter(
        is_active=True).order_by('-created_at')[:5]
    featured_products = Product.objects.filter(
        is_active=True, is_featured=True).order_by('-created_at')[:5]
    new_products = Product.objects.filter(
        is_active=True).order_by('-created_at')[:5]
    
    print("Context Processor Loaded: product_context", new_products)

    def calculate_discount(p): return ((p.compare_price - p.price) / p.compare_price *
                                       100) if p.compare_price and p.compare_price > p.price else 0
    for product in trending_products:
        product._discount_percent = calculate_discount(product)
    for product in featured_products:
        product._discount_percent = calculate_discount(product)
    for product in new_products:
        product._discount_percent = calculate_discount(product)

    return {
        'trending_products': trending_products,
        'featured_products': featured_products,
        'new_products': new_products,
    }


def get_categories(request):
    """Add product categories to context"""
    categories = Category.objects.filter(is_active=True).order_by('name')
    mobile_sub_categories = SubCategory.objects.filter(
        is_active=True, category__name='Mobile Phone').order_by('name')[:4]
    mobile_sub_categories_all = SubCategory.objects.filter(
        is_active=True, category__name='Mobile Phone').order_by('name')
    tablets_sub_categories = SubCategory.objects.filter(
        is_active=True, category__name='Tablet').order_by('name')
    mobile_sub_categories_products = Product.objects.filter(
        is_active=True, subcategory__in=mobile_sub_categories).order_by('-created_at')[:5]
    return {
        'categories': categories,
        "sub_categories": {
            "Navigation_Mobile": mobile_sub_categories,
            "Mobile": mobile_sub_categories_all,
            "Tablets": tablets_sub_categories,
        },
        "Products": mobile_sub_categories_products,
    }
