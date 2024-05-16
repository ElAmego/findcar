from django.urls import path

from .views import *

urlpatterns = [
    path('', index, name='home'),
    path('ads', table, name='table'),
    path('featured', featured, name='featured'),
    path('register/', RegisterForm.as_view(), name='register'),
    path('car/<slug:car_slug>', car_detail, name='car_detail'),
    path('login/', LoginForm.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
]