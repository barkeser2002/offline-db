from django.urls import path
from . import views

urlpatterns = [
    path('shopier/callback/', views.shopier_callback, name='shopier_callback'),
]
