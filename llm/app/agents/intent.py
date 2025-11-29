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
        'is this real', 'did this happen', 'confirm',
        'breaking news', 'according to', 'reports say',
        'allegedly', 'claims that', 'announced',
        'bank holiday', 'government', 'official',
        'study shows', 'research', 'scientists',
        'covid', 'vaccine', 'election', 'politics'
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
    if fact_check_score >= 1.5:
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
    
    # Default to chat for ambiguous cases
    return {
        'intent': 'chat',
        'confidence': 0.6,
        'reason': 'No strong fact-check indicators detected'
    }


def generate_chat_response(text: str) -> str:
    """
    Generate a friendly chat response for non-fact-check queries
    
    Args:
        text: User input
        
    Returns:
        Chat response string
    """
    
    text_lower = text.lower().strip()
    
    # Greetings
    if any(word in text_lower for word in ['hello', 'hi', 'hey']):
        return ("Hello! 👋 I'm SatyaMatrix, your AI fact-checking assistant. "
                "I can help you verify claims, check news articles, and analyze information. "
                "Just share a claim or statement you'd like me to fact-check!")
    
    # Help/capabilities
    if any(word in text_lower for word in ['help', 'what can you', 'how do you']):
        return ("I can help you fact-check claims! Here's what I can do:\n\n"
                "✅ Verify factual claims and statements\n"
                "✅ Check news articles and social media posts\n"
                "✅ Analyze images for misinformation\n"
                "✅ Search for credible sources\n"
                "✅ Generate detailed fact-check reports\n\n"
                "Just share any claim or statement you'd like me to verify!")
    
    # Thank you
    if 'thank' in text_lower:
        return "You're welcome! Feel free to ask me to fact-check anything. 😊"
    
    # Who are you
    if any(phrase in text_lower for phrase in ['who are you', 'what are you', 'your name']):
        return ("I'm SatyaMatrix, an AI-powered fact-checking system. "
                "I use multiple verification agents to analyze claims and provide accurate information. "
                "Share any claim you'd like me to verify!")
    
    # Default response
    return ("I'm here to help you fact-check claims! If you have a statement, news article, "
            "or claim you'd like me to verify, just share it with me. "
            "For example: 'Is it true that...?' or 'Verify: [claim]'")
