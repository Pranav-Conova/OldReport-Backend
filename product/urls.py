from django.urls import path
from .views import ProductListCreateView, ProductDeleteView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('products/', ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', ProductDeleteView.as_view(), name='product-delete'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)