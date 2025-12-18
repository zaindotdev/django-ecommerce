from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-account/', views.my_account_view, name='my_account'),
    path('contact/', views.contact_view, name='contact_us'),
    path('about/', views.about_us_view, name='about_us'),
    path('faq/', views.faq_view, name='faq'),
]
