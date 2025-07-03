from django.urls import path
from .views import user_details,UserAddressView

urlpatterns = [
    path("role/",user_details,name = "role"),
    path('address/', UserAddressView.as_view(), name='user-address'),
]
