from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from .models import Product, Category, Review, SubCategory


def home_view(request):
    """Homepage view"""
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': categories,
    }
    return render(request, 'index.html', context)


def product_list_view(request):
    """Product listing with filters"""
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['price', '-price', 'name', '-created_at']:
        products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'categories': categories,
    }
    return render(request, 'store/product.html', context)


def product_detail_view(request, slug):
    """Product detail view"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = Review.objects.filter(product=product).order_by('-created_at')
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    product_images = product.images.all()
    main_image_url = product_images[0].image.url if product_images else None

    # Prepare description_sections for the tab content
    descriptions = product.descriptions.all()
    description_sections = []
    for idx, desc in enumerate(descriptions):
        description_sections.append({
            'image': desc.image.url if desc.image else '',
            'title': desc.title,
            'content': desc.content,
            'is_right': idx % 2 == 1,  # alternate left/right
        })

    context = {
        'product': product,
        'reviews': reviews,
        'average_rating': average_rating,
        'product_images': product_images,
        'main_image_url': main_image_url,
        'description_sections': description_sections,
    }
    return render(request, 'store/product_detail.html', context)


def category_view(request, slug):
    """Category page view"""
    category = None
    subcategory = None
    
    # Try to find category first
    try:
        category = Category.objects.get(slug=slug, is_active=True)
        products = Product.objects.filter(category=category, is_active=True)
    except Category.DoesNotExist:
        # If not a category, try subcategory
        subcategory = get_object_or_404(SubCategory, slug=slug, is_active=True)
        products = Product.objects.filter(subcategory=subcategory, is_active=True)
    
    # Search/Filter by keywords
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['price', '-price', 'name', '-created_at']:
        products = products.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for sidebar
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'categories': categories,
        'page_obj': page_obj,
        'products': page_obj,
    }
    return render(request, 'store/product.html', context)


@login_required
def add_review(request, product_id):
    """Add product review"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title')
        comment = request.POST.get('comment')
        
        if rating and title and comment:
            try:
                Review.objects.create(
                    product=product,
                    user=request.user,
                    rating=int(rating),
                    title=title,
                    comment=comment
                )
                messages.success(request, 'Thank you for your review! It will be published after approval.')
            except:
                messages.error(request, 'You have already reviewed this product.')
        else:
            messages.error(request, 'Please fill in all fields.')
    
    return redirect('store:product_detail', slug=product.slug)


def search_view(request):
    """Search products"""
    query = request.GET.get('q', '').strip()
    products = Product.objects.none()
    print(f"Search query: {query}")
    
    if query:
        # Search in product name, description, and category
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(specifications__icontains=query) |
            Q(category__name__icontains=query) |
            Q(subcategory__name__icontains=query),
            is_active=True
        ).distinct()
        
        print(f"Found {products.count()} products matching the query.")
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    print(f"Displaying page {page_obj.number} of {paginator.num_pages}.")
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'store/search_results.html', context)
