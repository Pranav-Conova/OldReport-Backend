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
        # Prefetch related product to avoid N+1 when iterating items
        items_qs = cart.items.select_related("product_id").all()
        # Remove items for products that are not shown
        removed = False
        for item in list(items_qs):
            if not item.product_id.show:
                item.delete()
                removed = True

        # Refresh queryset after potential deletes
        items_qs = cart.items.select_related("product_id").all()

        # Check and update cart items if stock is less than cart quantity
        updated = False
        # Bulk fetch stocks for all (product, size) pairs to reduce queries
        wanted = [(item.product_id_id, item.size) for item in items_qs]
        if wanted:
            stocks = ProductStock.objects.filter(
                product_id__in={pid for pid, _ in wanted},
                size__in={s for _, s in wanted},
            )
            # Map (product_id, size) -> stock
            stock_map = {(s.product_id, s.size): s for s in stocks}
        else:
            stock_map = {}

        for item in items_qs:
            stock = stock_map.get((item.product_id_id, item.size))
            if not stock or item.quantity > stock.quantity:
                new_quantity = stock.quantity if stock else 0
                if item.quantity != new_quantity:
                    item.quantity = new_quantity
                    item.save(update_fields=["quantity"])
                    updated = True
        # Reload cart with prefetch to avoid N+1 in serializer
        cart_pref = (
            Cart.objects.filter(pk=cart.pk)
            .prefetch_related("items__product_id")
            .first()
        )
        serializer = CartSerializer(cart_pref or cart)
        response_data = serializer.data
        if updated:
            response_data["warning"] = (
                "Some cart items were updated due to limited stock."
            )
        if removed:
            response_data["removed"] = (
                "Some items were removed because the product is no longer available."
            )
        return Response(response_data)

    def post(self, request):
        cart = self.get_cart(request.user)
        product_id = request.data.get("product_id")
        size = request.data.get("size")
        quantity = int(request.data.get("quantity", 1))

        if not (product_id and size):
            return Response(
                {"error": "product_id and size are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product = get_object_or_404(Product, id=product_id)
        stock = ProductStock.objects.filter(product=product, size=size).first()

        if not stock or quantity > stock.quantity:
            available = stock.quantity if stock else 0
            return Response(
                {"error": f"Only {available} items available in size {size}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if same item already in cart → update quantity instead
        existing_item = (
            CartItem.objects.select_related("product_id")
            .filter(cart=cart, product_id=product, size=size)
            .first()
        )
        if existing_item:
            total_quantity = existing_item.quantity + quantity
            if total_quantity > stock.quantity:
                return Response(
                    {
                        "error": f"Only {stock.quantity} items available in total for size {size}."
                    },
                    status=400,
                )
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
        cart_item = get_object_or_404(
            CartItem.objects.select_related("product_id"),
            product_id=product_id,
            size=size,
            cart=cart,
        )
        stock = ProductStock.objects.filter(
            product=cart_item.product_id, size=cart_item.size
        ).first()

        if not stock or quantity > stock.quantity:
            available = stock.quantity if stock else 0
            return Response(
                {
                    "error": f"Only {available} items available in size {cart_item.size}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item.quantity = quantity
        cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    def delete(self, request):
        cart = self.get_cart(request.user)
        item_id = request.data.get("item_id")
        size = request.data.get("size")

        if not item_id:
            return Response(
                {"error": "item_id is required to delete a cart item."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cart_item = get_object_or_404(
            CartItem.objects.select_related("product_id"), id=item_id, cart=cart
        )
        cart_item.delete()
        return Response(
            {"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT
        )
