from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import CustomUser
import os

@login_required
@require_http_methods(["GET"])
def get_all_users(request):
    """
    API endpoint to get all users for email notifications
    Only returns users who have opted in for notifications
    """
    try:
        # Get all active users with email
        users = CustomUser.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(email='').values('id', 'name', 'email')
        
        users_list = [
            {
                'name': user['name'],
                'email': user['email']
            }
            for user in users
        ]
        
        return JsonResponse({
            'success': True,
            'users': users_list,
            'count': len(users_list)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
