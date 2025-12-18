from django.shortcuts import render, redirect

def home_view(request):
    """Redirect to home page"""
    return redirect('store:home')