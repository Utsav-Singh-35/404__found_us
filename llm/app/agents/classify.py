"""
Agent 1: Classify Agent
Purpose: Determine input type (image, URL, or text)
"""

from typing import Dict, Any

class ClassifyAgent:
    """
    Agent 1: Classify input type
    
    Determines whether the input is:
    - image (requires OCR)
    - url (requires web scraping)
    - text (direct processing)
    """
    
    def run(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the input type
        
        Args:
            submission: Submission document from MongoDB
            
        Returns:
            Classification result with metadata
        """
        
        input_type = submission.get('input_type')
        input_ref = submission.get('input_ref')
        
        result = {
            'input_type': input_type,
            'input_ref': input_ref,
            'metadata': {}
        }
        
        # Add type-specific metadata
        if input_type == 'image':
            result['metadata'] = {
                'requires_ocr': True,
                'file_path': input_ref
            }
        elif input_type == 'url':
            result['metadata'] = {
                'requires_scraping': True,
                'url': input_ref,
                'domain': self._extract_domain(input_ref)
            }
        elif input_type == 'text':
            result['metadata'] = {
                'length': len(input_ref),
                'word_count': len(input_ref.split())
            }
        
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc
        except:
            return ""

# Create singleton instance
classify_agent = ClassifyAgent()
