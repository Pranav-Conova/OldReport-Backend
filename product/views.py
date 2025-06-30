from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer
from api.permissions import IsManagerOrReadOnly
import json


class ProductListCreateView(APIView):
    # permission_classes = [IsManagerOrReadOnly]
    def get(self, request):
        products = Product.objects.prefetch_related('stock_details', 'images').all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    

    def post(self, request):
        data = request.data.copy()
        stock_details = data.get('stock_details')
        if isinstance(stock_details, str):
            try:
                data['stock_details'] = json.loads(stock_details)
            except Exception:
                return Response({"stock_details": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductDetailView(APIView):
    # permission_classes = [IsManagerOrReadOnly]

    def get(self, request, pk):
        try:
            product = Product.objects.prefetch_related('stock_details', 'images').get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product)
        return Response(serializer.data)
    
class ProductDeleteView(APIView):
    # permission_classes = [IsManagerOrReadOnly]
    def delete(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

        product.delete()
        return Response({"detail": "Product deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
