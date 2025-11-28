from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId

class MongoDBManager:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        if not settings.MONGODB_URI:
            print("⚠️  MongoDB not configured. Using SQLite only.")
            self._db = None
            return
            
        try:
            self._client = MongoClient(settings.MONGODB_URI)
            self._db = self._client[settings.MONGODB_NAME]
            # Test connection
            self._client.server_info()
            print("✅ MongoDB connected successfully!")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            print("⚠️  Continuing with SQLite only.")
            self._db = None
    
    @property
    def db(self):
        return self._db
    
    @property
    def users(self):
        if self._db is None:
            return None
        return self._db.users
    
    @property
    def conversations(self):
        if self._db is None:
            return None
        return self._db.conversations
    
    @property
    def chat_messages(self):
        if self._db is None:
            return None
        return self._db.chat_messages
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        return self._db is not None
    
    def close(self):
        if self._client:
            self._client.close()

# Global instance
mongodb = MongoDBManager()
