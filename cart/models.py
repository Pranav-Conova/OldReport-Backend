from django.db import models
from api.models import CustomUser as User  # Import your custom User model if you have one
from product.models import Product  # Import your Product model

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')

    def __str__(self):
        return f"Cart for {self.user.first_name}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5)  # Store selected size, e.g., "M", "L"
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product_id.name} ({self.size}) x {self.quantity} in {self.cart.user.email}'s cart"
