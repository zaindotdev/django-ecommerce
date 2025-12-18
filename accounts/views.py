from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Account
from .forms import RegisterForm, LoginForm, ProfileUpdateForm, ContactForm
from orders.models import Order

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Send welcome email
            try:
                send_mail(
                    subject='Welcome to ' + settings.SITE_NAME,
                    message=f'Hi {user.first_name},\n\nThank you for registering at {settings.SITE_NAME}!\n\nBest regards,\nThe Team',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except:
                pass
            
            # Authenticate and login
            authenticated_user = authenticate(username=user.username, password=form.cleaned_data['password'])
            if authenticated_user:
                login(request, authenticated_user)
                messages.success(request, 'Registration successful! Welcome to our store.')
                return redirect('store:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('store:home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, 'Welcome back!')
            next_url = request.GET.get('next', 'store:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('store:home')


@login_required
def my_account_view(request):
    """User account dashboard"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('my_account')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'form': form,
        'orders': orders,
    }
    return render(request, 'my_account.html', context)


def contact_view(request):
    """Contact form view"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            # Send email
            try:
                send_mail(
                    subject=f'Contact Form: {subject}',
                    message=f'From: {name} ({email})\n\n{message}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
                return redirect('contact_us')
            except Exception as e:
                messages.error(request, 'An error occurred. Please try again later.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()
    
    return render(request, 'contact_us.html', {'form': form})


def about_us_view(request):
    """About us page"""
    return render(request, 'about_us.html')


def faq_view(request):
    """FAQ page"""
    return render(request, 'faq.html')
