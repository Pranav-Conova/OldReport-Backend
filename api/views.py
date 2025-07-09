from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser
from rest_framework.views import APIView
from rest_framework import status, permissions
from .models import Address
from .serializers import AddressSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_details(request):
    user = CustomUser.objects.get(id=request.user.id)
    # Assuming 'role' is a field on your CustomUser model
    return Response({
        'username': user.username,
        'email': user.email,
        'role': user.role,
    })
    
class UserAddressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            address = request.user.address
            serializer = AddressSerializer(address)
            return Response(serializer.data)
        except Address.DoesNotExist:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            address = request.user.address
            # If address exists, update it
            serializer = AddressSerializer(address, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Address.DoesNotExist:
            # If address does not exist, create it
            serializer = AddressSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)