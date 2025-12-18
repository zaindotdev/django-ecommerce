# E-Commerce Django Application

A full-featured e-commerce web application built with Django, featuring product management, shopping cart, checkout with Stripe integration, user authentication, and email notifications.

## Features

### Store App
- Product catalog with categories
- Product search functionality
- Product detail pages with images
- Product reviews and ratings
- Related products suggestions
- Category filtering and sorting

### Orders App
- Shopping cart functionality
- Multi-step checkout process
- Stripe payment integration
- Order management
- Email order confirmations
- Order history for users

### Accounts App
- User registration and authentication
- User profile management
- Avatar upload
- Order history
- Contact form with email
- About Us and FAQ pages

## Tech Stack

- **Backend**: Django 5.0+
- **Database**: SQLite (development), PostgreSQL ready
- **Payment**: Stripe
- **Email**: SMTP (Gmail, SendGrid, etc.)
- **Image Processing**: Pillow
- **Environment Variables**: python-dotenv

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd ecommerce
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Update the `.env` file with your credentials:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email Settings (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Stripe Settings
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Site Settings
SITE_NAME=E-Commerce Store
SITE_URL=http://localhost:8000
```

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create superuser
```bash
python manage.py createsuperuser
```

### 7. Run the development server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to view the site.

## Configuration

### Email Setup (Gmail)

1. Enable 2-Factor Authentication in your Google account
2. Generate an App Password: Google Account → Security → 2-Step Verification → App passwords
3. Use the generated password in `EMAIL_HOST_PASSWORD`

### Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Dashboard
3. Add your test keys to the `.env` file
4. For webhooks:
   - Install Stripe CLI: https://stripe.com/docs/stripe-cli
   - Run: `stripe listen --forward-to localhost:8000/orders/webhook/stripe/`
   - Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET`

## Usage

### Admin Panel

Access the admin panel at `http://localhost:8000/admin/` to:
- Manage products and categories
- View and update orders
- Manage users
- Approve product reviews

### Adding Products

1. Log in to the admin panel
2. Navigate to Store → Products
3. Click "Add Product"
4. Fill in product details:
   - Name, description, price
   - Category
   - Stock quantity
   - Product image
   - Mark as featured (optional)

### Testing Stripe Payments

Use Stripe test cards:
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Any future expiry date and any 3-digit CVC

## Project Structure

```
ecommerce/
├── accounts/           # User authentication & profiles
│   ├── models.py      # Account model
│   ├── forms.py       # Registration, login, profile forms
│   ├── views.py       # Auth views
│   └── urls.py        # Account URLs
├── store/             # Product catalog
│   ├── models.py      # Product, Category, Review models
│   ├── views.py       # Product listing, detail, search
│   ├── urls.py        # Store URLs
│   └── admin.py       # Admin configuration
├── orders/            # Shopping cart & orders
│   ├── models.py      # Order, Cart, OrderItem models
│   ├── views.py       # Cart, checkout, payment views
│   ├── forms.py       # Checkout form
│   ├── urls.py        # Order URLs
│   └── admin.py       # Order admin
├── ecommerce/         # Project settings
│   ├── settings.py    # Django settings
│   ├── urls.py        # Main URL configuration
│   └── wsgi.py        # WSGI configuration
├── templates/         # HTML templates
├── media/             # User uploaded files
├── staticfiles/       # Collected static files
├── .env               # Environment variables
├── manage.py          # Django management script
└── requirements.txt   # Python dependencies
```

## API Endpoints

### Store
- `/` - Homepage
- `/products/` - Product listing
- `/product/<slug>/` - Product detail
- `/category/<slug>/` - Category products
- `/search/` - Search products

### Accounts
- `/accounts/register/` - User registration
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/my-account/` - User profile & orders
- `/accounts/contact/` - Contact form
- `/accounts/about/` - About page
- `/accounts/faq/` - FAQ page

### Orders
- `/orders/cart/` - Shopping cart
- `/orders/add-to-cart/<id>/` - Add item to cart
- `/orders/checkout/info/` - Checkout shipping info
- `/orders/checkout/payment/` - Checkout payment
- `/orders/checkout/complete/` - Order confirmation
- `/orders/order/<id>/` - Order detail

## Deployment

### Heroku Deployment

1. Install Heroku CLI
2. Create Heroku app: `heroku create your-app-name`
3. Add PostgreSQL: `heroku addons:create heroku-postgresql:mini`
4. Set environment variables:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set DEBUG=False
   heroku config:set STRIPE_PUBLIC_KEY=pk_live_...
   heroku config:set STRIPE_SECRET_KEY=sk_live_...
   ```
5. Deploy: `git push heroku main`
6. Run migrations: `heroku run python manage.py migrate`
7. Create superuser: `heroku run python manage.py createsuperuser`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License.

## Support

For support, email support@example.com or open an issue in the repository.
