from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ("Men", "Men"),
        ("Women", "Women"),
        ("Kids", "Kids"),
    ]

    SUBCATEGORY_CHOICES = [
        ("Topwear", "Topwear"),
        ("Bottomwear", "Bottomwear"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(max_length=20, choices=SUBCATEGORY_CHOICES)
    show = models.BooleanField(default=True)
    bestseller = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="product_images/")

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductStock(models.Model):
    SIZE_CHOICES = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
    ]

    product = models.ForeignKey(
        Product, related_name="stock_details", on_delete=models.CASCADE
    )
    size = models.CharField(max_length=2, choices=SIZE_CHOICES)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("product", "size")  # Prevent duplicate entries
        indexes = [
            models.Index(fields=["product", "size"]),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.size}: {self.quantity}"

    def delete(self, *args, **kwargs):
        # Remove product from all carts
        from cart.models import CartItem

        # CartItem.product_id points to Product, not ProductStock
        CartItem.objects.filter(product_id=self.product).delete()

        # Remove product from all orders
        from orderItem.models import OrderItem

        OrderItem.objects.filter(product=self.product).delete()

        super().delete(*args, **kwargs)
