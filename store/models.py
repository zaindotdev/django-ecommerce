from django.db import models
from django.utils.text import slugify
from django.urls import reverse
import uuid


class Category(models.Model):
    """Product categories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('store:category', kwargs={'slug': self.slug})


class SubCategory(models.Model):
    """Product sub-categories"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subcategories'
        verbose_name = 'SubCategory'
        verbose_name_plural = 'SubCategories'
        ordering = ['name']
        unique_together = ('category', 'name')
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('store:subcategory', kwargs={'slug': self.slug})

class Product(models.Model):
    """Product model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text='Product SKU/Code')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, related_name='products', 
                                    blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, help_text='Product brand/manufacturer')
    description = models.ForeignKey('ProductDescription', on_delete=models.SET_NULL, related_name='+',
                                    blank=True, null=True)
    specifications = models.TextField(blank=True, help_text='Product specifications (bullet points)')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                       help_text='Original price for showing discounts')
    stock = models.IntegerField(default=0)
    availability_status = models.CharField(max_length=50, default='In Stock', help_text='Stock availability status')
    warranty = models.CharField(max_length=255, blank=True, help_text='Warranty information (e.g., 1 Year Local Manufacturer Warranty)')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            total = sum(review.rating for review in reviews)
            return round(total / reviews.count(), 1)
        return 0
    
    @property
    def review_count(self):
        """Get total count of approved reviews"""
        return self.reviews.filter(is_approved=True).count()
    
class ProductDescription(models.Model):
    """Detailed product description"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='descriptions')
    image = models.ImageField(upload_to='products/descriptions/', blank=True, null=True)
    title = models.CharField(max_length=255, blank=True)
    content = models.TextField(help_text='Detailed HTML description of the product')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_descriptions'
        verbose_name = 'Product Description'
        verbose_name_plural = 'Product Descriptions'
    
    def __str__(self):
        return f"Product Description {self.id}"


class ProductImage(models.Model):
    """Additional product images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_thumbnail = models.BooleanField(default=False, help_text='Display in thumbnail gallery')
    display_order = models.IntegerField(default=0, help_text='Order in which images are displayed')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['display_order', 'created_at']
    
    def __str__(self):
        return f"{self.product.name} - Image"


class Review(models.Model):
    """Product reviews"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.Account', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=255)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    is_verified_purchase = models.BooleanField(default=False, help_text='User purchased this product')
    helpful_count = models.IntegerField(default=0, help_text='Number of users who found this helpful')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        unique_together = ('product', 'user')
    
    def __str__(self):
        return f"{self.product.name} - {self.user.username} - {self.rating} stars"


class ProductVariants(models.Model):
    """Product variants like size, color"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    variant_type = models.CharField(max_length=100, help_text='Type of variant (e.g., Size, Color)')
    variant_value = models.CharField(max_length=100, help_text='Value of the variant (e.g., Red, Large)')
    additional_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                           help_text='Additional price for this variant')
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        unique_together = ('product', 'variant_type', 'variant_value')
    
    def __str__(self):
        return f"{self.product.name} - {self.variant_type}: {self.variant_value}"
    
class ProductAdditionalInfo(models.Model):
    """Additional information about the product"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='additional_info')
    variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE, related_name='additional_info',
                                blank=True, null=True)
    key = models.CharField(max_length=255, help_text='Information key (e.g., Material, Dimensions)')
    value = models.TextField(max_length=2200, help_text='Information value (e.g., Cotton, 10x5x2 inches)')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_additional_info'
        verbose_name = 'Product Additional Info'
        verbose_name_plural = 'Product Additional Info'
    
    def __str__(self):
        return f"{self.product.name} - {self.key}"