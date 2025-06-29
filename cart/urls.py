from django.urls import path
from .views import CartDetailView, CartItemCreateView, CartItemUpdateDeleteView

urlpatterns = [
    path('cart/', CartDetailView.as_view(), name='cart-detail'),
    path('cart/items/', CartItemCreateView.as_view(), name='cartitem-create'),
    path('cart/items/<int:pk>/', CartItemUpdateDeleteView.as_view(), name='cartitem-update-delete'),
]