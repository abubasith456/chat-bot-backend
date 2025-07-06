import requests
import json
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class NvidiaLLMClient:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.model_name = settings.MODEL_NAME
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def generate_response(self, message: str, max_tokens: int = 512) -> Optional[str]:
        """Generate response using NVIDIA LLM API"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble processing your request right now."

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return "Sorry, I'm currently unavailable. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return "An unexpected error occurred. Please try again."
