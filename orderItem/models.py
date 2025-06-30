from django.db import models
from api.models import CustomUser as User
from product.models import Product


ORDER_STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Processing', 'Processing'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending')
    ordered_at = models.DateTimeField(auto_now_add=True)

    # 🔽 Payment-related fields
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    payment_intent_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=50, null=True, blank=True)
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.email} - {self.status}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=5)
    quantity = models.PositiveIntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)  # store price at order time

    def __str__(self):
        return f"{self.product.name} ({self.size}) x {self.quantity} in Order #{self.order.id}"
