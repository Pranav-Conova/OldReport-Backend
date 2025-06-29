from django.urls import path
from .views import user_details

urlpatterns = [
    path("role/",user_details,name = "role"),
]
