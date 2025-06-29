from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser

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