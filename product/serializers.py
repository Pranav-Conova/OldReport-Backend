from rest_framework import serializers
from .models import Product, ProductStock, ProductImage

class ProductStockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStock
        fields = ['id', 'size', 'quantity']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']


class ProductSerializer(serializers.ModelSerializer):
    stock_details = ProductStockSerializer(many=True,required = False)
    images = ProductImageSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'category', 'subcategory',
            'bestseller', 'show',
            'stock_details', 'images'
        ]

    def create(self, validated_data):
        stock_data = validated_data.pop('stock_details',[])
        image_data = validated_data.pop('images', [])
        product = Product.objects.create(**validated_data)

        # Create stock entries
        for stock in stock_data:
            ProductStock.objects.create(product=product, **stock)

        # Create image entries
        for image in image_data:
            ProductImage.objects.create(product=product, **image)

        return product
