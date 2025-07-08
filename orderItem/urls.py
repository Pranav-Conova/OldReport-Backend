from django.urls import path
from .views import CreateOrderView, VerifyPaymentView
from .views import allOrdersView, OrderListView  # Assuming this is for listing all orders
urlpatterns = [
    path('create-order/', CreateOrderView.as_view()),
    path('verify-payment/', VerifyPaymentView.as_view()),
    path('order-list/', OrderListView.as_view()),
    path('all-orders/', allOrdersView.as_view()),  # Assuming this is for listing all orders
    path('all-orders/<int:order_id>/', allOrdersView.as_view()),
]
