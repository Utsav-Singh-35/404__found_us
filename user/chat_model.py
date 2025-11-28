from datetime import datetime
from bson import ObjectId
from .mongodb import mongodb
import cloudinary
import cloudinary.uploader
from django.conf import settings

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

class Conversation:
    """Model for managing chat conversations"""
    
    @staticmethod
    def create_conversation(user_id, title="New Chat"):
        """Create a new conversation for a user"""
        if not mongodb.is_connected():
            return None
        
        conversation = {
            'user_id': str(user_id),
            'title': title,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'message_count': 0
        }
        
        result = mongodb.db.conversations.insert_one(conversation)
        conversation['_id'] = result.inserted_id
        return conversation
    
    @staticmethod
    def get_user_conversations(user_id, limit=50, skip=0):
        """Get all conversations for a user"""
        if not mongodb.is_connected():
            return []
        
        # Convert user_id to string for consistent comparison
        user_id_str = str(user_id)
        
        # Debug logging
        print(f"\n🔍 Fetching conversations for user_id: {user_id_str}")
        
        conversations = mongodb.db.conversations.find(
            {'user_id': user_id_str}
        ).sort('updated_at', -1).skip(skip).limit(limit)
        
        conversations_list = list(conversations)
        print(f"   Found {len(conversations_list)} conversations for this user")
        
        return conversations_list
    
    @staticmethod
    def get_conversation_by_id(conversation_id):
        """Get a specific conversation"""
        if not mongodb.is_connected():
            return None
        
        return mongodb.db.conversations.find_one({'_id': ObjectId(conversation_id)})
    
    @staticmethod
    def update_conversation(conversation_id, title=None):
        """Update conversation details"""
        if not mongodb.is_connected():
            return False
        
        update_data = {'updated_at': datetime.utcnow()}
        if title:
            update_data['title'] = title
        
        result = mongodb.db.conversations.update_one(
            {'_id': ObjectId(conversation_id)},
            {'$set': update_data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def delete_conversation(conversation_id):
        """Delete a conversation and all its messages"""
        if not mongodb.is_connected():
            return False
        
        # Delete all messages in this conversation
        messages = ChatMessage.get_conversation_messages(conversation_id)
        for msg in messages:
            ChatMessage.delete_message(str(msg['_id']))
        
        # Delete the conversation
        result = mongodb.db.conversations.delete_one({'_id': ObjectId(conversation_id)})
        return result.deleted_count > 0
    
    @staticmethod
    def increment_message_count(conversation_id):
        """Increment message count and update timestamp"""
        if not mongodb.is_connected():
            return False
        
        result = mongodb.db.conversations.update_one(
            {'_id': ObjectId(conversation_id)},
            {
                '$inc': {'message_count': 1},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        return result.modified_count > 0

class ChatMessage:
    """Model for storing chat messages in MongoDB"""
    
    @staticmethod
    def create_message(conversation_id, user_id, sender='user', message_type='text', content=None, file_url=None, file_type=None, metadata=None):
        """
        Create a new chat message
        
        Args:
            conversation_id: ID of the conversation this message belongs to
            user_id: User ID who sent the message
            sender: 'user' or 'bot'
            message_type: 'text', 'image', 'video', 'document'
            content: Text content (for text messages)
            file_url: Cloudinary URL (for file messages)
            file_type: File extension/type
            metadata: Additional metadata (file size, dimensions, etc.)
        """
        if not mongodb.is_connected():
            return None
        
        message = {
            'conversation_id': str(conversation_id),
            'user_id': str(user_id),
            'sender': sender,
            'message_type': message_type,
            'content': content,
            'file_url': file_url,
            'file_type': file_type,
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        try:
            result = mongodb.db.chat_messages.insert_one(message)
            message['_id'] = result.inserted_id
            
            print(f"✅ Message inserted into MongoDB:")
            print(f"   Collection: chat_messages")
            print(f"   Message ID: {result.inserted_id}")
            print(f"   Conversation ID: {conversation_id}")
            print(f"   Message Type: {message_type}")
            print(f"   File URL: {file_url}")
            
            # Update conversation's message count and timestamp
            Conversation.increment_message_count(conversation_id)
            
            return message
        except Exception as e:
            print(f"❌ Error inserting message into MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def upload_to_cloudinary(file, resource_type='auto'):
        """
        Upload file to Cloudinary
        
        Args:
            file: File object from request.FILES
            resource_type: 'image', 'video', 'raw' (for documents), or 'auto'
        
        Returns:
            dict with url, public_id, and metadata
        """
        try:
            print(f"🔄 Starting Cloudinary upload for: {file.name}")
            print(f"   Content Type: {file.content_type}")
            print(f"   File Size: {file.size} bytes")
            
            # Determine resource type based on file
            if resource_type == 'auto':
                content_type = file.content_type
                if content_type.startswith('image/'):
                    resource_type = 'image'
                elif content_type.startswith('video/'):
                    resource_type = 'video'
                else:
                    resource_type = 'raw'  # For documents, PDFs, etc.
            
            print(f"   Resource Type: {resource_type}")
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                resource_type=resource_type,
                folder='chat_files'
            )
            
            print(f"✅ Cloudinary upload successful!")
            print(f"   URL: {upload_result.get('secure_url')}")
            print(f"   Public ID: {upload_result.get('public_id')}")
            
            return {
                'url': upload_result.get('secure_url'),
                'public_id': upload_result.get('public_id'),
                'format': upload_result.get('format'),
                'size': upload_result.get('bytes'),
                'width': upload_result.get('width'),
                'height': upload_result.get('height'),
                'resource_type': upload_result.get('resource_type')
            }
        except Exception as e:
            print(f"❌ Cloudinary upload error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def get_conversation_messages(conversation_id, limit=100, skip=0):
        """Get all messages in a specific conversation"""
        if not mongodb.is_connected():
            return []
        
        messages = mongodb.db.chat_messages.find(
            {'conversation_id': str(conversation_id)}
        ).sort('created_at', 1).skip(skip).limit(limit)
        
        return list(messages)
    
    @staticmethod
    def get_user_messages(user_id, limit=50, skip=0):
        """Get recent messages for a specific user across all conversations"""
        if not mongodb.is_connected():
            return []
        
        messages = mongodb.db.chat_messages.find(
            {'user_id': str(user_id)}
        ).sort('created_at', -1).skip(skip).limit(limit)
        
        return list(messages)
    
    @staticmethod
    def get_message_by_id(message_id):
        """Get a specific message by ID"""
        if not mongodb.is_connected():
            return None
        
        return mongodb.db.chat_messages.find_one({'_id': ObjectId(message_id)})
    
    @staticmethod
    def delete_message(message_id):
        """Delete a message and its associated Cloudinary file"""
        if not mongodb.is_connected():
            return False
        
        message = ChatMessage.get_message_by_id(message_id)
        if not message:
            return False
        
        # Delete from Cloudinary if it has a file
        if message.get('metadata', {}).get('public_id'):
            try:
                cloudinary.uploader.destroy(
                    message['metadata']['public_id'],
                    resource_type=message['metadata'].get('resource_type', 'image')
                )
            except Exception as e:
                print(f"Error deleting from Cloudinary: {e}")
        
        # Delete from MongoDB
        result = mongodb.db.chat_messages.delete_one({'_id': ObjectId(message_id)})
        return result.deleted_count > 0
    
    @staticmethod
    def update_message(message_id, content):
        """Update message content (text only)"""
        if not mongodb.is_connected():
            return False
        
        result = mongodb.db.chat_messages.update_one(
            {'_id': ObjectId(message_id)},
            {
                '$set': {
                    'content': content,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def get_conversation_history(conversation_id, limit=100):
        """Get full conversation history for a specific conversation"""
        return ChatMessage.get_conversation_messages(conversation_id, limit=limit)
    
    @staticmethod
    def search_messages(user_id, query, limit=50):
        """Search messages by content"""
        if not mongodb.is_connected():
            return []
        
        messages = mongodb.db.chat_messages.find(
            {
                'user_id': str(user_id),
                'content': {'$regex': query, '$options': 'i'}
            }
        ).sort('created_at', -1).limit(limit)
        
        return list(messages)
