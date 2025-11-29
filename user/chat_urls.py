from django.urls import path
from . import chat_views

urlpatterns = [
    # Chat interface
    path('', chat_views.chat_view, name='chat'),
    path('<str:conversation_id>/', chat_views.chat_view, name='chat_conversation'),
    
    # Conversation management
    path('api/conversations/', chat_views.get_conversations, name='get_conversations'),
    path('api/conversations/create/', chat_views.create_conversation, name='create_conversation'),
    path('api/conversations/<str:conversation_id>/update/', chat_views.update_conversation, name='update_conversation'),
    path('api/conversations/<str:conversation_id>/delete/', chat_views.delete_conversation, name='delete_conversation'),
    
    # Message management
    path('api/<str:conversation_id>/messages/', chat_views.get_messages, name='get_messages'),
    path('api/<str:conversation_id>/messages/send/', chat_views.send_message, name='send_message'),
    path('api/<str:conversation_id>/history/', chat_views.get_conversation_history, name='get_conversation_history'),
    path('api/messages/<str:message_id>/delete/', chat_views.delete_message, name='delete_message'),
    path('api/messages/<str:message_id>/publish/', chat_views.publish_fact_check, name='publish_fact_check'),
]
