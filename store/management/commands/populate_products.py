from django.core.management.base import BaseCommand
from store.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with sample products'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample categories...')
        
        # Create categories
        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
            {'name': 'Computers', 'description': 'Laptops, desktops and accessories'},
            {'name': 'Smartphones', 'description': 'Mobile phones and tablets'},
            {'name': 'Accessories', 'description': 'Phone and computer accessories'},
            {'name': 'Audio', 'description': 'Headphones, speakers and audio equipment'},
            {'name': 'Gaming', 'description': 'Gaming consoles and accessories'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        
        self.stdout.write('Creating sample products...')
        
        # Create products
        products_data = [
            {
                'name': 'MacBook Pro 16"',
                'category': 'Computers',
                'description': 'Powerful laptop with M2 Pro chip, 16GB RAM, 512GB SSD',
                'price': Decimal('2499.00'),
                'compare_price': Decimal('2799.00'),
                'stock': 25,
                'is_featured': True,
            },
            {
                'name': 'iPhone 15 Pro',
                'category': 'Smartphones',
                'description': 'Latest iPhone with A17 Pro chip, 256GB storage, titanium design',
                'price': Decimal('1199.00'),
                'compare_price': Decimal('1299.00'),
                'stock': 50,
                'is_featured': True,
            },
            {
                'name': 'AirPods Pro 2',
                'category': 'Audio',
                'description': 'Active noise cancellation, spatial audio, USB-C charging',
                'price': Decimal('249.00'),
                'stock': 100,
                'is_featured': True,
            },
            {
                'name': 'iPad Air',
                'category': 'Smartphones',
                'description': '10.9-inch display, M1 chip, 64GB storage',
                'price': Decimal('599.00'),
                'compare_price': Decimal('649.00'),
                'stock': 40,
            },
            {
                'name': 'PlayStation 5',
                'category': 'Gaming',
                'description': 'Next-gen gaming console with 825GB SSD',
                'price': Decimal('499.00'),
                'stock': 15,
                'is_featured': True,
            },
            {
                'name': 'Samsung Galaxy S24',
                'category': 'Smartphones',
                'description': 'Flagship Android phone with 256GB storage',
                'price': Decimal('999.00'),
                'stock': 35,
            },
            {
                'name': 'Dell XPS 13',
                'category': 'Computers',
                'description': '13.4-inch laptop, Intel i7, 16GB RAM, 512GB SSD',
                'price': Decimal('1399.00'),
                'compare_price': Decimal('1599.00'),
                'stock': 20,
            },
            {
                'name': 'Sony WH-1000XM5',
                'category': 'Audio',
                'description': 'Premium noise cancelling headphones',
                'price': Decimal('399.00'),
                'stock': 60,
            },
            {
                'name': 'Magic Keyboard',
                'category': 'Accessories',
                'description': 'Wireless keyboard with Touch ID',
                'price': Decimal('149.00'),
                'stock': 80,
            },
            {
                'name': 'Logitech MX Master 3',
                'category': 'Accessories',
                'description': 'Advanced wireless mouse for productivity',
                'price': Decimal('99.00'),
                'compare_price': Decimal('119.00'),
                'stock': 75,
            },
        ]
        
        for prod_data in products_data:
            category_name = prod_data.pop('category')
            product, created = Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    **prod_data,
                    'category': categories[category_name]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database with sample data!'))
        self.stdout.write(self.style.WARNING('Note: Product images need to be added manually through the admin panel.'))
