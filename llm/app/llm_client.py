import requests
import json
from app.config import settings

class LLMClient:
    """
    Universal LLM client supporting OpenRouter, OpenAI, and Gemini
    """
    
    def __init__(self):
        self.provider = self._detect_provider()
    
    def _detect_provider(self):
        """Detect which LLM provider to use based on available API keys"""
        if settings.openrouter_api_key:
            return "openrouter"
        elif settings.openai_api_key:
            return "openai"
        elif settings.gemini_api_key:
            return "gemini"
        else:
            return None
    
    def generate(self, prompt: str, system_prompt: str = None, response_format: str = None):
        """
        Generate text using available LLM provider
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            response_format: "json" for JSON output (optional)
        
        Returns:
            Generated text
        """
        
        if self.provider == "openrouter":
            return self._call_openrouter(prompt, system_prompt, response_format)
        elif self.provider == "openai":
            return self._call_openai(prompt, system_prompt, response_format)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, system_prompt, response_format)
        else:
            raise Exception("No LLM API key configured. Please add OPENROUTER_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY to .env")
    
    def _call_openrouter(self, prompt: str, system_prompt: str = None, response_format: str = None):
        """Call OpenRouter API with support for free models"""
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": settings.openrouter_model,
            "messages": messages
        }
        
        # Add JSON mode if requested (not supported by all free models)
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        
        # Enable reasoning for free models that support it
        if ":free" in settings.openrouter_model:
            payload["extra_body"] = {
                "reasoning": {"enabled": True}
            }
        
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "HTTP-Referer": settings.openrouter_site_url,
                    "X-Title": settings.openrouter_site_name,
                    "Content-Type": "application/json"
                },
                data=json.dumps(payload),
                timeout=120
            )
            
            response.raise_for_status()
            data = response.json()
            
            return data['choices'][0]['message']['content']
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenRouter API error: {e}")
    
    def _call_openai(self, prompt: str, system_prompt: str = None, response_format: str = None):
        """Call OpenAI API directly"""
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            kwargs = {
                "model": "gpt-4",
                "messages": messages
            }
            
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**kwargs)
            
            return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def _call_gemini(self, prompt: str, system_prompt: str = None, response_format: str = None):
        """Call Google Gemini API"""
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-pro")
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = model.generate_content(full_prompt)
            
            return response.text
        
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

# Create singleton instance
llm_client = LLMClient()


def get_llm_response(prompt: str, system_prompt: str = None, temperature: float = 0.7, response_format: str = None):
    """
    Wrapper function for backward compatibility
    
    Args:
        prompt: User prompt
        system_prompt: System prompt (optional)
        temperature: Temperature (not used in current implementation)
        response_format: "json" for JSON output
    
    Returns:
        Generated text
    """
    return llm_client.generate(prompt, system_prompt, response_format)


def test_llm():
    """Test LLM connection"""
    try:
        response = llm_client.generate(
            prompt="Say 'Hello, I am working!' in one sentence.",
            system_prompt="You are a helpful assistant."
        )
        print(f"✅ LLM is working! Provider: {llm_client.provider}")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False


if __name__ == "__main__":
    # Test the LLM client
    test_llm()
