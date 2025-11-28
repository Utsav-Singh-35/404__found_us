from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .chat_model import ChatMessage, Conversation
import json

@login_required
def chat_view(request, conversation_id=None):
    """Render the chat interface"""
    user_id = request.user.id
    
    print(f"\n🎯 chat_view called by user_id: {user_id}")
    print(f"   Conversation ID: {conversation_id}")
    
    # If no conversation_id, create a new one or get the latest
    if not conversation_id:
        conversations = Conversation.get_user_conversations(user_id, limit=1)
        if conversations:
            conversation_id = str(conversations[0]['_id'])
        else:
            # Create first conversation
            new_conv = Conversation.create_conversation(user_id, "New Chat")
            conversation_id = str(new_conv['_id'])
        
        return redirect('chat_conversation', conversation_id=conversation_id)
    
    # Get current conversation
    conversation = Conversation.get_conversation_by_id(conversation_id)
    if not conversation:
        print(f"   ❌ Conversation not found: {conversation_id}")
        return redirect('chat')
    
    if conversation['user_id'] != str(user_id):
        print(f"   ❌ Unauthorized access attempt!")
        print(f"      Conversation owner: {conversation['user_id']}")
        print(f"      Current user: {user_id}")
        return redirect('chat')
    
    print(f"   ✅ Access granted to conversation")
    
    # Get all user conversations for sidebar
    conversations = Conversation.get_user_conversations(user_id)
    
    context = {
        'current_conversation': conversation,
        'conversations': conversations,
        'conversation_id': conversation_id
    }
    
    return render(request, 'dashboards/chat.html', context)

