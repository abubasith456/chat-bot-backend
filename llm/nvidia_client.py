import requests
import httpx
import json
import logging
from typing import Optional
from config import settings
import subprocess

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
        self.text_from = "en"
        self.text_to = "de"

    def generate_response(self, message: str, max_tokens: int = 512) -> Optional[str]:
        """Synchronous: Generate response using NVIDIA LLM API"""
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": message}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False,
            }

            logger.info(f"Sending request to NVIDIA API: {json.dumps(payload)}")

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            logger.info(f"Received response from NVIDIA API: {response}")

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

    async def async_generate_response(
        self, message: str, max_tokens: int = 512
    ) -> Optional[str]:
        """Asynchronous: Generate response using NVIDIA LLM API"""
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False,
        }

        logger.info(f"Sending async request to NVIDIA API: {json.dumps(payload)}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )

            logger.info(f"Received async response from NVIDIA API: {response}")

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"API Error: {response.status_code} - {response.text}")
                return "Sorry, I'm having trouble processing your request right now."

        except httpx.RequestError as e:
            logger.error(f"Async request failed: {e}")
            return "Sorry, I'm currently unavailable. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected async error: {e}")
            return "An unexpected error occurred. Please try again."

    async def translate_text(
        self, text: str, text_from: str = "en", text_to: str = "de"
    ) -> str:
        command = [
            "python",
            "python-clients/scripts/nmt/nmt.py",
            "--server",
            "grpc.nvcf.nvidia.com:443",
            "--use-ssl",
            "--metadata",
            "function-id",
            "0778f2eb-b64d-45e7-acae-7dd9b9b35b4d",
            "--metadata",
            "authorization",
            f"Bearer {self.api_key}",
            "--text",
            f"{text}",
            "--source-language-code",
            f"{text_from}",
            "--target-language-code",
            f"{text_to}",
        ]
        try:
            print("Running translation command:", " ".join(command))
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print("Error running command:", e)
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            return "Error during translation"

    async def get_languages(self) -> dict:
        """List available translation models/languages using the Riva NMT CLI."""
        command = [
            "python",
            "python-clients/scripts/nmt/nmt.py",
            "--server",
            "grpc.nvcf.nvidia.com:443",
            "--use-ssl",
            "--metadata",
            "function-id",
            "0778f2eb-b64d-45e7-acae-7dd9b9b35b4d",
            "--metadata",
            "authorization",
            f"Bearer {self.api_key}",
            "--list-models",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print("STDOUT:", result.stdout)
            return self._parse_languages(result.stdout)
        except subprocess.CalledProcessError as e:
            print("Error running command:", e)
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)
            return {}

    def _parse_languages(self, raw_output: str):
        src_langs = set()
        tgt_langs = set()
        for line in raw_output.splitlines():
            line = line.strip()
            if line.startswith("src_lang:"):
                lang = line.split("src_lang:")[1].strip().strip('"')
                src_langs.add(lang)
            elif line.startswith("tgt_lang:"):
                lang = line.split("tgt_lang:")[1].strip().strip('"')
                tgt_langs.add(lang)
        return {"from_text": sorted(src_langs), "to_text": sorted(tgt_langs)}


nvidia_service = NvidiaLLMClient()
