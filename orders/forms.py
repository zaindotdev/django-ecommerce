from django import forms
from .models import Order


class CheckoutForm(forms.ModelForm):
    """Checkout form for shipping information"""
    
    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone',
            'address', 'city', 'state', 'postal_code', 'country'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'John Doe'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'johndoe@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 234 567 8900'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '123 Main Street'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New York'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NY'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10001'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'United States'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill with user data if available
        if user and user.is_authenticated:
            self.fields['full_name'].initial = f"{user.first_name} {user.last_name}".strip()
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone_number or ''
