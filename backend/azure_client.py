import os
import requests
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

class AzureAIClient:
    def __init__(self):
        self.endpoint = os.getenv("AZURE_AI_ENDPOINT")
        self.api_key = os.getenv("AZURE_AI_KEY")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "DeepSeek-R1")
        self.embed_model = os.getenv("EMBED_MODEL", "text-embedding-3-small")

        if not self.endpoint or not self.api_key:
            raise ValueError("Environment variables AZURE_AI_ENDPOINT and AZURE_AI_KEY are required.")

        # STRICT VALIDATION: Endpoint must end with /models
        if not self.endpoint.endswith("/models"):
            raise ValueError(f"AZURE_AI_ENDPOINT must end with '/models'. Current: {self.endpoint}")

        self.headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embeddings for a LIST of strings (Batching support).
        """
        # Construction: {endpoint}/embeddings?api-version=...
        # If endpoint ends with /models, we strip it? No, user says BASE is .../models.
        # But wait, endpoint format usually `https://<res>.openai.azure.com/openai/deployments/...` for SDK.
        # Foundry format: `https://<res>.services.ai.azure.com/models`
        # Chat: `POST /chat/completions` relative to... what?
        # User said: "Base endpoint MUST be .../models"
        # "Chat endpoint: POST /chat/completions?..."
        # So full URL: https://.../models/chat/completions
        
        url = f"{self.endpoint}/embeddings?api-version=2024-05-01-preview"
        payload = {
            "input": texts,
            "model": self.embed_model
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in sorted_data]
        except requests.exceptions.RequestException as e:
            print(f"Azure Embedding Request Failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Server Response: {e.response.text}")
            raise

    def chat_completion(self, messages: list[dict]) -> str:
        url = f"{self.endpoint}/chat/completions?api-version=2024-05-01-preview"
        payload = {
            "messages": messages,
            "model": self.deepseek_model,
            "max_tokens": 1500,
            "temperature": 0.6
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            # Clean DeepSeek <think> tags
            clean_content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()
            return clean_content
        except requests.exceptions.RequestException as e:
            print(f"Azure Chat Request Failed: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Server Response: {e.response.text}")
            raise
