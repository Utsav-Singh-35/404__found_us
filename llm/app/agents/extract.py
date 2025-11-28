"""
Agent 2: Extraction Agent
Purpose: Extract claims from images (OCR), URLs (scraping), or text
"""

import requests
import re
from typing import Dict, Any
from newspaper import Article
from bs4 import BeautifulSoup
from app.config import settings

class ExtractionAgent:
    """
    Agent 2: Extract claims from various input types
    
    - Images: Use OCR.space API
    - URLs: Use newspaper3k or Playwright
    - Text: Parse and identify main claim
    """
    
    def __init__(self):
        self.ocr_api_key = settings.ocr_space_key
    
    def run(self, input_type: str, input_ref: str) -> Dict[str, Any]:
        """
        Extract claim based on input type
        
        Args:
            input_type: Type of input (image/url/text)
            input_ref: Reference to input (file path/url/text)
            
        Returns:
            Extracted claim and metadata
        """
        
        if input_type == "image":
            return self._extract_from_image(input_ref)
        elif input_type == "url":
            return self._extract_from_url(input_ref)
        elif input_type == "text":
            return self._extract_from_text(input_ref)
        else:
            raise ValueError(f"Unknown input type: {input_type}")
    
    def _extract_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        
        if not self.ocr_api_key:
            return {
                "claim_text": "[OCR not configured - add OCR_SPACE_KEY to .env]",
                "raw_content": "",
                "extracted_from": "ocr",
                "success": False
            }
        
        try:
            # Call OCR.space API
            with open(image_path, 'rb') as f:
                response = requests.post(
                    "https://api.ocr.space/parse/image",
                    files={"file": f},
                    data={
                        "apikey": self.ocr_api_key,
                        "language": "eng",
                        "isOverlayRequired": False,
                        "detectOrientation": True,
                        "scale": True,
                        "OCREngine": 2
                    },
                    timeout=60
                )
            
            if response.status_code != 200:
                raise Exception(f"OCR API error: {response.status_code}")
            
            data = response.json()
            
            if data.get('IsErroredOnProcessing'):
                error_msg = data.get('ErrorMessage', ['Unknown error'])[0]
                raise Exception(f"OCR processing error: {error_msg}")
            
            # Extract text
            raw_text = data['ParsedResults'][0]['ParsedText']
            
            # Extract best claim
            claim_text = self._select_best_claim(raw_text)
            
            return {
                "claim_text": claim_text,
                "raw_content": raw_text,
                "extracted_from": "ocr",
                "success": True,
                "metadata": {
                    "processing_time": data.get('ProcessingTimeInMilliseconds', 0)
                }
            }
        
        except Exception as e:
            return {
                "claim_text": f"[OCR extraction failed: {str(e)}]",
                "raw_content": "",
                "extracted_from": "ocr",
                "success": False,
                "error": str(e)
            }
    
    def _extract_from_url(self, url: str) -> Dict[str, Any]:
        """Extract article content from URL with multiple fallback methods"""
        
        # Method 1: Try newspaper3k with custom headers
        try:
            article = Article(url)
            
            # Set custom headers to avoid 403 errors
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            article.config.request_timeout = 15
            
            article.download()
            article.parse()
            
            if article.text and len(article.text.strip()) > 50:
                claim_text = article.title or self._select_best_claim(article.text)
                
                return {
                    "claim_text": claim_text,
                    "raw_content": article.text[:1000],
                    "extracted_from": "url",
                    "success": True,
                    "metadata": {
                        "title": article.title,
                        "authors": article.authors,
                        "publish_date": str(article.publish_date) if article.publish_date else None,
                        "method": "newspaper3k"
                    }
                }
        except Exception as e:
            print(f"⚠️  newspaper3k failed: {e}")
        
        # Method 2: Try requests + BeautifulSoup with browser headers
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find article content
            article_content = None
            title = None
            
            # Try common article selectors
            article_selectors = [
                'article',
                '[role="article"]',
                '.article-content',
                '.story-content',
                '.post-content',
                '.entry-content',
                'main',
                '#content'
            ]
            
            for selector in article_selectors:
                article_elem = soup.select_one(selector)
                if article_elem:
                    article_content = article_elem.get_text(separator=' ', strip=True)
                    if len(article_content) > 100:
                        break
            
            # If no article found, get all paragraphs
            if not article_content or len(article_content) < 100:
                paragraphs = soup.find_all('p')
                article_content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Try to find title
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            if article_content and len(article_content.strip()) > 50:
                claim_text = title or self._select_best_claim(article_content)
                
                return {
                    "claim_text": claim_text,
                    "raw_content": article_content[:1000],
                    "extracted_from": "url",
                    "success": True,
                    "metadata": {
                        "title": title,
                        "method": "beautifulsoup"
                    }
                }
        except Exception as e:
            print(f"⚠️  BeautifulSoup failed: {e}")
        
        # Method 3: Try Playwright (if available)
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
                page.wait_for_timeout(2000)  # Wait 2 seconds for dynamic content
                
                # Get title
                title = page.title()
                
                # Get article content
                article_content = page.evaluate('''() => {
                    // Remove unwanted elements
                    const unwanted = document.querySelectorAll('script, style, nav, footer, header, aside, .ad, .advertisement');
                    unwanted.forEach(el => el.remove());
                    
                    // Try to find article
                    const article = document.querySelector('article, [role="article"], main, .article-content, .story-content');
                    if (article) {
                        return article.innerText;
                    }
                    
                    // Fallback to all paragraphs
                    const paragraphs = Array.from(document.querySelectorAll('p'));
                    return paragraphs.map(p => p.innerText).join(' ');
                }''')
                
                browser.close()
                
                if article_content and len(article_content.strip()) > 50:
                    claim_text = title or self._select_best_claim(article_content)
                    
                    return {
                        "claim_text": claim_text,
                        "raw_content": article_content[:1000],
                        "extracted_from": "url",
                        "success": True,
                        "metadata": {
                            "title": title,
                            "method": "playwright"
                        }
                    }
        except Exception as e:
            print(f"⚠️  Playwright failed: {e}")
        
        # All methods failed
        return {
            "claim_text": f"[Unable to extract content from URL. The website may be blocking automated access. Please try copying the article text directly.]",
            "raw_content": "",
            "extracted_from": "url",
            "success": False,
            "error": "All extraction methods failed"
        }
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract claim from plain text"""
        
        claim_text = self._select_best_claim(text)
        
        return {
            "claim_text": claim_text,
            "raw_content": text,
            "extracted_from": "text",
            "success": True,
            "metadata": {
                "length": len(text),
                "word_count": len(text.split())
            }
        }
    
    def _select_best_claim(self, text: str) -> str:
        """
        Select the most likely claim from text
        
        Heuristics:
        - Prefer sentences with named entities
        - Prefer sentences with numbers/dates
        - Prefer sentences with assertion verbs
        - Prefer length 10-30 words
        """
        
        if not text or len(text.strip()) == 0:
            return "[No text found]"
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:200]  # Return first 200 chars
        
        # If only one sentence, return it
        if len(sentences) == 1:
            return sentences[0]
        
        # Score each sentence
        scored_sentences = []
        
        for sentence in sentences:
            score = 0
            words = sentence.split()
            word_count = len(words)
            
            # Length score (prefer 10-30 words)
            if 10 <= word_count <= 30:
                score += 3
            elif 5 <= word_count < 10 or 30 < word_count <= 50:
                score += 1
            
            # Has numbers or dates
            if re.search(r'\d', sentence):
                score += 2
            
            # Has assertion verbs
            assertion_verbs = ['is', 'are', 'will', 'has', 'have', 'was', 'were', 
                             'announced', 'confirmed', 'says', 'said']
            if any(verb in sentence.lower() for verb in assertion_verbs):
                score += 2
            
            # Has capitalized words (likely named entities)
            capitalized = len([w for w in words if w and w[0].isupper() and len(w) > 1])
            score += min(capitalized, 3)
            
            # Avoid questions
            if sentence.endswith('?'):
                score -= 2
            
            # Avoid very short sentences
            if word_count < 5:
                score -= 3
            
            scored_sentences.append((score, sentence))
        
        # Return highest scoring sentence
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        return scored_sentences[0][1] if scored_sentences else text[:200]

# Create singleton instance
extraction_agent = ExtractionAgent()
