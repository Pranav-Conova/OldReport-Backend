from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer
from api.permissions import IsManagerOrReadOnly
import json
from .models import Product, ProductImage, ProductStock
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
import io
import os


class ProductListCreateView(APIView):
    permission_classes = [IsManagerOrReadOnly]

    def get(self, request):
        products = Product.objects.filter(show=True).prefetch_related(
            "stock_details", "images"
        )
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data  # ❌ avoid .copy()
        images = request.FILES.getlist("images")

        # Parse stock_details JSON
        try:
            stock_details = json.loads(data.get("stock_details", "[]"))
        except json.JSONDecodeError:
            return Response(
                {"stock_details": "Invalid JSON."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create Product
        product = Product.objects.create(
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            category=data.get("category"),
            subcategory=data.get("subcategory"),
            bestseller=str(data.get("bestseller")).lower() == "true",
        )

        # Create ProductStock entries
        for stock in stock_details:
            ProductStock.objects.create(
                product=product, size=stock["size"], quantity=stock["quantity"]
            )

        # Create ProductImage entries with WebP conversion
        for image in images:
            webp_image = self.convert_to_webp(image)
            ProductImage.objects.create(product=product, image=image)

        return Response("created", status=status.HTTP_201_CREATED)

    def convert_to_webp(self, image_file):
        # Open the image
        img = Image.open(image_file)
        
        # Apply EXIF orientation (works for HEIC and all formats)
        img = ImageOps.exif_transpose(img)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Save as WebP
        img.save(buffer, format='WEBP', quality=85, optimize=True)
        buffer.seek(0)
        
        # Generate new filename
        original_name = os.path.splitext(image_file.name)[0]
        webp_filename = f"{original_name}.webp"
        
        return ContentFile(buffer.getvalue(), name=webp_filename)


class ProductDetailView(APIView):
    permission_classes = [IsManagerOrReadOnly]

    def get(self, request, pk):
        try:
            product = Product.objects.prefetch_related("stock_details", "images").get(
                pk=pk
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(product)
        return Response(serializer.data)


class ProductDeleteView(APIView):
    permission_classes = [IsManagerOrReadOnly]

    def delete(self, request, pk):
        try:
            product = Product.objects.only("id", "show").get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND
            )

        product.show = False
        product.save()
        return Response(
            {"detail": "Product deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
