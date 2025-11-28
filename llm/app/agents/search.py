"""
Agent 6: Web Search Agent
Purpose: Collect web evidence for claims
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse
from newspaper import Article
from app.config import settings

class WebSearchAgent:
    """Agent 6: Web search and evidence collection"""
    
    def __init__(self):
        self.serpapi_key = settings.serpapi_key
        
        # Trusted domains with reliability scores
        self.trusted_domains = {
            "reuters.com": 0.95,
            "apnews.com": 0.95,
            "bbc.com": 0.90,
            "bbc.co.uk": 0.90,
            "nytimes.com": 0.85,
            "washingtonpost.com": 0.85,
            "theguardian.com": 0.85,
            "cnn.com": 0.80,
            "npr.org": 0.90,
            "factcheck.org": 0.98,
            "snopes.com": 0.95,
            "politifact.com": 0.95,
            "who.int": 0.98,
            "cdc.gov": 0.98,
            "nih.gov": 0.98
        }
    
    async def search_and_collect(
        self,
        claim_text: str,
        entities: List[str],
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search web and collect evidence
        
        Returns list of evidence documents
        """
        
        # Build search queries
        queries = self._build_queries(claim_text, entities)
        
        # Search for each query
        all_urls = []
        for query in queries[:2]:  # Limit to 2 queries
            urls = await self._search_web(query, limit=5)
            all_urls.extend(urls)
        
        # Remove duplicates
        unique_urls = list(set(all_urls))[:max_results]
        
        if not unique_urls:
            print("⚠️  No URLs found from search")
            return []
        
        # Fetch and analyze each URL
        evidence_list = []
        for url in unique_urls:
            evidence = await self._fetch_and_analyze(url, claim_text)
            if evidence:
                evidence_list.append(evidence)
        
        return evidence_list
    
    def _build_queries(self, claim_text: str, entities: List[str]) -> List[str]:
        """Build multiple search queries"""
        
        queries = [
            f"{claim_text} fact check",  # Fact-check focused
        ]
        
        # Add entity-based query
        if entities:
            queries.append(f"{' '.join(entities[:3])} news")
        
        return queries
    
    async def _search_web(self, query: str, limit: int = 5) -> List[str]:
        """Search web using SerpAPI"""
        
        if not self.serpapi_key:
            print("⚠️  SerpAPI key not configured, using fallback URLs")
            # Return some default trusted sources
            return [
                "https://www.reuters.com",
                "https://www.bbc.com/news",
                "https://apnews.com"
            ]
        
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "num": limit,
            "engine": "google"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        print(f"⚠️  SerpAPI error: {resp.status}")
                        return []
                    
                    data = await resp.json()
                    
                    # Extract URLs from organic results
                    urls = []
                    for result in data.get('organic_results', []):
                        urls.append(result['link'])
                    
                    return urls
        
        except Exception as e:
            print(f"⚠️  Error searching web: {e}")
            return []
    
    async def _fetch_and_analyze(
        self,
        url: str,
        claim_text: str
    ) -> Optional[Dict]:
        """Fetch article and analyze"""
        
        try:
            # Try newspaper3k (faster)
            article = Article(url)
            article.download()
            article.parse()
            
            # Extract data
            title = article.title or "Untitled"
            text = article.text or ""
            publish_date = article.publish_date
            
            if not text or len(text) < 100:
                print(f"⚠️  Article too short or empty: {url}")
                return None
            
        except Exception as e:
            print(f"⚠️  Error fetching {url}: {e}")
            return None
        
        # Score reliability
        reliability = self._score_reliability(url, text)
        
        # Simple classification (will be improved in Phase 4 with LLM)
        classification = self._simple_classify(claim_text, text)
        
        return {
            "source_url": url,
            "title": title[:200],
            "snippet": text[:500],
            "published_date": publish_date,
            "reliability_score": reliability,
            "supports_claim": classification,
            "retrieved_at": datetime.utcnow()
        }
    
    def _score_reliability(self, url: str, text: str) -> float:
        """Score domain reliability"""
        
        domain = urlparse(url).netloc.replace('www.', '')
        
        # Check trusted domains
        if domain in self.trusted_domains:
            return self.trusted_domains[domain]
        
        # Default scoring
        score = 0.5  # Base score
        
        # HTTPS
        if url.startswith('https'):
            score += 0.1
        
        # Has citations
        if 'according to' in text.lower() or 'source:' in text.lower():
            score += 0.1
        
        # Length (longer articles tend to be more reliable)
        if len(text) > 1000:
            score += 0.05
        
        # Has author
        if 'by ' in text[:500].lower():
            score += 0.05
        
        return min(score, 1.0)
    
    def _simple_classify(self, claim: str, text: str) -> str:
        """
        Simple classification of evidence
        
        Will be replaced with LLM in Phase 4
        """
        
        claim_lower = claim.lower()
        text_lower = text.lower()
        
        # Count supporting/refuting keywords
        support_words = ['true', 'confirmed', 'verified', 'accurate', 'correct']
        refute_words = ['false', 'debunked', 'incorrect', 'misleading', 'fake']
        
        support_count = sum(1 for word in support_words if word in text_lower)
        refute_count = sum(1 for word in refute_words if word in text_lower)
        
        if refute_count > support_count:
            return "refutes"
        elif support_count > refute_count:
            return "supports"
        else:
            return "neutral"

# Create singleton
search_agent = WebSearchAgent()
