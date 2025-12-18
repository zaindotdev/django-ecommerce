#!/bin/bash

# E-Commerce Django Setup Script

echo "====================================="
echo "E-Commerce Django Setup"
echo "====================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please configure your .env file with proper credentials."
fi

# Create media directories
echo "Creating media directories..."
mkdir -p media/products
mkdir -p media/products/gallery
mkdir -p media/categories
mkdir -p media/avatars

# Run migrations
echo "Running migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations store
python manage.py makemigrations orders
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser prompt
echo ""
echo "====================================="
echo "Setup complete!"
echo "====================================="
echo ""
echo "Would you like to create a superuser? (y/n)"
read create_superuser

if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    python manage.py createsuperuser
fi

echo ""
echo "====================================="
echo "Next Steps:"
echo "====================================="
echo "1. Update .env file with your credentials"
echo "2. Run: python manage.py runserver"
echo "3. Visit: http://localhost:8000"
echo "4. Admin panel: http://localhost:8000/admin"
echo ""
echo "Happy coding!"
