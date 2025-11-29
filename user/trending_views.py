from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .trending_model import TrendingNews
from .mongodb import mongodb
import json

@login_required
def trending_view(request):
    """Render the trending page"""
    return render(request, 'dashboards/trending.html', {'user': request.user})

@login_required
def get_trending_news(request):
    """API endpoint to get trending news"""
    try:
        limit = int(request.GET.get('limit', 50))
        skip = int(request.GET.get('skip', 0))
        category = request.GET.get('category', None)
        
        if not mongodb.is_connected():
            return JsonResponse({
                'error': 'MongoDB not connected'
            }, status=500)
        
        news_items = TrendingNews.get_trending_news(limit=limit, skip=skip, category=category)
        
        # Convert ObjectId to string
        news_list = []
        for item in news_items:
            news_list.append({
                'id': str(item['_id']),
                'title': item['title'],
                'content': item.get('content', ''),
                'author': item['author'],
                'category': item['category'],
                'source_url': item.get('source_url'),
                'image_url': item.get('image_url'),
                'likes': item.get('likes', 0),
                'dislikes': item.get('dislikes', 0),
                'views': item.get('views', 0),
                'is_fact_checked': item.get('is_fact_checked', False),
                'fact_check_status': item.get('fact_check_status'),
                'created_at': item['created_at'].isoformat(),
                'time_ago': get_time_ago(item['created_at'])
            })
        
        return JsonResponse({
            'success': True,
            'news': news_list
        })
    
    except Exception as e:
        print(f"Error getting trending news: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def vote_news(request, news_id):
    """API endpoint to vote on news (like/dislike)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        vote_type = data.get('vote_type')  # 'like' or 'dislike'
        
        if vote_type not in ['like', 'dislike']:
            return JsonResponse({'error': 'Invalid vote type'}, status=400)
        
        success = TrendingNews.update_vote(news_id, vote_type)
        
        if success:
            # Get updated counts
            news = TrendingNews.get_news_by_id(news_id)
            return JsonResponse({
                'success': True,
                'likes': news.get('likes', 0),
                'dislikes': news.get('dislikes', 0)
            })
        else:
            return JsonResponse({'error': 'Failed to update vote'}, status=500)
    
    except Exception as e:
        print(f"Error voting on news: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def view_news(request, news_id):
    """API endpoint to increment view count"""
    try:
        TrendingNews.increment_views(news_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_news_statistics(request):
    """API endpoint to get trending news statistics"""
    try:
        stats = TrendingNews.get_statistics()
        return JsonResponse({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_categories(request):
    """API endpoint to get all news categories"""
    try:
        categories = TrendingNews.get_categories()
        return JsonResponse({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_time_ago(dt):
    """Convert datetime to human-readable time ago"""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes}m ago' if minutes > 1 else '1m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours}h ago' if hours > 1 else '1h ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days}d ago' if days > 1 else '1d ago'
    else:
        weeks = int(seconds / 604800)
        return f'{weeks}w ago' if weeks > 1 else '1w ago'
