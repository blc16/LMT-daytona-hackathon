import httpx
import json
from typing import Any, Dict, List, Type, TypeVar, Optional
from pydantic import BaseModel
from backend.config import settings

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    """
    Simple wrapper for OpenRouter to generate structured outputs.
    """
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/blc16/LMT-daytona-hackathon",
        }

    async def generate_json(self, model: str, system_prompt: str, user_prompt: str, schema: Type[T]) -> T:
        """
        Generate a response adhering to a Pydantic schema.
        """
        # Construct the JSON schema for the response
        json_schema = schema.model_json_schema()
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}, # Enforce JSON mode if model supports it
            "temperature": 0.7
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            if response.status_code != 200:
                error_text = response.text
                print(f"OpenRouter API Error {response.status_code}: {error_text}")
                print(f"API Key present: {bool(self.api_key)}")
                print(f"API Key length: {len(self.api_key) if self.api_key else 0}")
                print(f"Request payload model: {payload.get('model')}")
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            
            # Clean up potential markdown blocks if the model adds them
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
                
            return schema.model_validate_json(content)

    async def generate_text(self, model: str, system_prompt: str, user_prompt: str) -> str:
        """
        Generate plain text response (for code generation, etc).
        """
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