@login_required
@csrf_exempt
def create_conversation(request):
    """Create a new conversation"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .mongodb import mongodb
        from .chat_model import Conversation
        
        user_id = request.user.id
        
        # Parse request body
        try:
            data = json.loads(request.body)
            title = data.get('title', 'New Chat')
        except:
            title = 'New Chat'
        
        # Check if MongoDB is connected
        if not mongodb.is_connected():
            return JsonResponse({
                'error': 'MongoDB not connected. Please check server console for connection status.'
            }, status=500)
        
        conversation = Conversation.create_conversation(user_id, title)
        
        if conversation:
            return JsonResponse({
                'success': True,
                'conversation': {
                    'id': str(conversation['_id']),
                    'title': conversation['title'],
                    'created_at': conversation['created_at'].isoformat()
                }
            })
        else:
            return JsonResponse({'error': 'Failed to create conversation'}, status=500)
    
    except Exception as e:
        import traceback
        print(f"Error creating conversation: {e}")
        traceback.print_exc()
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@login_required
def get_conversations(request):
    """Get all conversations for the current user"""
    try:
        from .chat_model import Conversation
        
        user_id = request.user.id
        limit = int(request.GET.get('limit', 50))
        skip = int(request.GET.get('skip', 0))
        
        print(f"\n📋 get_conversations called by user_id: {user_id} (type: {type(user_id)})")
        print(f"   Name: {request.user.name}")
        print(f"   Email: {request.user.email}")
        
        conversations = Conversation.get_user_conversations(user_id, limit=limit, skip=skip)
        
        # Convert ObjectId to string and format for frontend
        conversations_list = []
        for conv in conversations:
            conversations_list.append({
                'id': str(conv['_id']),  # Use 'id' instead of '_id' for consistency
                '_id': str(conv['_id']),  # Keep _id for backward compatibility
                'user_id': conv['user_id'],
                'title': conv['title'],
                'message_count': conv.get('message_count', 0),
                'created_at': conv['created_at'].isoformat(),
                'updated_at': conv['updated_at'].isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'conversations': conversations_list
        })
    
    except Exception as e:
        import traceback
        print(f"Error getting conversations: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def update_conversation(request, conversation_id):
    """Update conversation title"""
    if request.method not in ['PUT', 'POST']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .chat_model import Conversation
        
        user_id = request.user.id
        
        # Verify conversation belongs to user
        conversation = Conversation.get_conversation_by_id(conversation_id)
        if not conversation or conversation['user_id'] != str(user_id):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        data = json.loads(request.body)
        title = data.get('title')
        
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)
        
        success = Conversation.update_conversation(conversation_id, title=title)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Failed to update'}, status=500)
    
    except Exception as e:
        import traceback
        print(f"Error updating conversation: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def delete_conversation(request, conversation_id):
    """Delete a conversation and all its messages"""
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .chat_model import Conversation
        
        user_id = request.user.id
        
        # Verify conversation belongs to user
        conversation = Conversation.get_conversation_by_id(conversation_id)
        if not conversation or conversation['user_id'] != str(user_id):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        success = Conversation.delete_conversation(conversation_id)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Conversation not found'}, status=404)
    
    except Exception as e:
        import traceback
        print(f"Error deleting conversation: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def send_message(request, conversation_id):
    """Handle sending a new chat message"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .mongodb import mongodb
        from .chat_model import Conversation, ChatMessage
        
        user_id = request.user.id
        message_text = request.POST.get('message', '').strip()
        files = request.FILES.getlist('files')
        
        # Check if MongoDB is connected
        if not mongodb.is_connected():
            return JsonResponse({
                'error': 'MongoDB not connected. Please configure MONGODB_URI in .env file.'
            }, status=500)
        
        # Verify conversation belongs to user
        conversation = Conversation.get_conversation_by_id(conversation_id)
        if not conversation or conversation['user_id'] != str(user_id):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        messages_created = []
        
        # Handle text message
        if message_text:
            message = ChatMessage.create_message(
                conversation_id=conversation_id,
                user_id=user_id,
                sender='user',
                message_type='text',
                content=message_text
            )
            if message:
                messages_created.append({
                    'id': str(message['_id']),
                    'sender': 'user',
                    'type': 'text',
                    'content': message_text,
                    'created_at': message['created_at'].isoformat()
                })
        
        # Handle file uploads
        print(f"\n🔄 Starting file upload process...")
        print(f"   Total files to process: {len(files)}")
        
        if len(files) == 0:
            print(f"   ⚠️  No files received in request!")
            print(f"   Check if files are being sent from frontend")
        
        for idx, file in enumerate(files, 1):
            print(f"\n📎 Processing file {idx}/{len(files)}")
            print(f"   Name: {file.name}")
            print(f"   Type: {file.content_type}")
            print(f"   Size: {file.size} bytes")
            
            # Upload to Cloudinary
            print(f"   Uploading to Cloudinary...")
            upload_result = ChatMessage.upload_to_cloudinary(file)
            
            if upload_result:
                print(f"✅ Cloudinary upload successful: {upload_result['url']}")
                
                # Determine message type based on file
                content_type = file.content_type
                if content_type.startswith('image/'):
                    msg_type = 'image'
                elif content_type.startswith('video/'):
                    msg_type = 'video'
                else:
                    msg_type = 'document'
                
                # Create message in MongoDB
                message = ChatMessage.create_message(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    sender='user',
                    message_type=msg_type,
                    file_url=upload_result['url'],
                    file_type=upload_result['format'],
                    metadata=upload_result
                )
                
                if message:
                    print(f"✅ Message saved to MongoDB: {message['_id']}")
                    messages_created.append({
                        'id': str(message['_id']),
                        'sender': 'user',
                        'type': msg_type,
                        'file_url': upload_result['url'],
                        'file_name': file.name,
                        'created_at': message['created_at'].isoformat()
                    })
                else:
                    print(f"❌ Failed to save message to MongoDB")
            else:
                print(f"❌ Cloudinary upload failed for {file.name}")
        
        # Generate and save bot response
        if message_text:
            # TODO: Replace this with actual AI integration (OpenAI, etc.)
            bot_response_text = generate_bot_response(message_text)
            
            # Save bot response to MongoDB
            bot_message = ChatMessage.create_message(
                conversation_id=conversation_id,
                user_id=user_id,
                sender='bot',
                message_type='text',
                content=bot_response_text
            )
            
            if bot_message:
                messages_created.append({
                    'id': str(bot_message['_id']),
                    'sender': 'bot',
                    'type': 'text',
                    'content': bot_response_text,
                    'created_at': bot_message['created_at'].isoformat()
                })
                
                # Send email notification to all users
                try:
                    from .email_utils import send_chatbot_response_email
                    
                    # Extract title from the query (first 50 chars)
                    email_title = f"Fact-Check: {message_text[:50]}{'...' if len(message_text) > 50 else ''}"
                    
                    send_chatbot_response_email(
                        chat_message=message_text,
                        response_text=bot_response_text,
                        title=email_title,
                        author="SatyaMatrix AI",
                        description="A new fact-check response has been generated for your query. Check the details below."
                    )
                except Exception as email_error:
                    print(f"⚠️  Email notification failed: {email_error}")
        
        return JsonResponse({
            'success': True,
            'messages': messages_created
        })
    
    except Exception as e:
        print(f"Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': f'Server error: {str(e)}'
        }, status=500)

