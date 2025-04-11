"""LLM provider abstraction for multi-model support."""

import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Send a completion request and return the generated text."""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat completion request."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider (supports OpenAI, Azure, vLLM, etc.)."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.2,
        max_tokens: int = 4096
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
    
    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Single-turn completion via chat API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat(messages, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion."""
        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens)
        )
        return response.choices[0].message.content or ""


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.2,
        max_tokens: int = 4096
    ):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic")
        
        self.client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def complete(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Single-turn completion."""
        messages = [{"role": "user", "content": user_prompt}]
        response = self.client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat completion."""
        response = self.client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            temperature=kwargs.get("temperature", self.temperature),
            messages=messages
        )
        return response.content[0].text


def get_provider(provider_name: str, **kwargs) -> LLMProvider:
    """Factory function to get the appropriate LLM provider."""
    provider_name = provider_name.lower()
    if provider_name in ("openai", "azure"):
        return OpenAIProvider(**kwargs)
    elif provider_name == "anthropic":
        return AnthropicProvider(**kwargs)
    else:
        # Default to OpenAI-compatible
        return OpenAIProvider(**kwargs)
