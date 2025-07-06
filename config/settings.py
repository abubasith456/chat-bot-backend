import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
    NVIDIA_BASE_URL = os.getenv(
        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
    )
    MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.1-8b-instruct")
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", 8888))

    @classmethod
    def validate(cls):
        if not cls.NVIDIA_API_KEY:
            raise ValueError("NVIDIA_API_KEY environment variable is required")
        return True


settings = Settings()
