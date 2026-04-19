"""
LLM Service for Ollama integration.
Handles communication with locally running Gemma4 model.
"""
import httpx
from typing import Optional


class OllamaLLMService:
    """Service for generating responses using local Ollama models."""
    
    def __init__(
        self,
        base_url: str = "https://wackiness-mannish-celibate.ngrok-free.dev",
        model: str = "gemma4:latest",
        timeout: int = 120,
        max_tokens: int = 4096
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response using the Ollama model.
        """
        full_prompt = self._build_prompt(prompt, context)
        
        # Use provided max_tokens or default
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        print(f"🔍 Prompt length: {len(full_prompt)} chars")
        
        # Use chat endpoint
        answer = await self._generate_with_chat_endpoint(full_prompt, temperature, tokens)
        
        if answer:
            return answer.strip()
        
        return "I'm having trouble generating a response right now. Please try again in a moment."
    
    async def _generate_with_chat_endpoint(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Use the /api/chat endpoint."""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            print(f"🔍 Sending to Ollama: {len(prompt)} chars (max_tokens={max_tokens})")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                message = result.get("message", {})
                content = message.get("content", "")
                
                # If content is empty but thinking exists, use thinking
                if not content and "thinking" in message:
                    content = message.get("thinking", "")
                    print(f"⚠️ Using 'thinking' field: {len(content)} chars")
                
                # Check if response was truncated
                if result.get("done_reason") == "length":
                    print(f"⚠️ Response truncated - consider increasing max_tokens")
                
                if content:
                    print(f"✅ Ollama returned: {len(content)} chars")
                else:
                    print(f"⚠️ Ollama returned empty response")
                    print(f"   Done reason: {result.get('done_reason')}")
                    print(f"   Eval count: {result.get('eval_count')}")
                
                return content
                
        except httpx.TimeoutException:
            print("❌ Ollama request timed out")
            return ""
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            return ""
    
    def _build_prompt(self, user_question: str, telemetry_context: Optional[str]) -> str:
        """Build a prompt for battery advice."""
        
        if telemetry_context and "No battery data available" not in telemetry_context:
            return f"""You are Battery AI, an expert assistant for smartphone battery health and optimization.

USER QUESTION: {user_question}

USER'S BATTERY DATA (LAST 7 DAYS):
{telemetry_context}

Based on this data, provide a helpful, specific response in 2-4 sentences. Be concise and actionable. Reference the user's actual data.

YOUR RESPONSE:"""
        else:
            return f"""You are Battery AI, an expert assistant for smartphone battery health.

USER QUESTION: {user_question}

Provide helpful battery advice in 2-3 sentences.

YOUR RESPONSE:"""
    
    async def health_check(self) -> bool:
        """Check if Ollama service is accessible."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False