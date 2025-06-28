from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.base_user import BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # remove username field
    email = models.EmailField(("email address"), unique=True)
    
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    
    USERNAME_FIELD = 'email'  # for authentication
    REQUIRED_FIELDS = []  # no required username
    
    objects = CustomUserManager()
    
    def __str__(self):
        return f"{self.email} ({self.role})"

class Movie(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField(null=True, blank=True)
    description = models.TextField()
    images = models.ImageField(upload_to='movies/', null=True, blank=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name