def generate_bot_response(user_message):
    """
    Generate bot response using deployed LLM API
    """
    import requests
    from django.conf import settings
    import time
    
    try:
        # Step 1: Submit claim to LLM API
        print(f"🔄 Submitting to LLM API: {user_message[:50]}...")
        
        response = requests.post(
            f"{settings.LLM_API_URL}/check",
            data={"text": user_message},
            timeout=120  # 120 seconds for submission (Render cold start can take 90s)
        )
        
        if response.status_code != 200:
            print(f"❌ LLM API submission failed: {response.status_code}")
            return "I'm having trouble processing your request. Please try again in a moment."
        
        data = response.json()
        submission_id = data.get('submission_id')
        
        if not submission_id:
            print(f"❌ No submission_id received")
            return "Failed to submit your claim for fact-checking."
        
        print(f"✅ Submission ID: {submission_id}")
        
        # Step 2: Poll for results (max 2 minutes)
        max_attempts = 24  # 24 * 5 seconds = 2 minutes
        
        for attempt in range(max_attempts):
            time.sleep(5)  # Wait 5 seconds between checks
            
            print(f"⏳ Polling attempt {attempt + 1}/{max_attempts}...")
            
            try:
                result_response = requests.get(
                    f"{settings.LLM_API_URL}/result/{submission_id}",
                    timeout=30
                )
                
                if result_response.status_code != 200:
                    continue
                
                result_data = result_response.json()
                status = result_data.get('status')
                
                print(f"📊 Status: {status}")
                
                if status == 'completed':
                    # Format response for chat
                    confidence = result_data.get('confidence', 0)
                    explanation = result_data.get('explanation', 'No explanation available.')
                    
                    confidence_pct = int(confidence * 100)
                    
                    # Determine confidence level emoji
                    if confidence_pct >= 70:
                        confidence_emoji = "🟢"
                    elif confidence_pct >= 40:
                        confidence_emoji = "🟡"
                    else:
                        confidence_emoji = "🔴"
                    
                    response_text = f"{confidence_emoji} **Fact-Check Result** (Confidence: {confidence_pct}%)\n\n"
                    response_text += explanation
                    
                    # Add sources if available
                    sources = result_data.get('sources', [])
                    if sources:
                        response_text += "\n\n**Sources:**\n"
                        for i, source in enumerate(sources[:3], 1):
                            source_title = source.get('title', 'Unknown')
                            source_url = source.get('url', '')
                            response_text += f"{i}. {source_title}\n"
                            if source_url:
                                response_text += f"   {source_url}\n"
                    
                    print(f"✅ Fact-check complete!")
                    return response_text
                
                elif status == 'error':
                    error_msg = result_data.get('explanation', 'Unknown error')
                    print(f"❌ Processing error: {error_msg}")
                    return f"Error processing your claim: {error_msg}"
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Polling error: {e}")
                continue
        
        # Timeout - still processing
        print(f"⏱️  Timeout after {max_attempts} attempts")
        return "Your claim is being processed. This is taking longer than expected. Please try asking again in a moment."
    
    except requests.exceptions.Timeout:
        print(f"⏱️  Request timeout")
        return "⏱️ The fact-checking service is waking up (this can take up to 2 minutes on first use). Please try your question again in a moment!"
    
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error")
        return "Cannot connect to the fact-checking service. Please check if the service is running."
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return "An error occurred while processing your request. Please try again."

@login_required
def get_messages(request, conversation_id):
    """Get chat history for a specific conversation"""
    try:
        from .mongodb import mongodb
        from .chat_model import Conversation, ChatMessage
        
        user_id = request.user.id
        limit = int(request.GET.get('limit', 100))
        skip = int(request.GET.get('skip', 0))
        
        # Verify conversation belongs to user
        conversation = Conversation.get_conversation_by_id(conversation_id)
        if not conversation or conversation['user_id'] != str(user_id):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        messages = ChatMessage.get_conversation_messages(conversation_id, limit=limit, skip=skip)
        
        # Convert ObjectId to string for JSON serialization
        messages_list = []
        for msg in messages:
            msg['_id'] = str(msg['_id'])
            msg['conversation_id'] = str(msg['conversation_id'])
            msg['created_at'] = msg['created_at'].isoformat()
            msg['updated_at'] = msg['updated_at'].isoformat()
            messages_list.append(msg)
        
        return JsonResponse({
            'success': True,
            'messages': messages_list
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
@csrf_exempt
def delete_message(request, message_id):
    """Delete a specific message"""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        from .chat_model import ChatMessage
        
        success = ChatMessage.delete_message(message_id)
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Message not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

@login_required
def get_conversation_history(request, conversation_id):
    """Get full conversation history"""
    try:
        from .mongodb import mongodb
        from .chat_model import Conversation, ChatMessage
        
        user_id = request.user.id
        limit = int(request.GET.get('limit', 100))
        
        # Verify conversation belongs to user
        conversation = Conversation.get_conversation_by_id(conversation_id)
        if not conversation or conversation['user_id'] != str(user_id):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        messages = ChatMessage.get_conversation_history(conversation_id, limit=limit)
        
        # Convert ObjectId to string for JSON serialization
        messages_list = []
        for msg in messages:
            msg['_id'] = str(msg['_id'])
            msg['conversation_id'] = str(msg['conversation_id'])
            msg['created_at'] = msg['created_at'].isoformat()
            msg['updated_at'] = msg['updated_at'].isoformat()
            messages_list.append(msg)
        
        return JsonResponse({
            'success': True,
            'messages': messages_list
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
