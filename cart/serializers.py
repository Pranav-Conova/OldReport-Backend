from rest_framework import serializers
from .models import Cart, CartItem
from product.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    # Use the actual FK field name to leverage select_related/prefetch_related properly
    product_name = serializers.ReadOnlyField(source="product_id.name")

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "product_name", "size", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "items"]
