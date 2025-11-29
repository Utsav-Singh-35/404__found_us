from datetime import datetime
from bson import ObjectId
from .mongodb import mongodb

class TrendingNews:
    """Model for managing trending news items"""
    
    @staticmethod
    def create_news(title, content, author, category, source_url=None, image_url=None, metadata=None):
        """Create a new trending news item"""
        if not mongodb.is_connected():
            return None
        
        news = {
            'title': title,
            'content': content,
            'author': author,
            'category': category,
            'source_url': source_url,
            'image_url': image_url,
            'likes': 0,
            'dislikes': 0,
            'views': 0,
            'is_fact_checked': False,
            'fact_check_status': None,  # 'verified', 'false', 'misleading', 'unverified'
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = mongodb.db.trending_news.insert_one(news)
            news['_id'] = result.inserted_id
            return news
        except Exception as e:
            print(f"Error creating trending news: {e}")
            return None
    
    @staticmethod
    def get_trending_news(limit=50, skip=0, category=None):
        """Get trending news sorted by engagement (likes + views)"""
        if not mongodb.is_connected():
            return []
        
        query = {}
        if category:
            query['category'] = category
        
        # Get news and sort by engagement score
        news_items = mongodb.db.trending_news.find(query).skip(skip).limit(limit)
        news_list = list(news_items)
        
        # Calculate engagement score and sort
        for item in news_list:
            engagement = (item.get('likes', 0) * 2) + item.get('views', 0) - (item.get('dislikes', 0) * 0.5)
            item['engagement_score'] = engagement
        
        news_list.sort(key=lambda x: x.get('engagement_score', 0), reverse=True)
        return news_list
    
    @staticmethod
    def get_news_by_id(news_id):
        """Get a specific news item"""
        if not mongodb.is_connected():
            return None
        
        return mongodb.db.trending_news.find_one({'_id': ObjectId(news_id)})
    
    @staticmethod
    def increment_views(news_id):
        """Increment view count"""
        if not mongodb.is_connected():
            return False
        
        result = mongodb.db.trending_news.update_one(
            {'_id': ObjectId(news_id)},
            {'$inc': {'views': 1}, '$set': {'updated_at': datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def update_vote(news_id, vote_type):
        """Update like or dislike count"""
        if not mongodb.is_connected():
            return False
        
        if vote_type not in ['like', 'dislike']:
            return False
        
        field = 'likes' if vote_type == 'like' else 'dislikes'
        result = mongodb.db.trending_news.update_one(
            {'_id': ObjectId(news_id)},
            {'$inc': {field: 1}, '$set': {'updated_at': datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def mark_as_fact_checked(news_id, status, fact_check_content=None):
        """Mark news as fact-checked with status"""
        if not mongodb.is_connected():
            return False
        
        update_data = {
            'is_fact_checked': True,
            'fact_check_status': status,
            'updated_at': datetime.utcnow()
        }
        
        if fact_check_content:
            update_data['fact_check_content'] = fact_check_content
        
        result = mongodb.db.trending_news.update_one(
            {'_id': ObjectId(news_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def delete_news(news_id):
        """Delete a news item"""
        if not mongodb.is_connected():
            return False
        
        result = mongodb.db.trending_news.delete_one({'_id': ObjectId(news_id)})
        return result.deleted_count > 0
    
    @staticmethod
    def create_from_fact_check(message_id, user_query, fact_check_result):
        """Create trending news from a published fact-check"""
        if not mongodb.is_connected():
            return None
        
        # Extract confidence from fact-check result
        confidence = 0
        if '🟢' in fact_check_result:
            confidence = 80
        elif '🟡' in fact_check_result:
            confidence = 50
        elif '🔴' in fact_check_result:
            confidence = 20
        
        # Determine status
        if confidence >= 70:
            status = 'verified'
        elif confidence >= 40:
            status = 'unverified'
        else:
            status = 'false'
        
        news = {
            'title': user_query[:100],
            'content': fact_check_result,
            'author': 'SatyaMatrix AI',
            'category': 'Fact-Check',
            'source_url': None,
            'image_url': None,
            'likes': 0,
            'dislikes': 0,
            'views': 0,
            'is_fact_checked': True,
            'fact_check_status': status,
            'fact_check_message_id': str(message_id),
            'metadata': {'confidence': confidence},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = mongodb.db.trending_news.insert_one(news)
            news['_id'] = result.inserted_id
            print(f"✅ Created trending news from fact-check: {result.inserted_id}")
            return news
        except Exception as e:
            print(f"❌ Error creating trending news from fact-check: {e}")
            return None
    
    @staticmethod
    def get_categories():
        """Get all unique categories"""
        if not mongodb.is_connected():
            return []
        
        return mongodb.db.trending_news.distinct('category')
    
    @staticmethod
    def get_statistics():
        """Get trending news statistics"""
        if not mongodb.is_connected():
            return {}
        
        total = mongodb.db.trending_news.count_documents({})
        fact_checked = mongodb.db.trending_news.count_documents({'is_fact_checked': True})
        
        # Get category breakdown
        pipeline = [
            {'$group': {'_id': '$category', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        categories = list(mongodb.db.trending_news.aggregate(pipeline))
        
        return {
            'total': total,
            'fact_checked': fact_checked,
            'categories': categories
        }
