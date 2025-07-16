from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer
from api.permissions import IsManagerOrReadOnly
import json
from.models import Product,ProductImage,ProductStock


class ProductListCreateView(APIView):
    permission_classes = [IsManagerOrReadOnly]
    def get(self, request):
        products = Product.objects.prefetch_related('stock_details', 'images').all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    

    def post(self, request):
        data = request.data  # ❌ avoid .copy()
        images = request.FILES.getlist('images')

        # Parse stock_details JSON
        try:
            stock_details = json.loads(data.get('stock_details', '[]'))
        except json.JSONDecodeError:
            return Response({"stock_details": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST)

        # Create Product
        product = Product.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            price=data.get('price'),
            category=data.get('category'),
            subcategory=data.get('subcategory'),
            bestseller=str(data.get('bestseller')).lower() == 'true'
        )

        # Create ProductStock entries
        for stock in stock_details:
            ProductStock.objects.create(
                product=product,
                size=stock['size'],
                quantity=stock['quantity']
            )

        # Create ProductImage entries
        for image in images:
            ProductImage.objects.create(
                product=product,
                image=image
            )

        return Response("created", status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsManagerOrReadOnly]

    def get(self, request, pk):
        try:
            product = Product.objects.prefetch_related('stock_details', 'images').get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product)
        return Response(serializer.data)
    
class ProductDeleteView(APIView):
    permission_classes = [IsManagerOrReadOnly]
    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        product.show = False
        product.save()
        return Response({"detail": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
