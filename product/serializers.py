from rest_framework import serializers
from .models import Product, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    image_files = serializers.ListField(
        child=serializers.ImageField(), write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price',
            'category', 'subcategory', 'sizes', 'bestseller', 'images', 'image_files'
        ]

    def create(self, validated_data):
        image_files = validated_data.pop('image_files', [])
        product = Product.objects.create(**validated_data)
        for image in image_files:
            ProductImage.objects.create(product=product, image=image)
        return product

    def update(self, instance, validated_data):
        image_files = validated_data.pop('image_files', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for image in image_files:
            ProductImage.objects.create(product=instance, image=image)

        return instance
