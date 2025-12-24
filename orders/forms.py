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
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Phone Number'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-fill with user data if available
        if user and user.is_authenticated:
            self.fields['full_name'].initial = f"{user.first_name} {user.last_name}".strip()
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone_number or ''
    def save(self):
        """Save the order instance"""
        order = super().save(commit=False)
        # Additional processing can be done here
        order.save()
        return order
