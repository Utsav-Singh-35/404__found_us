from django.urls import path, include
from . import views
from . import chat_views
from . import api_views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('trending/', views.trending_view, name='trending'),
    
    # Chat API routes (must come before chat view routes)
    path('chat/api/conversations/create/', chat_views.create_conversation, name='create_conversation'),
    path('chat/api/conversations/', chat_views.get_conversations, name='get_conversations'),
    path('chat/api/conversations/<str:conversation_id>/update/', chat_views.update_conversation, name='update_conversation'),
    path('chat/api/conversations/<str:conversation_id>/delete/', chat_views.delete_conversation, name='delete_conversation'),
    path('chat/api/<str:conversation_id>/messages/send/', chat_views.send_message, name='send_message'),
    path('chat/api/<str:conversation_id>/messages/', chat_views.get_messages, name='get_messages'),
    path('chat/api/<str:conversation_id>/history/', chat_views.get_conversation_history, name='get_conversation_history'),
    path('chat/api/messages/<str:message_id>/delete/', chat_views.delete_message, name='delete_message'),
    
    # Chat view routes (must come after API routes)
    path('chat/', chat_views.chat_view, name='chat'),
    path('chat/<str:conversation_id>/', chat_views.chat_view, name='chat_conversation'),
    
    # API routes
    path('api/users/all/', api_views.get_all_users, name='get_all_users'),
]
