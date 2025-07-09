from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.conf import settings
import razorpay
import hmac
import hashlib
from .models import Order, OrderItem
from cart.models import Cart, CartItem
from api.models import Address
from api.permissions import IsManagerOrReadOnly
from . import permissions as p
from api.models import Address
from django.core.exceptions import ObjectDoesNotExist

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        try:
            address = Address.objects.get(user=user)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found for user."}, status=404)
        amount = request.data.get("amount")
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        total_amount = sum(item.product_id.price * item.quantity for item in cart_items)
        print(f"Total amount calculated: {total_amount}")
        if not amount or int(amount) != int(total_amount):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        order = client.order.create({
            "amount": int(amount) * 100,
            "currency": "INR",
            "payment_capture": 1
        })

        return Response({
            "order_id": order["id"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "amount": order["amount"]
        })


class VerifyPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")

        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature == signature:
            user = request.user
            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            address = Address.objects.get(user=user)

            # Calculate total amount
            total_amount = sum(item.product_id.price * item.quantity for item in cart_items)

            # Create Order
            order = Order.objects.create(
                user=user,
                address=address,
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id,
                razorpay_signature=signature,
                total_amount=int(total_amount * 100),  # Assuming price is in INR, convert to paisa
                payment_status='paid'
            )

            # Create OrderItems
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product_id,
                    size=item.size,
                    quantity=item.quantity,
                    price=int(item.product_id.price * 100)  # Store price at time of order in paisa
                )

            # Clear the cart
            cart_items.delete()

            return Response({"status": "Payment verified, order created"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
    
class OrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        orders = Order.objects.filter(user=user)
        order_data = []
        for order in orders:
            order_data.append({
                "id": order.id,
                "total_amount": order.total_amount,
                "delivery_status": order.delivery_status,
                "created_at": order.created_at,
                "items": [
                    {
                        "product": item.product.name,
                        "size": item.size,
                        "quantity": item.quantity,
                        "price": item.price
                    } for item in order.items.all()
                ]
            })
        return Response(order_data, status=status.HTTP_200_OK)

class allOrdersView(APIView):
    permission_classes = [p.IsManager]

    def get(self, request):
        orders = Order.objects.all()
        order_data = []
        for order in orders:
            order_data.append({
                "id": order.id,
                "user": order.user.email,
                "total_amount": order.total_amount,
                "delivery_status": order.delivery_status,
                "created_at": order.created_at,
                "items": [
                    {
                        "product": item.product.name,
                        "size": item.size,
                        "quantity": item.quantity,
                        "price": item.price
                    } for item in order.items.all()
                ]
            })
        return Response(order_data, status=status.HTTP_200_OK)
    
    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        delivery_status = request.data.get("delivery_status")
        if delivery_status not in dict(Order.DELIVERY_STATUS_CHOICES).keys():
            return Response({"error": "Invalid delivery status"}, status=status.HTTP_400_BAD_REQUEST)

        order.delivery_status = delivery_status
        order.save()

        return Response({"status": "Delivery status updated successfully"}, status=status.HTTP_200_OK)

