from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from .models import Product, Category, Review, SubCategory, ProductImage


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
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]
    
    reviews = product.reviews.filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Get product images
    product_images = product.images.all()
    
    # Get main product image URL
    main_image_url = product.image.image.url if product.image else (product_images.first().image.url if product_images.exists() else None)
    
    # Parse product description into sections
    description_sections = []
    if product.description:
        # Normalize line endings (handle \r\n, \r, and \n)
        description = product.description.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split by double newlines to get sections
        sections = description.strip().split('\n\n')
        images_list = list(product_images)
        
        for i, section in enumerate(sections):
            if section.strip():
                lines = section.strip().split('\n', 1)
                title = lines[0].strip()
                content = lines[1].strip() if len(lines) > 1 else ''
                
                # Get corresponding image or use main product image
                if i < len(images_list):
                    image_url = images_list[i].image.url
                elif main_image_url:
                    image_url = main_image_url
                else:
                    image_url = None
                
                description_sections.append({
                    'title': title,
                    'content': content,
                    'image': image_url,
                    'is_right': i % 2 == 1  # Alternate between left and right
                })
    
    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'description_sections': description_sections,
        'product_images': product_images,
        'main_image_url': main_image_url,
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


def search_view(request):
    """Search products"""
    query = request.GET.get('q', '')
    products = Product.objects.none()
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True
        ).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
        'products': page_obj,
    }
    return render(request, 'search_results.html', context)


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
