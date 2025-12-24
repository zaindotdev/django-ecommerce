from django import forms
from django.contrib.auth import authenticate
from .models import Account
from django.core.exceptions import ValidationError

class RegisterForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'johndoe', 'class': 'form-control'}),
        max_length=150
    )
    full_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'John Doe', 'class': 'form-control'}),
        max_length=255
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'johndoe@mail.com', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': "********", 'class': 'form-control'}),
        min_length=8
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': "********", 'class': 'form-control'}),
        label='Confirm Password'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Account.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self):
        full_name = self.cleaned_data['full_name']
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        
        # Split full name into first and last name
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create user account
        account = Account.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        return account


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        
        if username and password:
            try:
                user = Account.objects.get(username=username)
                user = authenticate(username=user.username, password=password)
                if user is None:
                    raise ValidationError('Invalid username or password.')
                cleaned_data['user'] = user
            except Account.DoesNotExist:
                raise ValidationError('Invalid username or password.')
        
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Account
        fields = ['full_name', 'phone_number', 'avatar']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['full_name'].initial = f"{self.instance.first_name} {self.instance.last_name}".strip()
    
    def save(self, commit=True):
        account = super().save(commit=False)
        full_name = self.cleaned_data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        account.first_name = name_parts[0]
        account.last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if commit:
            account.save()
        return account


class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Your Name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Your Email', 'class': 'form-control'})
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Subject', 'class': 'form-control'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Your Message', 'class': 'form-control', 'rows': 5})
    )
    
    
    
    
    