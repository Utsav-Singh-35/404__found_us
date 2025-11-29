from django.urls import path, include
from . import views
from . import chat_views
from . import api_views
from . import trending_views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('trending/', trending_views.trending_view, name='trending'),
    
    # Chat API routes (must come before chat view routes)
    path('chat/api/conversations/create/', chat_views.create_conversation, name='create_conversation'),
    path('chat/api/conversations/', chat_views.get_conversations, name='get_conversations'),
    path('chat/api/conversations/<str:conversation_id>/update/', chat_views.update_conversation, name='update_conversation'),
    path('chat/api/conversations/<str:conversation_id>/delete/', chat_views.delete_conversation, name='delete_conversation'),
    path('chat/api/<str:conversation_id>/messages/send/', chat_views.send_message, name='send_message'),
    path('chat/api/<str:conversation_id>/messages/', chat_views.get_messages, name='get_messages'),
    path('chat/api/<str:conversation_id>/history/', chat_views.get_conversation_history, name='get_conversation_history'),
    path('chat/api/messages/<str:message_id>/delete/', chat_views.delete_message, name='delete_message'),
    path('chat/api/messages/<str:message_id>/publish/', chat_views.publish_fact_check, name='publish_fact_check'),
    
    # Chat view routes (must come after API routes)
    path('chat/', chat_views.chat_view, name='chat'),
    path('chat/<str:conversation_id>/', chat_views.chat_view, name='chat_conversation'),
    
    # API routes
    path('api/users/all/', api_views.get_all_users, name='get_all_users'),
    
    # Trending news API routes
    path('trending/api/news/', trending_views.get_trending_news, name='get_trending_news'),
    path('trending/api/news/<str:news_id>/vote/', trending_views.vote_news, name='vote_news'),
    path('trending/api/news/<str:news_id>/view/', trending_views.view_news, name='view_news'),
    path('trending/api/statistics/', trending_views.get_news_statistics, name='get_news_statistics'),
    path('trending/api/categories/', trending_views.get_categories, name='get_categories'),
]
