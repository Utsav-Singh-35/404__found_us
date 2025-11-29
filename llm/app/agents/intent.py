"""
Agent 0: Intent Classification
Determines if user input is a fact-checkable claim or general chat
"""

import re
from typing import Dict, Any

def intent_agent(text: str) -> Dict[str, Any]:
    """
    Classify user intent: 'fact_check' or 'chat'
    
    Args:
        text: User input text
        
    Returns:
        {
            'intent': 'fact_check' or 'chat',
            'confidence': float (0-1),
            'reason': str
        }
    """
    
    text_lower = text.lower().strip()
    
    # Fact-check indicators
    fact_check_keywords = [
        'is it true', 'fact check', 'verify', 'real or fake',
        'is this real', 'did this happen', 'confirm', 'has',
        'breaking news', 'according to', 'reports say',
        'allegedly', 'claims that', 'announced', 'cancelled', 'canceled',
        'bank holiday', 'government', 'official', 'launch', 'satellite',
        'study shows', 'research', 'scientists', 'mumbai', 'india',
        'covid', 'vaccine', 'election', 'politics', 'earth is',
        'gets', 'will', 'to launch', 'hackathon', 'event'
    ]
    
    # Chat indicators
    chat_keywords = [
        'hello', 'hi', 'hey', 'how are you',
        'what can you do', 'help', 'thank',
        'who are you', 'what is your name',
        'good morning', 'good evening',
        'how does this work', 'explain'
    ]
    
    # Question words that often indicate fact-checking
    question_patterns = [
        r'\b(is|are|was|were|did|does|has|have)\b.*\?',
        r'\b(when|where|who|what|why|how)\b.*\?',
    ]
    
    # Check for greetings/chat
    for keyword in chat_keywords:
        if keyword in text_lower:
            return {
                'intent': 'chat',
                'confidence': 0.9,
                'reason': f'Detected greeting/chat keyword: {keyword}'
            }
    
    # Check for fact-check keywords
    fact_check_score = 0
    matched_keywords = []
    for keyword in fact_check_keywords:
        if keyword in text_lower:
            fact_check_score += 1
            matched_keywords.append(keyword)
    
    # Check for question patterns
    is_question = False
    for pattern in question_patterns:
        if re.search(pattern, text_lower):
            is_question = True
            fact_check_score += 0.5
            break
    
    # Check for dates (often in claims)
    date_patterns = [
        r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',  # 29-11-25, 29/11/2025
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
        r'\b\d{4}\b'  # Year
    ]
    
    has_date = False
    for pattern in date_patterns:
        if re.search(pattern, text_lower):
            has_date = True
            fact_check_score += 0.5
            break
    
    # Check for specific entities (locations, organizations)
    entities = [
        'mumbai', 'delhi', 'india', 'usa', 'china',
        'government', 'ministry', 'department',
        'bank', 'rbi', 'who', 'un'
    ]
    
    entity_count = sum(1 for entity in entities if entity in text_lower)
    if entity_count > 0:
        fact_check_score += entity_count * 0.3
    
    # Check length (very short messages are likely chat)
    word_count = len(text.split())
    if word_count < 3:
        return {
            'intent': 'chat',
            'confidence': 0.7,
            'reason': 'Message too short to be a claim'
        }
    
    # Decision logic
    if fact_check_score >= 1.0:  # Lowered threshold from 1.5 to 1.0
        confidence = min(0.95, 0.6 + (fact_check_score * 0.1))
        reason = f"Detected fact-check indicators (score: {fact_check_score:.1f})"
        if matched_keywords:
            reason += f": {', '.join(matched_keywords[:3])}"
        return {
            'intent': 'fact_check',
            'confidence': confidence,
            'reason': reason
        }
    
    # If it's a question with some context, likely fact-check
    if is_question and word_count > 5:
        return {
            'intent': 'fact_check',
            'confidence': 0.7,
            'reason': 'Question format with sufficient context'
        }
    
    # If it has dates or entities and reasonable length, likely fact-check
    if (has_date or entity_count > 0) and word_count >= 4:
        return {
            'intent': 'fact_check',
            'confidence': 0.75,
            'reason': 'Contains factual elements (dates/entities)'
        }
    
    # Default to chat for ambiguous cases
    return {
        'intent': 'chat',
        'confidence': 0.6,
        'reason': 'No strong fact-check indicators detected'
    }


async def generate_chat_response(text: str) -> str:
    """
    Generate a friendly chat response using OpenRouter API
    
    Args:
        text: User input
        
    Returns:
        Chat response string
    """
    import os
    import aiohttp
    
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY', '')
    
    if not api_key:
        # Fallback to simple responses if no API key
        return _generate_simple_response(text)
    
    # System prompt for chat mode
    system_prompt = """You are SatyaMatrix, a friendly AI fact-checking assistant. 
You help users verify claims and check information. When users greet you or ask general questions, 
respond warmly and guide them on how to use your fact-checking capabilities. 
Keep responses concise (2-3 sentences) and friendly."""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': os.getenv('OPENROUTER_SITE_URL', 'http://localhost:8000'),
                    'X-Title': os.getenv('OPENROUTER_SITE_NAME', 'SatyaMatrix')
                },
                json={
                    'model': os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini:free'),
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': text}
                    ],
                    'max_tokens': 150,
                    'temperature': 0.7
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content'].strip()
                else:
                    return _generate_simple_response(text)
    except Exception as e:
        print(f"⚠️  OpenRouter API error: {e}")
        return _generate_simple_response(text)


def _generate_simple_response(text: str) -> str:
    """Fallback simple responses when API is unavailable"""
    text_lower = text.lower().strip()
    
    if any(word in text_lower for word in ['hello', 'hi', 'hey']):
        return ("Hello! 👋 I'm SatyaMatrix, your AI fact-checking assistant. "
                "Share any claim you'd like me to verify!")
    
    if any(word in text_lower for word in ['help', 'what can you', 'how do you']):
        return ("I can verify factual claims, check news articles, and analyze information. "
                "Just share a claim or statement you'd like me to fact-check!")
    
    if 'thank' in text_lower:
        return "You're welcome! Feel free to ask me to fact-check anything. 😊"
    
    if any(phrase in text_lower for phrase in ['who are you', 'what are you', 'your name']):
        return ("I'm SatyaMatrix, an AI-powered fact-checking system. "
                "Share any claim you'd like me to verify!")
    
    return ("I'm here to help you fact-check claims! Share any statement you'd like me to verify.")
