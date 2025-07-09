from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from product.models import Product, ProductStock
from django.shortcuts import get_object_or_404


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def get(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        cart = self.get_cart(request.user)
        product_id = request.data.get("product_id")
        size = request.data.get("size")
        quantity = int(request.data.get("quantity", 1))

        if not (product_id and size):
            return Response({"error": "product_id and size are required."}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Product, id=product_id)
        stock = ProductStock.objects.filter(product=product, size=size).first()

        if not stock or quantity > stock.quantity:
            available = stock.quantity if stock else 0
            return Response({"error": f"Only {available} items available in size {size}."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if same item already in cart → update quantity instead
        existing_item = CartItem.objects.filter(cart=cart, product_id=product, size=size).first()
        if existing_item:
            total_quantity = existing_item.quantity + quantity
            if total_quantity > stock.quantity:
                return Response({"error": f"Only {stock.quantity} items available in total for size {size}."}, status=400)
            existing_item.quantity = total_quantity
            existing_item.save()
            serializer = CartItemSerializer(existing_item)
            return Response(serializer.data)

        # New cart item
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(cart=cart, product_id=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        cart = self.get_cart(request.user)
        size = request.data.get("size")
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))
        cart_item = get_object_or_404(CartItem, product_id=product_id, size =size, cart=cart)
        stock = ProductStock.objects.filter(product=cart_item.product_id, size=cart_item.size).first()

        if not stock or quantity > stock.quantity:
            available = stock.quantity if stock else 0
            return Response({"error": f"Only {available} items available in size {cart_item.size}."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = quantity
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

def delete(self, request):
        cart = self.get_cart(request.user)
        item_id = request.data.get("item_id")
        size = request.data.get("size")

        if not item_id:
            return Response({"error": "item_id is required to delete a cart item."}, status=status.HTTP_400_BAD_REQUEST)

        cart_item = get_object_or_404(CartItem, id=item_id, size=size, cart=cart)
        cart_item.delete()
        return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)